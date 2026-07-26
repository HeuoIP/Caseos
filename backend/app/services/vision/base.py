"""Common infrastructure for vision analyzers.

This module exposes a small façade that concrete vision providers can reuse
when they later implement the ``VisionAnalyzer`` contract defined in
:mod:`app.services.vision.analyzer`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VisionResult:
    """Thin wrapper around a CaseOS analyzer response."""

    payload: dict[str, Any]