"""Knowledge Domain Taxonomy V1 (Sprint 23.1-A).

The taxonomy module declares the **structural constants**
that ``KnowledgeDomain`` instances must obey:

    * which fields are required,
    * what type each field is expected to be,
    * the version policy (first version, minimum version,
      default version),
    * the V1 ``domain_type`` allow-list.

The taxonomy is data-only: pure constants. It does NOT run
validation logic (that lives in ``validator.py``). It does
NOT enforce anything at runtime; the dataclass's
``__post_init__`` runs a minimal structural guard, and the
``KnowledgeDomainValidator`` runs the full check.

Domain types V1 (Sprint 23.1-A spec):

    * design_category   -- top-level design domains
                           (kindergarten, office, residential)
    * industry_vertical -- industry verticals
                           (education, healthcare, retail)
    * project_family    -- family of related projects
                           (renovation, new_build, fit-out)

These three taxonomy buckets cover the V1 use cases
without committing to a future-proof vocabulary. New types
are added in a future Sprint by extending
``DOMAIN_TYPE_ALLOW_LIST``.

Architecture boundary (Sprint 23.1-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.domain (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, Dict, FrozenSet, Tuple


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

REQUIRED_FIELDS: FrozenSet[str] = frozenset({
    # Identity
    "domain_id",
    "version",
    # Scope
    "domain_type",
    "name",
    "description",
    "parent_domain_id",
    "scope_tags",
    # Taxonomy
    "allowed_knowledge_types",
    "boundary_rules",
    "principle_rules",
    # Metadata
    "created_at",
    "updated_at",
    "source",
})


# ---------------------------------------------------------------------------
# Field types
# ---------------------------------------------------------------------------
# Each entry maps a field name to the expected Python type
# (or a tuple of acceptable types). Collection fields accept
# ``list`` or ``tuple`` for forward compatibility.
# ``parent_domain_id`` may be None (top-level domain).

FIELD_TYPES: Dict[str, Tuple[type, ...]] = {
    "domain_id": (str,),
    "version": (int,),
    "domain_type": (str,),
    "name": (str,),
    "description": (str,),
    "parent_domain_id": (str, type(None)),
    "scope_tags": (list, tuple),
    "allowed_knowledge_types": (list, tuple),
    "boundary_rules": (list, tuple),
    "principle_rules": (list, tuple),
    "created_at": (str,),
    "updated_at": (str,),
    "source": (str,),
}


# ---------------------------------------------------------------------------
# Version policy
# ---------------------------------------------------------------------------
# V1 rules (Sprint 23.1-A spec):
#
#   * version is an int.
#   * First published version is 1.
#   * version <= 0 is forbidden (the dataclass raises on
#     construction; the validator also reports it as a
#     structural error).

DOMAIN_VERSION_POLICY: Dict[str, Any] = {
    "version_type": int,
    "first_version": 1,
    "min_version": 1,
    "default_version": 1,
}


# ---------------------------------------------------------------------------
# Domain type allow-list
# ---------------------------------------------------------------------------
# V1 supports exactly three domain_type values. Adding new
# types requires extending this allow-list AND a schema-
# review Sprint that ensures downstream consumers (future
# Retrieval / Evolution sprints) understand the new type.

DOMAIN_TYPE_ALLOW_LIST: FrozenSet[str] = frozenset({
    "design_category",
    "industry_vertical",
    "project_family",
})


# Convenience exported for tests and reports.
ALL_FIELDS: FrozenSet[str] = REQUIRED_FIELDS


__all__ = [
    "REQUIRED_FIELDS",
    "FIELD_TYPES",
    "DOMAIN_VERSION_POLICY",
    "DOMAIN_TYPE_ALLOW_LIST",
    "ALL_FIELDS",
]
