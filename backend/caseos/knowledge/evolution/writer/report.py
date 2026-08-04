"""Writer Markdown Report V1 (Sprint 23.0-C, ADR-020).

The report module emits a human-readable Markdown summary of
a ``WriteResult``. The report is **purely descriptive**;
it does not execute any further writer logic.

Required sections (Sprint 23.0-C spec):

    # Knowledge Object Evolution Writer Report
    ## Write Request
    ## Store Appends
    ## Audit Record
    ## Mutation Status
    ## Safety Boundary

The Safety Boundary section MUST include:

    * ``VersionStore.append called: True/False``
    * ``AuditStore.append called: True/False``
    * ``Knowledge mutation: APPENDED to VersionStore + AuditStore``
      on success
    * ``Knowledge mutation: NOT EXECUTED`` on rejection

Architecture boundary (Sprint 23.0-C spec):

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

from .object import WriteResult


def _fmt_bool(flag: bool, *, yes: str, no: str) -> str:
    return yes if flag else no


def generate_writer_report(result: WriteResult) -> str:
    """Return a Markdown report describing ``result``."""
    sections: list[str] = []

    # Header
    sections.append("# Knowledge Object Evolution Writer Report")
    sections.append("")
    sections.append("**Sprint**: 23.0-C (Knowledge Object Evolution Writer V1)")
    sections.append("**ADR**: 020 -- Knowledge Evolution Safety Principle")
    sections.append("")

    # 1. Write Request
    sections.append("## Write Request")
    sections.append("")
    sections.append("- **write_id**: `" + str(result.write_id) + "`")
    sections.append("- **transaction_id**: `" + str(result.transaction_id) + "`")
    sections.append("- **target_identity**: `" + str(result.target_identity) + "`")
    sections.append("- **before_version**: `" + str(result.before_version) + "`")
    if result.new_version is not None:
        sections.append("- **new_version**: `" + str(result.new_version) + "`")
    else:
        sections.append("- **new_version**: `_n/a (rejected)_`")
    sections.append("")

    # 2. Store Appends
    sections.append("## Store Appends")
    sections.append("")
    sections.append(
        "- **VersionStore.append called**: "
        + _fmt_bool(
            result.version_appended,
            yes="`True`",
            no="`False`",
        )
    )
    sections.append(
        "- **AuditStore.append called**: "
        + _fmt_bool(
            result.audit_appended,
            yes="`True`",
            no="`False`",
        )
    )
    if result.version_id is not None:
        sections.append("- **version_id**: `" + str(result.version_id) + "`")
    if result.audit_id is not None:
        sections.append("- **audit_id**: `" + str(result.audit_id) + "`")
    sections.append("")

    # 3. Audit Record
    sections.append("## Audit Record")
    sections.append("")
    if result.audit_appended:
        sections.append(
            "- The writer appended an ``EvolutionAuditRecord`` "
            "to the ``AuditStore``. The record carries "
            "``before_snapshot`` and ``after_snapshot`` so a "
            "future Sprint 22.4.x rollback module can "
            "reconstruct the before/after state."
        )
    else:
        sections.append("- No audit record was appended (write rejected).")
    sections.append("")

    # 4. Mutation Status
    sections.append("## Mutation Status")
    sections.append("")
    sections.append(
        "- **mutation_executed**: `"
        + str(result.mutation_executed)
        + "`"
    )
    if result.success:
        sections.append("- The writer is the first layer in the Evolution")
        sections.append("  pipeline where ``mutation_executed=True`` is")
        sections.append("  meaningful. Prior layers (Adapter, Interpretation,")
        sections.append("  Proposal, Review) are candidate-only.")
    else:
        sections.append("- **rejection_reason**: " + str(result.rejection_reason))
    sections.append("")

    # 5. Safety Boundary
    sections.append("## Safety Boundary")
    sections.append("")
    sections.append(
        "- The writer does NOT mutate any existing KnowledgeVersion."
    )
    sections.append(
        "- The writer does NOT overwrite VersionStore or AuditStore."
    )
    sections.append(
        "- The writer does NOT touch any intelligence module or Retrieval."
    )
    sections.append(
        "- The writer does NOT touch an in-place Knowledge Object."
    )
    sections.append("")
    if result.success:
        sections.append(
            "- **Knowledge mutation**: APPENDED to VersionStore + AuditStore"
        )
    else:
        sections.append(
            "- **Knowledge mutation**: NOT EXECUTED"
        )
    sections.append("")

    return "\n".join(sections)


__all__ = ["generate_writer_report"]
