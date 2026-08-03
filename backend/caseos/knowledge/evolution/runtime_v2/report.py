"""Evolution Runtime V2 Report (Sprint 22.4-F, ADR-020).

Renders a Markdown summary of an ``EvolutionExecutionResult``
plus the version and audit records produced by the
``EvolutionExecutor``.

Required sections (Sprint 22.4-F spec Task 5):

    # Evolution Runtime V2 Report
    ## Transaction
    ## Governance
    ## Version
    ## Audit
    ## Knowledge Mutation

The ``## Knowledge Mutation`` section has a **fixed
output**:

    NOT IMPECUTED

This is the single most important line in the report. It
is the explicit "V1 simulation only" marker that a future
Sprint 22.4.x mutation runtime will replace with a
structured "EXECUTED at version N" block.

Architecture boundary (Sprint 22.4-F spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, Iterable, List, Optional

from ..audit_v2 import EvolutionAuditRecord
from ..object import EvolutionTransaction
from ..versioning import KnowledgeVersion
from .executor import EvolutionExecutionResult


def _safe(value: Any, fallback: str = "(none)") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def _render_versions(
    versions: Iterable[KnowledgeVersion],
) -> List[str]:
    versions = list(versions)
    if not versions:
        return ["(no versions produced)"]
    lines: List[str] = []
    for v in versions:
        lines.append("- v" + str(v.version_number)
                     + " `" + v.version_id + "`")
        lines.append("  - previous_version: `"
                     + _safe(v.previous_version, "(initial)") + "`")
        lines.append("  - created_by: `" + _safe(v.created_by) + "`")
        lines.append("  - change_reason: " + _safe(v.change_reason))
    return lines


def _render_audits(
    records: Iterable[EvolutionAuditRecord],
) -> List[str]:
    records = list(records)
    if not records:
        return ["(no audit records produced)"]
    lines: List[str] = []
    for r in records:
        lines.append("- audit `" + r.audit_id + "`")
        lines.append("  - transaction_id: `"
                     + _safe(r.transaction_id) + "`")
        lines.append("  - proposal_id: `" + _safe(r.proposal_id) + "`")
        lines.append("  - target_identity: `"
                     + _safe(r.target_identity) + "`")
        lines.append("  - previous_version: `"
                     + _safe(r.previous_version, "(initial)") + "`")
        lines.append("  - new_version: `" + str(r.new_version) + "`")
        lines.append("  - change_type: `" + _safe(r.change_type) + "`")
        lines.append("  - reviewer: `" + _safe(r.reviewer) + "`")
        lines.append("  - after_snapshot: "
                     + _safe(r.after_snapshot,
                             "(not yet computed in V1)"))
        lines.append("  - rollback_reference: `"
                     + _safe(r.rollback_reference) + "`")
    return lines


def generate_report(
    execution_result: EvolutionExecutionResult,
    *,
    transaction: Optional[EvolutionTransaction] = None,
    versions: Optional[Iterable[KnowledgeVersion]] = None,
    audits: Optional[Iterable[EvolutionAuditRecord]] = None,
    title: str = "Evolution Runtime V2 Report",
) -> str:
    """Render a Markdown report of one ``EvolutionExecutionResult``.

    Args:
        execution_result: the result to render.
        transaction: optional source transaction. When
            provided, the ``## Transaction`` section is
            populated with its fields.
        versions: optional iterable of KnowledgeVersion
            records produced by the executor.
        audits: optional iterable of EvolutionAuditRecord
            (V2) records produced by the executor.
        title: optional report title override.
    """
    lines: List[str] = []
    lines.append("# " + title)
    lines.append("")

    # ---- ## Transaction --------------------------------------------
    lines.append("## Transaction")
    lines.append("")
    if transaction is None:
        lines.append("- transaction_id: `" + _safe(
            execution_result.transaction_id,
        ) + "`")
    else:
        lines.append("- transaction_id: `" + _safe(transaction.transaction_id) + "`")
        lines.append("- proposal_id: `" + _safe(transaction.proposal_id) + "`")
        lines.append("- target_identity: `" + _safe(transaction.target_identity) + "`")
        lines.append("- change_type: `" + _safe(transaction.change_type) + "`")
        lines.append("- reviewer: `" + _safe(transaction.reviewer) + "`")
        lines.append("- status: `" + _safe(transaction.status) + "`")
    lines.append("")

    # ---- ## Governance --------------------------------------------
    lines.append("## Governance")
    lines.append("")
    lines.append("- governance_passed: **" + str(execution_result.governance_passed) + "**")
    lines.append("")

    # ---- ## Version -----------------------------------------------
    lines.append("## Version")
    lines.append("")
    lines.append("- version_created: **" + str(execution_result.version_created) + "**")
    lines.append("")
    if versions is not None:
        lines.extend(_render_versions(versions))
    lines.append("")

    # ---- ## Audit --------------------------------------------------
    lines.append("## Audit")
    lines.append("")
    lines.append("- audit_created: **" + str(execution_result.audit_created) + "**")
    lines.append("")
    if audits is not None:
        lines.extend(_render_audits(audits))
    lines.append("")

    # ---- ## Knowledge Mutation ------------------------------------
    lines.append("## Knowledge Mutation")
    lines.append("")
    lines.append("```")
    lines.append("NOT IMPLEMENTED")
    lines.append("```")
    lines.append("")
    lines.append("  The V1 simulation runtime records the")
    lines.append("  transaction, validates it, runs the governance")
    lines.append("  gate, appends a KnowledgeVersion to the version")
    lines.append("  store, and appends an EvolutionAuditRecord to")
    lines.append("  the audit store. It does NOT modify the")
    lines.append("  Knowledge Object, the corpus, the retrieval")
    lines.append("  ranking, the decision engine, the trust engine,")
    lines.append("  or the recommendation engine. The future")
    lines.append("  Knowledge Object mutation runtime is gated on")
    lines.append("  ADR-020 Rules 1-5 and on a concrete Sprint")
    lines.append("  22.4.x implementation.")
    lines.append("")
    lines.append("- Evolution Simulation: **IMPLEMENTED**")
    lines.append("- Knowledge Mutation: **NOT IMPLEMENTED**")
    lines.append("")

    return "\n".join(lines)


__all__ = ["generate_report"]
