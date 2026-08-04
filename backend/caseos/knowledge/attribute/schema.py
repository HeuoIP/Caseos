"""Knowledge Attribute Schema Constants V1 (Sprint 23.1-D).

This module declares the **structural constants** for
``KnowledgeAttribute`` records:

    * which fields are required,
    * what type each field is expected to be,
    * the version policy,
    * the V1 ``attribute_type`` allow-list,
    * the V1 ``data_type`` allow-list,
    * the V1 ``cardinality`` allow-list.

Attribute types V1:

    * property   -- general property slot
    * tag        -- tag / label slot
    * metric     -- measurable quantity

Data types V1:

    * string
    * number
    * boolean
    * enum
    * list
    * object

Cardinality values V1:

    * single     -- exactly one value
    * list       -- zero or more values, ordered, may repeat
    * set        -- zero or more values, unordered, no repeats

Architecture boundary (Sprint 23.1-D spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.attribute (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, Dict, FrozenSet, Tuple


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

REQUIRED_FIELDS: FrozenSet[str] = frozenset({
    # Identity
    "attribute_id",
    "version",
    # Content
    "name",
    "description",
    "attribute_type",
    "data_type",
    "cardinality",
    "required",
    "default_value",
    # Constraints
    "allowed_taxonomy_id",
    "allowed_node_ids",
    "min_value",
    "max_value",
    "pattern",
    # Metadata
    "created_at",
    "updated_at",
    "created_by",
    "source",
})


# ---------------------------------------------------------------------------
# Field types
# ---------------------------------------------------------------------------
# Each entry maps a field name to the expected Python type
# (or a tuple of acceptable types).

FIELD_TYPES: Dict[str, Tuple[type, ...]] = {
    "attribute_id": (str,),
    "version": (int,),
    "name": (str,),
    "description": (str,),
    "attribute_type": (str,),
    "data_type": (str,),
    "cardinality": (str,),
    "required": (bool,),
    "default_value": (str, type(None)),
    "allowed_taxonomy_id": (str, type(None)),
    "allowed_node_ids": (list, tuple),
    "min_value": (int, float, type(None)),
    "max_value": (int, float, type(None)),
    "pattern": (str, type(None)),
    "created_at": (str,),
    "updated_at": (str,),
    "created_by": (str,),
    "source": (str,),
}


# ---------------------------------------------------------------------------
# Version policy
# ---------------------------------------------------------------------------

VERSION_POLICY: Dict[str, Any] = {
    "version_type": int,
    "first_version": 1,
    "min_version": 1,
    "default_version": 1,
}


# ---------------------------------------------------------------------------
# Allow-lists
# ---------------------------------------------------------------------------

ATTRIBUTE_TYPE_ALLOW_LIST: FrozenSet[str] = frozenset({
    "property",
    "tag",
    "metric",
})

DATA_TYPE_ALLOW_LIST: FrozenSet[str] = frozenset({
    "string",
    "number",
    "boolean",
    "enum",
    "list",
    "object",
})

CARDINALITY_ALLOW_LIST: FrozenSet[str] = frozenset({
    "single",
    "list",
    "set",
})


# Convenience exported for tests and reports.
ALL_FIELDS: FrozenSet[str] = REQUIRED_FIELDS


__all__ = [
    "REQUIRED_FIELDS",
    "FIELD_TYPES",
    "VERSION_POLICY",
    "ATTRIBUTE_TYPE_ALLOW_LIST",
    "DATA_TYPE_ALLOW_LIST",
    "CARDINALITY_ALLOW_LIST",
    "ALL_FIELDS",
]
