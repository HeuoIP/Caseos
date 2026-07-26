"""Qwen-VL provider stub for CaseOS.

``QwenVisionAnalyzer`` will eventually talk to the Qwen3-VL model. For now it
only exists as a placeholder that satisfies the ``VisionAnalyzer`` contract.
"""

from __future__ import annotations

from typing import Any

from app.services.vision.analyzer import VisionAnalyzer


class QwenVisionAnalyzer(VisionAnalyzer):
    """Vision analyzer backed by Qwen3-VL."""

    def analyze(self, image_path: str) -> dict[str, Any]:
        """Analyze one playground image with Qwen3-VL.

        The implementation is intentionally left empty; V0 of CaseOS does not
        invoke the model.
        """
        raise NotImplementedError(
            "QwenVisionAnalyzer.analyze is not implemented yet"
        )