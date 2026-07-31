"""Tests for the Recommendation Intelligence engine (Sprint 19.4).

Acceptance Criteria from spec section 7 (Tests):
    Test 1 -- R-01 experience anchor: diagnosis contains "not lack of
              equipment", strategy contains "experience anchor",
              boundary preserved.
    Test 2 -- R-03 overloaded playground: recommendation contains
              "remove before adding"; no additional facilities listed.
    Test 3 -- Low-confidence decision: output contains
              "More information required" or equivalent uncertainty.

Plus auxiliary invariants for ADR-017:
    - Seven sections always present and named per ADR-017 Section 2.2
    - RCM-01 (no decision modification) always passes
    - RCM-02 (no equipment dumping) always passes
    - RCM-03 (trust always appears) always passes
    - Stage wire contract (name = "recommendation") preserved
    - Empty / missing Decision and Trust objects do not crash
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.brain.runtime.context import PipelineContext, ProjectContext
from caseos.intelligence.recommendation.module import (
    RecommendationEngine,
    RecommendationModule,
    SEVEN_SECTIONS,
    FORBIDDEN_EQUIPMENT,
)


# ------------- helpers -------------

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


def _decision_r1():
    """Decision Object shape for the R-01 experience-anchor path."""
    return {
        "situation": "user states the space has no clear identity",
        "observation": "some existing equipment but no narrative",
        "diagnosis": (
            "the problem is not insufficient equipment but a lack "
            "of spatial narrative"
        ),
        "decision": "Create a single thematically anchored experience",
        "reasoning": (
            "Rule R-01 fired: space_problem_lack_of_identity AND "
            "equipment_exists -> prior experience anchor over equipment addition"
        ),
        "boundary": "Do not add scattered, disconnected equipment",
        "applicability": "Suitable for renewal / re-theming projects",
        "_trace": {"rule_id": "R-01", "rule_name": "..."},
    }


def _decision_r3():
    """Decision Object shape for the R-03 overloaded path."""
    return {
        "situation": "the existing space shows signs of over-use",
        "observation": "scattered equipment with no visual hierarchy",
        "diagnosis": (
            "the problem is visual hierarchy; too many disconnected "
            "facilities compete for attention"
        ),
        "decision": "Remove before adding. Empty is better than cluttered.",
        "reasoning": (
            "Rule R-03 fired: existing_space_overloaded -> remove "
            "before adding; consolidate value"
        ),
        "boundary": (
            "Do not cover a weakness with a random object"
        ),
        "applicability": (
            "Suitable when site description flags overload, regardless of project type"
        ),
        "_trace": {"rule_id": "R-03", "rule_name": "Overloaded space"},
    }


def _decision_more_info():
    """Decision Object for the "no rule matched" / more-info path."""
    return {
        "situation": "the available signals do not yet warrant a decision",
        "observation": "no V1 rule matched the extracted signal set",
        "diagnosis": "insufficient information to recommend",
        "decision": "More information required",
        "reasoning": "No V1 rule matched the signal map",
        "boundary": "Do not commit to a recommendation until more is known",
        "applicability": "Suitable only as a placeholder",
        "_trace": {"rule_id": None, "rule_name": None},
    }


def _trust_medium():
    return {
        "schema_version": "trust_object_v1",
        "evidence": (
            "Decision supported by explicit reasoning rule and relevant "
            "knowledge object(s): GoldenCase.themed_anchor_kindergarten_v1"
        ),
        "source_reliability": ["real-project-completed"],
        "applicability_match": "high",
        "confidence": "Medium",
        "uncertainty_handling": [
            "No site image analysis available yet (Vision engine is "
            "out of scope for Sprint 19.3).",
        ],
    }


def _recommend(decision, trust, project=None, human=None):
    if project is None:
        project = _project(
            project_type="kindergarten_outdoor",
            site_description="some existing equipment, no clear identity",
            user_goal="improve enrollment",
            constraints="limited budget",
        )
    return RecommendationEngine().recommend(
        project=project,
        human_context=human,
        decision=decision,
        trust=trust,
    )


def _assert_seven_sections(rec: dict) -> None:
    sections = rec.get("sections") or {}
    for name in SEVEN_SECTIONS:
        assert name in sections, f"missing section: {name}"


# ------------- Test 1: R-01 experience anchor -------------

def test_rule_r1_recommendation_preserves_decision() -> None:
    rec = _recommend(_decision_r1(), _trust_medium())
    _assert_seven_sections(rec)

    # Spec test 1: diagnosis contains "not lack of equipment"
    diag = rec["sections"]["problem_diagnosis"]
    assert "not insufficient equipment" in diag, (
        f"diagnosis should preserve the not-insufficient-equipment phrase: {diag!r}"
    )

    # Strategy must contain the experience anchor concept
    strat = rec["sections"]["strategic_direction"]
    assert "anchored experience" in strat, (
        f"strategy should contain the experience-anchor concept: {strat!r}"
    )

    # Boundary must be preserved somewhere in the implementation or
    # strategy section (RCM-01)
    impl = rec["sections"]["implementation_direction"]
    assert "scattered" in impl, (
        f"boundary (no scattered equipment) must be preserved: {impl!r}"
    )

    # RCM-01 should pass for an honest R-01 path
    results = {r["rule_id"]: r["passed"] for r in rec["constraint_results"]}
    assert results["RCM-01"] is True, "RCM-01 must pass for R-01 path"


# ------------- Test 2: R-03 overloaded playground -------------

def test_rule_r3_remove_before_adding_no_facilities() -> None:
    rec = _recommend(_decision_r3(), _trust_medium())
    _assert_seven_sections(rec)

    # Spec test 2: recommendation contains "remove before adding"
    blob = (
        rec["sections"]["strategic_direction"]
        + " "
        + rec["sections"]["implementation_direction"]
    ).lower()
    assert "remove before adding" in blob, (
        f"R-03 should surface the remove-before-adding phrase: {blob!r}"
    )

    # No isolated facility recommendations (RCM-02)
    for word in FORBIDDEN_EQUIPMENT:
        assert word not in rec["sections"]["experience_concept"].lower(), (
            f"forbidden equipment word {word!r} leaked into experience_concept"
        )

    # RCM-02 should pass for the R-03 path
    results = {r["rule_id"]: r["passed"] for r in rec["constraint_results"]}
    assert results["RCM-02"] is True, "RCM-02 must pass for R-03 path"


# ------------- Test 3: Low confidence / more information required -------------

def test_low_confidence_emits_more_information_required() -> None:
    rec = _recommend(_decision_more_info(), _trust_medium())
    _assert_seven_sections(rec)

    blob = (
        rec["sections"]["strategic_direction"]
        + " "
        + rec["sections"]["implementation_direction"]
        + " "
        + rec["sections"]["experience_concept"]
    ).lower()
    assert "more information required" in blob, (
        f"low-confidence path must surface the more-information phrase: {blob!r}"
    )

    # Implementation should ask for clarification, not prescribe
    impl = rec["sections"]["implementation_direction"].lower()
    assert "additional information is required" in impl, (
        "implementation should ask for additional information"
    )


# ------------- Auxiliary: RCM-01 invariant -------------

def test_rcm01_preserves_diagnosis_and_strategy() -> None:
    """The Decision\'s diagnosis and strategy must always reach the
    rendered sections -- no modification, no rewording, no dropping.
    """
    rec = _recommend(_decision_r1(), _trust_medium())
    diag = rec["sections"]["problem_diagnosis"]
    strat = rec["sections"]["strategic_direction"]
    assert "not insufficient equipment" in diag
    assert "Create a single thematically anchored experience" in strat
    results = {r["rule_id"]: r["passed"] for r in rec["constraint_results"]}
    assert results["RCM-01"] is True


# ------------- Auxiliary: RCM-02 invariant -------------

def test_rcm02_no_equipment_dumping() -> None:
    rec = _recommend(_decision_r1(), _trust_medium())
    experience = rec["sections"]["experience_concept"].lower()
    impl = rec["sections"]["implementation_direction"].lower()
    for word in FORBIDDEN_EQUIPMENT:
        assert word not in experience
        assert word not in impl
    results = {r["rule_id"]: r["passed"] for r in rec["constraint_results"]}
    assert results["RCM-02"] is True


# ------------- Auxiliary: RCM-03 invariant -------------

def test_rcm03_trust_always_appears() -> None:
    rec = _recommend(_decision_r1(), _trust_medium())
    evidence = rec["sections"]["evidence"]
    cc = rec["sections"]["confidence_and_caveats"]
    assert evidence and evidence.strip()
    assert cc["confidence"] == "Medium"
    assert "caveats" in cc and isinstance(cc["caveats"], list)
    results = {r["rule_id"]: r["passed"] for r in rec["constraint_results"]}
    assert results["RCM-03"] is True


# ------------- Auxiliary: missing decision / trust do not crash -------------

def test_engine_handles_missing_decision_object() -> None:
    rec = _recommend(None, _trust_medium())
    _assert_seven_sections(rec)
    # Without a Decision, the engine should still emit sections; the
    # diagnosis / strategy should be honest fallbacks.
    assert "not yet allow a clear diagnosis" in rec["sections"]["problem_diagnosis"]
    assert "No strategic direction" in rec["sections"]["strategic_direction"]


def test_engine_handles_missing_trust_object() -> None:
    rec = _recommend(_decision_r1(), None)
    _assert_seven_sections(rec)
    cc = rec["sections"]["confidence_and_caveats"]
    assert cc["confidence"] == "Unknown"
    assert any("manual review" in c.lower() for c in cc["caveats"])


# ------------- Auxiliary: stage wire contract -------------

def test_stage_name_is_recommendation_and_in_default_pipeline() -> None:
    from caseos.brain.runtime import default_pipeline
    pipe = default_pipeline()
    names = [s.name for s in pipe.stages]
    assert "recommendation" in names
    for s in pipe.stages:
        if s.name == "recommendation":
            assert isinstance(s, RecommendationModule)


# ------------- Auxiliary: seven sections in canonical order -------------

def test_seven_sections_canonical_order() -> None:
    """The seven ADR-017 sections must appear in the documented order."""
    assert SEVEN_SECTIONS == (
        "situation_understanding",
        "problem_diagnosis",
        "strategic_direction",
        "experience_concept",
        "implementation_direction",
        "evidence",
        "confidence_and_caveats",
    )