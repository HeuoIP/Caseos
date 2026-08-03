"""Evolution Transaction Report V1 (Sprint 22.4-A, ADR-020).

Renders a Markdown summary of one ``EvolutionTransaction`` plus
its validation result and audit history.

Required sections (Sprint 22.4-A spec Task 5):

    # Evolution Transaction Report
    ## Transaction Summary
    ## Validation Result
    ## Audit History
    ## Evolution Status
    ## Safety Boundary

The Safety Boundary section must explicitly state:

    Knowledge mutation:
    NOT EXECUTED

This is the single most important line in the report. It is the
explicit "V1 hard-stop" marker that a future Sprint 22.4.x
mutation runtime will replace with "EXECUTED at version N".

Architecture boundary (Sprint 22.4-A spec Task 6):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.objects
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * stdlib
"""
from __future__ import annotations

from typing import Any, Iterable, List, Optional

from .audit import EvolutionAuditRecord
from .object import EvolutionStatus, EvolutionTransaction
from .validator import ValidationResult


def _safe(value: Any, fallback: str = "(none)") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def _render_snapshot(snapshot: Any) -> List[str]:
    if not isinstance(snapshot, dict):
        return [str(snapshot) if snapshot is not None else "(none)"]
    if not snapshot:
        return ["(empty)"]
    lines: List[str] = []
    for k in sorted(snapshot.keys()):
        v = snapshot[k]
        lines.append("- " + str(k) + ": `" + _safe(v) + "`")
    return lines


def _render_audit_history(
    records: Iterable[EvolutionAuditRecord],
) -> List[str]:
    records = list(records)
    if not records:
        return ["(no audit records)"]
    lines: List[str] = []
    for r in records:
        lines.append(
            "- `" + r.audit_id + "` action=`"
            + r.action + "` actor=`" + r.actor
            + "` reason=\"" + r.reason + "\""
        )
    return lines


def generate_report(
    transaction: EvolutionTransaction,
    *,
    validation: Optional[ValidationResult] = None,
    audit_records: Optional[Iterable[EvolutionAuditRecord]] = None,
    title: str = "Evolution Transaction Report",
) -> str:
    """Render a Markdown report of one EvolutionTransaction.

    Args:
        transaction: the EvolutionTransaction to render.
        validation: optional ValidationResult. When None, the
            report does not state a validation verdict.
        audit_records: optional iterable of EvolutionAuditRecord.
            When None, the report shows "(no audit records)".
        title: optional report title override.
    """
    lines: List[str] = []
    lines.append("# " + title)
    lines.append("")

    # ----- Transaction Summary -------------------------------------
    lines.append("## Transaction Summary")
    lines.append("")
    lines.append("- transaction_id: `" + _safe(transaction.transaction_id) + "`")
    lines.append("- proposal_id: `" + _safe(transaction.proposal_id) + "`")
    lines.append("- change_intent_id: `" + _safe(transaction.change_intent_id) + "`")
    lines.append("- target_identity: `" + _safe(transaction.target_identity) + "`")
    lines.append("- target_version: `" + str(transaction.target_version) + "`")
    lines.append("- change_type: `" + _safe(transaction.change_type) + "`")
    lines.append("- reviewer: `" + _safe(transaction.reviewer) + "`")
    lines.append("- status: `" + _safe(transaction.status) + "`")
    lines.append("- created_at: `" + _safe(transaction.created_at) + "`")
    lines.append("")
    lines.append("### before_snapshot")
    lines.append("")
    lines.extend(_render_snapshot(transaction.before_snapshot))
    lines.append("")

    if transaction.requested_change:
        lines.append("### requested_change")
        lines.append("")
        lines.append(transaction.requested_change)
        lines.append("")

    # ----- Validation Result ----------------------------------------
    lines.append("## Validation Result")
    lines.append("")
    if validation is None:
        lines.append("(not validated in this report)")
    else:
        if validation.is_valid:
            lines.append("- verdict: **VALID**")
            lines.append("- rule: (all rules passed)")
            lines.append("- reason: " + _safe(validation.reason, "(none)"))
        else:
            lines.append("- verdict: **REJECTED**")
            lines.append("- rule: `" + _safe(validation.rule, "?") + "`")
            lines.append("- reason: " + _safe(validation.reason, "(none)"))
    lines.append("")

    # ----- Audit History --------------------------------------------
    lines.append("## Audit History")
    lines.append("")
    if audit_records is None:
        lines.append("(no audit records)")
    else:
        lines.extend(_render_audit_history(audit_records))
    lines.append("")

    # ----- Evolution Status -----------------------------------------
    lines.append("## Evolution Status")
    lines.append("")
    lines.append("- current_status: `" + _safe(transaction.status) + "`")
    if transaction.status == EvolutionStatus.APPROVED:
        lines.append("- next_step: **V1 HARD-STOP**")
        lines.append(
            "- note: APPROVED is the V1 terminal state; the APPLIED"
        )
        lines.append(
            "  transition is gated on a future Sprint 22.4.x"
        )
        lines.append(
            "  Knowledge Object mutation runtime (ADR-020)."
        )
    elif transaction.status == EvolutionStatus.REJECTED:
        lines.append("- next_step: terminal (rejected)")
    elif transaction.status == EvolutionStatus.VALIDATING:
        lines.append("- next_step: APPROVED or REJECTED")
    else:
        lines.append("- next_step: VALIDATING")
    lines.append("")

    # ----- Safety Boundary ------------------------------------------
    lines.append("## Safety Boundary")
    lines.append("")
    lines.append("- **Knowledge mutation: NOT EXECUTED**")
    lines.append("")
    lines.append(
        "  The V1 evolution layer records the transaction, validates"
    )
    lines.append(
        "  it, and writes the audit history. It does NOT modify the"
    )
    lines.append(
        "  Knowledge Object, the corpus, the retrieval ranking, the"
    )
    lines.append(
        "  decision engine, the trust engine, or the recommendation"
    )
    lines.append(
        "  engine. The future Knowledge Object mutation runtime is"
    )
    lines.append(
        "  gated on ADR-020 Rules 1-5 and on a concrete Sprint 22.4.x"
    )
    lines.append(
        "  implementation. See ADR-018 Sections 14-17 and ADR-020"
    )
    lines.append(
        "  Section 3 for the contract."
    )
    lines.append("")

    return "\n".join(lines)


__all__ = ["generate_report"]
