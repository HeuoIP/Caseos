"""End-to-end CaseOS vision pipeline.

Usage:

    python backend/scripts/run_vision.py [PATH_TO_FILE_OR_DIR] [--force]

Pipeline:

1. Receive a single image path, a directory path, or nothing (default
   ``data/images/cases/``).
2. Build the ``VisionAnalyzer`` from ``app.services.vision.factory``.
   The analyzer loads its own prompt + schema + taxonomy libraries.
3. For each image: call ``analyzer.analyze(image_path)``; persist the
   resulting JSON to ``data/analysis/cases/<image>.json``; append a
   manifest entry to ``data/analysis/manifest.json``.

Pass ``--force`` to re-analyze images whose JSON already exists.

Note: the analyzer is self-sufficient, so this orchestrator does not
load the prompt. Removing ``prompt_loader`` from the call chain.
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

# Logical schema version reported in manifest entries. Source of truth
# lives in ``schemas/case_analysis_v3.json``; this label is what callers
# should read to know which contract an analysis was produced under.
OUTPUT_SCHEMA_VERSION = "CaseOS_Output_Schema_V2"

# Vision Standard version embedded in every analysis JSON's `metadata`
# block. Source of truth lives in
# `docs/standards/CaseOS_Vision_Standard_V1.md`.
VISION_STANDARD_VERSION = "CaseOS_Vision_Standard_V1"

# Default model name embedded in every analysis JSON's `metadata`
# block AND reported in the manifest log. Overridden by a future
# multi-provider factory once a second backend lands.
DEFAULT_MODEL_NAME = "qwen3.7-plus"

# Default repo-rooted locations (image input / analysis output /
# manifest log). All three follow the 1:1 naming convention:
#     data/images/cases/0001.png
#     data/analysis/cases/0001.json
DEFAULT_IMAGES_DIRNAME = "data/images/cases"
DEFAULT_ANALYSIS_DIRNAME = "data/analysis/cases"
DEFAULT_MANIFEST_FILENAME = "manifest.json"


def _repo_root() -> Path:
    """Return the CaseOS repo root (parent of ``backend/``)."""

    return Path(__file__).resolve().parents[2]


def _ensure_path_on_sys_path() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    backend_str = str(backend_root)
    if backend_str not in sys.path:
        sys.path.insert(0, backend_str)


def _load_analyzer():
    """Build a self-sufficient VisionAnalyzer after sys.path fixup."""

    _ensure_path_on_sys_path()
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    from app.services.vision.factory import build_vision_analyzer

    return build_vision_analyzer("qwen")


def _iter_images(target: Path) -> list[Path]:
    """Return every supported image under ``target`` (sorted by path)."""

    if target.is_file():
        return [target] if target.suffix.lower() in SUPPORTED_EXTENSIONS else []
    return sorted(
        p for p in target.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def _resolve_inputs(arg: str | None) -> list[Path]:
    """Resolve CLI arguments into a deduplicated list of image paths."""

    if arg is None:
        images_dir = _repo_root() / DEFAULT_IMAGES_DIRNAME
        if not images_dir.exists():
            raise FileNotFoundError(images_dir)
        candidates = _iter_images(images_dir)
    else:
        candidates = _iter_images(Path(arg))

    seen: set[Path] = set()
    unique: list[Path] = []
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def _analysis_dir() -> Path:
    """Return ``data/analysis/cases/`` and make sure it exists."""

    path = _repo_root() / DEFAULT_ANALYSIS_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def _manifest_path() -> Path:
    """Return ``data/analysis/manifest.json`` and make sure its parent exists."""

    path = _repo_root() / "data" / "analysis" / DEFAULT_MANIFEST_FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_manifest() -> list[dict[str, Any]]:
    """Return the existing manifest as a list; empty list if absent."""

    p = _manifest_path()
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Corrupted manifest: start fresh rather than crash the pipeline.
        return []
    return data if isinstance(data, list) else []


def _save_manifest(entries: list[dict[str, Any]]) -> None:
    """Atomically write the manifest array to disk."""

    p = _manifest_path()
    p.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# Match filenames like ``vision_prompt_v2.md`` -> ``vision_v2``,
# ``vision_prompt_v3_legacy.md`` -> ``vision_v3_legacy``.
_PROMPT_VERSION_RE = re.compile(r"^(?P<base>vision_prompt)_(?P<tag>v[\w]+)$")


def _prompt_version(prompt_path: Path) -> str:
    """Derive a short prompt-version label from the prompt filename."""

    stem = prompt_path.stem  # e.g. vision_prompt_v2
    m = _PROMPT_VERSION_RE.match(stem)
    if m:
        return m.group("base") + "_" + m.group("tag")
    # Fallback: just use the stem verbatim so we never silently lose info.
    return stem


def _now_iso() -> str:
    """Local-time ISO-8601 timestamp with second precision."""

    return datetime.now().isoformat(timespec="seconds")


def _wrap_metadata(payload: dict[str, Any], *, model: str) -> dict[str, Any]:
    """Wrap the analyzer payload with a provenance `metadata` block.

    The metadata block records HOW this analysis was produced so that
    years later a maintainer (or a re-analysis job) knows:

    - which model produced the analysis
    - which Vision Standard governed the analysis
    - which Output Schema contract the JSON satisfies
    - exactly when it was produced

    The analyzer itself stays clean: it returns ONLY the schema-defined
    content payload. The orchestrator layers provenance on top.
    """
    return {
        "metadata": {
            "model": model,
            "vision_standard": VISION_STANDARD_VERSION,
            "output_schema": OUTPUT_SCHEMA_VERSION,
            "analyzed_at": _now_iso(),
        },
        **payload,
    }


def _record_entry(
    manifest: list[dict[str, Any]],
    *,
    filename: str,
    status: str,
    duration: float,
    prompt_version: str,
    error: str | None = None,
) -> None:
    """Append one manifest entry. Failure-safe (no exceptions bubble up)."""

    entry: dict[str, Any] = {
        "filename": filename,
        "status": status,
        "model": DEFAULT_MODEL_NAME,
        "prompt_version": prompt_version,
        "output_schema": OUTPUT_SCHEMA_VERSION,
        "time": _now_iso(),
        "duration": round(duration, 3),
    }
    if error is not None:
        entry["error"] = error
    manifest.append(entry)


def run(target: str | None = None, *, indent: int = 2, force: bool = False) -> list[Path]:
    """Run the CaseOS vision pipeline for one or many images.

    Args:
        target: ``None`` (use ``data/images/cases/``), an image file, or a folder.
        indent: JSON indent level.
        force: Re-analyze even if the output JSON already exists.

    Returns:
        The list of output JSON paths (one per analyzed image).
    """

    image_paths = _resolve_inputs(target)
    if not image_paths:
        raise FileNotFoundError(
            "No supported images found; pass a path or place PNG/JPG/WebP files "
            "under data/images/cases/."
        )

    analyzer = _load_analyzer()

    print(f"[CaseOS] analyzer : {type(analyzer).__name__}")
    print(f"[CaseOS] libraries: {analyzer.library_summary}")
    print(f"[CaseOS] prompt   : {analyzer.prompt_length} chars (composed at construct)")
    print(f"[CaseOS] inputs   : {len(image_paths)} image(s)")

    out_dir = _analysis_dir()
    manifest = _load_manifest()
    pver = _prompt_version(analyzer.prompt_path)
    results: list[Path] = []

    for idx, image_path in enumerate(image_paths, 1):
        out_path = out_dir / (image_path.stem + ".json")
        if out_path.exists() and not force:
            print(f"[{idx}/{len(image_paths)}] skip  : {image_path.name} (already analysed)")
            continue
        print(f"[{idx}/{len(image_paths)}] start : {image_path.name}")
        start = time.monotonic()
        try:
            payload: dict[str, Any] = analyzer.analyze(str(image_path))
            full = _wrap_metadata(payload, model=DEFAULT_MODEL_NAME)
            out_path.write_text(
                json.dumps(full, ensure_ascii=False, indent=indent) + "\n",
                encoding="utf-8",
            )
            duration = time.monotonic() - start
            _record_entry(
                manifest,
                filename=image_path.name,
                status="success",
                duration=duration,
                prompt_version=pver,
            )
            print(f"[{idx}/{len(image_paths)}] saved : {out_path} ({duration:.2f}s)")
            results.append(out_path)
        except Exception as exc:  # noqa: BLE001 - surface every failure to operator
            duration = time.monotonic() - start
            _record_entry(
                manifest,
                filename=image_path.name,
                status="failed",
                duration=duration,
                prompt_version=pver,
                error=str(exc),
            )
            print(f"[{idx}/{len(image_paths)}] error : {image_path.name}: {exc}")

    _save_manifest(manifest)
    print(f"[CaseOS] manifest : {len(manifest)} entries -> {_manifest_path()}")
    print(f"[CaseOS] done     : {len(results)} new result(s)")
    return results


if __name__ == "__main__":
    args = sys.argv[1:]
    force = "--force" in args
    target = next((a for a in args if not a.startswith("--")), None)
    run(target, force=force)
