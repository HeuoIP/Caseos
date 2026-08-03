"""Evolution Transaction Lifecycle V1 (Sprint 22.4-A, ADR-020).

The lifecycle is a **state machine** with five declared states
and a small, explicit set of allowed transitions. V1 hard-stops
at APPROVED plus the audit record; the APPLIED state is in the
enum (so the lifecycle is future-extensible) but no transition
into APPLIED is allowed in V1.

States (Sprint 22.4-A spec Task 2):

    CREATED
        |
        v
    VALIDATING
        |
        v
    APPROVED  (V1 terminal in the happy path)

    CREATED
        |
        v
    REJECTED  (V1 terminal in the sad path)

    APPROVED
        |
        X  <-- APPLIED  FORBIDDEN in V1
                 (will be allowed in a future Sprint 22.4.x
                 when the Knowledge Object mutation runtime
                 ships under ADR-020 Rules 1-5)

Allowed transitions V1:

    CREATED      -> VALIDATING
    CREATED      -> REJECTED
    VALIDATING   -> APPROVED
    VALIDATING   -> REJECTED

Forbidden transitions V1:

    CREATED      -> APPROVED   (must go through VALIDATING)
    CREATED      -> APPLIED    (must go through APPROVED)
    VALIDATING   -> CREATED    (no rollback in V1)
    VALIDATING   -> APPLIED    (must go through APPROVED)
    APPROVED     -> APPLIED    (V1 hard-stop)
    APPROVED     -> CREATED    (no rollback in V1)
    APPROVED     -> VALIDATING (no rollback in V1)
    APPROVED     -> REJECTED   (terminal)
    REJECTED     -> *          (terminal)
    APPLIED      -> *          (terminal, but unreachable in V1)

Architecture boundary (Sprint 22.4-A spec Task 6):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.feedback
        * stdlib
"""
from __future__ import annotations

from typing import Mapping

from .object import EvolutionStatus


# Mapping: from_status -> set of allowed to_status values.
# V1 hard-stops at APPROVED. The APPLIED key is intentionally
# absent to make the V1 ceiling obvious.
ALLOWED_TRANSITIONS: Mapping[str, frozenset[str]] = {
    EvolutionStatus.CREATED: frozenset({
        EvolutionStatus.VALIDATING,
        EvolutionStatus.REJECTED,
    }),
    EvolutionStatus.VALIDATING: frozenset({
        EvolutionStatus.APPROVED,
        EvolutionStatus.REJECTED,
    }),
    EvolutionStatus.APPROVED: frozenset(),  # V1 terminal
    EvolutionStatus.REJECTED: frozenset(),  # terminal
    # APPLIED is not in the mapping; see module docstring.
}


def is_valid_transition(from_status: str, to_status: str) -> bool:
    """Return True iff the transition is in the V1 allow-list.

    The function is a pure check. It does NOT mutate state. It
    does NOT raise. A future Sprint 22.4.x may extend
    ``ALLOWED_TRANSITIONS`` to add the APPLIED transition; the
    contract of this function is "ask the table, return bool".
    """
    if from_status not in ALLOWED_TRANSITIONS:
        return False
    if to_status not in EvolutionStatus.ALL:
        return False
    return to_status in ALLOWED_TRANSITIONS[from_status]


__all__ = [
    "ALLOWED_TRANSITIONS",
    "is_valid_transition",
]
