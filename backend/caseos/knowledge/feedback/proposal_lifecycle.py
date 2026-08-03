"""Learning Proposal Lifecycle (Sprint 22.3, ADR-018).

The proposal lifecycle is **four states**:

    CREATED
        |
        v
    PENDING_REVIEW
        |
        +---------+
        |         |
        v         v
    APPROVED    REJECTED

Both APPROVED and REJECTED are terminal. The proposal lifecycle is
the human-review gate from Sprint 22.3 spec Task 2.

Forward-only rule (Sprint 22.3 spec Task 2):

    The lifecycle can ONLY move forward:

      * CREATED       -> PENDING_REVIEW
      * PENDING_REVIEW -> APPROVED
      * PENDING_REVIEW -> REJECTED

    Rejected transitions (enforced by ``is_valid_transition``):

      * APPROVED   -> CREATED        (backward)
      * REJECTED   -> APPROVED       (terminal -> terminal, forbidden)
      * PENDING_REVIEW -> CREATED    (backward)
      * Any same-state transition    (e.g. APPROVED -> APPROVED)
      * Any skip transition          (e.g. CREATED -> APPROVED)

The module declares lifecycle states only. The lifecycle store
(see ``proposal_store.py``) records the events; the integration
layer (``proposal_integration.py``) is the only place that
combines evaluation output with this lifecycle.
"""
from __future__ import annotations

from enum import Enum
from typing import Iterable


class ProposalStatus(str, Enum):
    """Four-state proposal lifecycle."""

    CREATED = "CREATED"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# Ordered lifecycle. Used by ``is_valid_transition`` to verify that
# a requested transition is forward-only and well-formed.
LIFECYCLE_ORDER: tuple[ProposalStatus, ...] = (
    ProposalStatus.CREATED,
    ProposalStatus.PENDING_REVIEW,
    ProposalStatus.APPROVED,
    ProposalStatus.REJECTED,
)

# Terminal states. Once a proposal is APPROVED or REJECTED, it
# does not move again. Sprint 22.3 does not implement a re-open
# path (that would be a future ADR).
TERMINAL_STATES: frozenset[ProposalStatus] = frozenset({
    ProposalStatus.APPROVED,
    ProposalStatus.REJECTED,
})


def is_valid_transition(
    from_status: ProposalStatus,
    to_status: ProposalStatus,
) -> bool:
    """Return True iff ``to_status`` is a permitted forward step.

    Rules enforced:

      * CREATED -> PENDING_REVIEW                (allowed)
      * PENDING_REVIEW -> APPROVED               (allowed)
      * PENDING_REVIEW -> REJECTED               (allowed)
      * APPROVED -> REJECTED                     (rejected, both terminal)
      * REJECTED -> APPROVED                     (rejected, both terminal)
      * APPROVED -> CREATED                      (rejected, backward)
      * REJECTED -> CREATED                      (rejected, backward)
      * PENDING_REVIEW -> CREATED                (rejected, backward)
      * CREATED -> APPROVED                      (rejected, skip)
      * CREATED -> REJECTED                      (rejected, skip)
      * Any same-state transition                (rejected)
    """
    if from_status not in LIFECYCLE_ORDER:
        return False
    if to_status not in LIFECYCLE_ORDER:
        return False
    if from_status in TERMINAL_STATES:
        return False
    if from_status == ProposalStatus.CREATED:
        return to_status == ProposalStatus.PENDING_REVIEW
    # from_status == PENDING_REVIEW
    return to_status in (ProposalStatus.APPROVED, ProposalStatus.REJECTED)


def is_terminal(status: ProposalStatus) -> bool:
    """Return True iff the status is APPROVED or REJECTED."""
    return status in TERMINAL_STATES


def allowed_next_states(
    from_status: ProposalStatus,
) -> tuple[ProposalStatus, ...]:
    """Return the set of states reachable from ``from_status``."""
    if from_status == ProposalStatus.CREATED:
        return (ProposalStatus.PENDING_REVIEW,)
    if from_status == ProposalStatus.PENDING_REVIEW:
        return (ProposalStatus.APPROVED, ProposalStatus.REJECTED)
    return ()


def all_statuses() -> Iterable[ProposalStatus]:
    """Yield every declared status, in lifecycle order."""
    return tuple(LIFECYCLE_ORDER)


__all__ = [
    "ProposalStatus",
    "LIFECYCLE_ORDER",
    "TERMINAL_STATES",
    "is_valid_transition",
    "is_terminal",
    "allowed_next_states",
    "all_statuses",
]
