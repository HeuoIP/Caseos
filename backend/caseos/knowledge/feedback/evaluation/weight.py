"""Source weighting for the Feedback Intelligence Evaluation foundation.

Weights describe the relative strength of evidence; they do not grant
feedback authority and are never applied to knowledge or trust state.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from caseos.knowledge.feedback.object import FeedbackSource

SOURCE_WEIGHTS: dict[str, int] = {
    FeedbackSource.EXPERT.value: 100,
    FeedbackSource.OUTCOME.value: 75,
    FeedbackSource.REASON.value: 50,
    FeedbackSource.PREFERENCE.value: 25,
}
SOURCE_PRIORITIES: dict[str, str] = {
    "EXPERT": "highest",
    "OUTCOME": "high",
    "REASON": "medium",
    "PREFERENCE": "low",
}
# Backwards-friendly name used by some callers.
SOURCE_PRIORITY_LABEL = SOURCE_PRIORITIES


@dataclass(frozen=True)
class WeightAssessment:
    source: str
    weight: int
    priority: str
    is_valid: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _value(source: Any) -> str:
    return source.value if isinstance(source, Enum) else str(source)


class FeedbackWeight:
    """Pure source-to-weight mapping."""

    def assess(self, source: FeedbackSource | str, feedback_type: Any = None) -> WeightAssessment:
        value = _value(source)
        return WeightAssessment(
            source=value,
            weight=SOURCE_WEIGHTS.get(value, 0),
            priority=SOURCE_PRIORITIES.get(value, "unknown"),
            is_valid=value in SOURCE_WEIGHTS,
        )

    def evaluate(self, source: FeedbackSource | str) -> WeightAssessment:
        return self.assess(source)


def source_weight(source: FeedbackSource | str) -> int:
    return FeedbackWeight().assess(source).weight


__all__ = ["FeedbackWeight", "WeightAssessment", "SOURCE_WEIGHTS", "SOURCE_PRIORITIES", "SOURCE_PRIORITY_LABEL", "source_weight"]
