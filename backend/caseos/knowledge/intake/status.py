"""Intake lifecycle status (Sprint 20.7 spec section 3).

The intake pipeline moves RawCaseObject through five states:

  NEW
    |
    v
  REVIEW_REQUIRED
    |
    v
  VALIDATED
    |
    v
  PROMOTED
    |
    v
  ACTIVE

Rules (per spec):

  - New incoming objects start as NEW.
  - The first governance check moves them to REVIEW_REQUIRED;
    on success they move to VALIDATED, on failure they stay in
    REVIEW_REQUIRED until a human reconsiders.
  - Promotion creates a Knowledge Object and moves the raw case
    to PROMOTED. The KO entering the corpus is then ACTIVE.
  - The original RawCaseObject is never mutated; transitions
    are append-only events on the manager, not rewrites of the
    stored object.

Intake is the stomach, governance is the immune system, the
Knowledge Object is the memory. This module only declares the
state names; transitions are enforced by IntakeManager."""

from __future__ import annotations

from enum import Enum


class IntakeStatus(str, Enum):
    "Five-state intake lifecycle.",
    NEW = "NEW",
    REVIEW_REQUIRED = "REVIEW_REQUIRED",
    VALIDATED = "VALIDATED",
    PROMOTED = "PROMOTED",
    ACTIVE = "ACTIVE"


# Ordered list of lifecycle states. Used by the manager to
# verify that a requested transition is forward-only.
LIFECYCLE_ORDER = (
    IntakeStatus.NEW,
    IntakeStatus.REVIEW_REQUIRED,
    IntakeStatus.VALIDATED,
    IntakeStatus.PROMOTED,
    IntakeStatus.ACTIVE,
)


def is_forward(from_status: "IntakeStatus", to_status: "IntakeStatus") -> bool:
    "Return True if 	o_status is strictly after rom_status",
    "in the lifecycle order. The manager rejects backward",
    "same-state, and skip transitions.",
    try:
        i = LIFECYCLE_ORDER.index(from_status)
        j = LIFECYCLE_ORDER.index(to_status)
    except ValueError:
        return False
    return j > i


__all__ = ["IntakeStatus", "LIFECYCLE_ORDER", "is_forward"]
