"""Review Item Object (Sprint 22.3.1, ADR-018 Section 3).

A ``ReviewItem`` is a single entry in the human review queue.
It is **not** a ``LearningProposal``; it is a side-channel
projection that the human reviewer reads and acts on. The
proposal itself stays in the proposal store; the review item is
the operator-facing surface.

Required fields (Sprint 22.3.1 spec section Task 1):

    review_id            unique identifier of the review
    proposal_id          the LearningProposal this review tracks
    target_identity      the Knowledge Object the proposal targets
    proposal_type        the proposal taxonomy value
    summary              a short human-readable description
                         (typically the proposal reason)
    status               ReviewStatus value (PENDING / APPROVED / REJECTED)
    created_at           ISO timestamp

Constraints:

    * ``@dataclass(frozen=True)`` -- immutable by contract.
    * ``to_dict()`` is JSON-safe.
    * No import from ``caseos.intelligence.*`` or
      ``caseos.knowledge.retrieval``.

State changes to a review are recorded by APPENDING a new
``ReviewItem`` (with the same ``review_id`` and a different
status) to the queue. The original PENDING item is never
mutated. See ``review.queue.ReviewQueue`` for the storage model.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ReviewStatus(str, Enum):
    """Lifecycle of a single review item."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


TERMINAL_REVIEW_STATES: frozenset[ReviewStatus] = frozenset({
    ReviewStatus.APPROVED,
    ReviewStatus.REJECTED,
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class ReviewItem:
    """A single human review entry."""

    review_id: str
    proposal_id: str
    target_identity: str
    proposal_type: str
    summary: str
    status: str
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "ReviewItem",
    "ReviewStatus",
    "TERMINAL_REVIEW_STATES",
]
