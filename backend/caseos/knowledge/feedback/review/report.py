"""Human Review Queue Report (Sprint 22.3.1, ADR-018 Section 3).

Renders a Markdown summary of the operator-facing review queue.

Structure:

    # Human Review Queue Report
    ## Pending Reviews
    - proposal_id
      - target_identity
      - proposal_type
      - reason (from ReviewItem.summary)
    ## History
    ### Approved
    ### Rejected

The report is pure Python over a ``ReviewQueue``; it does NOT
import from intelligence modules.
"""
from __future__ import annotations

from typing import Any

from .queue import ReviewQueue


def _safe(value: Any, fallback: str = "(none)") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def _render_item(item: Any) -> list[str]:
    lines: list[str] = []
    lines.append("- proposal_id: `" + _safe(item.proposal_id) + "`")
    lines.append("  - target_identity: `" + _safe(item.target_identity) + "`")
    lines.append("  - proposal_type: `" + _safe(item.proposal_type) + "`")
    lines.append("  - review_id: `" + _safe(item.review_id) + "`")
    lines.append("  - status: " + _safe(item.status))
    lines.append("  - created_at: " + _safe(item.created_at))
    lines.append("  - reason: " + _safe(item.summary, "(no reason)"))
    return lines


def generate_report(
    queue: ReviewQueue,
    title: str = "Human Review Queue Report",
) -> str:
    lines: list[str] = []
    lines.append("# " + title)
    lines.append("")
    lines.append("- Total review records: " + str(queue.count()))
    lines.append(
        "- Distinct reviews: " + str(queue.distinct_review_count())
    )
    lines.append("")

    lines.append("## Pending Reviews")
    lines.append("")
    pending = queue.list_pending()
    if pending:
        for item in pending:
            lines.extend(_render_item(item))
    else:
        lines.append("(none)")
    lines.append("")

    lines.append("## History")
    lines.append("")
    lines.append("### Approved")
    lines.append("")
    approved = queue.list_approved()
    if approved:
        for item in approved:
            lines.extend(_render_item(item))
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("### Rejected")
    lines.append("")
    rejected = queue.list_rejected()
    if rejected:
        for item in rejected:
            lines.extend(_render_item(item))
    else:
        lines.append("(none)")
    return "\n".join(lines)


__all__ = ["generate_report"]
