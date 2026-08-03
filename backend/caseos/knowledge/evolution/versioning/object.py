"""KnowledgeVersion Object (Sprint 22.4-D, ADR-020 Rule 2).

A ``KnowledgeVersion`` is a **frozen, append-only record** of
a Knowledge Object's state at one moment in time. Versions
form a chain via ``previous_version`` and are accumulated in
``VersionStore``.

In V1, no ``EvolutionTransaction -> KO mutation`` happens
anywhere. The version record is the **future container** that
a future Sprint 22.4.x mutation runtime will populate. The
record's contract is locked now so the runtime can be slotted
in later without re-shaping the storage layer.

Required fields (Sprint 22.4-D spec Task 1):

    version_id         unique identifier for this record
    target_identity    the KO this version belongs to
    version_number     monotonically increasing integer
                       (per identity)
    previous_version   the version_number that came before,
                       or None for the first version
    snapshot           a dict snapshot of the KO fields at
                       this version (deep-copied on entry so
                       that caller mutations do not leak in)
    created_at         ISO timestamp (datetime)
    created_by         the human or system that produced the
                       version
    change_reason      a short human-readable reason
    proposal_id        the LearningProposal that motivated
                       the change (may be empty for non-
                       evolution versions)

Architecture boundary (Sprint 22.4-D spec Task 4):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * caseos.knowledge.objects
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * stdlib
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class KnowledgeVersion:
    """A single versioned record. Immutable, append-only.

    The dataclass is **frozen**: mutation raises
    ``FrozenInstanceError``. The ``snapshot`` dict is
    deep-copied in ``__post_init__`` so caller mutations
    do not leak into the record.
    """

    version_id: str
    target_identity: str
    version_number: int
    previous_version: Optional[int]
    snapshot: dict[str, Any]
    created_at: datetime
    created_by: str
    change_reason: str
    proposal_id: str

    def __post_init__(self) -> None:
        # Defensive copy of the snapshot. The frozen dataclass
        # would otherwise share the caller's dict reference, and
        # a caller mutation would leak in.
        if isinstance(self.snapshot, dict):
            object.__setattr__(
                self, "snapshot", copy.deepcopy(self.snapshot),
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = asdict(self)
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out


__all__ = ["KnowledgeVersion"]
