"""Evolution Integration Verification Report V1 (Sprint 22.4-C, ADR-020).

Renders a Markdown summary of an ``EvolutionExecutionResult``
plus its source transaction and the audit records produced.

Required sections (Sprint 22.4-C spec Task 3):

    # Evolution Integration Verification Report
    ## Transaction
    ## Governance Result
    ## Audit Status
    ## Knowledge Mutation
    ## Safety Boundary

The ``## Knowledge Mutation`` section has a **fixed output**:

    NOT EXECUTED

This is the single most important line in the report. It is
the explicit "V1 hard-stop" marker that a future Sprint 22.4.x
mutation runtime will replace with a structured "EXECUTED at
version N" block.

Architecture boundary (Sprint 22.4-C spec Task 4):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, Iterable, List, Optional

from ..audit import EvolutionAuditRecord
from ..object import EvolutionTransaction
from .runtime import EvolutionExecutionResult


def _safe(value: Any, fallback: str = "(none)") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def _render_audit_records(
    records: Iterable[EvolutionAuditRecord],
) -> List[str]:
    records = list(records)
    if not records:
        return ["(no audit records)"]
    lines: List[str] = []
    for r in records:
        lines.append(
            "- `" + r.audit_id + "`"
            + " action=`" + r.action + "`"
            + " actor=`" + r.actor + "`"
            + " reason=\"" + r.reason + "\""
        )
    return lines


def generate_report(
    execution_result: EvolutionExecutionResult,
    *,
    transaction: Optional[EvolutionTransaction] = None,
    audit_records: Optional[Iterable[EvolutionAuditRecord]] = None,
    title: str = "Evolution Integration Verification Report",
) -> str:
    """Render a Markdown report of one ``EvolutionExecutionResult``.

    Args:
        execution_result: the result to render.
        transaction: optional source transaction. When provided,
            the ``## Transaction`` section is populated with
            its fields; otherwise a stub is rendered.
        audit_records: optional iterable of audit records. When
            ``None``, the ``## Audit Status`` section reports
            "(no audit records)" regardless of the
            ``audit_created`` boolean.
        title: optional report title override.
    """
    lines: List[str] = []
    lines.append("# " + title)
    lines.append("")

    # ---- ## Transaction -----------------------------------------------
    lines.append("## Transaction")
    lines.append("")
    if transaction is None:
        lines.append("- transaction_id: `" + _safe(
            execution_result.transaction_id,
        ) + "`")
    else:
        lines.append("- transaction_id: `" + _safe(transaction.transaction_id) + "`")
        lines.append("- proposal_id: `" + _safe(transaction.proposal_id) + "`")
        lines.append("- change_intent_id: `" + _safe(transaction.change_intent_id) + "`")
        lines.append("- target_identity: `" + _safe(transaction.target_identity) + "`")
        lines.append("- target_version: `" + str(transaction.target_version) + "`")
        lines.append("- change_type: `" + _safe(transaction.change_type) + "`")
        lines.append("- reviewer: `" + _safe(transaction.reviewer) + "`")
        lines.append("- status: `" + _safe(transaction.status) + "`")
    lines.append("")

    # ---- ## Governance Result ----------------------------------------
    lines.append("## Governance Result")
    lines.append("")
    gov = execution_result.governance_result
    if gov.approved:
        lines.append("- verdict: **APPROVED**")
        lines.append("- rule_id: (all rules passed)")
    else:
        lines.append("- verdict: **REJECTED**")
        lines.append("- rule_id: `" + _safe(gov.rule_id, "?") + "`")
        lines.append("- reason: " + _safe(gov.reason, "(none)"))
    lines.append("")

    # ---- ## Audit Status ---------------------------------------------
    lines.append("## Audit Status")
    lines.append("")
    lines.append("- audit_created: **" + str(execution_result.audit_created) + "**")
    if audit_records is not None:
        lines.append("")
        lines.extend(_render_audit_records(audit_records))
    lines.append("")

    # ---- ## Knowledge Mutation ---------------------------------------
    lines.append("## Knowledge Mutation")
    lines.append("")
    lines.append("```")
    lines.append("NOT EXECUTED")
    lines.append("```")
    lines.append("")
    lines.append(
        "  The V1 integration runtime records the transaction, validates"
    )
    lines.append(
        "  it, runs the governance gate, and writes the audit record."
    )
    lines.append(
        "  It does NOT modify the Knowledge Object, the corpus, the"
    )
    lines.append(
        "  retrieval ranking, the decision engine, the trust engine,"
    )
    lines.append(
        "  or the recommendation engine. The future Knowledge Object"
    )
    lines.append(
        "  mutation runtime is gated on ADR-020 Rules 1-5 and on a"
    )
    lines.append(
        "  concrete Sprint 22.4.x implementation. See ADR-018 Sections"
    )
    lines.append(
        "  14-17 and ADR-020 Section 3 for the contract."
    )
    lines.append("")

    # ---- ## Safety Boundary ------------------------------------------
    lines.append("## Safety Boundary")
    lines.append("")
    lines.append("- mutation_executed: `" + str(execution_result.mutation_executed) + "`")
    lines.append("- audit_created: `" + str(execution_result.audit_created) + "`")
    lines.append("- success: `" + str(execution_result.success) + "`")
    lines.append("")
    lines.append(
        "  The runtime is forbidden from changing the Knowledge Object,"
    )
    lines.append(
        "  increasing the KO version, or changing any Decision. The"
    )
    lines.append(
        "  only allowed side effect in V1 is the append-only audit"
    )
    lines.append(
        "  record. The future mutation runtime is a separate concern"
    )
    lines.append(
        "  gated on a new ADR and on ADR-020 Rules 1-5."
    )
    lines.append("")

    return "\n".join(lines)


__all__ = ["generate_report"]
