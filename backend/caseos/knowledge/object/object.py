"""Knowledge Object V1 (Sprint 23.0-A).

The ``KnowledgeObject`` is the **core business knowledge
record** of CaseOS. It is the canonical shape that:

    * Evolution mutations will write into (Sprint 22.4-H
      and beyond)
    * Retrieval will read from (future sprints; out of
      scope here)
    * AI Design Engine will consume (future sprints; out
      of scope here)

V1 is intentionally a **pure data contract** -- no
business logic, no embeddings, no image models, no
auto-tagging. The sprint ships only the schema, the
validator, the snapshot, and the serialization.

The dataclass is **frozen**. Collection-typed fields
are **deep-copied in __post_init__** so caller mutations
cannot leak into the record. The schema validation
runs in the constructor's ``__post_init__`` and raises
``KnowledgeObjectSchemaError`` on a structural violation
(field missing, wrong type, version <= 0).

Field groups:

    Identity
        knowledge_id, version
    Content
        title, description, category
    Case Context
        project_type, site_type, location_type, space_size
    Design Attributes
        theme, style, color_system, interaction_type,
        function_tags
    Assets
        image_refs, document_refs
    Metadata
        created_at, updated_at, source

Total field count: 19 (>= the spec's minimum of 15).

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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional, Tuple


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class KnowledgeObjectError(ValueError):
    """Base error for the knowledge.object package."""


class KnowledgeObjectSchemaError(KnowledgeObjectError):
    """Raised by ``KnowledgeObject.__post_init__`` on structural
    violations (missing required field, wrong type, invalid
    version, etc.).
    """


# Field group boundaries are documented as plain constants so
# validators, reports, and tests can introspect them without
# reaching into the dataclass internals.
IDENTITY_FIELDS: Tuple[str, ...] = ("knowledge_id", "version")
CONTENT_FIELDS: Tuple[str, ...] = (
    "title", "description", "category",
)
CASE_CONTEXT_FIELDS: Tuple[str, ...] = (
    "project_type", "site_type", "location_type", "space_size",
)
DESIGN_ATTRIBUTE_FIELDS: Tuple[str, ...] = (
    "theme", "style", "color_system",
    "interaction_type", "function_tags",
)
ASSET_FIELDS: Tuple[str, ...] = (
    "image_refs", "document_refs",
)
METADATA_FIELDS: Tuple[str, ...] = (
    "created_at", "updated_at", "source",
)


def _empty_list() -> list:
    return []


@dataclass(frozen=True)
class KnowledgeObject:
    """The core CaseOS Knowledge Object V1.

    See module docstring for the field layout. The dataclass
    is frozen; collection fields are deep-copied on entry.
    """

    # ---- Identity --------------------------------------------------
    knowledge_id: str
    version: int

    # ---- Content --------------------------------------------------
    title: str
    description: str
    category: str

    # ---- Case Context ---------------------------------------------
    project_type: str
    site_type: str
    location_type: str
    space_size: str

    # ---- Design Attributes ---------------------------------------
    theme: str
    style: str
    color_system: str
    interaction_type: str
    function_tags: list = field(default_factory=_empty_list)

    # ---- Assets ---------------------------------------------------
    image_refs: list = field(default_factory=_empty_list)
    document_refs: list = field(default_factory=_empty_list)

    # ---- Metadata -------------------------------------------------
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    source: str = ""

    # --------------------------------------------------------------
    # Post-init: defensive copy + minimal structural guard
    # --------------------------------------------------------------

    def __post_init__(self) -> None:
        # Defensive deep-copy of every collection-typed field.
        # The frozen dataclass freezes the *bindings*, not the
        # contents of mutable containers, so a deep copy is
        # required to make caller mutations safe.
        for fname in (
            "function_tags", "image_refs", "document_refs",
        ):
            raw = getattr(self, fname)
            if isinstance(raw, list):
                object.__setattr__(self, fname, copy.deepcopy(raw))
            elif isinstance(raw, tuple):
                object.__setattr__(self, fname, copy.deepcopy(list(raw)))

        # Minimal structural guards. Schema-level validation
        # lives in ``validator.py`` and runs at higher levels.
        if not isinstance(self.knowledge_id, str) or not self.knowledge_id:
            raise KnowledgeObjectSchemaError(
                "knowledge_id must be a non-empty string"
            )
        if not isinstance(self.version, int) or self.version < 1:
            raise KnowledgeObjectSchemaError(
                "version must be a positive integer (>= 1); got "
                + repr(self.version)
            )

    # --------------------------------------------------------------
    # Serialization
    # --------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation.

        The round-trip partner is ``KnowledgeObject.from_dict``.
        Collection fields are returned as plain lists so the
        output is JSON-native.
        """
        out = {
            "knowledge_id": self.knowledge_id,
            "version": self.version,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "project_type": self.project_type,
            "site_type": self.site_type,
            "location_type": self.location_type,
            "space_size": self.space_size,
            "theme": self.theme,
            "style": self.style,
            "color_system": self.color_system,
            "interaction_type": self.interaction_type,
            "function_tags": list(self.function_tags),
            "image_refs": list(self.image_refs),
            "document_refs": list(self.document_refs),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
        }
        return out

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "KnowledgeObject":
        """Build a ``KnowledgeObject`` from a dict-shaped input.

        Missing optional fields fall back to their dataclass
        defaults. Missing required fields raise
        ``KnowledgeObjectSchemaError``.
        """
        if not isinstance(data, dict):
            raise KnowledgeObjectSchemaError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict[str, Any] = {}
        for fname in (
            "knowledge_id", "version",
            "title", "description", "category",
            "project_type", "site_type", "location_type", "space_size",
            "theme", "style", "color_system", "interaction_type",
            "created_at", "updated_at", "source",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        for fname in ("function_tags", "image_refs", "document_refs"):
            if fname in data:
                raw = data[fname]
                if raw is None:
                    kwargs[fname] = []
                elif isinstance(raw, (list, tuple)):
                    kwargs[fname] = list(raw)
                else:
                    raise KnowledgeObjectSchemaError(
                        fname + " must be a list/tuple; got "
                        + type(raw).__name__
                    )
        return KnowledgeObject(**kwargs)


__all__ = [
    "KnowledgeObject",
    "KnowledgeObjectError",
    "KnowledgeObjectSchemaError",
    "IDENTITY_FIELDS",
    "CONTENT_FIELDS",
    "CASE_CONTEXT_FIELDS",
    "DESIGN_ATTRIBUTE_FIELDS",
    "ASSET_FIELDS",
    "METADATA_FIELDS",
]
