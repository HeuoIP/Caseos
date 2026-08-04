"""Change Intent Validator (Sprint 22.3.2, ADR-018 Section 3,
Sprint 22.4-I contract alignment).

Validates a ``ChangeIntent`` before it is exposed to downstream
consumers. The validator is a pure function of its input.

Checks (Sprint 22.3.2 spec Task 4, Sprint 22.4-I update):

    * required fields are present and non-empty:
        intent_id, proposal_id, target_identity,
        change_type (str or EvolutionChangeType),
        target_field, reason, risk_level
    * change_type is in the V1 allow-list
        (frozenset of EvolutionChangeType members)
    * risk_level is one of low / medium / high
    * requires_human_review is True (cannot be turned off)

Sprint 22.4-I aligned ``change_type`` with
``EvolutionChangeType``. The validator accepts both the
enum member and its underlying string form (``str(member)``
or ``member.value``) for backward compatibility. The intent
itself stores the enum member after coercion in
``ChangeIntent.__post_init__``; here we only need to read
the value.

The validator returns ``(is_valid, message)`` so the caller can
emit a human-readable reason. It does NOT raise on invalid input
because the policy already filters most cases; the validator is
a defence-in-depth check.

Architecture boundary: this module does NOT import from
``caseos.intelligence.*`` or any of the forbidden retrieval /
governance / intake packages.
"""
from __future__ import annotations

from typing import Any, Optional, Tuple

from ...evolution.contracts.change_type import EvolutionChangeType
from .object import (
    VALID_CHANGE_TYPES,
    VALID_RISK_LEVELS,
    ChangeIntent,
)


def _has_text(value: Any) -> bool:
    """True when ``value`` is a non-empty string or enum.

    After Sprint 22.4-I coercion the ``change_type`` field
    on a ChangeIntent is an ``EvolutionChangeType`` enum.
    Other required fields remain plain strings.
    """
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, EvolutionChangeType):
        return True
    return False


def _display(value: Any) -> str:
    """Render ``value`` as a string for diagnostic messages.

    Enums render as their ``.value`` so error messages stay
    human-readable.
    """
    if isinstance(value, EvolutionChangeType):
        return value.value
    return str(value)


REQUIRED_TEXT_FIELDS: tuple = (
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

    for field_name in REQUIRED_TEXT_FIELDS:
        value = getattr(intent, field_name, None)
        if not _has_text(value):
            return False, "missing field: " + field_name

    if intent.change_type not in VALID_CHANGE_TYPES:
        return (
            False,
            "change_type not in V1 allow-list: " + _display(intent.change_type),
        )

    if intent.risk_level not in VALID_RISK_LEVELS:
        return False, "risk_level not in V1 allow-list: " + str(intent.risk_level)

    if intent.requires_human_review is not True:
        return False, "requires_human_review must be True"

    return True, ""


__all__ = ["validate_change_intent", "REQUIRED_TEXT_FIELDS"]
