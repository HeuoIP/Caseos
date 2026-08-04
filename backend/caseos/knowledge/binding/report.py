"""Binding Markdown Report V1 (Sprint 23.1-B).

The report module emits a human-readable Markdown summary
of the ``KODomainBinding`` schema and an optional registry
snapshot.

Sections (Sprint 23.1-B spec):

    # KODomainBinding Schema Report
    ## Overview
    ## Identity Fields
    ## Reference Fields
    ## Metadata Fields
    ## Version Policy
    ## Binding Type Allow-list
    ## Validation Rules
    ## Registry Snapshot
    ## Architecture Boundary

The report is **purely descriptive**.

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

from typing import Any, Optional

from .object import (
    IDENTITY_FIELDS,
    KODomainBinding,
    METADATA_FIELDS,
    REFERENCE_FIELDS,
)
from .registry import BindingRegistry
from .schema import (
    BINDING_TYPE_ALLOW_LIST,
    BINDING_VERSION_POLICY,
    FIELD_TYPES,
    REQUIRED_FIELDS,
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


def _fmt_allow_list() -> str:
    return "\n".join("- `" + t + "`" for t in sorted(BINDING_TYPE_ALLOW_LIST))


def _fmt_registry(registry: Optional[BindingRegistry]) -> str:
    if registry is None:
        return "_no registry supplied_"
    if registry.count() == 0:
        return "_registry is empty_"
    rows = []
    rows.append(
        "- **total bindings**: " + str(registry.count())
    )
    rows.append(
        "- **distinct knowledge objects**: "
        + str(len(registry.knowledge_object_ids()))
    )
    rows.append(
        "- **distinct domains**: " + str(len(registry.domain_ids()))
    )
    rows.append("")
    rows.append("| binding_id | KO id | KO version | domain_id | type | priority |")
    rows.append("|---|---|---|---|---|---|")
    for b in registry.list():
        rows.append(
            "| "
            + b.binding_id
            + " | "
            + b.knowledge_object_id
            + " | "
            + str(b.knowledge_object_version)
            + " | "
            + b.domain_id
            + " | "
            + b.binding_type
            + " | "
            + str(b.priority)
            + " |"
        )
    return "\n".join(rows)


def generate_binding_report(
    registry: Optional[BindingRegistry] = None,
) -> str:
    """Return a Markdown report describing the V1 Binding schema
    and the optional ``registry`` snapshot.
    """
    sections: list[str] = []

    # Header
    sections.append("# KODomainBinding Schema Report")
    sections.append("")
    sections.append("**Sprint**: 23.1-B (Knowledge Object Domain Binding V1)")
    sections.append(
        "**ADR**: 018 (Feedback Learning Loop) / 020 (Knowledge Evolution)"
    )
    sections.append("")

    # 1. Overview
    sections.append("## Overview")
    sections.append("")
    sections.append(
        "A ``KODomainBinding`` declares that a specific"
        " ``KnowledgeObject`` belongs to a specific"
        " ``KnowledgeDomain``."
    )
    sections.append("")
    sections.append(
        "The binding NEVER mutates a Knowledge Object. It NEVER"
        " mutates a Knowledge Domain. It is a pure relationship"
        " record; future Retrieval / Evolution sprints may"
        " consume it."
    )
    sections.append("")
    sections.append(
        "- **Required field count**: " + str(len(REQUIRED_FIELDS))
    )
    sections.append(
        "- **Field groups**: 3 (identity, reference, metadata)"
    )
    sections.append(
        "- **Binding type allow-list size**: "
        + str(len(BINDING_TYPE_ALLOW_LIST))
    )
    sections.append("")

    # 2. Identity Fields
    sections.append("## Identity Fields")
    sections.append("")
    sections.append(_fmt_fields(IDENTITY_FIELDS))
    sections.append("")

    # 3. Reference Fields
    sections.append("## Reference Fields")
    sections.append("")
    sections.append(_fmt_fields(REFERENCE_FIELDS))
    sections.append("")

    # 4. Metadata Fields
    sections.append("## Metadata Fields")
    sections.append("")
    sections.append(_fmt_fields(METADATA_FIELDS))
    sections.append("")

    # 5. Version Policy
    sections.append("## Version Policy")
    sections.append("")
    sections.append(
        "- **version_type**: `"
        + getattr(
            BINDING_VERSION_POLICY.get("version_type"),
            "__name__",
            str(BINDING_VERSION_POLICY.get("version_type")),
        )
        + "`"
    )
    sections.append(
        "- **first_version**: `"
        + str(BINDING_VERSION_POLICY.get("first_version"))
        + "`"
    )
    sections.append(
        "- **min_version**: `"
        + str(BINDING_VERSION_POLICY.get("min_version"))
        + "`"
    )
    sections.append(
        "- **default_version**: `"
        + str(BINDING_VERSION_POLICY.get("default_version"))
        + "`"
    )
    sections.append("")

    # 6. Binding Type Allow-list
    sections.append("## Binding Type Allow-list")
    sections.append("")
    sections.append(_fmt_allow_list())
    sections.append("")

    # 7. Field Types
    sections.append("## Field Types")
    sections.append("")
    sections.append(_fmt_field_types())
    sections.append("")

    # 8. Validation Rules
    sections.append("## Validation Rules")
    sections.append("")
    sections.append("Single-record rules:")
    sections.append("- B1: `binding_id` must be a non-empty string")
    sections.append("- B2: `version >= 1`")
    sections.append("- B3: `knowledge_object_id` must be a non-empty string")
    sections.append("- B4: `knowledge_object_version >= 1`")
    sections.append("- B5: `domain_id` must be a non-empty string")
    sections.append(
        "- B6: `binding_type` must be in the V1 allow-list"
    )
    sections.append("- B7: `priority >= 1`")
    sections.append(
        "- B8: `membership_reason` must be a non-empty string"
    )
    sections.append("")
    sections.append("Cross-record rules (require the registry context):")
    sections.append(
        "- C1: `binding_id` is unique within the registry"
    )
    sections.append(
        "- C2: at most one `primary` binding per"
        " `knowledge_object_id` exists in the registry"
    )
    sections.append("")

    # 9. Registry Snapshot
    sections.append("## Registry Snapshot")
    sections.append("")
    sections.append(_fmt_registry(registry))
    sections.append("")

    # 10. Architecture Boundary
    sections.append("## Architecture Boundary")
    sections.append("")
    sections.append(
        "- The Binding package does NOT import from "
        "`caseos.intelligence.*` or `caseos.knowledge.retrieval`."
    )
    sections.append(
        "- The Binding package does NOT mutate any "
        "`KnowledgeObject` or `KnowledgeDomain` instance."
    )
    sections.append(
        "- The Binding package does NOT consume the Evolution"
        " pipeline; it is a pure relationship record."
    )
    sections.append(
        "- The BindingRegistry is append-only; the four"
        " forbidden methods (`update` / `delete` /"
        " `overwrite` / `clear`) raise `TypeError`."
    )
    sections.append("")

    return "\n".join(sections)


__all__ = ["generate_binding_report"]
