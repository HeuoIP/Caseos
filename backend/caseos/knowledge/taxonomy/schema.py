"""Knowledge Taxonomy Schema Constants V1 (Sprint 23.1-C).

This module declares the **structural constants** for both
``Taxonomy`` and ``TaxonomyNode`` records:

    * which fields are required,
    * what type each field is expected to be,
    * the version policy,
    * the V1 ``taxonomy_type`` allow-list,
    * the V1 ``node_type`` allow-list.

Taxonomy types V1:

    * style        -- design styles (Scandinavian, Industrial)
    * color        -- color systems (Earth-tones, Monochrome)
    * material     -- materials (Wood, Concrete)
    * space_type   -- space types (Indoor, Outdoor)
    * age_group    -- age groups (3-6, 7-12)
    * function     -- functional labels (Exploratory, Guided)

Node types V1:

    * concept      -- abstract concept
    * category     -- intermediate category
    * instance     -- concrete instance
    * value        -- value/option

Architecture boundary (Sprint 23.1-C spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.taxonomy (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, Dict, FrozenSet, Tuple


# =====================================================================
# Taxonomy
# =====================================================================

REQUIRED_FIELDS: FrozenSet[str] = frozenset({
    # Identity
    "taxonomy_id",
    "version",
    # Content
    "name",
    "description",
    "taxonomy_type",
    "root_node_ids",
    # Metadata
    "created_at",
    "updated_at",
    "created_by",
    "source",
})


FIELD_TYPES: Dict[str, Tuple[type, ...]] = {
    "taxonomy_id": (str,),
    "version": (int,),
    "name": (str,),
    "description": (str,),
    "taxonomy_type": (str,),
    "root_node_ids": (list, tuple),
    "created_at": (str,),
    "updated_at": (str,),
    "created_by": (str,),
    "source": (str,),
}


VERSION_POLICY: Dict[str, Any] = {
    "version_type": int,
    "first_version": 1,
    "min_version": 1,
    "default_version": 1,
}


TAXONOMY_TYPE_ALLOW_LIST: FrozenSet[str] = frozenset({
    "style",
    "color",
    "material",
    "space_type",
    "age_group",
    "function",
})


ALL_TAXONOMY_FIELDS: FrozenSet[str] = REQUIRED_FIELDS


# =====================================================================
# TaxonomyNode
# =====================================================================

NODE_REQUIRED_FIELDS: FrozenSet[str] = frozenset({
    # Identity
    "node_id",
    "version",
    # Content
    "label",
    "description",
    "node_type",
    "aliases",
    # Hierarchy
    "parent_node_id",
    "depth",
    "path",
    # Metadata
    "created_at",
    "updated_at",
    "created_by",
    "source",
})


NODE_FIELD_TYPES: Dict[str, Tuple[type, ...]] = {
    "node_id": (str,),
    "version": (int,),
    "label": (str,),
    "description": (str,),
    "node_type": (str,),
    "aliases": (list, tuple),
    "parent_node_id": (str, type(None)),
    "depth": (int,),
    "path": (list, tuple),
    "created_at": (str,),
    "updated_at": (str,),
    "created_by": (str,),
    "source": (str,),
}


NODE_TYPE_ALLOW_LIST: FrozenSet[str] = frozenset({
    "concept",
    "category",
    "instance",
    "value",
})


ALL_NODE_FIELDS: FrozenSet[str] = NODE_REQUIRED_FIELDS


__all__ = [
    # Taxonomy
    "REQUIRED_FIELDS",
    "FIELD_TYPES",
    "VERSION_POLICY",
    "TAXONOMY_TYPE_ALLOW_LIST",
    "ALL_TAXONOMY_FIELDS",
    # Node
    "NODE_REQUIRED_FIELDS",
    "NODE_FIELD_TYPES",
    "NODE_TYPE_ALLOW_LIST",
    "ALL_NODE_FIELDS",
]
