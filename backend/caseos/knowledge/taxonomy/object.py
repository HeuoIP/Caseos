"""Knowledge Taxonomy Object Schemas V1 (Sprint 23.1-C).

This module declares two frozen dataclasses:

    Taxonomy         -- a named, hierarchical classification
                        system (e.g. "Design Style Taxonomy")
    TaxonomyNode     -- a single labelled entry in a
                        Taxonomy (e.g. "Scandinavian")

Taxonomy fields:

    Identity
        taxonomy_id, version
    Content
        name, description, taxonomy_type,
        root_node_ids
    Metadata
        created_at, updated_at, created_by, source

Total: 11 fields.

TaxonomyNode fields:

    Identity
        node_id, version
    Content
        label, description, node_type, aliases
    Hierarchy
        parent_node_id, depth, path
    Metadata
        created_at, updated_at, created_by, source

Total: 14 fields.

The taxonomy system is a **pure data structure** that does
NOT mutate any KO, Domain, or Binding. Future Retrieval /
Evolution sprints may consume it.

V1 is intentionally simple. The taxonomy has no automatic
classification, no auto-completion, no AI. Adding a node
requires explicit human construction of the record.

Architecture boundary (Sprint 23.1-C spec):

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
        * caseos.knowledge.binding (sibling Binding)
        * stdlib
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class TaxonomyError(ValueError):
    """Base error for the knowledge.taxonomy package."""


class TaxonomySchemaError(TaxonomyError):
    """Raised by ``Taxonomy.__post_init__`` on structural
    violations (missing required field, wrong type,
    invalid version, etc.).
    """


class TaxonomyNodeError(TaxonomyError):
    """Base error for ``TaxonomyNode`` records."""


class TaxonomyNodeSchemaError(TaxonomyNodeError):
    """Raised by ``TaxonomyNode.__post_init__`` on structural
    violations.
    """


def _empty_list() -> list:
    return []


# =====================================================================
# Taxonomy
# =====================================================================

TAXONOMY_IDENTITY_FIELDS: Tuple[str, ...] = ("taxonomy_id", "version")
TAXONOMY_CONTENT_FIELDS: Tuple[str, ...] = (
    "name", "description", "taxonomy_type", "root_node_ids",
)
TAXONOMY_METADATA_FIELDS: Tuple[str, ...] = (
    "created_at", "updated_at", "created_by", "source",
)


@dataclass(frozen=True)
class Taxonomy:
    """A named, hierarchical classification system.

    The dataclass is frozen. Collection fields are
    deep-copied in ``__post_init__`` so caller mutations
    cannot leak into the record.
    """

    # ---- Identity --------------------------------------------------
    taxonomy_id: str
    version: int

    # ---- Content ---------------------------------------------------
    name: str
    description: str
    taxonomy_type: str
    root_node_ids: list = field(default_factory=_empty_list)

    # ---- Metadata --------------------------------------------------
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    created_by: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        # Defensive deep-copy of root_node_ids.
        raw = self.root_node_ids
        if isinstance(raw, list):
            object.__setattr__(self, "root_node_ids", copy.deepcopy(raw))
        elif isinstance(raw, tuple):
            object.__setattr__(
                self, "root_node_ids", copy.deepcopy(list(raw)),
            )

        # Minimal structural guards.
        if not isinstance(self.taxonomy_id, str) or not self.taxonomy_id:
            raise TaxonomySchemaError(
                "taxonomy_id must be a non-empty string"
            )
        if not isinstance(self.version, int) or self.version < 1:
            raise TaxonomySchemaError(
                "version must be a positive integer (>= 1); got "
                + repr(self.version)
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = {
            "taxonomy_id": self.taxonomy_id,
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "taxonomy_type": self.taxonomy_type,
            "root_node_ids": list(self.root_node_ids),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "source": self.source,
        }
        return out

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Taxonomy":
        """Build a ``Taxonomy`` from a dict-shaped input."""
        if not isinstance(data, dict):
            raise TaxonomySchemaError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict[str, Any] = {}
        for fname in (
            "taxonomy_id", "version",
            "name", "description", "taxonomy_type",
            "created_at", "updated_at", "created_by", "source",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        if "root_node_ids" in data:
            raw = data["root_node_ids"]
            if raw is None:
                kwargs["root_node_ids"] = []
            elif isinstance(raw, (list, tuple)):
                kwargs["root_node_ids"] = list(raw)
            else:
                raise TaxonomySchemaError(
                    "root_node_ids must be a list/tuple; got "
                    + type(raw).__name__
                )
        return Taxonomy(**kwargs)


# =====================================================================
# TaxonomyNode
# =====================================================================

IDENTITY_FIELDS: Tuple[str, ...] = ("node_id", "version")
CONTENT_FIELDS: Tuple[str, ...] = (
    "label", "description", "node_type", "aliases",
)
HIERARCHY_FIELDS: Tuple[str, ...] = (
    "parent_node_id", "depth", "path",
)
METADATA_FIELDS: Tuple[str, ...] = (
    "created_at", "updated_at", "created_by", "source",
)


@dataclass(frozen=True)
class TaxonomyNode:
    """A single labelled entry in a Taxonomy.

    The dataclass is frozen. Collection fields
    (``aliases``, ``path``) are deep-copied in
    ``__post_init__`` so caller mutations cannot leak into
    the record.
    """

    # ---- Identity --------------------------------------------------
    node_id: str
    version: int

    # ---- Content ---------------------------------------------------
    label: str
    description: str
    node_type: str
    aliases: list = field(default_factory=_empty_list)

    # ---- Hierarchy -------------------------------------------------
    parent_node_id: Optional[str] = None
    depth: int = 1
    path: list = field(default_factory=_empty_list)

    # ---- Metadata --------------------------------------------------
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    created_by: str = ""
    source: str = ""

    def __post_init__(self) -> None:
        # Defensive deep-copy of collection fields.
        for fname in ("aliases", "path"):
            raw = getattr(self, fname)
            if isinstance(raw, list):
                object.__setattr__(self, fname, copy.deepcopy(raw))
            elif isinstance(raw, tuple):
                object.__setattr__(self, fname, copy.deepcopy(list(raw)))

        # Minimal structural guards.
        if not isinstance(self.node_id, str) or not self.node_id:
            raise TaxonomyNodeSchemaError(
                "node_id must be a non-empty string"
            )
        if not isinstance(self.version, int) or self.version < 1:
            raise TaxonomyNodeSchemaError(
                "version must be a positive integer (>= 1); got "
                + repr(self.version)
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = {
            "node_id": self.node_id,
            "version": self.version,
            "label": self.label,
            "description": self.description,
            "node_type": self.node_type,
            "aliases": list(self.aliases),
            "parent_node_id": self.parent_node_id,
            "depth": int(self.depth),
            "path": list(self.path),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "source": self.source,
        }
        return out

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "TaxonomyNode":
        """Build a ``TaxonomyNode`` from a dict-shaped input."""
        if not isinstance(data, dict):
            raise TaxonomyNodeSchemaError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict[str, Any] = {}
        for fname in (
            "node_id", "version",
            "label", "description", "node_type",
            "parent_node_id", "depth",
            "created_at", "updated_at", "created_by", "source",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        for fname in ("aliases", "path"):
            if fname in data:
                raw = data[fname]
                if raw is None:
                    kwargs[fname] = []
                elif isinstance(raw, (list, tuple)):
                    kwargs[fname] = list(raw)
                else:
                    raise TaxonomyNodeSchemaError(
                        fname + " must be a list/tuple; got "
                        + type(raw).__name__
                    )
        return TaxonomyNode(**kwargs)


__all__ = [
    # Taxonomy
    "Taxonomy",
    "TaxonomyError",
    "TaxonomySchemaError",
    "TAXONOMY_IDENTITY_FIELDS",
    "TAXONOMY_CONTENT_FIELDS",
    "TAXONOMY_METADATA_FIELDS",
    # Node
    "TaxonomyNode",
    "TaxonomyNodeError",
    "TaxonomyNodeSchemaError",
    "IDENTITY_FIELDS",
    "CONTENT_FIELDS",
    "HIERARCHY_FIELDS",
    "METADATA_FIELDS",
]
