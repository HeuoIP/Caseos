"""KODomainBinding Schema V1 (Sprint 23.1-B).

The schema module declares the **structural constants**
that ``KODomainBinding`` instances must obey:

    * which fields are required,
    * what type each field is expected to be,
    * the version policy (first version, minimum version,
      default version),
    * the V1 ``binding_type`` allow-list.

The schema is data-only: pure constants. It does NOT run
validation logic (that lives in ``validator.py``).

Binding types V1 (Sprint 23.1-B spec):

    * primary    -- the canonical domain membership of the
                    Knowledge Object. At most ONE primary
                    binding per KO is allowed.
    * secondary  -- alternative domain memberships. Multiple
                    secondaries per KO are allowed.
    * derived    -- inferred from another binding (read-only
                    in V1; created by future Sprints, never
                    by the operator).

Adding new binding types requires extending the allow-list
AND a schema-review Sprint that ensures downstream
consumers (future Retrieval / Evolution sprints)
understand the new type.

Architecture boundary (Sprint 23.1-B spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.binding (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, Dict, FrozenSet, Tuple


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------

REQUIRED_FIELDS: FrozenSet[str] = frozenset({
    # Identity
    "binding_id",
    "version",
    # Reference
    "knowledge_object_id",
    "knowledge_object_version",
    "domain_id",
    "binding_type",
    "priority",
    # Metadata
    "membership_reason",
    "created_at",
    "updated_at",
    "created_by",
    "proposal_id",
})


# ---------------------------------------------------------------------------
# Field types
# ---------------------------------------------------------------------------
# Each entry maps a field name to the expected Python type
# (or a tuple of acceptable types).

FIELD_TYPES: Dict[str, Tuple[type, ...]] = {
    "binding_id": (str,),
    "version": (int,),
    "knowledge_object_id": (str,),
    "knowledge_object_version": (int,),
    "domain_id": (str,),
    "binding_type": (str,),
    "priority": (int,),
    "membership_reason": (str,),
    "created_at": (str,),
    "updated_at": (str,),
    "created_by": (str,),
    "proposal_id": (str,),
}


# ---------------------------------------------------------------------------
# Version policy
# ---------------------------------------------------------------------------
# V1 rules (Sprint 23.1-B spec):
#
#   * version is an int.
#   * First published version is 1.
#   * version <= 0 is forbidden (the dataclass raises on
#     construction; the validator also reports it as a
#     structural error).

BINDING_VERSION_POLICY: Dict[str, Any] = {
    "version_type": int,
    "first_version": 1,
    "min_version": 1,
    "default_version": 1,
}


# ---------------------------------------------------------------------------
# Binding type allow-list
# ---------------------------------------------------------------------------
# V1 supports exactly three binding_type values.

BINDING_TYPE_ALLOW_LIST: FrozenSet[str] = frozenset({
    "primary",
    "secondary",
    "derived",
})


# Convenience exported for tests and reports.
ALL_FIELDS: FrozenSet[str] = REQUIRED_FIELDS


__all__ = [
    "REQUIRED_FIELDS",
    "FIELD_TYPES",
    "BINDING_VERSION_POLICY",
    "BINDING_TYPE_ALLOW_LIST",
    "ALL_FIELDS",
]
