"""Learning Proposal (Sprint 22.1, ADR-018 Section 3 + Sprint 22.1 spec section 7).

A ``LearningProposal`` is a **suggestion**, not a change. It never
modifies the Knowledge Object it targets. It carries:

    target_identity    which KO the proposal is about
    current_state      a snapshot of the KO's ADR-015 fields at
                       proposal-generation time
    feedback_summary   the list of feedback events that triggered
                       this proposal
    proposed_change    a Markdown description of what *could* change
    risk               one of: low | medium | high
    requires_expert_review
                       whether expert review is required before
                       the proposal can be approved
    created_at         ISO timestamp

The proposal is the operational form of ADR-018 §3.A:

    "The Loop may update three fields:
        - applicability
        - boundary
        - principle"

The proposal expresses *what could change* in those three fields.
It does NOT write to the KO; the human review step is the gate.

ADR-018 §5 Principle 1:

    "Feedback updates knowledge, not just records activity."

The proposal is the operation that bridges feedback and knowledge
update. It is the only place where feedback is translated into a
candidate knowledge update. Whether the proposal is acted upon is
a human decision (REVIEW_REQUIRED -> APPROVED), and whether the
act of action translates into a real KO update is a *future*
sprint (Sprint 22.2+); Sprint 22.1 does NOT implement auto-update.

Risk and review rules (Sprint 22.1 spec section 7):

    * CONTRADICTION_SIGNAL or UNEXPECTED_DISCOVERY -> high risk,
      requires_expert_review = True.
    * EXPERT + NEGATIVE_CORRECTION            -> high risk,
      requires_expert_review = True.
    * EXPERT + POSITIVE_CONFIRMATION          -> low risk,
      requires_expert_review = False.
    * PREFERENCE source                       -> requires review
                                                (per ADR-018 §1).
    * Everything else                         -> medium risk.

The proposal function takes a ``current_state`` snapshot by value
(not by reference) so any subsequent mutation of the corpus does
not change the proposal's snapshot.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional

from .event import FeedbackEvent
from .object import (
    FeedbackSource,
    FeedbackType,
    SOURCE_PRIORITY,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class LearningProposal:
    """A suggested knowledge update. Does NOT modify the KO."""

    proposal_id: str
    target_identity: str
    current_state: dict[str, Any]
    feedback_summary: list[dict[str, Any]]  # serialised FeedbackEvents
    proposed_change: str  # Markdown text
    risk: str  # "low" | "medium" | "high"
    requires_expert_review: bool
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _render_proposal_markdown(
    feedback_events: list[FeedbackEvent],
    reasoning: str,
) -> str:
    """Compose a Markdown block describing the proposed change.

    The output is intentionally textual (not a structured edit).
    A human reviewer reads the text and decides what to do.
    """
    lines: list[str] = []
    lines.append(f"### Learning Proposal")
    lines.append("")
    lines.append(reasoning.strip())
    lines.append("")
    if feedback_events:
        lines.append("### Triggering Feedback")
        lines.append("")
        for ev in feedback_events:
            lines.append(
                f"- `{ev.to_status}` from "
                f"`{ev.snapshot.get('source', '?')}` "
                f"({ev.snapshot.get('feedback_type', '?')})"
            )
            content = (ev.snapshot.get("content") or "").strip()
            if content:
                lines.append(f"  - {content}")
        lines.append("")
    return "\n".join(lines)


def _assess_risk(
    feedback_events: list[FeedbackEvent],
) -> tuple[str, bool]:
    """Decide risk level and whether expert review is required.

    Returns (risk, requires_expert_review).
    """
    if not feedback_events:
        return "low", False

    # Take the strongest signal among the events. Strongest = highest
    # source priority (EXPERT first), then most disruptive type.
    def _event_strength(ev: FeedbackEvent) -> tuple[int, int]:
        src = ev.snapshot.get("source")
        ftype = ev.snapshot.get("feedback_type")
        try:
            src_priority = SOURCE_PRIORITY[FeedbackSource(src)]
        except (KeyError, ValueError):
            src_priority = 0
        # Type priority: CONTRADICTION > UNEXPECTED > NEGATIVE >
        # PREFERENCE > POSITIVE.
        type_priority = {
            FeedbackType.CONTRADICTION_SIGNAL.value: 5,
            FeedbackType.UNEXPECTED_DISCOVERY.value: 4,
            FeedbackType.NEGATIVE_CORRECTION.value: 3,
            FeedbackType.PREFERENCE_SIGNAL.value: 2,
            FeedbackType.POSITIVE_CONFIRMATION.value: 1,
        }.get(str(ftype), 0)
        return (src_priority, type_priority)

    strongest = max(feedback_events, key=_event_strength)
    src = strongest.snapshot.get("source")
    ftype = strongest.snapshot.get("feedback_type")

    # CONTRADICTION_SIGNAL or UNEXPECTED_DISCOVERY -> high risk,
    # required review.
    try:
        is_disruptive = (
            FeedbackType(ftype) in (
                FeedbackType.CONTRADICTION_SIGNAL,
                FeedbackType.UNEXPECTED_DISCOVERY,
            )
        )
    except (KeyError, ValueError):
        is_disruptive = False

    # EXPERT + NEGATIVE_CORRECTION -> high risk.
    is_expert_negative = (
        src == FeedbackSource.EXPERT.value
        and ftype == FeedbackType.NEGATIVE_CORRECTION.value
    )

    if is_disruptive or is_expert_negative:
        return "high", True

    # EXPERT + POSITIVE_CONFIRMATION -> low risk, no review.
    if (
        src == FeedbackSource.EXPERT.value
        and ftype == FeedbackType.POSITIVE_CONFIRMATION.value
    ):
        return "low", False

    # PREFERENCE source -> requires review (per ADR-018 §1).
    if src == FeedbackSource.PREFERENCE.value:
        return "medium", True

    return "medium", True


def _default_reasoning(
    feedback_events: list[FeedbackEvent],
    current_state: dict[str, Any],
    risk: str,
) -> str:
    """Build a human-readable proposal summary.

    The text is intentionally vague -- it tells the reviewer
    *what kind of change* is being suggested, not the exact edit.
    ADR-018 §3.A limits the field set to ``applicability``,
    ``boundary``, and ``principle``.
    """
    strongest = max(
        feedback_events,
        key=lambda e: (
            SOURCE_PRIORITY.get(FeedbackSource(e.snapshot.get("source")), 0),
            {
                FeedbackType.CONTRADICTION_SIGNAL.value: 5,
                FeedbackType.UNEXPECTED_DISCOVERY.value: 4,
                FeedbackType.NEGATIVE_CORRECTION.value: 3,
                FeedbackType.PREFERENCE_SIGNAL.value: 2,
                FeedbackType.POSITIVE_CONFIRMATION.value: 1,
            }.get(str(e.snapshot.get("feedback_type")), 0),
        ),
        default=None,
    )
    if strongest is None:
        return (
            "No feedback events were available. The proposal is a "
            "sanity placeholder; the reviewer should reject it."
        )
    ftype = strongest.snapshot.get("feedback_type", "?")
    src = strongest.snapshot.get("source", "?")

    target_field = "principle"
    if ftype == FeedbackType.CONTRADICTION_SIGNAL.value:
        target_field = "boundary"
    elif ftype == FeedbackType.UNEXPECTED_DISCOVERY.value:
        target_field = "applicability"
    elif ftype == FeedbackType.PREFERENCE_SIGNAL.value:
        target_field = "applicability"

    boundary = current_state.get("boundary")
    applicability = current_state.get("applicability")
    principle = current_state.get("principle")

    parts: list[str] = []
    parts.append(
        f"Based on {len(feedback_events)} feedback event(s) "
        f"({', '.join(e.snapshot.get('feedback_type', '?') for e in feedback_events)}), "
        f"the strongest signal is from `{src}` ({ftype})."
    )
    parts.append("")
    parts.append(f"Suggested review field: `{target_field}`.")
    parts.append("")
    parts.append("Current state snapshot:")
    if isinstance(boundary, list) and boundary:
        parts.append(f"- boundary: {'; '.join(str(b) for b in boundary)}")
    elif isinstance(boundary, str) and boundary:
        parts.append(f"- boundary: {boundary}")
    if isinstance(applicability, dict):
        parts.append(f"- applicability: {applicability}")
    if isinstance(principle, str) and principle:
        parts.append(f"- principle: {principle[:120]}{'...' if len(principle) > 120 else ''}")
    parts.append("")
    if risk == "high":
        parts.append(
            "**Risk: HIGH.** Human review is required before any "
            "knowledge update. The Loop must NOT auto-apply."
        )
    elif risk == "medium":
        parts.append(
            "**Risk: MEDIUM.** A reviewer should evaluate whether "
            "the principle OR applicability should be refined."
        )
    else:
        parts.append(
            "**Risk: LOW.** The proposed change is a positive "
            "confirmation; the existing knowledge stands and may be "
            "marked as re-validated."
        )
    return "\n".join(parts)


def generate_proposal(
    target_identity: str,
    current_state: dict[str, Any],
    feedback_events: list[FeedbackEvent],
    proposal_id: Optional[str] = None,
) -> LearningProposal:
    """Build a LearningProposal.

    IMPORTANT: this function does NOT mutate ``current_state``.
    It takes a snapshot by value. The caller (the manager) has
    already produced the snapshot by reading the corpus; the
    proposal is constructed from that snapshot and the manager
    keeps the corpus intact.

    Args:
        target_identity: the KO identity.
        current_state: a snapshot of the KO's relevant fields. The
            function copies it; the caller's reference is not
            modified.
        feedback_events: the events that triggered this proposal.
        proposal_id: an optional explicit ID (default: UUID).

    Returns:
        A ``LearningProposal`` with risk + review flag decided.
    """
    # Take a snapshot by value so the proposal is isolated.
    snapshot_state = dict(current_state or {})
    snapshot_events = [e.to_dict() for e in feedback_events]

    risk, requires_expert_review = _assess_risk(feedback_events)
    reasoning = _default_reasoning(feedback_events, snapshot_state, risk)
    markdown = _render_proposal_markdown(feedback_events, reasoning)

    return LearningProposal(
        proposal_id=proposal_id or str(uuid.uuid4()),
        target_identity=target_identity,
        current_state=snapshot_state,
        feedback_summary=snapshot_events,
        proposed_change=markdown,
        risk=risk,
        requires_expert_review=requires_expert_review,
    )


__all__ = [
    "LearningProposal",
    "generate_proposal",
]
