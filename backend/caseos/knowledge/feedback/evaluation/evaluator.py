"""Feedback evaluation orchestrator (foundation only)."""
from __future__ import annotations

from dataclasses import asdict
from enum import Enum
from typing import Any, Mapping

from .object import FeedbackEvaluation
from .weight import FeedbackWeight


def _dict_from_feedback(feedback: Any) -> dict[str, Any]:
    if isinstance(feedback, Mapping):
        data = dict(feedback)
    elif hasattr(feedback, "snapshot"):
        data = dict(getattr(feedback, "snapshot", {}) or {})
        data.setdefault("feedback_id", getattr(feedback, "feedback_id", ""))
        data.setdefault("created_at", getattr(feedback, "timestamp", ""))
    elif hasattr(feedback, "to_dict"):
        data = dict(feedback.to_dict())
    else:
        data = {}
        for name in ("id", "feedback_id", "source", "feedback_type", "created_at", "timestamp"):
            if hasattr(feedback, name):
                data[name] = getattr(feedback, name)
    return data


def _text(value: Any) -> str:
    return value.value if isinstance(value, Enum) else str(value or "")


class FeedbackEvaluator:
    """Analyze a feedback event without mutating any external state."""

    def __init__(self, weight_engine: FeedbackWeight | None = None) -> None:
        self.weight_engine = weight_engine or FeedbackWeight()

    def evaluate(self, feedback: Any) -> FeedbackEvaluation:
        data = _dict_from_feedback(feedback)
        feedback_id = str(data.get("feedback_id") or data.get("id") or "")
        source = _text(data.get("source"))
        feedback_type = _text(data.get("feedback_type"))
        assessment = self.weight_engine.assess(source, feedback_type)
        created_at = str(data.get("created_at") or data.get("timestamp") or "")
        kwargs = {
            "feedback_id": feedback_id,
            "source": source,
            "feedback_type": feedback_type,
            "weight": assessment.weight,
            "priority": assessment.priority,
            # Evaluation never auto-authorizes feedback. Human review is
            # therefore required for every foundation result.
            "requires_human_review": True,
        }
        if created_at:
            kwargs["created_at"] = created_at
        return FeedbackEvaluation(**kwargs)

    def evaluate_event(self, feedback: Any) -> FeedbackEvaluation:
        return self.evaluate(feedback)


def evaluate_feedback(feedback: Any) -> FeedbackEvaluation:
    return FeedbackEvaluator().evaluate(feedback)


__all__ = ["FeedbackEvaluator", "FeedbackEvaluation", "evaluate_feedback"]
