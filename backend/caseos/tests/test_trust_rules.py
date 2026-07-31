"""Tests for the Trust Intelligence rule engine (Sprint 19.3).

Acceptance Criteria from spec section 9 (Tests):
    Test 1 -- strong evidence case: R-01 decision + failure-pattern
              knowledge -> Confidence = Medium, Evidence present.
    Test 2 -- decision without evidence (no knowledge): Confidence =
              Low, Uncertainty present.
    Test 3 -- contradictory evidence: Confidence = Low, caveat
              "requires validation" present.

Plus auxiliary tests for:
    - High confidence is FORBIDDEN in V1 (spec section 7 + ADR-016).
    - The pipeline stage contract (name = "trust") is preserved.
    - The 5 ADR-016 Trust Object fields are always present.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.brain.runtime.context import PipelineContext, ProjectContext
from caseos.intelligence.trust.module import (
    TrustEngine,
    TrustModule,
    ALLOWED_LEVELS,
)


# ------------- helpers -------------

REQUIRED_FIELDS = (
    "evidence",
    "source_reliability",
    "applicability_match",
    "confidence",
    "uncertainty_handling",
)


def _project(**overrides) -> ProjectContext:
    base = dict(
        project_id="t",
        project_type="kindergarten_outdoor",
        site_description="",
        user_goal="",
        constraints="",
        extras={},
    )
    base.update(overrides)
    return ProjectContext(**base)


def _decision_with_rule(rule_id="R-01", decision="Create an anchored experience",
                       boundary="Do not add scattered equipment",
                       reason="Rule R-01 fired"):
    return {
        "decision": decision,
        "boundary": boundary,
        "reasoning": reason,
        "_trace": {"rule_id": rule_id, "rule_name": "Lacks identity + equipment exists"},
    }


# A FailurePattern knowledge object (used by Test 1)
_FAILURE_PATTERN_KO = {
    "identity": "FailurePattern.scatter_equipment_overload_v1",
    "principle": "Remove before add. Empty is better than cluttered.",
    "applicability": {"suitable": ["any_limited_budget"]},
    "boundary": ["do not apply to a site whose primary need is accessibility"],
}

# A GoldenCase knowledge object that applies to kindergarten_outdoor
_GOLDEN_CASE_KO = {
    "identity": "GoldenCase.themed_anchor_kindergarten_v1",
    "principle": "Create one memorable experience node before adding secondary facilities.",
    "applicability": {"suitable": ["kindergarten_outdoor", "public_park_open_area"]},
}

# A Decision Pattern that always applies (suitable_when list)
_DECISION_PATTERN_KO = {
    "identity": "DecisionPattern.first_move_anchor_v1",
    "principle": "The first move creates the centre. Everything else supports it.",
    "applicability": {"suitable_when": ["site is open or under-defined"]},
}


def _run_trust(decision, knowledge, project_type="kindergarten_outdoor"):
    ctx = PipelineContext(project=_project(project_type=project_type))
    ctx.decision_object = decision
    ctx.knowledge_patterns = knowledge
    TrustModule().run(ctx)
    return ctx.trust_object


def _assert_five_fields(obj):
    for field_name in REQUIRED_FIELDS:
        assert field_name in obj, f"missing Trust Object field: {field_name}"
    assert isinstance(obj["confidence"], str)


# ------------- Test 1 -------------

def test_rule_t01_strong_evidence_medium_confidence() -> None:
    """Decision trace + applicable supporting knowledge -> Medium."""

    decision = _decision_with_rule()
    knowledge = [_GOLDEN_CASE_KO]  # applies to kindergarten_outdoor

    trust = _run_trust(decision, knowledge, project_type="kindergarten_outdoor")
    _assert_five_fields(trust)

    assert trust["confidence"] == "Medium", "T-01 should produce Medium"
    assert "Decision supported by explicit reasoning rule" in trust["evidence"]
    assert trust["_trace"]["rule_id"] == "T-01"
    assert "GoldenCase" in trust["_trace"]["supporting_knowledge_identities"][0]
    # V1 enforcement: source_reliability must reflect knowledge type
    assert "real-project-completed" in trust["source_reliability"]


# ------------- Test 2 -------------

def test_rule_t02_decision_without_evidence_low_confidence() -> None:
    """Decision trace but no supporting knowledge -> Low."""

    decision = _decision_with_rule()
    knowledge = []  # no knowledge patterns loaded

    trust = _run_trust(decision, knowledge, project_type="kindergarten_outdoor")
    _assert_five_fields(trust)

    assert trust["confidence"] == "Low", "T-02 should produce Low"
    blob = " ".join(trust["uncertainty_handling"]).lower()
    assert "insufficient" in blob or "supporting evidence" in blob
    assert trust["_trace"]["rule_id"] == "T-02"


# ------------- Test 3 -------------

def test_rule_t03_contradictory_evidence_low_confidence() -> None:
    """FailurePattern that contradicts decision boundary -> Low + caveat."""

    # Build a Decision that explicitly violates a FailurePattern's
    # "do not add X" boundary.
    decision = {
        "decision": "Add scattered equipment across the site",
        "boundary": "Do not consolidate equipment",
        "reasoning": "test",
        "_trace": {"rule_id": "R-01", "rule_name": "stub"},
    }
    fp_ko = {
        "identity": "FailurePattern.scatter_equipment_overload_v1",
        "principle": "Remove before add. Equipment stacking is bad.",
        "applicability": {"suitable": ["any_limited_budget"]},
        "boundary": ["do not add scattered equipment"],
    }
    knowledge = [fp_ko]

    trust = _run_trust(decision, knowledge, project_type="kindergarten_outdoor")
    _assert_five_fields(trust)

    assert trust["confidence"] == "Low", "T-03 should produce Low"
    blob = " ".join(trust["uncertainty_handling"]).lower()
    assert "contradiction" in blob or "validation" in blob
    assert trust["_trace"]["rule_id"] == "T-03"


# ------------- Auxiliary tests -------------

def test_high_confidence_is_forbidden_in_v1() -> None:
    """Even a fully-decision-supported case cannot produce 'High'."""
    decision = _decision_with_rule()
    # Two KOs that both match project_type (so T-01 path).
    knowledge = [_GOLDEN_CASE_KO, _DECISION_PATTERN_KO]

    trust = _run_trust(decision, knowledge, project_type="kindergarten_outdoor")

    assert trust["confidence"] in ALLOWED_LEVELS
    assert trust["confidence"] != "High"
    # The allowed-list is exactly ('Medium', 'Low') per ADR-016 V1.
    assert "High" not in ALLOWED_LEVELS


def test_trust_object_always_has_five_fields_and_canonical_caveat() -> None:
    """The Sprint 19.3 worked-example caveat is included in every object."""

    decision = _decision_with_rule()
    knowledge = [_GOLDEN_CASE_KO]

    trust = _run_trust(decision, knowledge)
    _assert_five_fields(trust)
    blob = " ".join(trust["uncertainty_handling"]).lower()
    assert "no site image analysis" in blob, \
        "Worked-example caveat must appear in every V1 trust object"


def test_stage_name_is_trust_and_in_default_pipeline() -> None:
    from caseos.brain.runtime import default_pipeline
    pipe = default_pipeline()
    names = [s.name for s in pipe.stages]
    assert "trust" in names
    for s in pipe.stages:
        if s.name == "trust":
            assert isinstance(s, TrustModule)


def test_engine_returns_low_when_no_decision_object() -> None:
    """If the Decision stage refused (no decision_object), trust is Low."""
    ctx = PipelineContext(project=_project())
    # No decision_object set
    TrustModule().run(ctx)
    assert ctx.trust_object["confidence"] == "Low"
    assert ctx.trust_object["_trace"]["rule_id"] is None


def test_engine_priority_t03_over_t01() -> None:
    """If a contradiction exists, T-03 wins even when T-01 also matches."""
    decision = _decision_with_rule()
    # A FailurePattern that contradicts the boundary together with a
    # GoldenCase that supports the project_type. T-03 must win.
    fp = {
        "identity": "FailurePattern.scatter_equipment_overload_v1",
        "principle": "Remove before add. Equipment stacking is bad.",
        "applicability": {"suitable": ["any_limited_budget"]},
        "boundary": ["do not add scattered equipment"],
    }
    decision_contra = {
        "decision": "Add scattered equipment everywhere",
        "boundary": "Do not remove; keep the scatter",
        "reasoning": "test",
        "_trace": {"rule_id": "R-01", "rule_name": "stub"},
    }
    knowledge = [_GOLDEN_CASE_KO, fp]
    trust = _run_trust(decision_contra, knowledge, project_type="kindergarten_outdoor")
    assert trust["confidence"] == "Low"
    assert trust["_trace"]["rule_id"] == "T-03"