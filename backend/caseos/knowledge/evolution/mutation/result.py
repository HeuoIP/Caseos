"""Mutation Result V1 (Sprint 22.4-H, ADR-020).

Frozen result of a mutation attempt. ``success`` and
``mutation_executed`` are independent booleans:

    * ``success``        the runtime reached the mutation
                         stage (validation, identity match,
                         version lookup, etc.) and produced
                         a result. False only when something
                         structurally prevented the mutation.
    * ``mutation_executed``
                         True iff a new ``KnowledgeVersion``
                         and an ``EvolutionAuditRecord`` were
                         actually created and appended to the
                         stores. In V1 this is the same as
                         ``success``; the two fields are kept
                         separate so a future Sprint 22.4.x can
                         flip the single boolean from True to
                         False without changing the schema
                         (e.g. when ``mutation_executed`` becomes
                         a true runtime gate rather than a
                         V1 marker).

Forbidden: no ``apply`` / ``undo`` / ``rollback`` / ``restore``
methods on the result. The result is a description, not an
action.

Architecture boundary (Sprint 22.4-H spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class MutationResult:
    """The outcome of a ``KnowledgeMutationEngine.mutate`` call.

    Fields:

        mutation_id       the source MutationRequest id
        transaction_id    the source EvolutionTransaction id
        target_identity   the KO this result concerns
        old_version       the version_number before the
                          mutation (== request.before_version
                          on success). 0 when the runtime did
                          not look up a prior version.
        new_version       the version_number after the
                          mutation. 0 on failure.
        mutation_executed True iff a new KnowledgeVersion and
                          an EvolutionAuditRecord were created
                          and appended. False otherwise.
        audit_id          audit record id, populated when
                          ``mutation_executed`` is True. ``None``
                          otherwise.
        success           True iff the mutation stage
                          completed without error. False when
                          validation rejected the request.
        rejection_rule_id the validator rule_id that fired
                          (e.g. ``"M5"``). Empty when success.
        rejection_reason  human-readable rejection reason.
                          Empty when success.
        created_at        ISO timestamp (datetime).
    """

    mutation_id: str
    transaction_id: str
    target_identity: str
    old_version: int
    new_version: int
    mutation_executed: bool
    audit_id: Optional[str]
    success: bool
    rejection_rule_id: str = ""
    rejection_reason: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = asdict(self)
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out


__all__ = ["MutationResult"]
