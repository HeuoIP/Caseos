"""EvolutionTransaction Object (Sprint 22.4-A, ADR-020).

An ``EvolutionTransaction`` is the **safe transaction-shaped
wrapper** around an approved ``ChangeIntent``. The transaction
is the unit of audit, governance validation, and (in a future
Sprint 22.4.x) the unit of Knowledge Object write-back.

V1 hard rule: this object does NOT mutate any external state.
It is a frozen, JSON-serialisable record that can be validated,
queued, audited, and rendered as a report. It is NOT applied.

Required fields (Sprint 22.4-A spec Task 1):

    transaction_id         unique identifier
    proposal_id            the LearningProposal this tx maps from
    change_intent_id       the ChangeIntent this tx maps from
    target_identity        the KO this tx would affect
    target_version         the version this tx would produce
    change_type            taxonomy (boundary_update / principle_update)
    before_snapshot        snapshot of the KO field at the
                           time the tx was created
    requested_change       human-readable description of the
                           change (may be None in V1)
    reviewer               the human who approved the tx
    status                 EvolutionStatus value
    created_at             ISO timestamp (datetime)

Architecture boundary (Sprint 22.4-A spec Task 6):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.objects
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * stdlib

The dataclass is **frozen**. The transaction is append-only by
contract. ``to_dict`` converts ``created_at`` to an ISO string
so the result is JSON-safe.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


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


@dataclass(frozen=True)
class EvolutionTransaction:
    """A safe transaction. Never auto-applied.

    The transaction is the contract of intent between the
    Interpretation Policy and the future Knowledge Evolution
    runtime. In V1 it stops at APPROVED + Audit Record; the
    APPLIED transition is gated on a future Sprint 22.4.x.
    """

    transaction_id: str
    proposal_id: str
    change_intent_id: str
    target_identity: str
    target_version: int
    change_type: str
    before_snapshot: dict[str, Any]
    requested_change: Optional[str]
    reviewer: str
    status: str
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = asdict(self)
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out


__all__ = [
    "EvolutionTransaction",
    "EvolutionStatus",
]
