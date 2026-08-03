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
    change_type             taxonomy value: boundary_update | principle_update
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
        * caseos.knowledge.objects
        * stdlib

The dataclass is **frozen**. The intent is append-only by contract.
``to_dict`` converts ``created_at`` to an ISO string so the result
is JSON-safe.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


VALID_CHANGE_TYPES: frozenset[str] = frozenset({
    "boundary_update",
    "principle_update",
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
    change_type: str
    target_field: str
    current_value: Optional[str]
    proposed_value: Optional[str]
    reason: str
    risk_level: str
    requires_human_review: bool
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        # JSON-safe: serialise datetime as ISO string.
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out


__all__ = [
    "ChangeIntent",
    "VALID_CHANGE_TYPES",
    "VALID_RISK_LEVELS",
]
