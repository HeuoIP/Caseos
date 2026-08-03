"""Change Intent Validator (Sprint 22.3.2, ADR-018 Section 3).

Validates a ``ChangeIntent`` before it is exposed to downstream
consumers. The validator is a pure function of its input.

Checks (Sprint 22.3.2 spec Task 4):

    * required string fields are non-empty
        (intent_id, proposal_id, target_identity, change_type,
        target_field, reason)
    * change_type is in the V1 allow-list
    * risk_level is one of low / medium / high
    * requires_human_review is True (cannot be turned off)

The validator returns ``(is_valid, message)`` so the caller can
emit a human-readable reason. It does NOT raise on invalid input
because the policy already filters most cases; the validator is
a defence-in-depth check.

Architecture boundary: this module does NOT import from
``caseos.intelligence.*`` or any of the forbidden retrieval /
governance / intake packages.
"""
from __future__ import annotations

from typing import Optional, Tuple

from .object import (
    VALID_CHANGE_TYPES,
    VALID_RISK_LEVELS,
    ChangeIntent,
)


REQUIRED_STRING_FIELDS: tuple[str, ...] = (
    "intent_id",
    "proposal_id",
    "target_identity",
    "change_type",
    "target_field",
    "reason",
    "risk_level",
)


def validate_change_intent(
    intent: Optional[ChangeIntent],
) -> Tuple[bool, str]:
    """Return ``(True, "")`` when the intent is valid.

    On any failure, return ``(False, reason)``.
    """
    if intent is None:
        return False, "intent is None"

    for field_name in REQUIRED_STRING_FIELDS:
        value = getattr(intent, field_name, None)
        if not isinstance(value, str) or not value.strip():
            return False, "missing field: " + field_name

    if intent.change_type not in VALID_CHANGE_TYPES:
        return False, "change_type not in V1 allow-list: " + intent.change_type

    if intent.risk_level not in VALID_RISK_LEVELS:
        return False, "risk_level not in V1 allow-list: " + intent.risk_level

    if intent.requires_human_review is not True:
        return False, "requires_human_review must be True"

    return True, ""


__all__ = ["validate_change_intent", "REQUIRED_STRING_FIELDS"]
