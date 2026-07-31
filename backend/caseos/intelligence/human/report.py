"""Human Understanding Report -- Sprint 21 (ADR-013 Section 8).

The report is a *human-readable* summary of the HumanContext that
the pipeline produced for a project. It is the surface an operator
uses to review whether the system understood the user correctly.

The renderer is pure Python over the HumanContext; it does not
query any external system. It is used by:

    * the CLI markdown renderer (to add a "Human Understanding"
      section to the final report)
    * the Sprint 21 review report (to show what the V1 module
      produced for the canonical examples)
    * operators inspecting `ctx.human_context` after a run
"""
from __future__ import annotations

from typing import Any

from .object import HumanContext, UNKNOWN
from .validator import HumanValidationResult


def _safe(value: Any, fallback: str = "unknown") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        s = value.strip()
        if not s or s == UNKNOWN:
            return fallback
        return s
    return str(value)


def human_context_to_markdown(
    ctx: HumanContext,
    validation: HumanValidationResult | None = None,
) -> str:
    """Render a HumanContext as a Markdown block.

    The block follows the structure:

        # Human Understanding
        - User Goal: ...
        - Business Context: ...
        - Emotional Preference: ...
        - Budget Context: ...
        - Constraints:    - ...
        - Success Definition: ...
        - Risk Tolerance: ...
        - Decision Priority: ...
        - Unknowns: ...
        - Validation: VALID / INVALID (warnings=..., errors=...)
    """
    lines: list[str] = []
    lines.append("# Human Understanding")
    lines.append("")
    lines.append(f"- User Goal: {_safe(ctx.user_goal)}")
    lines.append(f"- Business Context: {_safe(ctx.business_context)}")
    lines.append(f"- Emotional Preference: {_safe(ctx.emotional_preference)}")
    lines.append(f"- Budget Context: {_safe(ctx.budget_context)}")
    if ctx.constraints:
        lines.append("- Constraints:")
        for c in ctx.constraints:
            lines.append(f"  - {c}")
    else:
        lines.append("- Constraints: (none provided)")
    lines.append(f"- Success Definition: {_safe(ctx.success_definition)}")
    lines.append(f"- Risk Tolerance: {_safe(ctx.risk_tolerance)}")
    lines.append(f"- Decision Priority: {_safe(ctx.decision_priority)}")
    unknowns = ctx.unknowns()
    if unknowns:
        lines.append(f"- Unknowns: {', '.join(unknowns)}")
    else:
        lines.append("- Unknowns: (none -- all fields supplied)")
    if validation is not None:
        verdict = "VALID" if validation.valid else "INVALID"
        lines.append(
            f"- Validation: {verdict} "
            f"(warnings={len(validation.warnings)}, "
            f"errors={len(validation.errors)})"
        )
        for w in validation.warnings:
            lines.append(f"  - WARN: {w}")
        for e in validation.errors:
            lines.append(f"  - ERROR: {e}")
    lines.append("")
    return "\n".join(lines)


def human_context_to_summary(
    ctx: HumanContext,
    validation: HumanValidationResult | None = None,
) -> dict[str, Any]:
    """Compact summary, suitable for embedding in a JSON dump."""
    out = ctx.summary()
    if validation is not None:
        out["validation"] = validation.to_dict()
    return out


__all__ = [
    "human_context_to_markdown",
    "human_context_to_summary",
]
