"""Adapter Markdown Report V1 (Sprint 23.0-B, ADR-020).

The report module emits a human-readable Markdown summary of
an ``AdapterResult``. The report is **purely descriptive**;
it does not execute any further adapter logic.

Required sections (Sprint 23.0-B spec):

    # Knowledge Object Evolution Adapter Report
    ## Request
    ## Mapping Decision
    ## Output Snapshot
    ## Safety Boundary
    ## Architecture Boundary

The Safety Boundary section MUST include the literal
sentence ``Knowledge mutation: NOT EXECUTED`` so that a
human reviewer can confirm at a glance that the adapter is
candidate-only.

Architecture boundary (Sprint 23.0-B spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.evolution (sibling packages)
        * caseos.knowledge.evolution.contracts
        * caseos.knowledge.object (KO V1 schema)
        * stdlib
"""
from __future__ import annotations

from typing import Any, Optional

from .object import AdapterResult, FieldMapping


def _fmt_mapping(mapping: Optional[FieldMapping]) -> str:
    if mapping is None:
        return "_no mapping (request rejected)_"
    ct = mapping.change_type
    if hasattr(ct, "value"):
        ct_str = ct.value
    else:
        ct_str = str(ct)
    return (
        "- **change_type**: `" + ct_str + "`\n"
        + "- **requested_target_field**: `" + mapping.requested_target_field + "`\n"
        + "- **resolved_target_field**: `" + mapping.resolved_target_field + "`\n"
        + "- **applied**: `" + str(mapping.applied) + "`\n"
        + "- **note**: " + mapping.note + "\n"
    )


def _fmt_snapshot(new_snapshot: Optional[dict]) -> str:
    if new_snapshot is None:
        return "_no snapshot (request rejected)_"
    lines: list[str] = []
    lines.append("```json")
    for key in sorted(new_snapshot.keys()):
        val = new_snapshot[key]
        if isinstance(val, (list, dict)):
            rendered = repr(val)
        else:
            rendered = repr(val)
        lines.append("- " + key + ": " + rendered)
    lines.append("```")
    return "\n".join(lines)


def _fmt_rejection_reason(reason: str) -> str:
    if not reason:
        return "_none_"
    return reason


def generate_adapter_report(result: AdapterResult) -> str:
    """Return a Markdown report describing ``result``."""
    sections: list[str] = []

    # Header
    sections.append("# Knowledge Object Evolution Adapter Report")
    sections.append("")
    sections.append("**Sprint**: 23.0-B (Knowledge Object Evolution Adapter V1)")
    sections.append("**ADR**: 020 -- Knowledge Evolution Safety Principle")
    sections.append("")

    # 1. Request
    sections.append("## Request")
    sections.append("")
    sections.append("- **request_id**: `" + str(result.request_id) + "`")
    sections.append("- **transaction_id**: `" + str(result.transaction_id) + "`")
    sections.append("- **target_identity**: `" + str(result.target_identity) + "`")
    sections.append("- **before_version**: `" + str(result.before_version) + "`")
    if result.next_version is not None:
        sections.append("- **next_version**: `" + str(result.next_version) + "`")
    else:
        sections.append("- **next_version**: `_n/a (rejected)_`")
    sections.append("- **success**: `" + str(result.success) + "`")
    sections.append("")

    # 2. Mapping Decision
    sections.append("## Mapping Decision")
    sections.append("")
    sections.append(_fmt_mapping(result.mapping))
    sections.append("")

    # 3. Output Snapshot
    sections.append("## Output Snapshot")
    sections.append("")
    sections.append(_fmt_snapshot(result.new_snapshot))
    sections.append("")

    # 4. Safety Boundary
    sections.append("## Safety Boundary")
    sections.append("")
    if result.success:
        sections.append("- `mutation_executed`: `" + str(result.mutation_executed) + "`")
        sections.append("- **Knowledge mutation**: NOT EXECUTED")
        sections.append(
            "- The adapter produced a candidate snapshot only; "
            "the caller decides whether to apply it."
        )
    else:
        sections.append("- `success`: `False`")
        sections.append("- `mutation_executed`: `False`")
        sections.append("- **Knowledge mutation**: NOT EXECUTED")
        sections.append("- **Rejection reason**: " + _fmt_rejection_reason(result.rejection_reason))
    sections.append("")

    # 5. Architecture Boundary
    sections.append("## Architecture Boundary")
    sections.append("")
    sections.append(
        "- The adapter does NOT import from "
        "`caseos.intelligence.*` or `caseos.knowledge.retrieval`."
    )
    sections.append(
        "- The adapter does NOT mutate the input ``AdapterRequest`` "
        "or the input ``before_snapshot``."
    )
    sections.append(
        "- The adapter does NOT append to ``VersionStore`` or "
        "``AuditStore``."
    )
    sections.append("")

    return "\n".join(sections)


__all__ = ["generate_adapter_report"]
