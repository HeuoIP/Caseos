"""Knowledge Object Schema Report V1 (Sprint 23.0-A).

Generates the operator-facing Markdown report that
describes the ``KnowledgeObject`` schema, version policy,
and validation rules.

Sections (Sprint 23.0-A spec Task 7):

    # Knowledge Object Schema Report
    ## Identity
    ## Context
    ## Design Attributes
    ## Assets
    ## Version Policy
    ## Validation Rules

The report consumes the schema constants from
``schema.py`` rather than the dataclass itself so that
schema changes (add/remove fields, change types) show
up automatically without editing this file.

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

from typing import Any, Iterable, Optional

from .object import (
    ASSET_FIELDS,
    CASE_CONTEXT_FIELDS,
    CONTENT_FIELDS,
    DESIGN_ATTRIBUTE_FIELDS,
    IDENTITY_FIELDS,
    METADATA_FIELDS,
)
from .schema import FIELD_TYPES, REQUIRED_FIELDS, VERSION_POLICY


def _format_field(name: str) -> str:
    """Render a field entry ``- name: type``."""
    types = FIELD_TYPES.get(name, (object,))
    type_names = ", ".join(t.__name__ for t in types)
    return "- `" + name + "`: `" + type_names + "`"


def _format_field_group(
    title: str,
    fields: Iterable[str],
    extra_note: Optional[str] = None,
) -> list[str]:
    lines: list[str] = ["### " + title, ""]
    if extra_note:
        lines.append(extra_note)
        lines.append("")
    for fname in fields:
        lines.append(_format_field(fname))
    lines.append("")
    return lines


def generate_schema_report() -> str:
    """Return the Markdown schema report (string)."""
    lines: list[str] = []
    lines.append("# Knowledge Object Schema Report")
    lines.append("")

    # ---- Identity --------------------------------------------------
    lines.append("## Identity")
    lines.append("")
    lines.extend(_format_field_group(
        "Identity Fields",
        IDENTITY_FIELDS,
        extra_note=(
            "`knowledge_id` is the stable anchor; "
            "`version` is the integer version starting at 1."
        ),
    ))

    # ---- Content --------------------------------------------------
    lines.append("## Content")
    lines.append("")
    lines.extend(_format_field_group(
        "Content Fields",
        CONTENT_FIELDS,
    ))

    # ---- Context --------------------------------------------------
    lines.append("## Context")
    lines.append("")
    lines.extend(_format_field_group(
        "Case Context Fields",
        CASE_CONTEXT_FIELDS,
        extra_note="All four fields are required strings.",
    ))

    # ---- Design Attributes ----------------------------------------
    lines.append("## Design Attributes")
    lines.append("")
    lines.extend(_format_field_group(
        "Design Attribute Fields",
        DESIGN_ATTRIBUTE_FIELDS,
        extra_note=(
            "`function_tags` is a JSON-safe list of strings; the "
            "other four fields are strings."
        ),
    ))

    # ---- Assets ---------------------------------------------------
    lines.append("## Assets")
    lines.append("")
    lines.extend(_format_field_group(
        "Asset Fields",
        ASSET_FIELDS,
        extra_note=(
            "`image_refs` and `document_refs` are JSON-safe lists "
            "of strings (URI / path references)."
        ),
    ))

    # ---- Metadata -------------------------------------------------
    lines.append("## Metadata")
    lines.append("")
    lines.extend(_format_field_group(
        "Metadata Fields",
        METADATA_FIELDS,
        extra_note=(
            "`created_at` and `updated_at` are ISO-8601 strings; "
            "`source` is a free-text tag."
        ),
    ))

    # ---- Version Policy -------------------------------------------
    lines.append("## Version Policy")
    lines.append("")
    lines.append(
        "- version_type: `"
        + str(VERSION_POLICY.get("version_type", int).__name__)
        + "`"
    )
    lines.append(
        "- first_version: "
        + str(VERSION_POLICY.get("first_version", 1))
    )
    lines.append(
        "- min_version: "
        + str(VERSION_POLICY.get("min_version", 1))
    )
    lines.append(
        "- default_version: "
        + str(VERSION_POLICY.get("default_version", 1))
    )
    lines.append("")

    # ---- Validation Rules -----------------------------------------
    lines.append("## Validation Rules")
    lines.append("")
    lines.append(
        "The validator enforces the following checks; "
        "every rule must pass for the result to be `valid`."
    )
    lines.append("")
    lines.append(
        "- **Identity**: `knowledge_id` must be a non-empty string."
    )
    lines.append(
        "- **Version**: `version` must be a positive integer "
        "(>= " + str(VERSION_POLICY.get("min_version", 1)) + ")."
    )
    lines.append(
        "- **Required Fields**: every entry in "
        "`REQUIRED_FIELDS` must be present on the object."
    )
    lines.append(
        "- **Type Safety**: each field must satisfy "
        "`FIELD_TYPES`."
    )
    lines.append(
        "- **JSON Safety**: collection fields "
        "(`function_tags`, `image_refs`, `document_refs`) "
        "must contain only JSON-safe scalars."
    )
    lines.append(
        "- **Frozen**: the dataclass is `@dataclass(frozen=True)`; "
        "runtime mutation raises `FrozenInstanceError`."
    )
    lines.append("")
    lines.append(
        "Total required fields: "
        + str(len(REQUIRED_FIELDS))
    )
    lines.append("")
    return "\n".join(lines)


__all__ = ["generate_schema_report"]
