"""Human Review Action Surface (Sprint 22.3.1, ADR-018 Section 3).

A ``ReviewManager`` is the human-gate side of the queue. It
exposes two methods:

    approve(review_id, reviewer, note)  -> ProposalEvent
    reject(review_id, reviewer, note)   -> ProposalEvent

Both methods APPEND a new ``ReviewItem`` to the queue and APPEND
a ``ProposalEvent`` to the proposal store. The original
``LearningProposal`` object is **never modified**.

Lifecycle binding (Sprint 22.3.1 spec Task 4):

    * Review actions drive the proposal lifecycle forward:
        CREATED       -> PENDING_REVIEW -> APPROVED  (approve)
                                    \\-> REJECTED   (reject)
    * The transition is validated by
      ``proposal_lifecycle.is_valid_transition`` -- no shortcut.
    * The proposal lifecycle is the source of truth. The queue
      reflects the operator-facing state.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from ..proposal_lifecycle import (
    ProposalStatus,
    is_valid_transition as is_valid_proposal_transition,
)
from ..proposal_store import ProposalEvent, ProposalStore
from .object import ReviewItem, ReviewStatus
from .queue import ReviewQueue


class ReviewAction(str, Enum):
    """Two possible human review verdicts."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_proposal_status(action: ReviewAction) -> ProposalStatus:
    if action == ReviewAction.APPROVE:
        return ProposalStatus.APPROVED
    return ProposalStatus.REJECTED


def _to_review_status(action: ReviewAction) -> ReviewStatus:
    if action == ReviewAction.APPROVE:
        return ReviewStatus.APPROVED
    return ReviewStatus.REJECTED


class ReviewError(ValueError):
    """Raised when a review action violates the lifecycle."""


@dataclass
class ReviewManager:
    """Review gate over a ReviewQueue + ProposalStore."""

    queue: ReviewQueue
    proposal_store: ProposalStore

    def approve(
        self,
        review_id: str,
        reviewer: str = "",
        note: str = "",
    ) -> ProposalEvent:
        return self._act(ReviewAction.APPROVE, review_id, reviewer, note)

    def reject(
        self,
        review_id: str,
        reviewer: str = "",
        note: str = "",
    ) -> ProposalEvent:
        return self._act(ReviewAction.REJECT, review_id, reviewer, note)

    def _act(
        self,
        action: ReviewAction,
        review_id: str,
        reviewer: str,
        note: str,
    ) -> ProposalEvent:
        latest = self.queue.get(review_id)
        if latest is None:
            raise ReviewError("unknown review_id: " + str(review_id))
        if latest.status != ReviewStatus.PENDING.value:
            raise ReviewError(
                "review " + str(review_id) + " is not PENDING "
                "(latest status: " + str(latest.status) + ")"
            )

        new_proposal_status = _to_proposal_status(action)
        if not is_valid_proposal_transition(
            ProposalStatus.PENDING_REVIEW, new_proposal_status,
        ):
            raise ReviewError(
                "forbidden proposal transition: PENDING_REVIEW -> "
                + new_proposal_status.value
            )

        self.queue.append_status_change(
            review_id, _to_review_status(action).value,
        )

        verb = "approved" if action == ReviewAction.APPROVE else "rejected"
        event = ProposalEvent(
            proposal_id=latest.proposal_id,
            feedback_id="",
            target_identity=latest.target_identity,
            from_status=ProposalStatus.PENDING_REVIEW.value,
            to_status=new_proposal_status.value,
            timestamp=_now_iso(),
            note=(
                verb + " by " + (reviewer or "<unspecified>")
                + (": " + note if note else "")
            ),
        )
        self.proposal_store.append(event)
        return event


__all__ = [
    "ReviewAction",
    "ReviewError",
    "ReviewManager",
]
