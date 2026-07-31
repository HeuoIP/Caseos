"""Feedback Lifecycle (Sprint 22.1, ADR-018 Section 4 + Sprint 22.1 spec section 4).

The feedback lifecycle is **eight states**:

    RECEIVED
        |
        v
    VALIDATING
        |
        +-- rejected ---------------> REJECTED
        |
        v
    VALIDATED
        |
        v
    PROPOSAL_CREATED
        |
        v
    REVIEW_REQUIRED
        |
        +-- approved --------------> APPROVED
        |
        +-- rejected (human) -----> REJECTED
        |
        v
    APPLIED   (out of scope for Sprint 22.1 V1)

Rules (Sprint 22.1 spec section 4):

    * New incoming feedback starts as RECEIVED.
    * The first governance check (Validator) moves it to VALIDATING.
      On success it moves to VALIDATED; on failure it moves to
      REJECTED.
    * Once validated, the proposal generator moves it to
      PROPOSAL_CREATED, then immediately to REVIEW_REQUIRED (so
      that a human reviewer picks it up).
    * A human reviewer can transition REVIEW_REQUIRED -> APPROVED
      or REVIEW_REQUIRED -> REJECTED.
    * Approval may (in a future sprint) eventually transition to
      APPLIED. Sprint 22.1 does NOT implement APPLIED.

Forbidden transitions (Sprint 22.1 spec section 4):

    * RECEIVED -> APPLIED  (skip validation; direct application)
    * any backward transition (e.g. VALIDATED -> RECEIVED)
    * any same-state transition (REJECTED -> REJECTED)

This module is the only place lifecycle states are declared.
The manager enforces the forward-only rule via `is_forward`.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class FeedbackStatus(str, Enum):
    """Eight-stage feedback lifecycle."""

    RECEIVED = "RECEIVED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    PROPOSAL_CREATED = "PROPOSAL_CREATED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    APPLIED = "APPLIED"


# Ordered lifecycle. Used by ``is_forward`` to verify that a
# requested transition is forward-only.
LIFECYCLE_ORDER: tuple[FeedbackStatus, ...] = (
    FeedbackStatus.RECEIVED,
    FeedbackStatus.VALIDATING,
    FeedbackStatus.VALIDATED,
    FeedbackStatus.PROPOSAL_CREATED,
    FeedbackStatus.REVIEW_REQUIRED,
    FeedbackStatus.APPROVED,
    FeedbackStatus.APPLIED,
)

# Terminal states. APPLIED is NOT terminal in V1 because we do not
# implement it; it remains a forward-only future slot.
TERMINAL_STATES: frozenset[FeedbackStatus] = frozenset({
    FeedbackStatus.REJECTED,
})

# Statuses that represent a feedback that has been "drained" out
# of the active loop. APPROVED is the gate before APPLIED.
DRAINED_STATES: frozenset[FeedbackStatus] = frozenset({
    FeedbackStatus.APPROVED,
    FeedbackStatus.APPLIED,
})


def is_forward(from_status: FeedbackStatus, to_status: FeedbackStatus) -> bool:
    """Return True if `to_status` is strictly after `from_status`
    in the lifecycle order.

    Same-state, backward, and skip transitions are rejected.

    Special cases:

      * ``REJECTED`` is terminal. No forward transition from
        REJECTED is allowed (a rejected feedback stays rejected).
      * ``PROPOSAL_CREATED -> REVIEW_REQUIRED`` is a forward
        transition (index 3 -> index 4) and is allowed.

    The Sprint 22.1 spec also forbids ``RECEIVED -> APPLIED``
    directly. ``is_forward`` reports ``False`` for that pair
    because their indices differ by 6 (number of intermediate
    states), which is not a single forward step. The transition
    is rejected in the manager by checking `is_forward` strictly.
    """
    try:
        i = LIFECYCLE_ORDER.index(from_status)
        j = LIFECYCLE_ORDER.index(to_status)
    except ValueError:
        return False
    if from_status in TERMINAL_STATES:
        return False
    return j == i + 1


def is_terminal(status: FeedbackStatus) -> bool:
    """Return True if the status is terminal (REJECTED)."""
    return status in TERMINAL_STATES


def is_valid_transition(
    from_status: FeedbackStatus, to_status: FeedbackStatus,
) -> bool:
    """Strict transition check. Returns True if and only if
    `to_status` is the immediate successor of `from_status`, OR
    `to_status` is a terminal state reachable from a
    non-terminal predecessor.

    Rules:

      * ``REJECTED`` (terminal) is reachable from VALIDATING
        (rejection at validation time) and from REVIEW_REQUIRED
        (rejection by human reviewer).
      * Any other same-state, backward, or skip transition is
        rejected.

    This is the gate the manager uses. The forbidden transition
    ``RECEIVED -> APPLIED`` is rejected because ``APPLIED`` is
    not the immediate successor of ``RECEIVED`` (it is 6 steps
    ahead).
    """
    if from_status in TERMINAL_STATES:
        return False
    if to_status in TERMINAL_STATES:
        # REJECTED is reachable from VALIDATING and REVIEW_REQUIRED.
        return from_status in (
            FeedbackStatus.VALIDATING,
            FeedbackStatus.REVIEW_REQUIRED,
        )
    return is_forward(from_status, to_status)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class FeedbackEvent:
    """A single append-only lifecycle event.

    Each transition appends a new ``FeedbackEvent`` to the store.
    The current logical state of a feedback is the latest event
    for that feedback_id. The original ``FeedbackObject`` is never
    mutated; the ``snapshot`` field carries the object state at the
    moment of the transition for audit purposes.
    """

    event_id: str
    feedback_id: str
    from_status: Optional[str]  # None for the initial RECEIVED event
    to_status: str
    timestamp: str = field(default_factory=_now_iso)
    snapshot: dict[str, Any] = field(default_factory=dict)
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_event(
    feedback_id: str,
    from_status: Optional[FeedbackStatus],
    to_status: FeedbackStatus,
    snapshot: Optional[dict[str, Any]] = None,
    note: str = "",
    event_id: Optional[str] = None,
) -> FeedbackEvent:
    """Convenience constructor for ``FeedbackEvent``."""
    return FeedbackEvent(
        event_id=event_id or str(uuid.uuid4()),
        feedback_id=feedback_id,
        from_status=from_status.value if from_status is not None else None,
        to_status=to_status.value,
        snapshot=dict(snapshot or {}),
        note=note,
    )


__all__ = [
    "FeedbackEvent",
    "FeedbackStatus",
    "LIFECYCLE_ORDER",
    "TERMINAL_STATES",
    "DRAINED_STATES",
    "is_forward",
    "is_valid_transition",
    "is_terminal",
    "new_event",
]
