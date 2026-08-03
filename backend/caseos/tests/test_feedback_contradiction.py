"""Unit tests for ContradictionAnalyzer (Sprint 22.2-B.3).

Scope: only the analyzer behavior (ContradictionAnalyzer.analyze()).
No pipeline, no CLI, no pytest-integration, no reports.

The analyzer is treated as a pure function of
(feedback, knowledge_object). These tests do not exercise any other
module and do not modify the analyzer implementation.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.knowledge.feedback.evaluation.contradiction import (
    ContradictionResult,
)
from caseos.knowledge.feedback.evaluation.analyzer import (
    ContradictionAnalyzer,
)


# ---------------------------------------------------------------------------
# Test 1: Boundary conflict
# ---------------------------------------------------------------------------

def test_boundary_conflict_is_detected() -> None:
    """KO 'do not add scattered equipment' + feedback
    'add scattered equipment everywhere' must report a
    boundary_conflict."""
    ko = {
        "identity": "test_boundary",
        "boundary": ["Do not add scattered equipment"],
    }
    feedback = {"content": "Add scattered equipment everywhere"}

    result = ContradictionAnalyzer().analyze(feedback, ko)

    assert isinstance(result, ContradictionResult)
    assert result.has_conflict is True
    assert result.conflict_type == "boundary_conflict"
    assert result.matched_field == "boundary"
    assert result.requires_human_review is True


# ---------------------------------------------------------------------------
# Test 2: Principle conflict
# ---------------------------------------------------------------------------

def test_principle_conflict_is_detected() -> None:
    """KO 'Create hierarchy before adding facilities' + feedback
    'Add facilities without hierarchy' must report a
    principle_conflict."""
    ko = {
        "identity": "test_principle",
        "principle": "Create hierarchy before adding facilities",
    }
    feedback = {"content": "Add facilities without hierarchy"}

    result = ContradictionAnalyzer().analyze(feedback, ko)

    assert result.has_conflict is True
    assert result.conflict_type == "principle_conflict"
    assert result.matched_field == "principle"
    assert result.requires_human_review is True


# ---------------------------------------------------------------------------
# Test 3: Unknown / no clear conflict
# ---------------------------------------------------------------------------

def test_unknown_returns_no_conflict_with_review_flag() -> None:
    """When no clear conflict is detected, the analyzer returns
    has_conflict=False, conflict_type=None, but still flags the
    result for human review (Rule 3 in the spec)."""
    ko = {
        "identity": "test_unknown",
        "principle": "Create hierarchy before adding facilities",
        "boundary": ["Do not add scattered equipment"],
    }
    feedback = {"content": "This looks good overall"}

    result = ContradictionAnalyzer().analyze(feedback, ko)

    assert result.has_conflict is False
    assert result.conflict_type is None
    assert result.matched_field == ""
    assert result.requires_human_review is True


# ---------------------------------------------------------------------------
# Safety rule: false-positive guard
# ---------------------------------------------------------------------------

def test_description_only_feedback_does_not_trigger_boundary() -> None:
    """A purely descriptive feedback (no directive verb) must not
    trigger a boundary_conflict even if it mentions the violation
    phrase."""
    ko = {"identity": "x", "boundary": ["Do not add scattered equipment"]}
    feedback = {"content": "The site already has scattered equipment"}

    result = ContradictionAnalyzer().analyze(feedback, ko)
    assert result.has_conflict is False
    assert result.conflict_type is None


def test_no_negation_in_boundary_does_not_trigger() -> None:
    """Boundary statements without a recognised negation prefix
    must not produce a false-positive boundary_conflict."""
    ko = {"identity": "x", "boundary": ["Add shade in summer"]}
    feedback = {"content": "Add shade in summer"}

    result = ContradictionAnalyzer().analyze(feedback, ko)
    assert result.has_conflict is False
    assert result.conflict_type is None


# ---------------------------------------------------------------------------
# Field plumbing
# ---------------------------------------------------------------------------

def test_target_identity_is_propagated_from_ko() -> None:
    ko = {
        "identity": "KO-42",
        "boundary": ["Do not add scattered equipment"],
    }
    feedback = {"content": "Add scattered equipment everywhere"}
    result = ContradictionAnalyzer().analyze(feedback, ko)
    assert result.target_identity == "KO-42"


def test_feedback_id_is_propagated_from_dict() -> None:
    ko = {"identity": "KO-1", "principle": "x before y"}
    feedback = {"id": "fb-99", "content": "y without x"}
    result = ContradictionAnalyzer().analyze(feedback, ko)
    assert result.feedback_id == "fb-99"


# ---------------------------------------------------------------------------
# Accepts FeedbackObject / FeedbackEvent
# ---------------------------------------------------------------------------

def test_accepts_feedback_object() -> None:
    from caseos.knowledge.feedback import (
        new_feedback, FeedbackSource, FeedbackType,
    )
    ko = {
        "identity": "test_boundary",
        "boundary": ["Do not add scattered equipment"],
    }
    fb = new_feedback(
        FeedbackSource.EXPERT, FeedbackType.CONTRADICTION_SIGNAL,
        "test_boundary", "Add scattered equipment everywhere",
    )
    result = ContradictionAnalyzer().analyze(fb, ko)
    assert result.has_conflict is True
    assert result.conflict_type == "boundary_conflict"
    assert result.matched_field == "boundary"


def test_accepts_feedback_event_with_snapshot() -> None:
    from caseos.knowledge.feedback import new_event, FeedbackStatus
    ko = {
        "identity": "test_boundary",
        "boundary": ["Do not add scattered equipment"],
    }
    snapshot = {"content": "Add scattered equipment everywhere"}
    ev = new_event("fb-evt", None, FeedbackStatus.RECEIVED,
                   snapshot=snapshot)
    result = ContradictionAnalyzer().analyze(ev, ko)
    assert result.has_conflict is True
    assert result.conflict_type == "boundary_conflict"


# ---------------------------------------------------------------------------
# Statelessness
# ---------------------------------------------------------------------------

def test_analyzer_is_stateless() -> None:
    ko = {
        "identity": "test_boundary",
        "boundary": ["Do not add scattered equipment"],
    }
    feedback = {"content": "Add scattered equipment everywhere"}
    a = ContradictionAnalyzer()
    r1 = a.analyze(feedback, ko)
    r2 = a.analyze(feedback, ko)
    assert r1.has_conflict == r2.has_conflict
    assert r1.conflict_type == r2.conflict_type
    assert r1.matched_field == r2.matched_field
