"""Knowledge Object Schema V1 (Sprint 23.0-A).

The schema module declares the **structural contract** that
``KnowledgeObject`` instances must obey:

    * which fields are required,
    * what type each field is expected to be,
    * the version policy (first version, minimum version,
      default version).

The schema is data-only: pure constants. It does NOT run
validation logic (that lives in ``validator.py``). It does
NOT enforce anything at runtime; the dataclass's
``__post_init__`` runs a minimal structural guard, and the
``KnowledgeObjectValidator`` runs the full check.

Splitting schema constants from validator behaviour keeps
the schema usable in three contexts:

    1. ``KnowledgeObjectValidator`` consults the constants
       to drive its checks.
    2. ``KnowledgeObjectSchemaReport`` consults the
       constants to build a Markdown report.
    3. Tests introspect the constants directly.

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

from typing import Any, Dict, FrozenSet, Tuple


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

REQUIRED_FIELDS: FrozenSet[str] = frozenset({
    # Identity
    "knowledge_id",
    "version",
    # Content
    "title",
    "description",
    "category",
    # Case context
    "project_type",
    "site_type",
    "location_type",
    "space_size",
    # Design attributes
    "theme",
    "style",
    "color_system",
    "interaction_type",
    "function_tags",
    # Assets
    "image_refs",
    "document_refs",
    # Metadata
    "created_at",
    "updated_at",
    "source",
})


# ---------------------------------------------------------------------------
# Field types
# ---------------------------------------------------------------------------
# Each entry maps a field name to the expected Python type
# (or a tuple of acceptable types). ``None`` means the
# field has no type expectation (e.g. timestamps stored as
# ISO strings). Collection fields (``function_tags``,
# ``image_refs``, ``document_refs``) accept ``list`` or
# ``tuple`` for forward compatibility.

FIELD_TYPES: Dict[str, Tuple[type, ...]] = {
    "knowledge_id": (str,),
    "version": (int,),
    "title": (str,),
    "description": (str,),
    "category": (str,),
    "project_type": (str,),
    "site_type": (str,),
    "location_type": (str,),
    "space_size": (str,),
    "theme": (str,),
    "style": (str,),
    "color_system": (str,),
    "interaction_type": (str,),
    "function_tags": (list, tuple),
    "image_refs": (list, tuple),
    "document_refs": (list, tuple),
    "created_at": (str,),
    "updated_at": (str,),
    "source": (str,),
}


# ---------------------------------------------------------------------------
# Version policy
# ---------------------------------------------------------------------------
# V1 rules (Sprint 23.0-A spec Task 3):
#
#   * version is an int.
#   * First published version is 1.
#   * version <= 0 is forbidden (the dataclass raises on
#     construction; the validator also reports it as a
#     structural error).

VERSION_POLICY: Dict[str, Any] = {
    "version_type": int,
    "first_version": 1,
    "min_version": 1,
    "default_version": 1,
}


# Convenience exported for tests and reports.
ALL_FIELDS: FrozenSet[str] = REQUIRED_FIELDS


__all__ = [
    "REQUIRED_FIELDS",
    "FIELD_TYPES",
    "VERSION_POLICY",
    "ALL_FIELDS",
]
