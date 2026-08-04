"""Knowledge Attribute Markdown Report V1 (Sprint 23.1-D).

The report module emits a human-readable Markdown summary
of the Attribute schema and an optional registry snapshot.

Sections:

    # Knowledge Attribute Schema Report
    ## Overview
    ## Identity / Content / Constraint / Metadata Fields
    ## Version Policy
    ## Attribute Type Allow-list
    ## Data Type Allow-list
    ## Cardinality Allow-list
    ## Validation Rules
    ## Registry Snapshot
    ## Architecture Boundary

The report is purely descriptive.

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

from typing import Any, Optional

from .object import (
    CONSTRAINT_FIELDS,
    CONTENT_FIELDS,
    IDENTITY_FIELDS,
    METADATA_FIELDS,
)
from .registry import AttributeRegistry
from .schema import (
    ATTRIBUTE_TYPE_ALLOW_LIST,
    CARDINALITY_ALLOW_LIST,
    DATA_TYPE_ALLOW_LIST,
    FIELD_TYPES,
    REQUIRED_FIELDS,
    VERSION_POLICY,
)


def _fmt_fields(fields: tuple) -> str:
    return "\n".join("- `" + f + "`" for f in fields)


def _fmt_field_types() -> str:
    rows = []
    for fname in sorted(FIELD_TYPES.keys()):
        accepted = FIELD_TYPES[fname]
        names = ", ".join(t.__name__ for t in accepted)
        rows.append("- `" + fname + "`: " + names)
    return "\n".join(rows)


def _fmt_allow_list(items: frozenset) -> str:
    return "\n".join("- `" + t + "`" for t in sorted(items))


def _fmt_registry(registry: Optional[AttributeRegistry]) -> str:
    if registry is None:
        return "_no registry supplied_"
    if registry.count() == 0:
        return "_registry is empty_"
    rows: list[str] = []
    rows.append("- **total attributes**: " + str(registry.count()))
    rows.append(
        "- **distinct attribute ids**: "
        + str(len(registry.attribute_ids()))
    )
    rows.append("- **required attributes**: " + str(len(registry.required())))
    rows.append("- **optional attributes**: " + str(len(registry.optional())))
    rows.append("")
    rows.append("| attribute_id | name | type | data_type | cardinality | required | allowed_taxonomy_id |")
    rows.append("|---|---|---|---|---|---|---|")
    for a in registry.list():
        rows.append(
            "| "
            + a.attribute_id
            + " | "
            + a.name
            + " | "
            + a.attribute_type
            + " | "
            + a.data_type
            + " | "
            + a.cardinality
            + " | "
            + str(bool(a.required))
            + " | "
            + (a.allowed_taxonomy_id or "(none)")
            + " |"
        )
    return "\n".join(rows)


def generate_attribute_report(
    registry: Optional[AttributeRegistry] = None,
) -> str:
    """Return a Markdown report describing the V1 Attribute schema
    and the optional ``registry`` snapshot.
    """
    sections: list[str] = []

    # Header
    sections.append("# Knowledge Attribute Schema Report")
    sections.append("")
    sections.append(
        "**Sprint**: 23.1-D (Knowledge Attribute Schema V1)"
    )
    sections.append(
        "**ADR**: 018 (Feedback Learning Loop) / 020 (Knowledge Evolution)"
    )
    sections.append("")

    # 1. Overview
    sections.append("## Overview")
    sections.append("")
    sections.append(
        "A ``KnowledgeAttribute`` declares the schema for a single"
        " property slot on a ``KnowledgeObject`` (e.g."
        " ``style``, ``theme``, ``color_system``), including data"
        " type, cardinality, and value constraints."
    )
    sections.append("")
    sections.append(
        "The attribute NEVER mutates a KnowledgeObject, a Domain, a"
        " Binding, or a Taxonomy. It is a pure schema declaration"
        " that future Retrieval / Evolution sprints may consult."
    )
    sections.append("")
    sections.append(
        "- **Required field count**: " + str(len(REQUIRED_FIELDS))
    )
    sections.append(
        "- **Field groups**: 4 (identity, content, constraint, metadata)"
    )
    sections.append(
        "- **attribute_type allow-list size**: "
        + str(len(ATTRIBUTE_TYPE_ALLOW_LIST))
    )
    sections.append(
        "- **data_type allow-list size**: "
        + str(len(DATA_TYPE_ALLOW_LIST))
    )
    sections.append(
        "- **cardinality allow-list size**: "
        + str(len(CARDINALITY_ALLOW_LIST))
    )
    sections.append("")

    # 2. Identity Fields
    sections.append("## Identity Fields")
    sections.append("")
    sections.append(_fmt_fields(IDENTITY_FIELDS))
    sections.append("")

    # 3. Content Fields
    sections.append("## Content Fields")
    sections.append("")
    sections.append(_fmt_fields(CONTENT_FIELDS))
    sections.append("")

    # 4. Constraint Fields
    sections.append("## Constraint Fields")
    sections.append("")
    sections.append(_fmt_fields(CONSTRAINT_FIELDS))
    sections.append("")

    # 5. Metadata Fields
    sections.append("## Metadata Fields")
    sections.append("")
    sections.append(_fmt_fields(METADATA_FIELDS))
    sections.append("")

    # 6. Version Policy
    sections.append("## Version Policy")
    sections.append("")
    sections.append(
        "- **version_type**: `"
        + getattr(
            VERSION_POLICY.get("version_type"),
            "__name__",
            str(VERSION_POLICY.get("version_type")),
        )
        + "`"
    )
    sections.append(
        "- **first_version**: `"
        + str(VERSION_POLICY.get("first_version"))
        + "`"
    )
    sections.append(
        "- **min_version**: `"
        + str(VERSION_POLICY.get("min_version"))
        + "`"
    )
    sections.append(
        "- **default_version**: `"
        + str(VERSION_POLICY.get("default_version"))
        + "`"
    )
    sections.append("")

    # 7. Attribute Type Allow-list
    sections.append("## Attribute Type Allow-list")
    sections.append("")
    sections.append(_fmt_allow_list(ATTRIBUTE_TYPE_ALLOW_LIST))
    sections.append("")

    # 8. Data Type Allow-list
    sections.append("## Data Type Allow-list")
    sections.append("")
    sections.append(_fmt_allow_list(DATA_TYPE_ALLOW_LIST))
    sections.append("")

    # 9. Cardinality Allow-list
    sections.append("## Cardinality Allow-list")
    sections.append("")
    sections.append(_fmt_allow_list(CARDINALITY_ALLOW_LIST))
    sections.append("")

    # 10. Field Types
    sections.append("## Field Types")
    sections.append("")
    sections.append(_fmt_field_types())
    sections.append("")

    # 11. Validation Rules
    sections.append("## Validation Rules")
    sections.append("")
    sections.append("Single-record rules:")
    sections.append("- A1: `attribute_id` must be a non-empty string")
    sections.append("- A2: `version >= 1`")
    sections.append("- A3: `name` must be a non-empty string")
    sections.append("- A4: `description` must be a non-empty string")
    sections.append(
        "- A5: `attribute_type` must be in the V1 allow-list"
    )
    sections.append(
        "- A6: `data_type` must be in the V1 allow-list"
    )
    sections.append(
        "- A7: `cardinality` must be in the V1 allow-list"
    )
    sections.append("- A8: `required` must be a bool")
    sections.append(
        "- A9: `default_value`, when present, must be a non-empty string"
    )
    sections.append(
        "- A10: `min_value <= max_value` when both are numbers"
    )
    sections.append(
        "- A11: for `data_type=enum`, `allowed_node_ids` is non-empty"
    )
    sections.append(
        "- A12: `cardinality=set` requires `allowed_node_ids` non-empty"
    )
    sections.append("")
    sections.append("Cross-record rules:")
    sections.append(
        "- AC1: `attribute_id` is unique within the attribute registry"
    )
    sections.append(
        "- AC2: `allowed_taxonomy_id`, when present, must refer to"
        " a registered taxonomy"
    )
    sections.append("")

    # 12. Registry Snapshot
    sections.append("## Registry Snapshot")
    sections.append("")
    sections.append(_fmt_registry(registry))
    sections.append("")

    # 13. Architecture Boundary
    sections.append("## Architecture Boundary")
    sections.append("")
    sections.append(
        "- The Attribute package does NOT import from"
        " `caseos.intelligence.*` or `caseos.knowledge.retrieval`."
    )
    sections.append(
        "- The Attribute package does NOT mutate any"
        " KnowledgeObject, KnowledgeDomain, KODomainBinding, or"
        " Taxonomy / TaxonomyNode."
    )
    sections.append(
        "- The AttributeRegistry is append-only; the four"
        " forbidden methods raise `TypeError`."
    )
    sections.append("")

    return "\n".join(sections)


__all__ = ["generate_attribute_report"]
