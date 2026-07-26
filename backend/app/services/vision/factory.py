"""Factory for selecting a :class:`VisionAnalyzer` implementation."""

from __future__ import annotations

from typing import Any

from app.services.vision.analyzer import VisionAnalyzer


def build_vision_analyzer(provider: str = "qwen") -> VisionAnalyzer:
    """Return a :class:`VisionAnalyzer` instance for the requested provider.

    Args:
        provider: Provider name. Only ``"qwen"`` is recognised in V0.

    Raises:
        ValueError: If ``provider`` does not match a known backend.
    """
    if provider == "qwen":
        from app.services.vision.providers.qwen import QwenVisionAnalyzer

        return QwenVisionAnalyzer()
    raise ValueError(f"Unknown vision provider: {provider!r}")


__all__: list[Any] = ["build_vision_analyzer"]