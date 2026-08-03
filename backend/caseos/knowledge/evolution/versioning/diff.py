"""Knowledge Diff (Sprint 22.4-D, ADR-020 Rule 2).

The ``KnowledgeDiff`` is a **pure, deterministic** comparison
of two KO snapshots. The differ does NOT judge correctness,
does NOT propose a new value, and does NOT auto-generate
anything. It is a structural diff.

Allowed (Sprint 22.4-D spec Task 3):

    * Field-level comparison
    * Identifies added, removed, and modified fields
    * Returns the changed field names, the before dict, and
      the after dict (deep-copied so the caller cannot mutate
      the result)

Forbidden:

    * Automatic correctness judgement
    * Automatic content modification
    * Automatic proposal generation
    * Mutation of the input dicts

The differ is the read-side companion to ``VersionStore``.
A future Sprint 22.4.x mutation runtime will compute a diff
between an EvolutionTransaction's ``before_snapshot`` and a
freshly-built candidate snapshot, decide whether the diff is
acceptable, and append a ``KnowledgeVersion`` to the store.
In V1 the runtime does not exist; the differ is shipped
standalone so the contract is locked.

Architecture boundary (Sprint 22.4-D spec Task 4):

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
from typing import Any, Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class KnowledgeDiff:
    """The structural diff between two snapshots.

    Attributes:
        changed_fields: sorted tuple of field names whose
            value differs between ``before`` and ``after``,
            or that appear in only one of them.
        before: deep copy of the before snapshot.
        after: deep copy of the after snapshot.
    """

    changed_fields: Tuple[str, ...]
    before: Dict[str, Any]
    after: Dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "changed_fields": list(self.changed_fields),
            "before": self.before,
            "after": self.after,
        }

    @property
    def is_empty(self) -> bool:
        """True iff no fields changed."""
        return len(self.changed_fields) == 0


class KnowledgeDiffer:
    """Stateless differ. ``diff`` is a pure function."""

    @staticmethod
    def diff(
        before: Any,
        after: Any,
    ) -> KnowledgeDiff:
        """Compute a structural diff between two snapshots.

        Non-dict inputs are normalised to empty dicts so the
        function never raises on shape mismatch. The returned
        ``before`` and ``after`` are deep-copied.

        Returns a ``KnowledgeDiff`` with:
            * ``changed_fields`` -- sorted tuple of field names
            * ``before`` -- deep copy of normalised before
            * ``after`` -- deep copy of normalised after
        """
        b = before if isinstance(before, dict) else {}
        a = after if isinstance(after, dict) else {}
        all_keys = set(b.keys()) | set(a.keys())
        changed: List[str] = []
        for k in sorted(all_keys):
            if b.get(k) != a.get(k):
                changed.append(k)
        return KnowledgeDiff(
            changed_fields=tuple(changed),
            before=copy.deepcopy(b),
            after=copy.deepcopy(a),
        )


__all__ = [
    "KnowledgeDiff",
    "KnowledgeDiffer",
]
