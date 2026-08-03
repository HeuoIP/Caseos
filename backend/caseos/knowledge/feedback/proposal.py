"""Learning Proposal (Sprint 22.1 + Sprint 22.3, ADR-018 Section 3).

A ``LearningProposal`` is a **suggestion**, not a change. It never
modifies the Knowledge Object it targets. It carries:

    proposal_id            unique identifier
    feedback_id            the feedback that triggered this proposal
    target_identity        which KO the proposal is about
    proposal_type          one of the ADR-018 / 22.3 taxonomy values
                           (e.g. "boundary_update_candidate",
                           "principle_update_candidate",
                           "applicability_update_candidate")
    current_state          a snapshot of the KO's ADR-015 fields at
                           proposal-generation time (taken by VALUE,
                           never by reference)
    suggested_change       a short human-readable statement of what
                           could change in the future knowledge
    reason                 why the proposal was raised (a one- or
                           two-sentence explanation traceable to the
                           feedback)
    requires_human_review  True in 22.3. The proposal is always
                           gated on a human reviewer. ADR-018
                           Section 1 + 22.3 Task 4 enforce this.
    status                 ProposalStatus value (CREATED in V1)
    created_at             ISO timestamp

The proposal is the operational form of ADR-018 Section 3.A:

    "The Loop may update three fields:
        - applicability
        - boundary
        - principle"

The proposal expresses *what could change* in those three fields.
It does NOT write to the KO; the human review step is the gate.

Sprint 22.3 (this file) lifts the proposal out of the bare 22.1
shape into the integration contract required by ADR-018:
10 fields, frozen, JSON-serialisable, and disconnected from any
``KnowledgeObject`` reference. The proposal object never imports
from ``caseos.intelligence.*`` or ``caseos.knowledge.retrieval``
(per the architecture boundary).
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
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


@dataclass(frozen=True)
class LearningProposal:
    """A suggested knowledge update. Does NOT modify the KO.

    Required fields (Sprint 22.3 spec section Task 1):

        proposal_id            unique id
        feedback_id            source feedback id
        target_identity        KO identity
        proposal_type          taxonomy tag (string)
        current_state          snapshot dict of KO ADR-015 fields
        suggested_change       human-readable change description
        reason                 short explanation
        requires_human_review  always True in 22.3
        status                 ProposalStatus value
        created_at             ISO timestamp

    The dataclass is **frozen**: the proposal is append-only by
    contract. Lifecycle transitions create new events on the
    proposal store; the proposal object itself never mutates.
    """

    proposal_id: str
    feedback_id: str
    target_identity: str
    proposal_type: str
    current_state: dict[str, Any]
    suggested_change: str
    reason: str
    requires_human_review: bool
    status: str
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Proposal taxonomy (Sprint 22.3)
# ---------------------------------------------------------------------------

PROPOSAL_TYPE_BOUNDARY = "boundary_update_candidate"
PROPOSAL_TYPE_PRINCIPLE = "principle_update_candidate"
PROPOSAL_TYPE_APPLICABILITY = "applicability_update_candidate"

_VALID_PROPOSAL_TYPES = frozenset({
    PROPOSAL_TYPE_BOUNDARY,
    PROPOSAL_TYPE_PRINCIPLE,
    PROPOSAL_TYPE_APPLICABILITY,
})


def proposal_type_for_feedback_event(
    feedback_event: FeedbackEvent,
) -> str:
    """Decide the proposal_type from the strongest feedback signal.

    The mapping mirrors the 22.1 risk-rule mapping (see
    ``_assess_risk`` below). The function returns one of the three
    ADR-018 Section 3.A candidate fields.

    Falls back to ``applicability_update_candidate`` for unknown
    shapes (the safest field per ADR-018's "Loop never invents new
    knowledge fields" rule).
    """
    src = feedback_event.snapshot.get("source")
    ftype = feedback_event.snapshot.get("feedback_type")

    try:
        is_disruptive = (
            FeedbackType(ftype) in (
                FeedbackType.CONTRADICTION_SIGNAL,
                FeedbackType.UNEXPECTED_DISCOVERY,
            )
        )
    except (KeyError, ValueError):
        is_disruptive = False

    is_expert_negative = (
        src == FeedbackSource.EXPERT.value
        and ftype == FeedbackType.NEGATIVE_CORRECTION.value
    )

    if is_disruptive or is_expert_negative:
        # CONTRADICTION signals almost always point at boundary or
        # principle. Default to boundary; the caller can override
        # when more context is available.
        return PROPOSAL_TYPE_BOUNDARY

    if (
        src == FeedbackSource.EXPERT.value
        and ftype == FeedbackType.POSITIVE_CONFIRMATION.value
    ):
        return PROPOSAL_TYPE_APPLICABILITY

    return PROPOSAL_TYPE_APPLICABILITY


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _render_suggested_change(
    target_field: str, current_state: dict[str, Any]
) -> str:
    """Compose a short ``suggested_change`` text."""
    snippet = current_state.get(target_field)
    if isinstance(snippet, list) and snippet:
        snippet_text = "; ".join(str(x) for x in snippet)
    elif isinstance(snippet, str) and snippet:
        snippet_text = snippet
    elif isinstance(snippet, dict):
        snippet_text = str(snippet)
    else:
        snippet_text = "(absent)"
    return (
        f"Candidate update for ``{target_field}`` based on the "
        f"current value: {snippet_text}. The reviewer decides the "
        "exact edit."
    )


def _default_reason(
    feedback_events: list[FeedbackEvent],
    proposal_type: str,
) -> str:
    """Build a short reason string."""
    if not feedback_events:
        return (
            "No feedback events were available. The proposal is a "
            "sanity placeholder; the reviewer should reject it."
        )
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
    )
    src = strongest.snapshot.get("source", "?")
    ftype = strongest.snapshot.get("feedback_type", "?")
    return (
        f"Strongest signal: ``{src}`` ({ftype}). "
        f"Mapping to ``{proposal_type}`` per ADR-018 Section 3.A."
    )


# ---------------------------------------------------------------------------
# Public generator
# ---------------------------------------------------------------------------

def generate_proposal(
    target_identity: str,
    current_state: dict[str, Any],
    feedback_events: list[FeedbackEvent],
    proposal_id: Optional[str] = None,
    feedback_id: Optional[str] = None,
    status: str = "CREATED",
) -> LearningProposal:
    """Build a LearningProposal matching the 22.3 contract.

    The function takes a snapshot by value (``dict(current_state or {})``)
    so the corpus is never mutated. The ``feedback_events`` list is
    not retained on the proposal -- the proposal records only the
    triggering ``feedback_id`` (or, when not supplied, the most
    recent event's feedback_id).

    The generator ALWAYS sets ``requires_human_review=True``. ADR-018
    requires human-in-the-loop in 22.3.
    """
    snapshot_state = dict(current_state or {})

    if feedback_id is None and feedback_events:
        feedback_id = feedback_events[-1].feedback_id
    if not feedback_id:
        feedback_id = ""

    proposal_type = (
        proposal_type_for_feedback_event(feedback_events[-1])
        if feedback_events else PROPOSAL_TYPE_APPLICABILITY
    )
    reason = _default_reason(feedback_events, proposal_type)
    suggested_change = _render_suggested_change(
        _target_field_for_type(proposal_type), snapshot_state
    )

    return LearningProposal(
        proposal_id=proposal_id or str(uuid.uuid4()),
        feedback_id=feedback_id,
        target_identity=target_identity,
        proposal_type=proposal_type,
        current_state=snapshot_state,
        suggested_change=suggested_change,
        reason=reason,
        requires_human_review=True,
        status=status,
    )


def _target_field_for_type(proposal_type: str) -> str:
    if proposal_type == PROPOSAL_TYPE_BOUNDARY:
        return "boundary"
    if proposal_type == PROPOSAL_TYPE_PRINCIPLE:
        return "principle"
    if proposal_type == PROPOSAL_TYPE_APPLICABILITY:
        return "applicability"
    return "boundary"


__all__ = [
    "LearningProposal",
    "generate_proposal",
    "proposal_type_for_feedback_event",
    "PROPOSAL_TYPE_BOUNDARY",
    "PROPOSAL_TYPE_PRINCIPLE",
    "PROPOSAL_TYPE_APPLICABILITY",
]
