"""Feedback Evolution Runtime Report V1 (Sprint 22.5-A, ADR-018/020).

Generates a Markdown report from a ``FeedbackEvolutionResult``.
The report is the operator-facing surface for the runtime: it
shows each pipeline stage, what was produced, and (when the
human gate did not open) a clear "WAITING / NOT EXECUTED"
posture.

Architecture boundary (Sprint 22.5-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.feedback
        * caseos.knowledge.evolution
        * stdlib
"""
from __future__ import annotations

from typing import Any

from .object import (
    EVOLUTION_STATUS_APPROVED_AND_EXECUTED,
    EVOLUTION_STATUS_APPROVED_BUT_BLOCKED,
    EVOLUTION_STATUS_REJECTED,
    EVOLUTION_STATUS_WAITING_HUMAN_REVIEW,
    FeedbackEvolutionResult,
)


def _safe(value: Any) -> str:
    """Render ``value`` as a Markdown-safe inline string."""
    if value is None:
        return "None"
    return str(value).replace("`", "\u02cb")


def generate_report(result: FeedbackEvolutionResult) -> str:
    """Build the Markdown report for a single runtime execution.

    The sections follow the spec's required structure:

        # Feedback Evolution Runtime Report
        ## Feedback
        ## Proposal
        ## Human Review
        ## ChangeIntent
        ## Evolution Transaction
        ## Mutation
        ## Version
        ## Audit

    When the human gate did not open, the report shows:

        Human Review: WAITING
        Mutation: NOT EXECUTED

    When the proposal was rejected, the report shows:

        Human Review: REJECTED
        Mutation: NOT EXECUTED
    """
    lines: list[str] = []
    lines.append("# Feedback Evolution Runtime Report")
    lines.append("")

    # Feedback
    lines.append("## Feedback")
    lines.append("")
    lines.append("- feedback_id: `" + _safe(result.feedback_id) + "`")
    lines.append("")

    # Proposal
    lines.append("## Proposal")
    lines.append("")
    lines.append("- proposal_id: `" + _safe(result.proposal_id) + "`")
    lines.append("")

    # Human Review -- posture depends on evolution_status.
    lines.append("## Human Review")
    lines.append("")
    if result.evolution_status == EVOLUTION_STATUS_WAITING_HUMAN_REVIEW:
        lines.append("- Human Review: WAITING")
    elif result.evolution_status == EVOLUTION_STATUS_REJECTED:
        lines.append("- Human Review: REJECTED")
    elif result.evolution_status == EVOLUTION_STATUS_APPROVED_BUT_BLOCKED:
        lines.append("- Human Review: APPROVED (but blocked downstream)")
    else:
        lines.append("- Human Review: APPROVED")
    lines.append("")

    # ChangeIntent
    lines.append("## ChangeIntent")
    lines.append("")
    if result.change_intent is None:
        lines.append("- ChangeIntent: None")
    else:
        ci = result.change_intent
        ct = getattr(ci, "change_type", None)
        ct_value = getattr(ct, "value", None) if ct is not None else None
        lines.append("- intent_id: `" + _safe(getattr(ci, "intent_id", "")) + "`")
        lines.append(
            "- change_type: `"
            + _safe(ct_value if ct_value is not None else ct)
            + "`"
        )
        lines.append(
            "- target_field: `" + _safe(getattr(ci, "target_field", "")) + "`"
        )
        lines.append(
            "- target_identity: `"
            + _safe(getattr(ci, "target_identity", ""))
            + "`"
        )
    lines.append("")

    # Evolution Transaction
    lines.append("## Evolution Transaction")
    lines.append("")
    lines.append(
        "- transaction_id: `" + _safe(result.transaction_id) + "`"
    )
    lines.append(
        "- evolution_status: `"
        + _safe(result.evolution_status)
        + "`"
    )
    lines.append("")

    # Mutation posture
    lines.append("## Mutation")
    lines.append("")
    if result.mutation_executed:
        lines.append("- Mutation: EXECUTED")
    else:
        lines.append("- Mutation: NOT EXECUTED")
    lines.append("")

    # Version
    lines.append("## Version")
    lines.append("")
    if result.version_number > 0:
        lines.append("- version_number: " + str(result.version_number))
    else:
        lines.append("- version_number: 0 (no version created)")
    lines.append("")

    # Audit
    lines.append("## Audit")
    lines.append("")
    if result.audit_id is None:
        lines.append("- audit_id: None")
    else:
        lines.append("- audit_id: `" + _safe(result.audit_id) + "`")
    lines.append("")

    return "\n".join(lines)


__all__ = ["generate_report"]
