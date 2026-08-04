"""Adapter Object Schemas V1 (Sprint 23.0-B, ADR-020).

The adapter layer needs three frozen dataclasses:

    AdapterRequest    input contract
    AdapterResult     output contract (with new_snapshot)
    FieldMapping      one resolved mapping decision

All three are immutable. Collection-typed fields are
deep-copied in ``__post_init__`` so caller mutations cannot
leak into the adapter's internal state.

AdapterRequest fields (Sprint 23.0-B spec):

    request_id          unique identifier for the adapter call
    transaction_id      the EvolutionTransaction id this
                        adapter call belongs to
    change_intent_id    the ChangeIntent id this call maps
    target_identity     the KO identity (knowledge_id)
    target_version      the version we mutate FROM (>= 1)
    change_type         EvolutionChangeType enum (or string)
    before_snapshot     dict snapshot of the KO before the
                        change (deep-copied on entry)
    requested_change    Optional[str]; the proposed new value
    reviewer            non-empty string (human approver)
    created_at          ISO timestamp (datetime)

AdapterResult fields:

    success             True iff a candidate was produced
    request_id          echoes AdapterRequest.request_id
    transaction_id      echoes AdapterRequest.transaction_id
    target_identity     echoes AdapterRequest.target_identity
    before_version      echoes AdapterRequest.target_version
    next_version        before_version + 1 (only set when
                        success=True)
    new_snapshot        dict candidate KO state, or None on
                        failure (deep-copied on entry)
    mapping             the FieldMapping decision, or None on
                        failure
    rejection_reason    empty when success=True; otherwise a
                        human-readable reason
    mutation_executed   always False in V1 (the adapter is
                        candidate-only; the caller applies it)
    created_at          ISO timestamp (datetime)

FieldMapping fields:

    change_type                the requested EvolutionChangeType
    requested_target_field     what the upstream ChangeIntent
                               asked for (e.g. "boundary")
    resolved_target_field      what we mapped it to in KO V1
                               (e.g. "category")
    applied                    True iff the mapping succeeded
    note                       human-readable explanation

Architecture boundary (Sprint 23.0-B spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.evolution (sibling packages)
        * caseos.knowledge.evolution.contracts
        * caseos.knowledge.object (the new KO V1 schema)
        * stdlib
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ..contracts.change_type import EvolutionChangeType


class AdapterError(ValueError):
    """Base error for the evolution.adapter package."""


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
class AdapterRequest:
    """A single adapter call. Immutable."""

    request_id: str
    transaction_id: str
    change_intent_id: str
    target_identity: str
    target_version: int
    change_type: Any  # EvolutionChangeType (annotation only)
    before_snapshot: dict
    requested_change: Optional[str]
    reviewer: str
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        # Defensive deep-copy of before_snapshot.
        if isinstance(self.before_snapshot, dict):
            object.__setattr__(
                self, "before_snapshot",
                copy.deepcopy(self.before_snapshot),
            )
        # Sprint 22.4-I contract alignment: coerce string
        # change_type to EvolutionChangeType. Invalid strings
        # stay as strings; the AdapterValidator will then
        # reject them.
        coerced = _coerce_change_type(self.change_type)
        if coerced is not self.change_type:
            object.__setattr__(self, "change_type", coerced)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = {
            "request_id": self.request_id,
            "transaction_id": self.transaction_id,
            "change_intent_id": self.change_intent_id,
            "target_identity": self.target_identity,
            "target_version": int(self.target_version),
            "change_type": (
                self.change_type.value
                if isinstance(self.change_type, EvolutionChangeType)
                else self.change_type
            ),
            "before_snapshot": self.before_snapshot,
            "requested_change": self.requested_change,
            "reviewer": self.reviewer,
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                if isinstance(self.created_at, datetime)
                else self.created_at,
        }
        return out


@dataclass(frozen=True)
class FieldMapping:
    """The adapter's mapping decision for one change_type.

    ``applied=True`` means the adapter successfully resolved
    the requested target field to an actual KO V1 field and
    the change was applied to ``new_snapshot``. ``applied=False``
    means the mapping failed; ``note`` explains why.
    """

    change_type: Any  # EvolutionChangeType
    requested_target_field: str
    resolved_target_field: str
    applied: bool
    note: str

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        ct = out.get("change_type")
        if isinstance(ct, EvolutionChangeType):
            out["change_type"] = ct.value
        return out


@dataclass(frozen=True)
class AdapterResult:
    """The outcome of a ``KnowledgeObjectAdapter.adapt`` call.

    V1 contract:

        * ``success=True`` -> ``new_snapshot`` is a non-empty
          dict compatible with ``KnowledgeObject.from_dict``.
        * ``success=False`` -> ``new_snapshot`` is None and
          ``rejection_reason`` is non-empty.
        * ``mutation_executed`` is always False in V1. The
          adapter is candidate-only; it never appends to
          VersionStore or AuditStore.
    """

    success: bool
    request_id: str
    transaction_id: str
    target_identity: str
    before_version: int
    next_version: Optional[int]
    new_snapshot: Optional[dict]
    mapping: Optional[FieldMapping]
    rejection_reason: str
    mutation_executed: bool
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        ts = out.get("created_at")
        if isinstance(ts, datetime):
            out["created_at"] = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        if isinstance(self.mapping, FieldMapping):
            out["mapping"] = self.mapping.to_dict()
        return out


def _new_request_id() -> str:
    return "adp-" + str(uuid.uuid4())


__all__ = [
    "AdapterError",
    "AdapterRequest",
    "AdapterResult",
    "FieldMapping",
]
