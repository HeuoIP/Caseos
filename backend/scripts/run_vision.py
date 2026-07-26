"""End-to-end CaseOS vision pipeline.

Usage:

    python backend/scripts/run_vision.py [PATH_TO_FILE_OR_DIR] [--force]

Pipeline:

1. Receive a single image path, a directory path, or nothing (default
   ``data/images/``).
2. Read the registered ``VisionAnalyzer`` from ``app.services.vision.factory``.
3. Load ``backend/prompts/vision_prompt_v1.md`` automatically.
4. Call ``Qwen3.7-Plus`` via DashScope.
5. Persist each response to ``data/analysis/<image>.json``.

Pass ``--force`` to re-analyze images whose JSON already exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def _ensure_path_on_sys_path() -> None:
    backend_root = Path(__file__).resolve().parents[1]
    backend_str = str(backend_root)
    if backend_str not in sys.path:
        sys.path.insert(0, backend_str)


def _load_analyzer():
    """Import and resolve the analyzer after sys.path fixup."""

    _ensure_path_on_sys_path()
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    from app.services.vision.factory import build_vision_analyzer

    return build_vision_analyzer("qwen")


def _load_prompt() -> str:
    """Read the V1 vision prompt off disk."""

    from scripts.vision.prompt_loader import load_vision_prompt

    return load_vision_prompt()


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
        images_dir = Path(__file__).resolve().parents[2] / "data" / "images"
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
    """Return ``data/analysis/`` and make sure it exists."""

    path = Path(__file__).resolve().parents[2] / "data" / "analysis"
    path.mkdir(parents=True, exist_ok=True)
    return path


def run(target: str | None = None, *, indent: int = 2, force: bool = False) -> list[Path]:
    """Run the CaseOS vision pipeline for one or many images.

    Args:
        target: ``None`` (use ``data/images/``), an image file, or a folder.
        indent: JSON indent level.
        force: Re-analyze even if the output JSON already exists.

    Returns:
        The list of output JSON paths (one per analyzed image).
    """

    image_paths = _resolve_inputs(target)
    if not image_paths:
        raise FileNotFoundError(
            "No supported images found; pass a path or place PNG/JPG/WebP files under data/images/."
        )

    analyzer = _load_analyzer()
    prompt = _load_prompt()

    print(f"[CaseOS] analyzer : {type(analyzer).__name__}")
    print(f"[CaseOS] prompt   : {len(prompt)} chars")
    print(f"[CaseOS] inputs   : {len(image_paths)} image(s)")

    out_dir = _analysis_dir()
    results: list[Path] = []

    for idx, image_path in enumerate(image_paths, 1):
        out_path = out_dir / (image_path.stem + ".json")
        if out_path.exists() and not force:
            print(f"[{idx}/{len(image_paths)}] skip  : {image_path.name} (already analysed)")
            continue
        print(f"[{idx}/{len(image_paths)}] start : {image_path.name}")
        try:
            payload: dict[str, Any] = analyzer.analyze(str(image_path), prompt=prompt)
            out_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=indent) + "\n",
                encoding="utf-8",
            )
            print(f"[{idx}/{len(image_paths)}] saved : {out_path}")
            results.append(out_path)
        except Exception as exc:  # noqa: BLE001 - surface every failure to operator
            print(f"[{idx}/{len(image_paths)}] error : {image_path.name}: {exc}")
    print(f"[CaseOS] done     : {len(results)} new result(s)")
    return results


if __name__ == "__main__":
    args = sys.argv[1:]
    force = "--force" in args
    target = next((a for a in args if not a.startswith("--")), None)
    run(target, force=force)