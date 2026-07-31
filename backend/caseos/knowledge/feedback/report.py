"""Feedback Report (Sprint 22.1, ADR-018 Section 2 + Sprint 22.1 spec section 8).

The report is a Markdown summary of the feedback state. It is the
operator-facing surface for the Feedback Learning Loop.

Output structure:

    # Feedback Report
    - Total events: N
    - Total feedback: M
    - Distribution by status: ...
    - Distribution by source: ...
    - Distribution by feedback_type: ...
    - Targets with feedback: ...
    - Review-required feedback: ...
    - Approved feedback: ...
    - Rejected feedback: ...

The report is pure Python over the FeedbackStore; it does not
import from intelligence modules.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Optional

from .manager import FeedbackManager
from .event import FeedbackStatus, DRAINED_STATES, TERMINAL_STATES


def _safe(value: Any, fallback: str = "n/a") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def generate_report(manager: FeedbackManager) -> str:
    """Render a Markdown report of the manager's state."""
    events = manager.store.list()
    lines: list[str] = []
    lines.append("# Feedback Report")
    lines.append("")

    # 1. Total events + total feedback
    total_events = len(events)
    feedback_ids = sorted({e.feedback_id for e in events})
    total_feedback = len(feedback_ids)
    lines.append(f"- Total events: {total_events}")
    lines.append(f"- Total feedback objects: {total_feedback}")
    lines.append("")

    # 2. Distribution by current status
    status_counter: Counter = Counter()
    for fid in feedback_ids:
        latest = manager.store.latest_for(fid)
        if latest is not None:
            status_counter[latest.to_status] += 1
    lines.append("## Distribution by status")
    lines.append("")
    if status_counter:
        for status, count in sorted(status_counter.items()):
            lines.append(f"- {status}: {count}")
    else:
        lines.append("- (no feedback recorded)")
    lines.append("")

    # 3. Distribution by source
    source_counter: Counter = Counter()
    for fid in feedback_ids:
        latest = manager.store.latest_for(fid)
        if latest is not None:
            source_counter[latest.snapshot.get("source", "?")] += 1
    lines.append("## Distribution by source")
    lines.append("")
    if source_counter:
        for source, count in sorted(source_counter.items()):
            lines.append(f"- {source}: {count}")
    else:
        lines.append("- (no feedback recorded)")
    lines.append("")

    # 4. Distribution by feedback_type
    type_counter: Counter = Counter()
    for fid in feedback_ids:
        latest = manager.store.latest_for(fid)
        if latest is not None:
            type_counter[latest.snapshot.get("feedback_type", "?")] += 1
    lines.append("## Distribution by feedback_type")
    lines.append("")
    if type_counter:
        for ftype, count in sorted(type_counter.items()):
            lines.append(f"- {ftype}: {count}")
    else:
        lines.append("- (no feedback recorded)")
    lines.append("")

    # 5. Targets with feedback
    targets = sorted({
        e.snapshot.get("target_identity", "")
        for e in events
        if e.snapshot.get("target_identity")
    })
    lines.append("## Targets with feedback")
    lines.append("")
    if targets:
        for t in targets:
            count = manager.store.count_by_target(t)
            lines.append(f"- {t}: {count} event(s)")
    else:
        lines.append("- (none)")
    lines.append("")

    def _line(fb):
        return (f"- {fb.id} ({fb.source} / "
                f"{fb.feedback_type}) -> "
                f"`{fb.target_identity}`")

    # 6. Review-required feedback
    review_required = manager.list_by_status(FeedbackStatus.REVIEW_REQUIRED)
    lines.append("## Review-required feedback")
    lines.append("")
    if review_required:
        for fb in review_required:
            lines.append(_line(fb))
    else:
        lines.append("- (none)")
    lines.append("")

    # 7. Approved feedback
    approved = manager.list_by_status(FeedbackStatus.APPROVED)
    lines.append("## Approved feedback")
    lines.append("")
    if approved:
        for fb in approved:
            lines.append(_line(fb))
    else:
        lines.append("- (none)")
    lines.append("")

    # 8. Rejected feedback
    rejected = manager.list_by_status(FeedbackStatus.REJECTED)
    lines.append("## Rejected feedback")
    lines.append("")
    if rejected:
        for fb in rejected:
            lines.append(_line(fb))
    else:
        lines.append("- (none)")
    lines.append("")

    return "\n".join(lines)


def generate_summary(manager: FeedbackManager) -> dict[str, Any]:
    """Compact summary, suitable for embedding in a JSON dump."""
    events = manager.store.list()
    feedback_ids = sorted({e.feedback_id for e in events})
    total_feedback = len(feedback_ids)
    by_status: dict[str, int] = {}
    by_source: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for fid in feedback_ids:
        latest = manager.store.latest_for(fid)
        if latest is None:
            continue
        by_status[latest.to_status] = by_status.get(latest.to_status, 0) + 1
        src = latest.snapshot.get("source", "?")
        by_source[src] = by_source.get(src, 0) + 1
        ftype = latest.snapshot.get("feedback_type", "?")
        by_type[ftype] = by_type.get(ftype, 0) + 1
    return {
        "total_events": total_feedback and len(events),
        "total_feedback": total_feedback,
        "by_status": by_status,
        "by_source": by_source,
        "by_feedback_type": by_type,
    }


__all__ = [
    "generate_report",
    "generate_summary",
]
