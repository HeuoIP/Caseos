"""Feedback Evaluation -> Learning Proposal Integration (Sprint 22.3).

Bridge layer between:

    ContradictionResult (Sprint 22.2-B.1/B.2)
        |
        v
    LearningProposal  (Sprint 22.3, this module)
        |
        v
    Human Review Queue (lifecycle: CREATED -> PENDING_REVIEW -> APPROVED/REJECTED)

This module is the only place that turns a ContradictionResult
into a LearningProposal. It does NOT mutate the Knowledge Object,
does NOT update Decision / Trust / Recommendation, and does NOT
short-circuit the human review step.

Architecture boundary (Sprint 22.3 spec):

    Allowed imports:
        * caseos.knowledge.feedback (parent package)
        * caseos.knowledge.governance (read-only trust tier)
    Forbidden imports:
        * caseos.intelligence.decision
        * caseos.intelligence.trust
        * caseos.intelligence.recommendation
        * caseos.knowledge.retrieval

All proposals created by this module have:

    * requires_human_review = True    (Sprint 22.3 spec Task 4)
    * status = CREATED                (lifecycle starts at CREATED)

The proposal never modifies any external state. It captures a
snapshot of the KO at the moment of proposal creation; the
snapshot is taken by VALUE so the corpus is not affected.

The function is the single public entry point. There is no
background daemon, no scheduler, no automation.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Optional

from .evaluation.contradiction import ContradictionResult
from .proposal import (
    LearningProposal,
    PROPOSAL_TYPE_APPLICABILITY,
    PROPOSAL_TYPE_BOUNDARY,
    PROPOSAL_TYPE_PRINCIPLE,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _snapshot_state(knowledge_object: Any) -> dict[str, Any]:
    """Take a snapshot of the KO by VALUE.

    The snapshot covers the ADR-015 fields the proposal may
    reference (``boundary``, ``principle``, ``applicability``,
    ``identity``). The caller may pass any object; if the object
    is a dict, those keys are read; otherwise the snapshot is
    empty (the proposal still carries the target_identity
    independently).
    """
    if not isinstance(knowledge_object, dict):
        return {}
    import copy
    snapshot: dict[str, Any] = {}
    for key in ("identity", "boundary", "principle", "applicability"):
        if key in knowledge_object:
            snapshot[key] = copy.deepcopy(knowledge_object[key])
    return snapshot


def _proposal_type_from_conflict(contradiction: ContradictionResult) -> str:
    """Map a ContradictionResult to a proposal_type.

    boundary_conflict  -> boundary_update_candidate
    principle_conflict -> principle_update_candidate
    other              -> applicability_update_candidate
    """
    ctype = (contradiction.conflict_type or "").lower()
    if "boundary" in ctype:
        return PROPOSAL_TYPE_BOUNDARY
    if "principle" in ctype:
        return PROPOSAL_TYPE_PRINCIPLE
    return PROPOSAL_TYPE_APPLICABILITY


def _target_field_from_type(proposal_type: str) -> str:
    if proposal_type == PROPOSAL_TYPE_BOUNDARY:
        return "boundary"
    if proposal_type == PROPOSAL_TYPE_PRINCIPLE:
        return "principle"
    return "applicability"


def _suggested_change(
    proposal_type: str,
    contradiction: ContradictionResult,
    snapshot: dict[str, Any],
) -> str:
    field_name = _target_field_from_type(proposal_type)
    snippet = snapshot.get(field_name)
    if isinstance(snippet, list) and snippet:
        snippet_text = "; ".join(str(x) for x in snippet)
    elif isinstance(snippet, str) and snippet:
        snippet_text = snippet
    elif isinstance(snippet, dict):
        snippet_text = str(snippet)
    else:
        snippet_text = "(absent)"
    return (
        "Candidate update for ``" + field_name + "``: " + snippet_text
        + ". Reviewer decides the exact edit. Source contradiction: "
        + (contradiction.explanation or "")
    )


def propose_from_contradiction(
    feedback: Any,
    contradiction: ContradictionResult,
    knowledge_object: Any,
    *,
    proposal_id: Optional[str] = None,
    status: str = "CREATED",
) -> Optional[LearningProposal]:
    """Turn a ContradictionResult into a LearningProposal.

    Returns ``None`` when the contradiction has ``has_conflict=False``;
    the integration layer never produces proposals for non-conflict
    evaluations.

    Args:
        feedback: the feedback payload (FeedbackObject, dict,
            FeedbackEvent, or anything carrying an ``id`` /
            ``feedback_id`` field).
        contradiction: a ContradictionResult from the analyzer.
        knowledge_object: the target KO (read-only; never mutated).
        proposal_id: optional explicit id (default: UUID4).
        status: initial status (default ``"CREATED"``).

    Returns:
        A ``LearningProposal`` with ``requires_human_review=True``
        and ``status=CREATED`` (or whatever was passed in), or
        ``None`` if the contradiction is non-conflicting.
    """
    if contradiction is None or not getattr(
        contradiction, "has_conflict", False
    ):
        return None

    feedback_id = _extract_feedback_id(feedback)
    if not feedback_id and contradiction.feedback_id:
        feedback_id = contradiction.feedback_id

    target_identity = (
        contradiction.target_identity
        or _extract_target_identity(knowledge_object)
    )

    snapshot = _snapshot_state(knowledge_object)
    proposal_type = _proposal_type_from_conflict(contradiction)
    suggested_change = _suggested_change(proposal_type, contradiction, snapshot)

    return LearningProposal(
        proposal_id=proposal_id or str(uuid.uuid4()),
        feedback_id=feedback_id,
        target_identity=target_identity,
        proposal_type=proposal_type,
        current_state=snapshot,
        suggested_change=suggested_change,
        reason=contradiction.explanation or "",
        requires_human_review=True,
        status=status,
    )


def _extract_feedback_id(feedback: Any) -> str:
    for attr in ("id", "feedback_id"):
        v = getattr(feedback, attr, None)
        if isinstance(v, str) and v:
            return v
    if isinstance(feedback, dict):
        for k in ("id", "feedback_id"):
            v = feedback.get(k)
            if isinstance(v, str) and v:
                return v
        snap = feedback.get("snapshot")
        if isinstance(snap, dict):
            for k in ("id", "feedback_id"):
                v = snap.get(k)
                if isinstance(v, str) and v:
                    return v
    return ""


def _extract_target_identity(knowledge_object: Any) -> str:
    if isinstance(knowledge_object, dict):
        v = knowledge_object.get("identity")
        if isinstance(v, str):
            return v
    return ""


__all__ = ["propose_from_contradiction"]
