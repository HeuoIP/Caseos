"""Evolution Audit Record V1 (Sprint 22.4-E, ADR-020 Rule 3).

The ``EvolutionAuditRecord`` is the **13-field, immutable
audit schema** mandated by ADR-020 Rule 3:

    before
    after
    reason
    proposal_id
    reviewer
    timestamp

extended to a complete per-evolution record with the
versioning and identity fields a future Sprint 22.4.x
mutation runtime will need.

The record is **frozen**. The ``before_snapshot`` and
``after_snapshot`` dicts are **deep-copied** in
``__post_init__`` so caller mutations cannot leak in.

Required fields (Sprint 22.4-E spec Task 1):

    audit_id            unique identifier
    transaction_id      the EvolutionTransaction this audit
                        describes
    proposal_id         the LearningProposal that originated
                        the change
    target_identity     the KO that would change
    previous_version    the version_number before the change
                        (None for initial version)
    new_version         the version_number after the change
    before_snapshot     snapshot of KO before the change
    after_snapshot      snapshot of KO after the change
                        (None in V1; the runtime does not yet
                        compute the new value)
    change_type         taxonomy (boundary_update / ...)
    reason              human-readable reason
    reviewer            the human who approved the change
    created_at          ISO timestamp (datetime)
    rollback_reference  pointer to the rollback audit record;
                        stored but never used in V1

Architecture boundary (Sprint 22.4-E spec Task 3):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from ..contracts.change_type import EvolutionChangeType


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _coerce_change_type(value):
    # Coerce string -> EvolutionChangeType when possible.
    # Tolerant: invalid strings stay as strings.
    if isinstance(value, EvolutionChangeType):
        return value
    if isinstance(value, str):
        try:
            return EvolutionChangeType(value)
        except ValueError:
            return value
    return value


@dataclass(frozen=True)
class EvolutionAuditRecord:
    """A single per-evolution audit record. Immutable.

    The dataclass is **frozen**: mutation raises
    ``FrozenInstanceError``. The ``before_snapshot`` and
    ``after_snapshot`` dicts are deep-copied in
    ``__post_init__`` so caller mutations do not leak in.
    """

    audit_id: str
    transaction_id: str
    proposal_id: str
    target_identity: str
    previous_version: Optional[int]
    new_version: int
    before_snapshot: dict[str, Any]
    after_snapshot: Optional[dict[str, Any]]
    change_type: Any  # EvolutionChangeType (annotation only)
    reason: str
    reviewer: str
    created_at: datetime
    rollback_reference: Optional[str]

    def __post_init__(self) -> None:
        # Defensive deep-copy of both snapshot dicts so caller
        # mutations cannot leak into the record. The frozen
        # dataclass would otherwise share the caller's dict
        # reference.
        if isinstance(self.before_snapshot, dict):
            object.__setattr__(
                self, "before_snapshot",
                copy.deepcopy(self.before_snapshot),
            )
        if isinstance(self.after_snapshot, dict):
            object.__setattr__(
                self, "after_snapshot",
                copy.deepcopy(self.after_snapshot),
            )
        # Sprint 22.4-I: coerce string change_type to
        # EvolutionChangeType. Invalid strings are left as-is
        # so the audit still records what was attempted.
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


__all__ = ["EvolutionAuditRecord"]
