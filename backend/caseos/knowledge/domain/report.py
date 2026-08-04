"""Knowledge Domain Markdown Report V1 (Sprint 23.1-A).

The report module emits a human-readable Markdown summary of
the ``KnowledgeDomain`` schema and an optional instance.

Sections (Sprint 23.1-A spec):

    # Knowledge Domain Schema Report
    ## Overview
    ## Identity Fields
    ## Scope Fields
    ## Taxonomy Fields
    ## Metadata Fields
    ## Version Policy
    ## Domain Type Allow-list
    ## Validation Rules

The report is **purely descriptive**. It does not mutate
anything and does not import from any forbidden module.

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

from typing import Any, Optional

from .object import (
    IDENTITY_FIELDS,
    KnowledgeDomain,
    METADATA_FIELDS,
    SCOPE_FIELDS,
    TAXONOMY_FIELDS,
)
from .schema import (
    DOMAIN_TYPE_ALLOW_LIST,
    DOMAIN_VERSION_POLICY,
    FIELD_TYPES,
    REQUIRED_FIELDS,
)
from .validator import KnowledgeDomainValidator


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
    return "\n".join("- `" + t + "`" for t in sorted(DOMAIN_TYPE_ALLOW_LIST))


def _fmt_instance(domain: Optional[KnowledgeDomain]) -> str:
    if domain is None:
        return "_no instance supplied_"
    d = domain.to_dict()
    rows = []
    for key in sorted(d.keys()):
        val = d[key]
        if isinstance(val, (list, tuple)):
            rendered = "[" + ", ".join(repr(x) for x in val) + "]"
        else:
            rendered = repr(val)
        rows.append("- " + key + ": " + rendered)
    return "\n".join(rows)


def generate_domain_report(
    instance: Optional[KnowledgeDomain] = None,
    *,
    validator: Optional[KnowledgeDomainValidator] = None,
) -> str:
    """Return a Markdown report describing the V1 Domain schema.

    Parameters:
        instance: optional ``KnowledgeDomain`` to include in
            the report. When supplied, the validator (or a
            fresh one) is run against the instance and the
            validation outcome is reported.
        validator: optional validator override; defaults to a
            fresh ``KnowledgeDomainValidator``.
    """
    sections: list[str] = []

    # Header
    sections.append("# Knowledge Domain Schema Report")
    sections.append("")
    sections.append("**Sprint**: 23.1-A (Knowledge Domain Schema V1)")
    sections.append(
        "**ADR**: 020 -- Knowledge Evolution Safety Principle"
    )
    sections.append("")

    # 1. Overview
    sections.append("## Overview")
    sections.append("")
    sections.append(
        "A ``KnowledgeDomain`` groups related ``KnowledgeObject``"
    )
    sections.append(
        "instances under a named scope with explicit boundary"
    )
    sections.append(
        "and principle rules. V1 is a pure data contract."
    )
    sections.append("")
    sections.append(
        "- **Required field count**: "
        + str(len(REQUIRED_FIELDS))
    )
    sections.append(
        "- **Field groups**: 4 (identity, scope, taxonomy, metadata)"
    )
    sections.append(
        "- **Domain type allow-list size**: "
        + str(len(DOMAIN_TYPE_ALLOW_LIST))
    )
    sections.append("")

    # 2. Identity Fields
    sections.append("## Identity Fields")
    sections.append("")
    sections.append(_fmt_fields(IDENTITY_FIELDS))
    sections.append("")

    # 3. Scope Fields
    sections.append("## Scope Fields")
    sections.append("")
    sections.append(_fmt_fields(SCOPE_FIELDS))
    sections.append("")

    # 4. Taxonomy Fields
    sections.append("## Taxonomy Fields")
    sections.append("")
    sections.append(_fmt_fields(TAXONOMY_FIELDS))
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
            DOMAIN_VERSION_POLICY.get("version_type"),
            "__name__",
            str(DOMAIN_VERSION_POLICY.get("version_type")),
        )
        + "`"
    )
    sections.append(
        "- **first_version**: `"
        + str(DOMAIN_VERSION_POLICY.get("first_version"))
        + "`"
    )
    sections.append(
        "- **min_version**: `"
        + str(DOMAIN_VERSION_POLICY.get("min_version"))
        + "`"
    )
    sections.append(
        "- **default_version**: `"
        + str(DOMAIN_VERSION_POLICY.get("default_version"))
        + "`"
    )
    sections.append("")

    # 7. Domain Type Allow-list
    sections.append("## Domain Type Allow-list")
    sections.append("")
    sections.append(_fmt_allow_list())
    sections.append("")

    # 8. Field Types
    sections.append("## Field Types")
    sections.append("")
    sections.append(_fmt_field_types())
    sections.append("")

    # 9. Validation Rules
    sections.append("## Validation Rules")
    sections.append("")
    sections.append("- Identity: `domain_id` must be a non-empty string")
    sections.append("- Version: `version >= 1` (V1 first_version)")
    sections.append(
        "- Required Fields: every REQUIRED_FIELDS entry must be present"
    )
    sections.append(
        "- Domain Type: `domain_type` must be in the V1 allow-list"
    )
    sections.append(
        "- Type Safety: each field must satisfy its FIELD_TYPES entry"
    )
    sections.append(
        "- JSON Safety: collection fields must contain JSON-safe values"
    )
    sections.append(
        "- Hierarchy: `parent_domain_id`, when present, must be a "
        "non-empty string and must not equal `domain_id`"
    )
    sections.append("")

    # 10. Instance (optional)
    sections.append("## Instance")
    sections.append("")
    sections.append(_fmt_instance(instance))
    if instance is not None:
        v = validator or KnowledgeDomainValidator()
        result = v.validate(instance)
        sections.append("")
        sections.append("### Validation Result")
        sections.append("")
        sections.append("- **valid**: `" + str(result.valid) + "`")
        if not result.valid:
            for err in result.errors:
                sections.append("- error: " + err)
        sections.append("")

    # 11. Architecture Boundary
    sections.append("## Architecture Boundary")
    sections.append("")
    sections.append(
        "- The Domain package does NOT import from "
        "`caseos.intelligence.*` or `caseos.knowledge.retrieval`."
    )
    sections.append(
        "- The Domain package does NOT mutate any "
        "`KnowledgeObject` instance."
    )
    sections.append(
        "- The Domain package does NOT consume the Evolution "
        "pipeline; it is a pure data contract."
    )
    sections.append("")

    return "\n".join(sections)


__all__ = ["generate_domain_report"]
