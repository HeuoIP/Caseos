"""Vision analysis interface for CaseOS.

This module defines the ``VisionAnalyzer`` contract. The implementation is
intentionally left for a future task; callers depend on the abstract
``analyze`` method only.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VisionAnalyzer(ABC):
    """Abstract vision analyzer used by CaseOS."""

    @abstractmethod
    def analyze(self, image_path: str) -> dict[str, Any]:
        """Analyze one playground image.

        Args:
            image_path: Filesystem path to the input image.

        Returns:
            A ``dict`` matching the CaseOS analysis schema (see
            ``schemas/case_analysis_v1.json``).
        """
        raise NotImplementedError