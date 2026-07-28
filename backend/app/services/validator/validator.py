"""CaseOS Validator -- the gatekeeper between VisionAnalyzer and Database."

Pipeline position:

    VisionAnalyzer
        v
    CaseOSValidator    <-- this module
        v
    Database

Every analysis JSON must pass through CaseOSValidator before it can
be persisted. The validator enforces the Output Schema contract and
taxonomy library membership, and emits a quality report with score /
warnings / suggestions.

Checks (in order):

    - JSON is syntactically valid
    - All required top-level fields are present
    - Each taxonomy ID exists in its library
    - theme has exactly one primary entry
    - confidence is in [0.0, 1.0]
    - vision_summary contains no forbidden marketing words
    - Quality heuristics (length, keyword count, theme richness)

Use:

    from app.services.validator.validator import CaseOSValidator
    v = CaseOSValidator(schema_path, taxonomy_root)
    result = v.validate_file("data/analysis/cases/0001.json")
    if result.passed:
        save_to_db(data, result)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.services.vision.analyzer import TAXONOMY_FIELDS, _group_to_slug, _ID_LINE_RE


# Required top-level fields in every analysis JSON.
# metadata is OPTIONAL (orchestrator adds it on disk only).
REQUIRED_FIELDS = (
    "project_name",
    "theme", "style", "site_type", "age_group",
    "play_behaviors", "functional_units", "materials", "colors",
    "design_keywords", "vision_summary", "design_interpretation",
)


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of validating one analysis JSON."

    Attributes:
        passed: True iff errors is empty. Database may persist.
        score: 0-100 quality score. Higher is better.
        errors: Blocking issues. Must be empty for passed.
        warnings: Non-blocking issues.
        suggestions: Hints; never affect score.
        file_path: Source path for batch reporting.
    """

    passed: bool
    score: int
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    suggestions: list = field(default_factory=list)
    file_path: str | None = None

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "score": self.score,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "suggestions": list(self.suggestions),
            "file_path": self.file_path,
        }


@dataclass(frozen=True)
class TaxonomyLibrary:
    """Loaded contents of one taxonomy library."""

    group: str
    slug: str
    root: Path
    ids: list = field(default_factory=list)

    def has(self, stable_id: str) -> bool:
        return stable_id in self.ids


# Marketing-language words forbidden in vision_summary.
FORBIDDEN_SUMMARY_WORDS = (
    "striking", "beautiful", "amazing", "impressive", "iconic",
    "world-class", "stunning", "gorgeous", "magnificent",
    "breathtaking", "spectacular", "incredible", "fantastic",
    "wonderful", "epic", "magical",
)


# Scoring weights.
_ERROR_PENALTY = 25
_WARNING_PENALTY = 5


class CaseOSValidator:
    """Self-sufficient CaseOS validator."""

    def __init__(self, schema_path, taxonomy_root) -> None:
        self.schema_path = Path(schema_path)
        self.taxonomy_root = Path(taxonomy_root)

        if not self.schema_path.exists():
            raise FileNotFoundError('Schema not found: ' + str(self.schema_path))
        self._schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        self._libraries = self._load_libraries()

    # -- Loading ---

    def _load_libraries(self):
        result = {}
        for _field, group in TAXONOMY_FIELDS.items():
            slug = _group_to_slug(group)
            lib_dir = self.taxonomy_root / slug
            ids = self._extract_ids(lib_dir) if lib_dir.is_dir() else []
            result[group] = TaxonomyLibrary(group=group, slug=slug, root=lib_dir, ids=ids)
        return result

    @staticmethod
    def _extract_ids(lib_dir):
        ids = []
        for md in sorted(lib_dir.glob("*.md")):
            if md.name.lower() == "readme.md":
                continue
            text = md.read_text(encoding="utf-8")
            for match in _ID_LINE_RE.finditer(text):
                ids.append(match.group(1))
        seen = set()
        unique = []
        for i in ids:
            if i not in seen:
                seen.add(i)
                unique.append(i)
        return unique

    @property
    def library_summary(self) -> dict:
        return {grp: len(lib.ids) for grp, lib in self._libraries.items()}

    # -- Validate ---

    def validate(self, data) -> ValidationResult:
        errors = []
        warnings = []
        suggestions = []

        if not isinstance(data, dict):
            return ValidationResult(
                passed=False, score=0,
                errors=[f"top-level must be a dict, got {type(data).__name__}"],
            )

        self._check_required_fields(data, errors)
        self._check_project_name(data, errors)
        self._check_theme(data.get("theme"), errors, warnings, suggestions)
        self._check_site_type(data.get("site_type"), errors)
        for f in ("style", "age_group", "play_behaviors",
                  "functional_units", "materials", "colors"):
            self._check_id_list(data.get(f), f, errors)
        self._check_design_keywords(data.get("design_keywords"), errors)
        self._check_text_field(data.get("vision_summary"), "vision_summary", errors)
        self._check_text_field(data.get("design_interpretation"), "design_interpretation", errors)
        self._check_forbidden_words(data.get("vision_summary"), errors)
        self._quality_checks(data, warnings, suggestions)
        self._check_metadata(data, warnings)

        score = self._compute_score(errors, warnings)
        return ValidationResult(
            passed=len(errors) == 0,
            score=score,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def validate_file(self, path) -> ValidationResult:
        p = Path(path)
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return ValidationResult(
                passed=False, score=0,
                errors=[f"invalid JSON: {exc}"],
                file_path=str(p),
            )
        result = self.validate(data)
        return ValidationResult(
            passed=result.passed,
            score=result.score,
            errors=result.errors,
            warnings=result.warnings,
            suggestions=result.suggestions,
            file_path=str(p),
        )

    # -- Individual checks ---

    def _check_required_fields(self, data, errors):
        for f in REQUIRED_FIELDS:
            if f not in data:
                errors.append(f"missing required field: {f!r}")

    def _check_project_name(self, data, errors):
        v = data.get("project_name")
        if v is None:
            return
        if not isinstance(v, str):
            errors.append(f"`project_name` must be a string; got {type(v).__name__}")
        elif not v.strip():
            errors.append("`project_name` must be non-empty")

    def _check_theme(self, theme, errors, warnings, suggestions):
        if theme is None:
            return
        if not isinstance(theme, list):
            errors.append(f"`theme` must be a list; got {type(theme).__name__}")
            return
        if not theme:
            errors.append("`theme` must be non-empty")
            return
        primaries = 0
        for entry in theme:
            if not isinstance(entry, dict):
                errors.append(f"`theme` entries must be dicts; got {type(entry).__name__}")
                continue
            for k in ("id", "role", "confidence"):
                if k not in entry:
                    errors.append(f"`theme` entry missing key {k!r}: {entry!r}")
            sid = entry.get("id")
            if isinstance(sid, str):
                self._check_id(sid, "theme", errors)
            role = entry.get("role")
            if role == "primary":
                primaries += 1
            elif role not in ("primary", "secondary", None):
                errors.append(f"`theme.role` must be primary|secondary; got {role!r}")
            conf = entry.get("confidence")
            if conf is not None and (not isinstance(conf, (int, float)) or not 0.0 <= float(conf) <= 1.0):
                errors.append(f"`theme.confidence` must be 0.0..1.0; got {conf!r}")
        if primaries == 0:
            errors.append("`theme` must have exactly one primary; got 0")
        elif primaries > 1:
            errors.append(f"`theme` must have exactly one primary; got {primaries}")
        if len(theme) == 1:
            suggestions.append("Consider adding a secondary theme for richer analysis")

    def _check_site_type(self, st, errors):
        if st is None:
            return
        if not isinstance(st, str):
            errors.append(f"`site_type` must be a string; got {type(st).__name__}")
            return
        self._check_id(st, "site_type", errors)

    def _check_id_list(self, ids, field, errors):
        if ids is None:
            return
        if not isinstance(ids, list):
            errors.append(f"`{field}` must be a list; got {type(ids).__name__}")
            return
        for i in ids:
            if not isinstance(i, str):
                errors.append(f"`{field}` entries must be strings; got {type(i).__name__}")
                continue
            self._check_id(i, field, errors)

    def _check_id(self, stable_id, field, errors):
        group = TAXONOMY_FIELDS[field]
        lib = self._libraries.get(group)
        if lib is None or not lib.ids:
            return
        if not lib.has(stable_id):
            errors.append(
                f"{field}: id {stable_id!r} not in {group} library "
                f"({len(lib.ids)} known IDs)"
            )

    def _check_design_keywords(self, kw, errors):
        if kw is None:
            return
        if not isinstance(kw, list):
            errors.append(f"`design_keywords` must be a list; got {type(kw).__name__}")
            return
        for k in kw:
            if not isinstance(k, str):
                errors.append(f"`design_keywords` entries must be strings; got {type(k).__name__}")

    def _check_text_field(self, val, field, errors):
        if val is None:
            return
        if not isinstance(val, str):
            errors.append(f"`{field}` must be a string; got {type(val).__name__}")
            return
        if not val.strip():
            errors.append(f"`{field}` must be non-empty")

    def _check_forbidden_words(self, summary, errors):
        if not isinstance(summary, str):
            return
        low = summary.lower()
        hits = [w for w in FORBIDDEN_SUMMARY_WORDS if w in low]
        if hits:
            errors.append(f"`vision_summary` contains forbidden marketing word(s): {hits}")

    def _quality_checks(self, data, warnings, suggestions):
        vs = data.get("vision_summary")
        if isinstance(vs, str):
            words = len(vs.split())
            if words < 12:
                warnings.append(f"vision_summary has only {words} words; recommend 12+")
        di = data.get("design_interpretation")
        if isinstance(di, str):
            words = len(di.split())
            if words < 10:
                warnings.append(f"design_interpretation has only {words} words; recommend 10+")
        kw = data.get("design_keywords")
        if isinstance(kw, list) and len(kw) < 3:
            warnings.append(f"design_keywords has only {len(kw)} entries; recommend 3+")
        for f in ("style", "play_behaviors", "functional_units", "materials", "colors"):
            v = data.get(f)
            if isinstance(v, list) and len(v) == 0:
                warnings.append(f"`{f}` is empty; analysis looks thin")
        ag = data.get("age_group")
        if isinstance(ag, list) and len(ag) == 1:
            suggestions.append("age_group has only one entry; consider adjacent age ranges for richer targeting")

    def _check_metadata(self, data, warnings):
        md = data.get("metadata")
        if md is None:
            warnings.append("`metadata` block missing; on-disk JSON should carry provenance")
            return
        if not isinstance(md, dict):
            warnings.append(f"`metadata` must be a dict; got {type(md).__name__}")
            return
        for k in ("model", "vision_standard", "output_schema", "analyzed_at"):
            if k not in md:
                warnings.append(f"`metadata` missing key: {k!r}")
            elif not isinstance(md[k], str):
                warnings.append(f"`metadata.{k}` must be a string")

    # -- Scoring ---

    @staticmethod
    def _compute_score(errors, warnings) -> int:
        score = 100 - _ERROR_PENALTY * len(errors) - _WARNING_PENALTY * len(warnings)
        return max(0, score)


__all__ = [
    "CaseOSValidator",
    "FORBIDDEN_SUMMARY_WORDS",
    "REQUIRED_FIELDS",
    "TaxonomyLibrary",
    "ValidationResult",
]

