"""Factory for CaseOS vision analyzers.

Builds a self-sufficient ``CaseVisionAnalyzer`` that loads its own
prompt, schema, and taxonomy libraries on construction.
"""

from __future__ import annotations

from pathlib import Path

from app.services.vision.analyzer import CaseVisionAnalyzer, VisionAnalyzer


# Resolve repo root once at import time. The factory file lives at
# backend/app/services/vision/factory.py, so 3 parents up is the repo.
_REPO_ROOT = Path(__file__).resolve().parents[4]

_DEFAULT_PROMPT = _REPO_ROOT / "backend" / "prompts" / "vision_prompt_v2.md"
_DEFAULT_SCHEMA = _REPO_ROOT / "schemas" / "case_analysis_v3.json"
_DEFAULT_TAXONOMY = _REPO_ROOT / "knowledge" / "taxonomy"


def build_vision_analyzer(
    provider: str = "qwen",
    *,
    prompt_path: Path | None = None,
    schema_path: Path | None = None,
    taxonomy_root: Path | None = None,
) -> VisionAnalyzer:
    """Return a self-sufficient ``CaseVisionAnalyzer``.

    The returned analyzer loads prompt + schema + libraries at construction;
    callers only need to invoke ``analyze(image_path)``.

    Args:
        provider: Provider name. Only ``"qwen"`` is recognised in V0.
        prompt_path: Override path to the prompt template.
        schema_path: Override path to the output schema.
        taxonomy_root: Override path to the taxonomy libraries root.

    Raises:
        ValueError: If ``provider`` is not a known backend.
    """
    if provider != "qwen":
        raise ValueError(f"Unknown vision provider: {provider!r}")

    from app.services.vision.providers.qwen import QwenProvider

    return CaseVisionAnalyzer(
        provider=QwenProvider(),
        prompt_path=prompt_path or _DEFAULT_PROMPT,
        schema_path=schema_path or _DEFAULT_SCHEMA,
        taxonomy_root=taxonomy_root or _DEFAULT_TAXONOMY,
    )


__all__ = ["build_vision_analyzer"]
