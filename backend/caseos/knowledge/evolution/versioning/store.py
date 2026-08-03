"""VersionStore (Sprint 22.4-D, ADR-020 Rule 2).

The ``VersionStore`` is the **append-only container** for
``KnowledgeVersion`` records. It is the storage layer that
a future Sprint 22.4.x mutation runtime will write to.

The store is intentionally minimal in V1. It does not enforce
a global ordering or a version-number invariant; that is the
job of the future mutation runtime. The store is just a
typed list with an append-only contract.

Append-only contract (Sprint 22.4-D spec Task 2):

    Allowed methods:
        * append(version)  -- add a KnowledgeVersion
        * get(identity)    -- latest version for identity
        * history(identity)-- all versions in append order
        * count()          -- total records
        * list()           -- copy of all records

    Forbidden methods (raise TypeError):
        * update
        * delete
        * overwrite
        * clear

The forbidden methods accept any arguments (positional or
keyword) and always raise ``TypeError``. This mirrors the
Sprint 22.3.1 Review Queue and Sprint 22.4-A Audit store
discipline.

Architecture boundary (Sprint 22.4-D spec Task 4):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, List, Optional

from .object import KnowledgeVersion


class VersionStoreError(Exception):
    """Raised when a forbidden operation is attempted on the store."""


class VersionStore:
    """Append-only container for ``KnowledgeVersion`` records.

    The internal list is a ``list`` and is only ever appended
    to via the ``append`` method. The four forbidden methods
    raise ``TypeError`` so the contract is testable in CI.
    """

    def __init__(self) -> None:
        self._versions: List[KnowledgeVersion] = []

    # ---- Allowed operations ----------------------------------------

    def append(self, version: KnowledgeVersion) -> KnowledgeVersion:
        """Append a new version record. Returns the same record."""
        if not isinstance(version, KnowledgeVersion):
            raise VersionStoreError(
                "version must be a KnowledgeVersion instance"
            )
        self._versions.append(version)
        return version

    def get(self, identity: str) -> Optional[KnowledgeVersion]:
        """Return the latest version for ``identity`` or None."""
        history = self.history(identity)
        return history[-1] if history else None

    def history(self, identity: str) -> List[KnowledgeVersion]:
        """Return all versions for ``identity``, in append order."""
        return [
            v for v in self._versions if v.target_identity == identity
        ]

    def count(self) -> int:
        return len(self._versions)

    def list(self) -> List[KnowledgeVersion]:
        """Return a copy of the record list."""
        return list(self._versions)

    def identities(self) -> List[str]:
        """Return the distinct list of target_identities, in first-seen order."""
        seen: List[str] = []
        for v in self._versions:
            if v.target_identity not in seen:
                seen.append(v.target_identity)
        return seen

    # ---- Forbidden operations (Sprint 22.4-D spec Task 2) ---------

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "VersionStore.update is forbidden; store is append-only"
        )

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "VersionStore.delete is forbidden; store is append-only"
        )

    def overwrite(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "VersionStore.overwrite is forbidden; store is append-only"
        )

    def clear(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "VersionStore.clear is forbidden; store is append-only"
        )


__all__ = [
    "VersionStore",
    "VersionStoreError",
]
