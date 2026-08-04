"""Evolution Transaction Object V1 (Sprint 22.4-A, ADR-020 Rule 1).

The transaction is the contract of intent between the
Interpretation Policy and the Knowledge Evolution runtime.
It is a safe, never-auto-applied artifact.

Sprint 22.4-I aligned ``change_type`` with the unified
``EvolutionChangeType`` enum. The field type is annotated
as ``Any`` because dataclass annotations are informational;
the value is coerced from a plain string in
``__post_init__`` so legacy callers that pass
``"boundary_update"`` keep working. JSON serialisation
outputs the underlying string value via ``.value``.

Architecture boundary (Sprint 22.4-A spec Task 6):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * caseos.knowledge.evolution.contracts
        * stdlib
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .contracts.change_type import EvolutionChangeType


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


class EvolutionStatus:
    """Lifecycle states for an EvolutionTransaction.

    The strings are the canonical values. The class is a
    namespace; it is not an Enum so that JSON serialisation
    stays trivial (the value IS the string).

    V1 special rule (Sprint 22.4-A spec Task 2):

        The ``APPLIED`` state exists in the enum but
        transitions INTO ``APPLIED`` are FORBIDDEN in V1.
        V1 hard-stops at ``APPROVED`` plus the audit record.
    """

    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    APPROVED = "APPROVED"
    APPLIED = "APPLIED"  # declared, not reachable in V1
    REJECTED = "REJECTED"

    ALL: frozenset[str] = frozenset({
        CREATED,
        VALIDATING,
        APPROVED,
        APPLIED,
        REJECTED,
    })

    TERMINAL: frozenset[str] = frozenset({
        APPROVED,
        APPLIED,
        REJECTED,
    })


def _coerce_change_type(value: Any) -> Any:
    """Coerce ``value`` to ``EvolutionChangeType`` when possible.

    Returns the value unchanged when the value cannot be
    coerced (e.g. an invalid string). Downstream validators
    are responsible for rejecting values outside the
    ``ALLOWED_CHANGE_TYPES`` set.
    """
    if isinstance(value, EvolutionChangeType):
        return value
    if isinstance(value, str):
        try:
            return EvolutionChangeType(value)
        except ValueError:
            return value
    return value


@dataclass(frozen=True)
class EvolutionTransaction:
    """A safe transaction. Never auto-applied.

    Sprint 22.4-I contract alignment: ``change_type`` is
    the unified ``EvolutionChangeType`` enum.
    """

    transaction_id: str
    proposal_id: str
    change_intent_id: str
    target_identity: str
    target_version: int
    change_type: Any  # EvolutionChangeType (annotation only)
    before_snapshot: dict
    requested_change: Optional[str]
    reviewer: str
    status: str
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        # Coerce strings to EvolutionChangeType. Invalid strings
        # remain strings; the Governance Gate (G1) will then
        # reject them. The dataclass is frozen, so we use
        # object.__setattr__ for the reassignment.
        coerced = _coerce_change_type(self.change_type)
        if coerced is not self.change_type:
            object.__setattr__(self, "change_type", coerced)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = asdict(self)
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        ct = out.get("change_type")
        if isinstance(ct, EvolutionChangeType):
            out["change_type"] = ct.value
        return out


__all__ = ["EvolutionTransaction"]
