"""Review Queue (Sprint 22.3.1, ADR-018 Section 3).

The Review Queue is an **append-only** surface for ``ReviewItem``
records. It mirrors the design of ``FeedbackStore`` and
``ProposalStore``: every state change appends a new entry, no
existing entry is ever modified or removed.

Storage model:

    enqueue(proposal)            appends a ReviewItem(status=PENDING)
    approve / reject             appends a ReviewItem(status=APPROVED / REJECTED)
                                 with the SAME review_id

The "current state" of a review is the latest entry in the
queue for that ``review_id``. Earlier entries form an immutable
history.

Forbidden methods:

    update / delete / overwrite / clear
    All raise ``TypeError`` on any call. The queue is append-only.

Architecture boundary (Sprint 22.3.1 spec):

    This module does NOT import from:
        * caseos.intelligence.decision
        * caseos.intelligence.trust
        * caseos.intelligence.recommendation
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.feedback (parent package)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from .object import ReviewItem, ReviewStatus


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _summary_from_proposal(proposal: Any) -> str:
    reason = getattr(proposal, "reason", None)
    suggested = getattr(proposal, "suggested_change", None)
    if isinstance(reason, str) and reason:
        return reason
    if isinstance(suggested, str) and suggested:
        return suggested
    return ""


def _proposal_type_of(proposal: Any) -> str:
    pt = getattr(proposal, "proposal_type", "")
    return pt if isinstance(pt, str) else str(pt or "")


def _target_identity_of(proposal: Any) -> str:
    ti = getattr(proposal, "target_identity", "")
    return ti if isinstance(ti, str) else str(ti or "")


@dataclass
class ReviewQueue:
    """Append-only review queue.

    The internal list only ever grows via ``enqueue`` /
    ``append_status_change``. No item is ever modified, removed,
    or replaced. ``update``, ``delete``, ``overwrite``, and
    ``clear`` are explicitly forbidden: any call raises
    ``TypeError`` immediately.
    """

    _items: list[ReviewItem] = field(default_factory=list)

    def enqueue(self, proposal: Any) -> ReviewItem:
        review_id = str(uuid.uuid4())
        item = ReviewItem(
            review_id=review_id,
            proposal_id=str(getattr(proposal, "proposal_id", "")),
            target_identity=_target_identity_of(proposal),
            proposal_type=_proposal_type_of(proposal),
            summary=_summary_from_proposal(proposal),
            status=ReviewStatus.PENDING.value,
        )
        self._items.append(item)
        return item

    def append_status_change(
        self,
        review_id: str,
        new_status: str,
        created_at: Optional[str] = None,
    ) -> ReviewItem:
        latest = self.get(review_id)
        if latest is None:
            raise KeyError("unknown review_id: " + str(review_id))
        item = ReviewItem(
            review_id=review_id,
            proposal_id=latest.proposal_id,
            target_identity=latest.target_identity,
            proposal_type=latest.proposal_type,
            summary=latest.summary,
            status=new_status,
            created_at=created_at or _now_iso(),
        )
        self._items.append(item)
        return item

    def get(self, review_id: str) -> Optional[ReviewItem]:
        if not review_id:
            return None
        latest: Optional[ReviewItem] = None
        for item in self._items:
            if item.review_id == review_id:
                latest = item
        return latest

    def history_for(self, review_id: str) -> list[ReviewItem]:
        if not review_id:
            return []
        return [i for i in self._items if i.review_id == review_id]

    def list_all(self) -> list[ReviewItem]:
        return list(self._items)

    def list_pending(self) -> list[ReviewItem]:
        return self._latest_by_status(ReviewStatus.PENDING.value)

    def list_approved(self) -> list[ReviewItem]:
        return self._latest_by_status(ReviewStatus.APPROVED.value)

    def list_rejected(self) -> list[ReviewItem]:
        return self._latest_by_status(ReviewStatus.REJECTED.value)

    def count(self) -> int:
        return len(self._items)

    def distinct_review_count(self) -> int:
        seen: set[str] = set()
        for item in self._items:
            seen.add(item.review_id)
        return len(seen)

    # Forbidden API -- always raise TypeError
    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "ReviewQueue.update is forbidden: the queue is append-only."
        )

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "ReviewQueue.delete is forbidden: the queue is append-only."
        )

    def overwrite(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "ReviewQueue.overwrite is forbidden: the queue is append-only."
        )

    def clear(self) -> None:
        raise TypeError(
            "ReviewQueue.clear is forbidden: the queue is append-only."
        )

    def _latest_by_status(self, status: str) -> list[ReviewItem]:
        latest: dict[str, ReviewItem] = {}
        for item in self._items:
            latest[item.review_id] = item
        return [item for item in latest.values() if item.status == status]


__all__ = ["ReviewQueue"]
