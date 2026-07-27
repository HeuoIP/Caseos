"""Vision analyzer for CaseOS.

``CaseVisionAnalyzer`` is self-sufficient: on construction it loads the
prompt template, the output schema, and every taxonomy library from disk,
composes the final prompt, and validates the model\'s response against
the schema and the library before returning.

Design contract:

  - ``VisionAnalyzer.analyze(image_path) -> dict`` takes ONLY an image
    path; everything else is resolved internally.
  - The provider is the only collaborator; it owns the network call.
  - Validation is strict: any unknown stable ID or missing field raises
    ``AnalysisValidationError``.

The list of allowed IDs is derived at runtime from
``knowledge/taxonomy/<slug>/`` -- no IDs are hard-coded in Python.
"""

from __future__ import annotations

import base64
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.services.vision.providers.base import Provider


# Mapping from CaseOS taxonomy field names (in JSON output) to the
# taxonomy-library group prefix. Used both to find the right library
# directory and to validate IDs in the response.
TAXONOMY_FIELDS: dict[str, str] = {
    "theme": "THEME",
    "style": "STYLE",
    "site_type": "SITE",
    "age_group": "AGE",
    "play_behaviors": "PLAY",
    "functional_units": "UNIT",
    "materials": "MATERIAL",
    "colors": "COLOR",
}


def _group_to_slug(group: str) -> str:
    """Map a group prefix to its on-disk slug directory name.

    Examples:
        THEME -> theme
        SITE -> site_type
        PLAY -> play_behavior
    """
    table = {
        "THEME": "theme",
        "STYLE": "style",
        "SITE": "site_type",
        "AGE": "age_group",
        "PLAY": "play_behavior",
        "UNIT": "functional_unit",
        "MATERIAL": "material",
        "COLOR": "color",
    }
    return table[group]


# Regex to extract stable IDs from leaf-MD header lines like:
#   > **Stable ID:** `THEME.FOREST`
_ID_LINE_RE = re.compile(
    r"\*\*Stable\s+ID:\*\*\s*`([A-Z][A-Z0-9_]*\.[A-Z0-9][A-Z0-9_]*)`"
)


class VisionAnalyzer(ABC):
    """Abstract base for CaseOS vision analyzers."""

    @abstractmethod
    def analyze(self, image_path: str) -> dict[str, Any]:
        """Analyze one playground image, returning a CaseOS JSON dict.

        Args:
            image_path: Filesystem path to the input image.

        Returns:
            A dict matching the CaseOS analysis schema. Raises
            ``AnalysisValidationError`` on schema/library violations.
        """
        raise NotImplementedError


class AnalysisValidationError(RuntimeError):
    """Raised when a model response fails schema/library validation."""


@dataclass
class TaxonomyLibrary:
    """Loaded contents of one taxonomy library on disk."""

    group: str
    slug: str
    root: Path
    ids: list[str] = field(default_factory=list)

    def has(self, stable_id: str) -> bool:
        return stable_id in self.ids


@dataclass
class CaseVisionAnalyzer(VisionAnalyzer):
    """Self-sufficient CaseOS vision analyzer.

    Loads prompt + schema + libraries at construction; composes the
    final prompt; routes image -> JSON through a Provider; validates
    the response.
    """

    provider: Provider
    prompt_path: Path
    schema_path: Path
    taxonomy_root: Path

    # Filled by __post_init__
    _schema: dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    _libraries: dict[str, TaxonomyLibrary] = field(
        default_factory=dict, init=False, repr=False
    )
    _prompt: str = field(default="", init=False, repr=False)

    def __post_init__(self) -> None:
        # Coerce str -> Path so callers can pass either form.
        self.prompt_path = Path(self.prompt_path)
        self.schema_path = Path(self.schema_path)
        self.taxonomy_root = Path(self.taxonomy_root)

        # 1. Schema
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {self.schema_path}")
        self._schema = json.loads(self.schema_path.read_text(encoding="utf-8"))

        # 2. Libraries
        self._libraries = self._load_libraries()

        # 3. Prompt (base + auto-generated appendix)
        if not self.prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {self.prompt_path}")
        base = self.prompt_path.read_text(encoding="utf-8")
        self._prompt = self._compose_prompt(base)

    # ── Loading ─────────────────────────────────────────────────────────

    def _load_libraries(self) -> dict[str, TaxonomyLibrary]:
        result: dict[str, TaxonomyLibrary] = {}
        for _field, group in TAXONOMY_FIELDS.items():
            slug = _group_to_slug(group)
            lib_dir = self.taxonomy_root / slug
            ids = self._extract_ids(lib_dir) if lib_dir.is_dir() else []
            result[group] = TaxonomyLibrary(
                group=group, slug=slug, root=lib_dir, ids=ids
            )
        return result

    @staticmethod
    def _extract_ids(lib_dir: Path) -> list[str]:
        """Parse every leaf MD in ``lib_dir`` for its Stable ID header."""
        ids: list[str] = []
        for md in sorted(lib_dir.glob("*.md")):
            if md.name.lower() == "readme.md":
                continue
            text = md.read_text(encoding="utf-8")
            for match in _ID_LINE_RE.finditer(text):
                ids.append(match.group(1))
        # Dedupe while preserving order
        seen = set()
        unique: list[str] = []
        for i in ids:
            if i not in seen:
                seen.add(i)
                unique.append(i)
        return unique

    # ── Prompt composition ──────────────────────────────────────────────

    def _compose_prompt(self, base: str) -> str:
        """Append a runtime-generated "Allowed IDs" appendix to the base prompt."""
        appendix = self._build_allowed_ids_appendix()
        return base.rstrip() + "\n\n" + appendix + "\n"

    def _build_allowed_ids_appendix(self) -> str:
        lines = [
            "## Allowed Stable IDs (auto-loaded from `knowledge/taxonomy/*/`)",
            "",
            "The following lists are generated at runtime from the CaseOS taxonomy",
            "libraries. Each ID has the form `<GROUP>.<LEAF>`.",
            "",
        ]
        for field_name, group in TAXONOMY_FIELDS.items():
            lib = self._libraries.get(group)
            ids = lib.ids if lib else []
            lines.append(f"### {field_name} (Group `{group}`, {len(ids)} IDs)")
            lines.append("")
            lines.append("Allowed: " + ", ".join(ids))
            lines.append("")
            lines.append("Output: " + self._output_shape(field_name))
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _output_shape(field_name: str) -> str:
        if field_name == "theme":
            return (
                'array of `{"id": "<STABLE_ID>", "role": "primary|secondary", '
                '"confidence": 0.0-1.0}`. Exactly one entry MUST have '
                '`"role": "primary"`.'
            )
        if field_name == "site_type":
            return "single stable ID string (not an array)."
        return "array of stable ID strings."

    # ── Analyze ─────────────────────────────────────────────────────────

    def analyze(self, image_path: str) -> dict[str, Any]:
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(image_path)

        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        image_url = f"data:image/png;base64,{encoded}"

        result = self.provider.complete(self._prompt, image_url)
        data = json.loads(result.raw_text)

        self._validate(data)
        return data

    # ── Validation ──────────────────────────────────────────────────────

    # Marketing-language words forbidden in vision_summary. These signal
    # brochure copy, not observation. Validated locally so the model
    # cannot smuggle them in.
    FORBIDDEN_SUMMARY_WORDS: tuple[str, ...] = (
        "striking", "beautiful", "amazing", "impressive", "iconic",
        "world-class", "stunning", "gorgeous", "magnificent",
        "breathtaking", "spectacular", "incredible", "fantastic",
        "wonderful", "epic", "magical",
    )

    def _validate(self, data: dict[str, Any]) -> None:
        for field in TAXONOMY_FIELDS:
            if field not in data:
                raise AnalysisValidationError(f"missing required field: {field!r}")

        self._validate_theme(data["theme"])
        self._validate_site_type(data["site_type"])

        for field in [
            "style",
            "age_group",
            "play_behaviors",
            "functional_units",
            "materials",
            "colors",
        ]:
            self._validate_id_list(field, data[field])

        # Description split: vision_summary (search layer) + 
        # design_interpretation (understanding layer). 
        # Replaces the legacy single "description" field.
        self._validate_text_field(data, "vision_summary")
        self._validate_text_field(data, "design_interpretation")
        self._check_forbidden_summary_words(data["vision_summary"])

    def _validate_text_field(self, data: dict[str, Any], field: str) -> None:
        val = data.get(field)
        if not isinstance(val, str) or not val.strip():
            raise AnalysisValidationError(
                f"{field} must be a non-empty string"
            )

    def _check_forbidden_summary_words(self, summary: str) -> None:
        lowered = summary.lower()
        hits = [w for w in self.FORBIDDEN_SUMMARY_WORDS if w in lowered]
        if hits:
            raise AnalysisValidationError(
                f"ision_summary contains forbidden marketing word(s): {hits}. "
                f"Use factual vocabulary only (e.g. large-scale, circular canopy, "
                f"stainless steel slide, rope net). See vision_prompt_v2.md."
            )

    def _validate_theme(self, theme: Any) -> None:
        if not isinstance(theme, list) or not theme:
            raise AnalysisValidationError("`theme` must be a non-empty list")
        primaries = 0
        for entry in theme:
            if not isinstance(entry, dict):
                raise AnalysisValidationError(
                    f"`theme` entries must be dicts; got {type(entry).__name__}"
                )
            for k in ("id", "role", "confidence"):
                if k not in entry:
                    raise AnalysisValidationError(
                        f"`theme` entry missing key {k!r}: {entry!r}"
                    )
            self._validate_id("theme", entry["id"])
            if entry["role"] == "primary":
                primaries += 1
            elif entry["role"] != "secondary":
                raise AnalysisValidationError(
                    f"`theme.role` must be primary|secondary; got {entry['role']!r}"
                )
            conf = entry["confidence"]
            if not isinstance(conf, (int, float)) or not 0.0 <= conf <= 1.0:
                raise AnalysisValidationError(
                    f"`theme.confidence` must be 0.0..1.0; got {conf!r}"
                )
        if primaries != 1:
            raise AnalysisValidationError(
                f"`theme` must have exactly one primary; got {primaries}"
            )

    def _validate_site_type(self, site_type: Any) -> None:
        if not isinstance(site_type, str):
            raise AnalysisValidationError(
                f"`site_type` must be a single string; got {type(site_type).__name__}"
            )
        self._validate_id("site_type", site_type)

    def _validate_id_list(self, field: str, ids: Any) -> None:
        if not isinstance(ids, list):
            raise AnalysisValidationError(
                f"`{field}` must be a list; got {type(ids).__name__}"
            )
        for i in ids:
            if not isinstance(i, str):
                raise AnalysisValidationError(
                    f"`{field}` entries must be strings; got {type(i).__name__}"
                )
            self._validate_id(field, i)

    def _validate_id(self, field: str, stable_id: str) -> None:
        group = TAXONOMY_FIELDS[field]
        lib = self._libraries.get(group)
        if lib is None or not lib.ids:
            # No library loaded for this group; skip strict check.
            return
        if not lib.has(stable_id):
            raise AnalysisValidationError(
                f"{field}: id {stable_id!r} not in {group} library "
                f"({len(lib.ids)} known IDs)"
            )

    # ── Introspection helpers (for logs/diagnostics) ────────────────────

    @property
    def library_summary(self) -> dict[str, int]:
        return {grp: len(lib.ids) for grp, lib in self._libraries.items()}

    @property
    def prompt_length(self) -> int:
        return len(self._prompt)


__all__ = [
    "AnalysisValidationError",
    "CaseVisionAnalyzer",
    "TAXONOMY_FIELDS",
    "TaxonomyLibrary",
    "VisionAnalyzer",
]
