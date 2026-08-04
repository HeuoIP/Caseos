"""Binding Registry V1 (Sprint 23.1-B, ADR-018 / ADR-020).

The ``BindingRegistry`` is the **append-only container**
for ``KODomainBinding`` records. It is the storage layer
that a future Sprint's Retrieval / Evolution runtime may
read from. The registry is intentionally minimal in V1: it
does not enforce any global ordering or referential
integrity to actual KO / Domain instances; that is the job
of a future Sprint.

Append-only contract (Sprint 23.1-B spec):

    Allowed methods:
        * append(binding)        -- add a KODomainBinding
        * get(binding_id)        -- retrieve by id
        * for_knowledge_object   -- list bindings for a KO
        * for_domain             -- list bindings for a Domain
        * count()                -- total records
        * list()                 -- copy of all records
        * binding_ids()          -- distinct binding_ids
        * knowledge_object_ids() -- distinct KO ids

    Forbidden methods (raise TypeError):
        * update
        * delete
        * overwrite
        * clear

The forbidden methods accept any arguments (positional or
keyword) and always raise ``TypeError``.

Architecture boundary (Sprint 23.1-B spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.binding (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, List, Optional

from .object import KODomainBinding


class BindingRegistryError(Exception):
    """Raised when a forbidden operation is attempted on the registry."""


class BindingRegistry:
    """Append-only container for ``KODomainBinding`` records.

    The internal list is a ``list`` and is only ever appended
    to via the ``append`` method. The four forbidden methods
    raise ``TypeError`` so the contract is testable in CI.
    """

    def __init__(self) -> None:
        self._bindings: List[KODomainBinding] = []

    # ---- Allowed operations ----------------------------------------

    def append(self, binding: KODomainBinding) -> KODomainBinding:
        """Append a new binding record. Returns the same record."""
        if not isinstance(binding, KODomainBinding):
            raise BindingRegistryError(
                "binding must be a KODomainBinding instance"
            )
        self._bindings.append(binding)
        return binding

    def get(self, binding_id: str) -> Optional[KODomainBinding]:
        """Return the binding with the given binding_id, or None."""
        for b in self._bindings:
            if b.binding_id == binding_id:
                return b
        return None

    def for_knowledge_object(
        self, knowledge_object_id: str
    ) -> List[KODomainBinding]:
        """Return all bindings for ``knowledge_object_id``,
        in append order."""
        return [
            b
            for b in self._bindings
            if b.knowledge_object_id == knowledge_object_id
        ]

    def for_domain(self, domain_id: str) -> List[KODomainBinding]:
        """Return all bindings for ``domain_id``, in append order."""
        return [b for b in self._bindings if b.domain_id == domain_id]

    def count(self) -> int:
        return len(self._bindings)

    def list(self) -> List[KODomainBinding]:
        """Return a copy of the record list."""
        return list(self._bindings)

    def binding_ids(self) -> List[str]:
        """Return the distinct list of binding_ids, in first-seen order."""
        seen: List[str] = []
        for b in self._bindings:
            if b.binding_id not in seen:
                seen.append(b.binding_id)
        return seen

    def knowledge_object_ids(self) -> List[str]:
        """Return the distinct list of KO ids, in first-seen order."""
        seen: List[str] = []
        for b in self._bindings:
            if b.knowledge_object_id not in seen:
                seen.append(b.knowledge_object_id)
        return seen

    def domain_ids(self) -> List[str]:
        """Return the distinct list of Domain ids, in first-seen order."""
        seen: List[str] = []
        for b in self._bindings:
            if b.domain_id not in seen:
                seen.append(b.domain_id)
        return seen

    # ---- Forbidden operations (Sprint 23.1-B spec) -----------------

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "BindingRegistry.update is forbidden; registry is append-only"
        )

    def delete(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "BindingRegistry.delete is forbidden; registry is append-only"
        )

    def overwrite(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "BindingRegistry.overwrite is forbidden; registry is append-only"
        )

    def clear(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError(
            "BindingRegistry.clear is forbidden; registry is append-only"
        )


__all__ = [
    "BindingRegistry",
    "BindingRegistryError",
]
