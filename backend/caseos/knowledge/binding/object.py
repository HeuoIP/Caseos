"""Knowledge Object Domain Binding Object V1 (Sprint 23.1-B).

The ``KODomainBinding`` is the **relationship record** that
associates a ``KnowledgeObject`` (Sprint 23.0-A) with a
``KnowledgeDomain`` (Sprint 23.1-A). It is a pure data
contract:

    * It does NOT mutate the Knowledge Object.
    * It does NOT mutate the Knowledge Domain.
    * It does NOT auto-create or auto-delete other bindings.
    * It does NOT touch any intelligence / retrieval /
      evolution module.

The binding carries enough metadata for a future Retrieval
or Evolution sprint to reason about KO <-> Domain
relationships:

    * which KO version is bound (so a future rollback can
      know which version was associated at binding time),
    * what type of membership (primary / secondary /
      derived),
    * the priority (1 = highest),
    * the human-readable reason for the membership,
    * the proposal_id that motivated the binding (may be
      empty when the binding was created directly).

Field groups:

    Identity
        binding_id, version
    Reference
        knowledge_object_id, knowledge_object_version,
        domain_id, binding_type, priority
    Metadata
        membership_reason, created_at, updated_at,
        created_by, proposal_id

Total field count: 12 (>= the spec's minimum of 10).

Architecture boundary (Sprint 23.1-B spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.object (sibling KO schema)
        * caseos.knowledge.domain (sibling Domain schema)
        * stdlib
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Tuple


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class KODomainBindingError(ValueError):
    """Base error for the knowledge.binding package."""


class KODomainBindingSchemaError(KODomainBindingError):
    """Raised by ``KODomainBinding.__post_init__`` on
    structural violations (missing required field, wrong
    type, invalid version, etc.).
    """


# Field-group boundaries are exposed as plain constants so
# validators, reports, and tests can introspect them without
# reaching into the dataclass internals.

IDENTITY_FIELDS: Tuple[str, ...] = ("binding_id", "version")
REFERENCE_FIELDS: Tuple[str, ...] = (
    "knowledge_object_id",
    "knowledge_object_version",
    "domain_id",
    "binding_type",
    "priority",
)
METADATA_FIELDS: Tuple[str, ...] = (
    "membership_reason",
    "created_at",
    "updated_at",
    "created_by",
    "proposal_id",
)


@dataclass(frozen=True)
class KODomainBinding:
    """The CaseOS KODomainBinding V1.

    The dataclass is frozen. The dataclass's own
    ``__post_init__`` runs a minimal structural guard
    (identity + version). Full schema validation lives in
    ``validator.py``.
    """

    # ---- Identity --------------------------------------------------
    binding_id: str
    version: int

    # ---- Reference -------------------------------------------------
    knowledge_object_id: str
    knowledge_object_version: int
    domain_id: str
    binding_type: str
    priority: int

    # ---- Metadata --------------------------------------------------
    membership_reason: str
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    created_by: str = ""
    proposal_id: str = ""

    # --------------------------------------------------------------
    # Post-init: minimal structural guard
    # --------------------------------------------------------------

    def __post_init__(self) -> None:
        if not isinstance(self.binding_id, str) or not self.binding_id:
            raise KODomainBindingSchemaError(
                "binding_id must be a non-empty string"
            )
        if not isinstance(self.version, int) or self.version < 1:
            raise KODomainBindingSchemaError(
                "version must be a positive integer (>= 1); got "
                + repr(self.version)
            )

    # --------------------------------------------------------------
    # Serialization
    # --------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation.

        The round-trip partner is ``KODomainBinding.from_dict``.
        """
        out = {
            "binding_id": self.binding_id,
            "version": self.version,
            "knowledge_object_id": self.knowledge_object_id,
            "knowledge_object_version": int(self.knowledge_object_version),
            "domain_id": self.domain_id,
            "binding_type": self.binding_type,
            "priority": int(self.priority),
            "membership_reason": self.membership_reason,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "proposal_id": self.proposal_id,
        }
        return out

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "KODomainBinding":
        """Build a ``KODomainBinding`` from a dict-shaped input.

        Missing optional fields fall back to their dataclass
        defaults. Missing required fields raise
        ``KODomainBindingSchemaError``.
        """
        if not isinstance(data, dict):
            raise KODomainBindingSchemaError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict[str, Any] = {}
        for fname in (
            "binding_id", "version",
            "knowledge_object_id", "knowledge_object_version",
            "domain_id", "binding_type", "priority",
            "membership_reason",
            "created_at", "updated_at",
            "created_by", "proposal_id",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        return KODomainBinding(**kwargs)


__all__ = [
    "KODomainBinding",
    "KODomainBindingError",
    "KODomainBindingSchemaError",
    "IDENTITY_FIELDS",
    "REFERENCE_FIELDS",
    "METADATA_FIELDS",
]
