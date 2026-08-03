"""Evolution Audit V1 (Sprint 22.4-A, ADR-020).

The audit log is the **single source of truth for what
happened** in the evolution layer. In V1, "what happened" is
the validator pass/fail decision, the lifecycle transition,
and any future rollback. The audit log is append-only by
construction; corrections arrive as new records, not as edits.

Required fields (Sprint 22.4-A spec Task 4):

    audit_id       unique identifier
    transaction_id the EvolutionTransaction this record
                   describes
    action         the action performed
                   (e.g. "validated", "rejected", "transitioned",
                    "stopped_v1_boundary")
    actor          the human or system that performed the action
    before         snapshot of state before the action
                   (may be a dict, a status string, or None)
    after          snapshot of state after the action
                   (may be a dict, a status string, or None)
    reason         human-readable reason for the action
    timestamp      ISO timestamp (datetime)

Append-only contract (Sprint 22.4-A spec Task 4):

    Forbidden methods on the store (raise TypeError):
        * update
        * delete
        * overwrite
        * clear

    The only write is ``append(audit_record)``.
    The only reads are ``list()``, ``count()``,
    ``list_for_transaction(transaction_id)``.

Architecture boundary (Sprint 22.4-A spec Task 6):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.objects
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * stdlib
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, List, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


class EvolutionAuditError(Exception):
    """Raised when a forbidden operation is attempted on the store."""


@dataclass(frozen=True)
class EvolutionAuditRecord:
    """A single audit record. Append-only by contract."""

    audit_id: str
    transaction_id: str
    action: str
    actor: str
    before: Any
    after: Any
    reason: str
    timestamp: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        ts = out.get("timestamp")
        if isinstance(ts, datetime):
            out["timestamp"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out


class EvolutionAuditStore:
    """Append-only audit store.

    The internal list is a ``list`` and is only ever appended
    to via the ``append`` method. The four forbidden methods
    (``update``, ``delete``, ``overwrite``, ``clear``) raise
    ``TypeError`` so the contract is testable in CI.
    """

    def __init__(self) -> None:
        self._records: List[EvolutionAuditRecord] = []

    def append(self, record: EvolutionAuditRecord) -> EvolutionAuditRecord:
        """Append a new audit record. Returns the same record."""
        if not isinstance(record, EvolutionAuditRecord):
            raise EvolutionAuditError(
                "record must be an EvolutionAuditRecord instance"
            )
        self._records.append(record)
        return record

    def make_and_append(
        self,
        *,
        transaction_id: str,
        action: str,
        actor: str,
        before: Any = None,
        after: Any = None,
        reason: str = "",
        audit_id: Optional[str] = None,
    ) -> EvolutionAuditRecord:
        """Convenience: build a record with a fresh audit_id and append."""
        record = EvolutionAuditRecord(
            audit_id=audit_id or str(uuid.uuid4()),
            transaction_id=transaction_id,
            action=action,
            actor=actor,
            before=before,
            after=after,
            reason=reason,
        )
        return self.append(record)

    def list(self) -> List[EvolutionAuditRecord]:
        """Return a copy of the record list. Caller cannot mutate store."""
        return list(self._records)

    def count(self) -> int:
        return len(self._records)

    def list_for_transaction(
        self, transaction_id: str,
    ) -> List[EvolutionAuditRecord]:
        """Return all records for a given transaction_id, in append order."""
        return [
            r for r in self._records if r.transaction_id == transaction_id
        ]

    # -- Forbidden operations (Sprint 22.4-A spec Task 4) -------------

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "EvolutionAuditStore.update is forbidden; store is append-only"
        )

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "EvolutionAuditStore.delete is forbidden; store is append-only"
        )

    def overwrite(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "EvolutionAuditStore.overwrite is forbidden; store is append-only"
        )

    def clear(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "EvolutionAuditStore.clear is forbidden; store is append-only"
        )


__all__ = [
    "EvolutionAuditRecord",
    "EvolutionAuditStore",
    "EvolutionAuditError",
]
