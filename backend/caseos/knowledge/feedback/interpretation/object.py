"""Change Intent Object (Sprint 22.3.2, ADR-018 Section 3).

A ``ChangeIntent`` is the **safe, audit-friendly translation** of an
approved Learning Proposal into a candidate knowledge update.
It is **not** a write to the Knowledge Object. It is a structured
suggestion that a future Knowledge Evolution sprint (22.4) will
turn into an actual KO field change.

Required fields (Sprint 22.3.2 spec section Task 1):

    intent_id               unique identifier
    proposal_id             the LearningProposal this intent maps from
    target_identity         the KO this intent targets
    change_type             EvolutionChangeType (enum). Sprint 22.4-I
                            aligned this field with the rest of the
                            evolution pipeline. The enum value is
                            coerced from a plain string in
                            ``__post_init__`` so legacy callers that
                            pass ``"boundary_update"`` keep working.
                            JSON serialisation outputs the underlying
                            string value (e.g. ``"boundary_update"``).
    target_field            the KO field name: boundary | principle
    current_value           string snapshot of the KO field today
                            (None when the field is absent)
    proposed_value          string proposal for the future value
                            (None in V1 -- the policy never invents values)
    reason                  why the change is suggested (from proposal)
    risk_level              low | medium | high
    requires_human_review   always True in V1 (cannot be turned off)
    created_at              ISO timestamp (datetime)

Architecture boundary (Sprint 22.3.2 spec Task 6):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.governance
        * caseos.knowledge.intake
    This module MAY import from:
        * caseos.knowledge.feedback
        * caseos.knowledge.evolution.contracts
        * caseos.knowledge.objects
        * stdlib

The dataclass is **frozen**. The intent is append-only by contract.
``to_dict`` converts ``created_at`` to an ISO string and
``change_type`` to its enum ``value`` so the result is JSON-safe.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ...evolution.contracts.change_type import EvolutionChangeType


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _coerce_change_type(value: Any) -> Any:
    """Coerce ``value`` to ``EvolutionChangeType`` when possible.

    Returns the value unchanged (e.g. an invalid string) when
    the value cannot be coerced. The downstream validator
    (``validate_change_intent``) is responsible for rejecting
    any value that is not in ``VALID_CHANGE_TYPES``.
    """
    if isinstance(value, EvolutionChangeType):
        return value
    if isinstance(value, str):
        try:
            return EvolutionChangeType(value)
        except ValueError:
            return value
    return value


VALID_CHANGE_TYPES: frozenset = frozenset({
    EvolutionChangeType.BOUNDARY_UPDATE,
    EvolutionChangeType.PRINCIPLE_UPDATE,
})

VALID_RISK_LEVELS: frozenset[str] = frozenset({
    "low",
    "medium",
    "high",
})


@dataclass(frozen=True)
class ChangeIntent:
    """A safe change intent. Never auto-applies."""

    intent_id: str
    proposal_id: str
    target_identity: str
    change_type: Any  # EvolutionChangeType (annotation only)
    target_field: str
    current_value: Optional[str]
    proposed_value: Optional[str]
    reason: str
    risk_level: str
    requires_human_review: bool
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        # Coerce strings to EvolutionChangeType. The dataclass
        # is frozen, so we must use object.__setattr__. Invalid
        # strings are left as-is; validate_change_intent will
        # then reject the intent.
        coerced = _coerce_change_type(self.change_type)
        if coerced is not self.change_type:
            object.__setattr__(self, "change_type", coerced)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        # JSON-safe: serialise datetime as ISO string.
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        # JSON-safe: serialise EvolutionChangeType as its value.
        ct = out.get("change_type")
        if isinstance(ct, EvolutionChangeType):
            out["change_type"] = ct.value
        return out


__all__ = [
    "ChangeIntent",
    "VALID_CHANGE_TYPES",
    "VALID_RISK_LEVELS",
]
