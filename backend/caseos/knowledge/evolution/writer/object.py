"""Writer Object Schemas V1 (Sprint 23.0-C, ADR-020).

The writer layer needs three frozen dataclasses:

    WriteRequest     input contract
    WriteResult      output contract
    WriteError       base error

WriteRequest fields (Sprint 23.0-C spec):

    write_id             unique identifier for this write call
    transaction_id       the EvolutionTransaction id this
                         write belongs to
    proposal_id          the LearningProposal that motivated
                         the change
    change_intent_id     the ChangeIntent id
    target_identity      the KO identity (knowledge_id)
    change_type          EvolutionChangeType (annotation only)
    before_version       the version_number we write FROM
                         (must already exist in VersionStore)
    before_snapshot      dict snapshot of KO before the write
                         (deep-copied on entry)
    new_snapshot         dict candidate KO state produced by
                         the Adapter (deep-copied on entry)
    reviewer             non-empty string (human approver)
    change_reason        short human-readable reason
    created_at           ISO timestamp (datetime)

WriteResult fields:

    success              True iff both stores received a
                         record
    write_id             echoes WriteRequest.write_id
    transaction_id       echoes WriteRequest.transaction_id
    target_identity      echoes WriteRequest.target_identity
    before_version       echoes WriteRequest.before_version
    new_version          the version_number of the appended
                         KnowledgeVersion (before_version + 1
                         when no concurrent writer is present)
    version_id           the appended KnowledgeVersion.version_id
    audit_id             the appended EvolutionAuditRecord.audit_id
    version_appended     True iff a KnowledgeVersion was appended
    audit_appended       True iff an EvolutionAuditRecord was appended
    mutation_executed    True iff BOTH stores were updated.
                         False on any rejection. The writer is
                         the first layer in the Evolution pipeline
                         where mutation_executed=True is meaningful.
    rejection_reason     empty when success=True; otherwise a
                         human-readable reason
    created_at           ISO timestamp (datetime)

Architecture boundary (Sprint 23.0-C spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.evolution (sibling packages)
        * caseos.knowledge.evolution.contracts
        * stdlib
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ..contracts.change_type import EvolutionChangeType


class WriteError(ValueError):
    """Base error for the evolution.writer package."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _coerce_change_type(value: Any) -> Any:
    """Coerce ``value`` to ``EvolutionChangeType`` when possible.

    Returns the value unchanged when the value cannot be
    coerced (e.g. an invalid string). Downstream validators
    are responsible for rejecting values outside the V1
    allow-list.
    """
    if isinstance(value, EvolutionChangeType):
        return value
    if isinstance(value, str):
        try:
            return EvolutionChangeType(value)
        except ValueError:
            return value
    return value


@dataclass(frozen=True)
class WriteRequest:
    """A single writer call. Immutable."""

    write_id: str
    transaction_id: str
    proposal_id: str
    change_intent_id: str
    target_identity: str
    change_type: Any  # EvolutionChangeType (annotation only)
    before_version: int
    before_snapshot: dict
    new_snapshot: dict
    reviewer: str
    change_reason: str
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        # Defensive deep-copy of both snapshot dicts so
        # caller mutations cannot leak into the request.
        if isinstance(self.before_snapshot, dict):
            object.__setattr__(
                self, "before_snapshot",
                copy.deepcopy(self.before_snapshot),
            )
        if isinstance(self.new_snapshot, dict):
            object.__setattr__(
                self, "new_snapshot",
                copy.deepcopy(self.new_snapshot),
            )
        # Sprint 22.4-I contract alignment: coerce string
        # change_type to EvolutionChangeType. Invalid strings
        # stay as strings; WriterValidator will then reject
        # them.
        coerced = _coerce_change_type(self.change_type)
        if coerced is not self.change_type:
            object.__setattr__(self, "change_type", coerced)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = {
            "write_id": self.write_id,
            "transaction_id": self.transaction_id,
            "proposal_id": self.proposal_id,
            "change_intent_id": self.change_intent_id,
            "target_identity": self.target_identity,
            "change_type": (
                self.change_type.value
                if isinstance(self.change_type, EvolutionChangeType)
                else self.change_type
            ),
            "before_version": int(self.before_version),
            "before_snapshot": self.before_snapshot,
            "new_snapshot": self.new_snapshot,
            "reviewer": self.reviewer,
            "change_reason": self.change_reason,
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                if isinstance(self.created_at, datetime)
                else self.created_at,
        }
        return out


@dataclass(frozen=True)
class WriteResult:
    """The outcome of a ``KnowledgeObjectWriter.write`` call.

    The writer is the FIRST layer in the Evolution pipeline
    where ``mutation_executed=True`` is meaningful. Prior
    layers are candidate-only.

    V1 contract:

        * ``success=True`` -> both ``version_appended`` and
          ``audit_appended`` are True, ``new_version`` is the
          appended version's number, and ``version_id`` /
          ``audit_id`` are non-empty.
        * ``success=False`` -> both ``version_appended`` and
          ``audit_appended`` are False, ``new_version`` is
          None, and ``rejection_reason`` is non-empty.
        * ``mutation_executed`` is True iff ``success=True``.
    """

    success: bool
    write_id: str
    transaction_id: str
    target_identity: str
    before_version: int
    new_version: Optional[int]
    version_id: Optional[str]
    audit_id: Optional[str]
    version_appended: bool
    audit_appended: bool
    mutation_executed: bool
    rejection_reason: str
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        return out


def _new_write_id() -> str:
    return "wrt-" + str(uuid.uuid4())


__all__ = [
    "WriteError",
    "WriteRequest",
    "WriteResult",
]
