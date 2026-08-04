"""Knowledge Domain Snapshot V1 (Sprint 23.1-A).

The ``KnowledgeDomainSnapshot`` is a **point-in-time capture**
of a ``KnowledgeDomain``. It is the **bridge** to future
Evolution-layer Sprints that need to freeze a domain state
before applying an approved change:

    KnowledgeDomain
        |
        | snapshot at version N
        v
    KnowledgeDomainSnapshot
        |
        v
    (future Sprint: Evolution consumption)

The snapshot is **immutable** (frozen dataclass) and its
``snapshot`` dict is **deep-copied in __post_init__** so the
Evolution store cannot be polluted by later mutations of the
caller's dict.

Architecture boundary (Sprint 23.1-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.domain (sibling modules)
        * stdlib
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .object import KnowledgeDomain


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class KnowledgeDomainSnapshot:
    """A frozen, deep-copied capture of a ``KnowledgeDomain``.

    Fields:
        domain_id: the source object's id
        version: the source object's version
        snapshot: a JSON-safe dict produced by
                  ``KnowledgeDomain.to_dict``; deep-copied
                  in ``__post_init__`` so caller mutations
                  do not leak into the record
        created_at: ISO timestamp (datetime)
        source_object_id: optional id linking the snapshot
                          back to the original
                          ``KnowledgeDomain`` (defaults to
                          ``domain_id`` when not supplied)
    """

    domain_id: str
    version: int
    snapshot: dict
    created_at: datetime = field(default_factory=_now)
    source_object_id: Optional[str] = None

    def __post_init__(self) -> None:
        # Defensive deep-copy of the snapshot dict.
        if isinstance(self.snapshot, dict):
            object.__setattr__(
                self, "snapshot",
                copy.deepcopy(self.snapshot),
            )
        # Default source_object_id to domain_id when absent.
        if self.source_object_id is None:
            object.__setattr__(
                self, "source_object_id", self.domain_id,
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = asdict(self)
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out

    @staticmethod
    def from_knowledge_domain(
        obj: KnowledgeDomain,
        *,
        created_at: Optional[datetime] = None,
        source_object_id: Optional[str] = None,
    ) -> "KnowledgeDomainSnapshot":
        """Capture ``obj`` into a snapshot.

        The snapshot's ``snapshot`` field is the result of
        ``obj.to_dict()``. The caller may pass an explicit
        ``created_at`` (useful for tests); otherwise the
        current UTC time is used.
        """
        if not isinstance(obj, KnowledgeDomain):
            raise TypeError(
                "from_knowledge_domain expects a KnowledgeDomain; got "
                + type(obj).__name__
            )
        snap = obj.to_dict()
        return KnowledgeDomainSnapshot(
            domain_id=obj.domain_id,
            version=int(obj.version),
            snapshot=snap,
            created_at=created_at if created_at is not None else _now(),
            source_object_id=source_object_id,
        )


__all__ = ["KnowledgeDomainSnapshot"]
