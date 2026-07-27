"""Vision prompt loader.

``load_vision_prompt`` locates ``backend/prompts/vision_prompt_v2.md``
(or v1 as fallback) no matter where the Python interpreter is invoked from.
The file is treated as UTF-8 text.
"""

from __future__ import annotations

from pathlib import Path


def _prompt_path() -> Path:
    """Locate the case vision prompt on disk.

    Prefers ``vision_prompt_v2.md`` (stable-ID format); falls back to v1.
    """
    here = Path(__file__).resolve()
    for ancestor in here.parents:
        prompts_dir = ancestor / "prompts"
        v2 = prompts_dir / "vision_prompt_v2.md"
        if v2.exists():
            return v2
        v1 = prompts_dir / "vision_prompt_v1.md"
        if v1.exists():
            return v1
    raise FileNotFoundError(
        "Could not locate backend/prompts/vision_prompt_v2.md or v1.md"
    )


def load_vision_prompt() -> str:
    """Return the raw text of the case vision prompt."""
    return _prompt_path().read_text(encoding="utf-8").strip()
