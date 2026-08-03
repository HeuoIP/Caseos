"""Feedback Interpretation Report (Sprint 22.3.2, ADR-018 Section 3).

Renders a Markdown summary of a single ``ChangeIntent``:

    # Feedback Interpretation Report
    ## Target
    ## Change Type
    ## Target Field
    ## Current Value
    ## Proposed Value
    ## Risk
    ## Human Review Required

The report is pure Python over a ``ChangeIntent``; it does NOT
import from intelligence modules.
"""
from __future__ import annotations

from typing import Any

from .object import ChangeIntent


def _safe(value: Any, fallback: str = "(none)") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def _render_value(value: Any) -> list[str]:
    if value is None:
        return ["(none)"]
    text = str(value)
    if not text.strip():
        return ["(empty)"]
    return [text]


def generate_report(
    intent: ChangeIntent,
    title: str = "Feedback Interpretation Report",
) -> str:
    """Render a Markdown report of one ChangeIntent."""
    lines: list[str] = []
    lines.append("# " + title)
    lines.append("")

    lines.append("## Target")
    lines.append("")
    lines.append("- intent_id: `" + _safe(intent.intent_id) + "`")
    lines.append("- proposal_id: `" + _safe(intent.proposal_id) + "`")
    lines.append("- target_identity: `" + _safe(intent.target_identity) + "`")
    lines.append("- created_at: `" + _safe(intent.created_at) + "`")
    lines.append("")

    lines.append("## Change Type")
    lines.append("")
    lines.append("- change_type: `" + _safe(intent.change_type) + "`")
    lines.append("")

    lines.append("## Target Field")
    lines.append("")
    lines.append("- target_field: `" + _safe(intent.target_field) + "`")
    lines.append("")

    lines.append("## Current Value")
    lines.append("")
    lines.extend(_render_value(intent.current_value))
    lines.append("")

    lines.append("## Proposed Value")
    lines.append("")
    lines.extend(_render_value(intent.proposed_value))
    lines.append("")

    lines.append("## Risk")
    lines.append("")
    lines.append("- risk_level: `" + _safe(intent.risk_level) + "`")
    lines.append("")

    lines.append("## Human Review Required")
    lines.append("")
    lines.append(
        "- requires_human_review: **" + str(intent.requires_human_review) + "**"
    )
    return "\n".join(lines)


__all__ = ["generate_report"]
