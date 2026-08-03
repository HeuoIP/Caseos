"""Small serializable report helpers for evaluation results."""
from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

from .object import FeedbackEvaluation


def _items(evaluations: FeedbackEvaluation | Iterable[FeedbackEvaluation]) -> list[FeedbackEvaluation]:
    if isinstance(evaluations, FeedbackEvaluation):
        return [evaluations]
    return list(evaluations)


def generate_summary(evaluations: FeedbackEvaluation | Iterable[FeedbackEvaluation]) -> dict[str, Any]:
    items = _items(evaluations)
    return {
        "total_evaluations": len(items),
        "weight_distribution": dict(Counter(item.weight for item in items)),
        "priority_distribution": dict(Counter(item.priority for item in items)),
        "reviews_required": sum(item.requires_human_review for item in items),
    }


def generate_report(evaluations: FeedbackEvaluation | Iterable[FeedbackEvaluation], title: str = "Feedback Evaluation Report") -> str:
    items = _items(evaluations)
    summary = generate_summary(items)
    lines = [f"# {title}", "", f"- Total evaluations: {summary['total_evaluations']}", f"- Reviews required: {summary['reviews_required']}", "", "## Per-evaluation detail", ""]
    if not items:
        lines.append("_No evaluations were supplied._")
    for index, item in enumerate(items, 1):
        lines.extend([
            f"### Evaluation {index}", "",
            f"- Feedback ID: `{item.feedback_id}`",
            f"- Source: `{item.source}`",
            f"- Feedback type: `{item.feedback_type}`",
            f"- Weight: {item.weight}",
            f"- Priority: {item.priority}",
            f"- Requires human review: {item.requires_human_review}",
            f"- Created at: {item.created_at}", "",
        ])
    return "\n".join(lines)


__all__ = ["generate_report", "generate_summary"]
