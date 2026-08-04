"""Rollback Object Schemas V1 (Sprint 22.4-G, ADR-020 Rule 4).

This module defines the three frozen dataclasses that
constitute the rollback contract:

    RollbackRequest         (input)
    RollbackValidationResult (validator output)
    RollbackPlan            (planner output, frozen)

All three are **frozen**. None expose an
``apply / execute / restore / rollback / mutate`` method.
The plan carries a ``mutation_executed`` field that is
**always False** in V1.

Architecture boundary (Sprint 22.4-G spec Task 6):

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
from typing import Any, Tuple


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class RollbackRequest:
    """A request to roll a Knowledge Object back to a prior version.

    Required fields (Sprint 22.4-G spec Task 1):

        rollback_id      unique identifier
        transaction_id   the original EvolutionTransaction
                         that produced the version we want
                         to roll back FROM
        target_identity  the KO this rollback targets
        from_version     the version we are rolling back from
                         (must be > to_version)
        to_version       the version we are rolling back to
                         (must be >= 1)
        reason           human-readable reason
        requested_by     the human or system that filed the
                         request
        created_at       ISO timestamp (datetime)
    """

    rollback_id: str
    transaction_id: str
    target_identity: str
    from_version: int
    to_version: int
    reason: str
    requested_by: str
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = asdict(self)
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out


@dataclass(frozen=True)
class RollbackValidationResult:
    """The outcome of a ``RollbackValidator.validate`` call.

    Attributes:
        valid: True iff every rule passed.
        rule_id: The first rule that failed (e.g. ``"R1"``).
            Empty string when ``valid``.
        reason: Human-readable reason for the decision.
            Empty string when ``valid``.
    """

    valid: bool
    rule_id: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RollbackPlan:
    """A static description of a rollback. NOT an executor.

    Required fields (Sprint 22.4-G spec Task 3):

        rollback_id          unique identifier
        target_identity      the KO this plan targets
        source_version       the version we are rolling back
                             FROM (= request.from_version)
        destination_version  the version we are rolling back
                             TO (= request.to_version)
        diff_summary         a short human-readable summary
                             of the change
        steps                an ordered tuple of step
                             descriptions (immutable)
        created_at           ISO timestamp (datetime)

    V1 marker:

        mutation_executed    ALWAYS False in V1. The field
                             exists so a future Sprint 22.4.x
                             runtime can flip the single
                             boolean from False to True
                             without changing the schema.

    Forbidden methods (Sprint 22.4-G spec Task 4):

        The dataclass has NO:
            * apply()
            * execute()
            * restore()
            * rollback()
            * mutate()
    """

    rollback_id: str
    target_identity: str
    source_version: int
    destination_version: int
    diff_summary: str
    steps: Tuple[str, ...]
    created_at: datetime = field(default_factory=_now)
    mutation_executed: bool = False  # ALWAYS False in V1

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = asdict(self)
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out


__all__ = [
    "RollbackRequest",
    "RollbackValidationResult",
    "RollbackPlan",
]
