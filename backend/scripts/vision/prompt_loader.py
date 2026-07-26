"""Vision prompt loader.

``load_vision_prompt`` locates ``backend/prompts/vision_prompt_v1.md`` no matter
where the Python interpreter is invoked from. The file is treated as UTF-8 text.
"""

from __future__ import annotations

from pathlib import Path


def _prompt_path() -> Path:
    """Locate the case vision prompt ``vision_prompt_v1.md`` on disk."""

    here = Path(__file__).resolve()
    for ancestor in here.parents:
        candidate = ancestor / "prompts" / "vision_prompt_v1.md"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Could not locate backend/prompts/vision_prompt_v1.md"
    )


def load_vision_prompt() -> str:
    """Return the raw text of the case vision prompt."""

    return _prompt_path().read_text(encoding="utf-8").strip()