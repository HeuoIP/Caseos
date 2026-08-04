"""Rollback Report V1 (Sprint 22.4-G, ADR-020 Rule 4).

Renders a Markdown summary of a rollback request, the
validator verdict, and (if valid) the plan. The report
is the **operator-facing audit surface** of the rollback
foundation; it does not perform any rollback.

Required sections (Sprint 22.4-G spec Task 5):

    # Evolution Rollback Report
    ## Rollback Request
    ## Validation Result
    ## Rollback Plan
    ## Knowledge Mutation

The ``## Knowledge Mutation`` section has a **fixed
output**:

    NOT EXECUTED

The ``## Safety Boundary`` section ends with:

    Rollback foundation only.

Both lines are the explicit V1 hard-stop markers. A
future Sprint 22.4.x rollback runtime will keep the
second line and change the first to "EXECUTED at
version N".

Architecture boundary (Sprint 22.4-G spec Task 6):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, List, Optional

from .object import RollbackPlan, RollbackRequest, RollbackValidationResult


def _safe(value: Any, fallback: str = "(none)") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def _render_plan(plan: Optional[RollbackPlan]) -> List[str]:
    if plan is None:
        return ["(no plan: validation failed)"]
    lines: List[str] = []
    lines.append("- rollback_id: `" + _safe(plan.rollback_id) + "`")
    lines.append("- target_identity: `" + _safe(plan.target_identity) + "`")
    lines.append("- source_version: `" + str(plan.source_version) + "`")
    lines.append("- destination_version: `"
                 + str(plan.destination_version) + "`")
    lines.append("- diff_summary: " + _safe(plan.diff_summary))
    lines.append("- mutation_executed: `"
                 + str(plan.mutation_executed) + "`")
    lines.append("- steps:")
    for s in plan.steps:
        lines.append("    - " + s)
    return lines


def generate_report(
    request: Optional[RollbackRequest],
    validation: Optional[RollbackValidationResult],
    plan: Optional[RollbackPlan] = None,
    *,
    title: str = "Evolution Rollback Report",
) -> str:
    """Render a Markdown report of one rollback flow.

    Args:
        request: the rollback request (may be None).
        validation: the validation result (may be None).
        plan: the produced plan (None when validation failed).
        title: optional report title override.
    """
    lines: List[str] = []
    lines.append("# " + title)
    lines.append("")

    # ---- ## Rollback Request --------------------------------------
    lines.append("## Rollback Request")
    lines.append("")
    if request is None:
        lines.append("(no request)")
    else:
        lines.append("- rollback_id: `" + _safe(request.rollback_id) + "`")
        lines.append("- transaction_id: `" + _safe(request.transaction_id) + "`")
        lines.append("- target_identity: `" + _safe(request.target_identity) + "`")
        lines.append("- from_version: `" + str(request.from_version) + "`")
        lines.append("- to_version: `" + str(request.to_version) + "`")
        lines.append("- reason: " + _safe(request.reason))
        lines.append("- requested_by: `" + _safe(request.requested_by) + "`")
        lines.append("- created_at: `" + _safe(request.created_at) + "`")
    lines.append("")

    # ---- ## Validation Result ------------------------------------
    lines.append("## Validation Result")
    lines.append("")
    if validation is None:
        lines.append("(no validation result)")
    else:
        if validation.valid:
            lines.append("- verdict: **VALID**")
            lines.append("- rule_id: (all rules passed)")
        else:
            lines.append("- verdict: **REJECTED**")
            lines.append("- rule_id: `" + _safe(validation.rule_id, "?") + "`")
            lines.append("- reason: " + _safe(validation.reason, "(none)"))
    lines.append("")

    # ---- ## Rollback Plan -----------------------------------------
    lines.append("## Rollback Plan")
    lines.append("")
    lines.extend(_render_plan(plan))
    lines.append("")

    # ---- ## Knowledge Mutation -----------------------------------
    lines.append("## Knowledge Mutation")
    lines.append("")
    lines.append("```")
    lines.append("NOT EXECUTED")
    lines.append("```")
    lines.append("")
    lines.append("  The V1 rollback foundation produces a plan but")
    lines.append("  does not apply it. No Knowledge Object is")
    lines.append("  restored, no corpus is touched, no intelligence")
    lines.append("  engine is called. A future Sprint 22.4.x")
    lines.append("  rollback runtime will consume the plan under")
    lines.append("  ADR-020 Rule 4 and a new rollback ADR.")
    lines.append("")

    # ---- ## Safety Boundary ---------------------------------------
    lines.append("## Safety Boundary")
    lines.append("")
    lines.append("- mutation_executed: `"
                 + str(getattr(plan, "mutation_executed", False)) + "`")
    lines.append("")
    lines.append("- Rollback foundation only.")
    lines.append("")
    lines.append("  The rollback package exposes a planner and a")
    lines.append("  validator, and a frozen plan dataclass. It has")
    lines.append("  no restore / rollback / apply / execute /")
    lines.append("  mutate method. The plan is a static description")
    lines.append("  of the rollback; it is the operator-facing")
    lines.append("  audit artifact, not an action.")
    lines.append("")

    return "\n".join(lines)


__all__ = ["generate_report"]
