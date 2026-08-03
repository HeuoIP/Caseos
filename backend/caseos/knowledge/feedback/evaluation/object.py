"""Structured result produced by the feedback evaluation foundation."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class FeedbackEvaluation:
    """An immutable, audit-friendly evaluation of one feedback event.

    This object is an observation about feedback.  It is deliberately
    not a Knowledge Object, Decision, Trust value, or recommendation.
    """

    feedback_id: str
    source: str
    feedback_type: str
    weight: int
    priority: str
    requires_human_review: bool
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def as_dict(self) -> dict[str, Any]:
        """Alias useful to callers that use the repository's dict API."""
        return self.to_dict()


__all__ = ["FeedbackEvaluation"]
