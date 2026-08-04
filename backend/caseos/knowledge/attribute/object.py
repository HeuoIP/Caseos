"""Knowledge Attribute Object Schema V1 (Sprint 23.1-D).

The ``KnowledgeAttribute`` is the **typed property slot
record** that declares the schema for a single property on
a ``KnowledgeObject`` (e.g. ``style``, ``theme``,
``color_system``).

Field groups:

    Identity
        attribute_id, version
    Content
        name, description, attribute_type, data_type,
        cardinality, required, default_value
    Constraints
        allowed_taxonomy_id, allowed_node_ids,
        min_value, max_value, pattern
    Metadata
        created_at, updated_at, created_by, source

Total field count: 19 (>= the spec's minimum of 10).

V1 is intentionally a pure data contract. No business
logic, no embeddings, no AI. The attribute NEVER mutates a
KnowledgeObject, a Taxonomy, a Domain, or a Binding. It
is a pure schema declaration that future Retrieval /
Evolution sprints may consult.

Architecture boundary (Sprint 23.1-D spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.object (sibling KO schema)
        * caseos.knowledge.taxonomy (sibling Taxonomy)
        * stdlib
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Tuple


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class KnowledgeAttributeError(ValueError):
    """Base error for the knowledge.attribute package."""


class KnowledgeAttributeSchemaError(KnowledgeAttributeError):
    """Raised by ``KnowledgeAttribute.__post_init__`` on
    structural violations (missing required field, wrong
    type, invalid version, etc.).
    """


# Field-group boundaries are exposed as plain constants so
# validators, reports, and tests can introspect them without
# reaching into the dataclass internals.

IDENTITY_FIELDS: Tuple[str, ...] = ("attribute_id", "version")
CONTENT_FIELDS: Tuple[str, ...] = (
    "name", "description", "attribute_type", "data_type",
    "cardinality", "required", "default_value",
)
CONSTRAINT_FIELDS: Tuple[str, ...] = (
    "allowed_taxonomy_id", "allowed_node_ids",
    "min_value", "max_value", "pattern",
)
METADATA_FIELDS: Tuple[str, ...] = (
    "created_at", "updated_at", "created_by", "source",
)


def _empty_list() -> list:
    return []


@dataclass(frozen=True)
class KnowledgeAttribute:
    """The CaseOS KnowledgeAttribute V1.

    The dataclass is frozen. Collection fields
    (``allowed_node_ids``) are deep-copied in
    ``__post_init__`` so caller mutations cannot leak into
    the record. The minimal structural guards (identity +
    version) run inside ``__post_init__``; full schema
    validation lives in ``validator.py``.
    """

    # ---- Identity --------------------------------------------------
    attribute_id: str
    version: int

    # ---- Content ---------------------------------------------------
    name: str
    description: str
    attribute_type: str
    data_type: str
    cardinality: str
    required: bool = False
    default_value: Optional[str] = None

    # ---- Constraints -----------------------------------------------
    allowed_taxonomy_id: Optional[str] = None
    allowed_node_ids: list = field(default_factory=_empty_list)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None

    # ---- Metadata --------------------------------------------------
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    created_by: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        # Defensive deep-copy of allowed_node_ids.
        raw = self.allowed_node_ids
        if isinstance(raw, list):
            object.__setattr__(
                self, "allowed_node_ids", copy.deepcopy(raw),
            )
        elif isinstance(raw, tuple):
            object.__setattr__(
                self, "allowed_node_ids", copy.deepcopy(list(raw)),
            )

        # Minimal structural guards.
        if not isinstance(self.attribute_id, str) or not self.attribute_id:
            raise KnowledgeAttributeSchemaError(
                "attribute_id must be a non-empty string"
            )
        if not isinstance(self.version, int) or self.version < 1:
            raise KnowledgeAttributeSchemaError(
                "version must be a positive integer (>= 1); got "
                + repr(self.version)
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = {
            "attribute_id": self.attribute_id,
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "attribute_type": self.attribute_type,
            "data_type": self.data_type,
            "cardinality": self.cardinality,
            "required": bool(self.required),
            "default_value": self.default_value,
            "allowed_taxonomy_id": self.allowed_taxonomy_id,
            "allowed_node_ids": list(self.allowed_node_ids),
            "min_value": self.min_value,
            "max_value": self.max_value,
            "pattern": self.pattern,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "source": self.source,
        }
        return out

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "KnowledgeAttribute":
        """Build a ``KnowledgeAttribute`` from a dict-shaped input."""
        if not isinstance(data, dict):
            raise KnowledgeAttributeSchemaError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict[str, Any] = {}
        for fname in (
            "attribute_id", "version",
            "name", "description",
            "attribute_type", "data_type", "cardinality",
            "required", "default_value",
            "allowed_taxonomy_id",
            "min_value", "max_value", "pattern",
            "created_at", "updated_at", "created_by", "source",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        if "allowed_node_ids" in data:
            raw = data["allowed_node_ids"]
            if raw is None:
                kwargs["allowed_node_ids"] = []
            elif isinstance(raw, (list, tuple)):
                kwargs["allowed_node_ids"] = list(raw)
            else:
                raise KnowledgeAttributeSchemaError(
                    "allowed_node_ids must be a list/tuple; got "
                    + type(raw).__name__
                )
        return KnowledgeAttribute(**kwargs)


__all__ = [
    "KnowledgeAttribute",
    "KnowledgeAttributeError",
    "KnowledgeAttributeSchemaError",
    "IDENTITY_FIELDS",
    "CONTENT_FIELDS",
    "CONSTRAINT_FIELDS",
    "METADATA_FIELDS",
]
