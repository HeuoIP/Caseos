"""End-to-end CaseOS vision pipeline.

Usage:

    python -m backend.scripts.run_vision PATH_TO_IMAGE

Pipeline:

1. Receive ``PATH_TO_IMAGE`` (or the first PNG inside ``data/images/`` if
   omitted).
2. Read the registered ``VisionAnalyzer`` from ``app.services.vision.factory``.
3. Load ``backend/prompts/vision_prompt_v1.md`` automatically.
4. Call ``Qwen3.7-Plus`` (the active V1 provider).
5. Persist the returned JSON to ``data/analysis/<image>.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


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


def _resolve_image(arg: str | None) -> Path:
    """Return the playground image to analyse."""

    if arg is None:
        images_dir = Path(__file__).resolve().parents[2] / "data" / "images"
        for candidate in sorted(images_dir.iterdir()):
            if candidate.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
                return candidate
        raise FileNotFoundError(
            f"No playground image found in {images_dir}"
        )
    candidate = Path(arg)
    if not candidate.exists():
        raise FileNotFoundError(candidate)
    return candidate


def _analysis_dir() -> Path:
    """Return ``data/analysis/`` and make sure it exists."""

    path = Path(__file__).resolve().parents[2] / "data" / "analysis"
    path.mkdir(parents=True, exist_ok=True)
    return path


def run(image_arg: str | None = None, *, indent: int = 2) -> Path:
    """Run the CaseOS vision pipeline for ``image_arg`` and return the JSON path."""

    image_path = _resolve_image(image_arg)
    analyzer = _load_analyzer()
    prompt = _load_prompt()

    print(f"[CaseOS] image    : {image_path}")
    print(f"[CaseOS] analyzer : {type(analyzer).__name__}")
    print(f"[CaseOS] prompt   : {len(prompt)} chars")

    payload: dict[str, Any] = analyzer.analyze(str(image_path), prompt=prompt)

    out_dir = _analysis_dir()
    out_path = out_dir / (image_path.stem + ".json")
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=indent) + "\n",
        encoding="utf-8",
    )
    print(f"[CaseOS] saved    : {out_path}")
    return out_path


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    run(arg)
