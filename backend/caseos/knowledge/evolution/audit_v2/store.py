"""AuditStore V1 (Sprint 22.4-E, ADR-020 Rule 3).

The ``AuditStore`` is the **append-only container** for
``EvolutionAuditRecord`` instances. It is the schema-level
storage layer that a future Sprint 22.4.x mutation runtime
will write to.

The store is intentionally minimal in V1. It does not
enforce any global ordering, version-number invariant, or
transaction invariant; that is the job of the future
mutation runtime. The store is just a typed list with an
append-only contract.

Append-only contract (Sprint 22.4-E spec Task 2):

    Allowed methods:
        * append(record)          -- add an EvolutionAuditRecord
        * get(audit_id)           -- retrieve by audit_id
        * history(target_identity)-- all records for a KO,
                                    in append order
        * count()                 -- total records
        * list()                  -- copy of all records

    Forbidden methods (raise TypeError):
        * update
        * delete
        * overwrite
        * clear

The forbidden methods accept any arguments (positional or
keyword) and always raise ``TypeError``.

Rollback contract (Sprint 22.4-E spec Task 4):

    The store does NOT define:
        * restore()
        * rollback()
        * apply()

    The ``rollback_reference`` field on the record is
    stored but never used in V1. A future Sprint 22.4.x
    will introduce a separate rollback module under a new
    ADR; this store remains append-only.

Architecture boundary (Sprint 22.4-E spec Task 3):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, List, Optional

from .object import EvolutionAuditRecord


class AuditStoreError(Exception):
    """Raised when a forbidden operation is attempted on the store."""


class AuditStore:
    """Append-only container for ``EvolutionAuditRecord`` records.

    The internal list is a ``list`` and is only ever appended
    to via the ``append`` method. The four forbidden methods
    raise ``TypeError`` so the contract is testable in CI.

    The store has **no** ``restore``, ``rollback``, or
    ``apply`` method. The rollback_reference field on the
    record is preserved but never used.
    """

    def __init__(self) -> None:
        self._records: List[EvolutionAuditRecord] = []

    # ---- Allowed operations ----------------------------------------

    def append(self, record: EvolutionAuditRecord) -> EvolutionAuditRecord:
        """Append a new audit record. Returns the same record."""
        if not isinstance(record, EvolutionAuditRecord):
            raise AuditStoreError(
                "record must be an EvolutionAuditRecord instance"
            )
        self._records.append(record)
        return record

    def get(self, audit_id: str) -> Optional[EvolutionAuditRecord]:
        """Return the audit record with the given audit_id, or None."""
        for r in self._records:
            if r.audit_id == audit_id:
                return r
        return None

    def history(self, target_identity: str) -> List[EvolutionAuditRecord]:
        """Return all records for a target_identity, in append order."""
        return [
            r for r in self._records if r.target_identity == target_identity
        ]

    def count(self) -> int:
        return len(self._records)

    def list(self) -> List[EvolutionAuditRecord]:
        """Return a copy of the record list."""
        return list(self._records)

    def identities(self) -> List[str]:
        """Return the distinct list of target_identities, in first-seen order."""
        seen: List[str] = []
        for r in self._records:
            if r.target_identity not in seen:
                seen.append(r.target_identity)
        return seen

    # ---- Forbidden operations (Sprint 22.4-E spec Task 2) --------

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "AuditStore.update is forbidden; store is append-only"
        )

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "AuditStore.delete is forbidden; store is append-only"
        )

    def overwrite(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "AuditStore.overwrite is forbidden; store is append-only"
        )

    def clear(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "AuditStore.clear is forbidden; store is append-only"
        )

    # ---- Rollback contract (Sprint 22.4-E spec Task 4) -----------

    # Intentionally NO restore(), rollback(), or apply() method.
    # The rollback_reference field is stored on the record but
    # never used. A future Sprint 22.4.x rollback module will
    # consume the records under a new ADR.


__all__ = [
    "AuditStore",
    "AuditStoreError",
]
