"""Knowledge Object Snapshot V1 (Sprint 23.0-A).

The ``KnowledgeObjectSnapshot`` is a **point-in-time capture**
of a ``KnowledgeObject``. It is the **bridge** to the
Evolution layer:

    KnowledgeObject (mutable in spirit, frozen in storage)
        |
        | snapshot at version N
        v
    KnowledgeObjectSnapshot
        |
        v
    Evolution stores the snapshot (Sprint 22.4-D and
    beyond). The Evolution layer never touches a
    ``KnowledgeObject`` directly; it only ever touches
    snapshots.

The snapshot is **immutable** (frozen dataclass) and its
``snapshot`` dict is **deep-copied in __post_init__** so
the Evolution store cannot be polluted by later mutations
of the caller's dict.

Architecture boundary (Sprint 23.0-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
    This module MAY import from:
        * caseos.knowledge.object (sibling modules)
        * stdlib
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .object import KnowledgeObject


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class KnowledgeObjectSnapshot:
    """A frozen, deep-copied capture of a ``KnowledgeObject``.

    Fields:
        knowledge_id: the source object's id
        version:      the source object's version
        snapshot:     a JSON-safe dict produced by
                      ``KnowledgeObject.to_dict``; deep-copied
                      in ``__post_init__`` so caller mutations
                      do not leak into the record
        created_at:   ISO timestamp (datetime)
        source_object_id: optional id linking the snapshot back
                      to the original ``KnowledgeObject``
                      (defaults to ``knowledge_id`` when not
                      supplied)
    """

    knowledge_id: str
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
        # Default source_object_id to knowledge_id when absent.
        if self.source_object_id is None:
            object.__setattr__(
                self, "source_object_id", self.knowledge_id,
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = asdict(self)
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out

    @staticmethod
    def from_knowledge_object(
        obj: KnowledgeObject,
        *,
        created_at: Optional[datetime] = None,
        source_object_id: Optional[str] = None,
    ) -> "KnowledgeObjectSnapshot":
        """Capture ``obj`` into a snapshot.

        The snapshot's ``snapshot`` field is the result of
        ``obj.to_dict()``. The caller may pass an explicit
        ``created_at`` (useful for tests); otherwise the
        current UTC time is used.
        """
        if not isinstance(obj, KnowledgeObject):
            raise TypeError(
                "from_knowledge_object expects a KnowledgeObject; got "
                + type(obj).__name__
            )
        snap = obj.to_dict()
        return KnowledgeObjectSnapshot(
            knowledge_id=obj.knowledge_id,
            version=int(obj.version),
            snapshot=snap,
            created_at=created_at if created_at is not None else _now(),
            source_object_id=source_object_id,
        )


__all__ = ["KnowledgeObjectSnapshot"]
