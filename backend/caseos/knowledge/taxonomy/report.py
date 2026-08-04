"""Knowledge Taxonomy Markdown Report V1 (Sprint 23.1-C).

The report module emits a human-readable Markdown summary
of the Taxonomy schema and an optional registry snapshot.

Sections:

    # Knowledge Taxonomy Schema Report
    ## Overview
    ## Taxonomy Identity / Content / Metadata Fields
    ## Taxonomy Version Policy
    ## Taxonomy Type Allow-list
    ## Taxonomy Validation Rules
    ## Node Identity / Content / Hierarchy / Metadata Fields
    ## Node Type Allow-list
    ## Node Validation Rules
    ## Registry Snapshot
    ## Architecture Boundary

The report is purely descriptive.

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

from typing import Any, Optional

from .object import (
    TAXONOMY_CONTENT_FIELDS,
    TAXONOMY_IDENTITY_FIELDS,
    TAXONOMY_METADATA_FIELDS,
    CONTENT_FIELDS as NODE_CONTENT_FIELDS,
    HIERARCHY_FIELDS as NODE_HIERARCHY_FIELDS,
    IDENTITY_FIELDS as NODE_IDENTITY_FIELDS,
    METADATA_FIELDS as NODE_METADATA_FIELDS,
)
from .registry import TaxonomyRegistry
from .schema import (
    FIELD_TYPES,
    NODE_FIELD_TYPES,
    NODE_REQUIRED_FIELDS,
    NODE_TYPE_ALLOW_LIST,
    REQUIRED_FIELDS,
    TAXONOMY_TYPE_ALLOW_LIST,
    VERSION_POLICY,
)


def _fmt_fields(fields: tuple) -> str:
    return "\n".join("- `" + f + "`" for f in fields)


def _fmt_field_types(types_dict: dict) -> str:
    rows = []
    for fname in sorted(types_dict.keys()):
        accepted = types_dict[fname]
        names = ", ".join(t.__name__ for t in accepted)
        rows.append("- `" + fname + "`: " + names)
    return "\n".join(rows)


def _fmt_allow_list(items: frozenset) -> str:
    return "\n".join("- `" + t + "`" for t in sorted(items))


def _fmt_registry(registry: Optional[TaxonomyRegistry]) -> str:
    if registry is None:
        return "_no registry supplied_"
    if registry.count_taxonomies() == 0 and registry.count_nodes() == 0:
        return "_registry is empty_"
    rows: list[str] = []
    rows.append(
        "- **total taxonomies**: " + str(registry.count_taxonomies())
    )
    rows.append(
        "- **total nodes**: " + str(registry.count_nodes())
    )
    rows.append(
        "- **distinct taxonomy ids**: "
        + str(len(registry.taxonomy_ids()))
    )
    rows.append(
        "- **distinct node ids**: " + str(len(registry.node_ids()))
    )
    rows.append("")
    rows.append("### Taxonomies")
    rows.append("")
    rows.append("| taxonomy_id | name | type | version | root_node_ids |")
    rows.append("|---|---|---|---|---|")
    for t in registry.list_taxonomies():
        rows.append(
            "| "
            + t.taxonomy_id
            + " | "
            + t.name
            + " | "
            + t.taxonomy_type
            + " | "
            + str(t.version)
            + " | "
            + ", ".join(t.root_node_ids)
            + " |"
        )
    rows.append("")
    rows.append("### Nodes")
    rows.append("")
    rows.append(
        "| node_id | label | type | depth | parent | path |"
    )
    rows.append("|---|---|---|---|---|---|")
    for n in registry.list_nodes():
        path_str = "/".join(n.path) if n.path else "(root)"
        parent_str = n.parent_node_id if n.parent_node_id else "(root)"
        rows.append(
            "| "
            + n.node_id
            + " | "
            + n.label
            + " | "
            + n.node_type
            + " | "
            + str(n.depth)
            + " | "
            + parent_str
            + " | "
            + path_str
            + " |"
        )
    return "\n".join(rows)


def generate_taxonomy_report(
    registry: Optional[TaxonomyRegistry] = None,
) -> str:
    """Return a Markdown report describing the V1 Taxonomy schema
    and the optional ``registry`` snapshot.
    """
    sections: list[str] = []

    # Header
    sections.append("# Knowledge Taxonomy Schema Report")
    sections.append("")
    sections.append(
        "**Sprint**: 23.1-C (Knowledge Taxonomy Schema V1)"
    )
    sections.append(
        "**ADR**: 018 (Feedback Learning Loop) / 020 (Knowledge Evolution)"
    )
    sections.append("")

    # 1. Overview
    sections.append("## Overview")
    sections.append("")
    sections.append(
        "A ``Taxonomy`` is a named, hierarchical classification system"
        " (e.g. \"Design Style Taxonomy\"). A ``TaxonomyNode`` is a"
        " single labelled entry in a Taxonomy (e.g."
        " \"Scandinavian\")."
    )
    sections.append("")
    sections.append(
        "The taxonomy NEVER mutates a Knowledge Object, a Domain, or"
        " a Binding. It is a pure data structure that future"
        " Retrieval / Evolution sprints may consume."
    )
    sections.append("")
    sections.append(
        "- **Taxonomy required field count**: "
        + str(len(REQUIRED_FIELDS))
    )
    sections.append(
        "- **Taxonomy field groups**: 3 (identity, content, metadata)"
    )
    sections.append(
        "- **Taxonomy type allow-list size**: "
        + str(len(TAXONOMY_TYPE_ALLOW_LIST))
    )
    sections.append(
        "- **Node required field count**: "
        + str(len(NODE_REQUIRED_FIELDS))
    )
    sections.append(
        "- **Node field groups**: 4 (identity, content, hierarchy, metadata)"
    )
    sections.append(
        "- **Node type allow-list size**: "
        + str(len(NODE_TYPE_ALLOW_LIST))
    )
    sections.append("")

    # 2. Taxonomy Identity
    sections.append("## Taxonomy Identity Fields")
    sections.append("")
    sections.append(_fmt_fields(TAXONOMY_IDENTITY_FIELDS))
    sections.append("")

    # 3. Taxonomy Content
    sections.append("## Taxonomy Content Fields")
    sections.append("")
    sections.append(_fmt_fields(TAXONOMY_CONTENT_FIELDS))
    sections.append("")

    # 4. Taxonomy Metadata
    sections.append("## Taxonomy Metadata Fields")
    sections.append("")
    sections.append(_fmt_fields(TAXONOMY_METADATA_FIELDS))
    sections.append("")

    # 5. Taxonomy Version Policy
    sections.append("## Taxonomy Version Policy")
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

    # 6. Taxonomy Type Allow-list
    sections.append("## Taxonomy Type Allow-list")
    sections.append("")
    sections.append(_fmt_allow_list(TAXONOMY_TYPE_ALLOW_LIST))
    sections.append("")

    # 7. Taxonomy Field Types
    sections.append("## Taxonomy Field Types")
    sections.append("")
    sections.append(_fmt_field_types(FIELD_TYPES))
    sections.append("")

    # 8. Taxonomy Validation Rules
    sections.append("## Taxonomy Validation Rules")
    sections.append("")
    sections.append("Single-record rules:")
    sections.append("- T1: `taxonomy_id` must be a non-empty string")
    sections.append("- T2: `version >= 1`")
    sections.append("- T3: `name` must be a non-empty string")
    sections.append("- T4: `description` must be a non-empty string")
    sections.append(
        "- T5: `taxonomy_type` must be in the V1 allow-list"
    )
    sections.append(
        "- T6: `root_node_ids` must be a list (may be empty)"
    )
    sections.append("")
    sections.append("Cross-record rules (require the registry context):")
    sections.append(
        "- C1: `taxonomy_id` is unique within the registry"
    )
    sections.append(
        "- C3: every Taxonomy.root_node_ids entry must refer to"
        " a registered TaxonomyNode"
    )
    sections.append("")

    # 9. Node Identity
    sections.append("## Node Identity Fields")
    sections.append("")
    sections.append(_fmt_fields(NODE_IDENTITY_FIELDS))
    sections.append("")

    # 10. Node Content
    sections.append("## Node Content Fields")
    sections.append("")
    sections.append(_fmt_fields(NODE_CONTENT_FIELDS))
    sections.append("")

    # 11. Node Hierarchy
    sections.append("## Node Hierarchy Fields")
    sections.append("")
    sections.append(_fmt_fields(NODE_HIERARCHY_FIELDS))
    sections.append("")

    # 12. Node Metadata
    sections.append("## Node Metadata Fields")
    sections.append("")
    sections.append(_fmt_fields(NODE_METADATA_FIELDS))
    sections.append("")

    # 13. Node Type Allow-list
    sections.append("## Node Type Allow-list")
    sections.append("")
    sections.append(_fmt_allow_list(NODE_TYPE_ALLOW_LIST))
    sections.append("")

    # 14. Node Field Types
    sections.append("## Node Field Types")
    sections.append("")
    sections.append(_fmt_field_types(NODE_FIELD_TYPES))
    sections.append("")

    # 15. Node Validation Rules
    sections.append("## Node Validation Rules")
    sections.append("")
    sections.append("Single-record rules:")
    sections.append("- N1: `node_id` must be a non-empty string")
    sections.append("- N2: `version >= 1`")
    sections.append("- N3: `label` must be a non-empty string")
    sections.append("- N4: `description` must be a non-empty string")
    sections.append(
        "- N5: `node_type` must be in the V1 allow-list"
    )
    sections.append(
        "- N6: `parent_node_id`, when present, must be a"
        " non-empty string and must not equal `node_id`"
    )
    sections.append("- N7: `depth >= 1`")
    sections.append(
        "- N8: `path`, when non-empty, must contain only"
        " non-empty strings"
    )
    sections.append("")
    sections.append("Cross-record rules:")
    sections.append(
        "- C2: `node_id` is unique within the registry"
    )
    sections.append("")

    # 16. Registry Snapshot
    sections.append("## Registry Snapshot")
    sections.append("")
    sections.append(_fmt_registry(registry))
    sections.append("")

    # 17. Architecture Boundary
    sections.append("## Architecture Boundary")
    sections.append("")
    sections.append(
        "- The Taxonomy package does NOT import from "
        "`caseos.intelligence.*` or `caseos.knowledge.retrieval`."
    )
    sections.append(
        "- The Taxonomy package does NOT mutate any"
        " KnowledgeObject, KnowledgeDomain, or KODomainBinding."
    )
    sections.append(
        "- The TaxonomyRegistry is append-only; the four"
        " forbidden methods raise `TypeError`."
    )
    sections.append("")

    return "\n".join(sections)


__all__ = ["generate_taxonomy_report"]
