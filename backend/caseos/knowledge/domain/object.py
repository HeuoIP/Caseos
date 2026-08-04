"""Knowledge Domain Object V1 (Sprint 23.1-A).

The ``KnowledgeDomain`` is the **higher-level categorization
record** of CaseOS. It describes a cluster of related
``KnowledgeObject`` instances and the rules that govern
which objects may belong to the cluster.

Whereas a ``KnowledgeObject`` describes ONE design / case /
pattern, a ``KnowledgeDomain`` describes the SCOPE and
APPLICABILITY of a category of objects. The two records are
independent: a Domain can exist with zero KOs (just declared
scope), and a KO can exist outside any explicit Domain
(default-domain membership).

V1 is intentionally a pure data contract. No business
logic, no embeddings, no AI.

Field groups:

    Identity
        domain_id, version
    Scope
        domain_type, name, description,
        parent_domain_id, scope_tags
    Taxonomy
        allowed_knowledge_types,
        boundary_rules, principle_rules
    Metadata
        created_at, updated_at, source

Total field count: 14 (>= the spec's minimum of 10).

Architecture boundary (Sprint 23.1-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.object (sibling KO schema)
        * stdlib
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Tuple


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class KnowledgeDomainError(ValueError):
    """Base error for the knowledge.domain package."""


class KnowledgeDomainSchemaError(KnowledgeDomainError):
    """Raised by ``KnowledgeDomain.__post_init__`` on
    structural violations (missing required field, wrong
    type, invalid version, etc.).
    """


# Field-group boundaries are exposed as plain constants so
# validators, reports, and tests can introspect them without
# reaching into the dataclass internals.

IDENTITY_FIELDS: Tuple[str, ...] = ("domain_id", "version")
SCOPE_FIELDS: Tuple[str, ...] = (
    "domain_type", "name", "description",
    "parent_domain_id", "scope_tags",
)
TAXONOMY_FIELDS: Tuple[str, ...] = (
    "allowed_knowledge_types",
    "boundary_rules",
    "principle_rules",
)
METADATA_FIELDS: Tuple[str, ...] = (
    "created_at", "updated_at", "source",
)


def _empty_list() -> list:
    return []


@dataclass(frozen=True)
class KnowledgeDomain:
    """The CaseOS Knowledge Domain V1.

    The dataclass is frozen. Collection fields are
    deep-copied in ``__post_init__`` so caller mutations
    cannot leak into the record. The minimal structural
    guards (identity + version) run inside ``__post_init__``;
    full schema validation lives in ``validator.py``.
    """

    # ---- Identity --------------------------------------------------
    domain_id: str
    version: int

    # ---- Scope -----------------------------------------------------
    domain_type: str
    name: str
    description: str
    parent_domain_id: Optional[str] = None
    scope_tags: list = field(default_factory=_empty_list)

    # ---- Taxonomy --------------------------------------------------
    allowed_knowledge_types: list = field(default_factory=_empty_list)
    boundary_rules: list = field(default_factory=_empty_list)
    principle_rules: list = field(default_factory=_empty_list)

    # ---- Metadata --------------------------------------------------
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    source: str = ""

    # --------------------------------------------------------------
    # Post-init: defensive copy + minimal structural guard
    # --------------------------------------------------------------

    def __post_init__(self) -> None:
        # Defensive deep-copy of every collection-typed field.
        # The frozen dataclass freezes the *bindings*, not the
        # contents of mutable containers.
        for fname in (
            "scope_tags",
            "allowed_knowledge_types",
            "boundary_rules",
            "principle_rules",
        ):
            raw = getattr(self, fname)
            if isinstance(raw, list):
                object.__setattr__(self, fname, copy.deepcopy(raw))
            elif isinstance(raw, tuple):
                object.__setattr__(self, fname, copy.deepcopy(list(raw)))

        # Minimal structural guards. Schema-level validation
        # lives in ``validator.py`` and runs at higher levels.
        if not isinstance(self.domain_id, str) or not self.domain_id:
            raise KnowledgeDomainSchemaError(
                "domain_id must be a non-empty string"
            )
        if not isinstance(self.version, int) or self.version < 1:
            raise KnowledgeDomainSchemaError(
                "version must be a positive integer (>= 1); got "
                + repr(self.version)
            )

    # --------------------------------------------------------------
    # Serialization
    # --------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation.

        The round-trip partner is ``KnowledgeDomain.from_dict``.
        Collection fields are returned as plain lists so the
        output is JSON-native.
        """
        out = {
            "domain_id": self.domain_id,
            "version": self.version,
            "domain_type": self.domain_type,
            "name": self.name,
            "description": self.description,
            "parent_domain_id": self.parent_domain_id,
            "scope_tags": list(self.scope_tags),
            "allowed_knowledge_types": list(self.allowed_knowledge_types),
            "boundary_rules": list(self.boundary_rules),
            "principle_rules": list(self.principle_rules),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
        }
        return out

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "KnowledgeDomain":
        """Build a ``KnowledgeDomain`` from a dict-shaped input.

        Missing optional fields fall back to their dataclass
        defaults. Missing required fields raise
        ``KnowledgeDomainSchemaError``.
        """
        if not isinstance(data, dict):
            raise KnowledgeDomainSchemaError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict[str, Any] = {}
        for fname in (
            "domain_id", "version",
            "domain_type", "name", "description",
            "parent_domain_id",
            "created_at", "updated_at", "source",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        for fname in (
            "scope_tags",
            "allowed_knowledge_types",
            "boundary_rules",
            "principle_rules",
        ):
            if fname in data:
                raw = data[fname]
                if raw is None:
                    kwargs[fname] = []
                elif isinstance(raw, (list, tuple)):
                    kwargs[fname] = list(raw)
                else:
                    raise KnowledgeDomainSchemaError(
                        fname + " must be a list/tuple; got "
                        + type(raw).__name__
                    )
        return KnowledgeDomain(**kwargs)


__all__ = [
    "KnowledgeDomain",
    "KnowledgeDomainError",
    "KnowledgeDomainSchemaError",
    "IDENTITY_FIELDS",
    "SCOPE_FIELDS",
    "TAXONOMY_FIELDS",
    "METADATA_FIELDS",
]
