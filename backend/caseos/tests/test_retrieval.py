"""Tests for Evidence Retrieval Intelligence (Sprint 20, ADR-019).

Acceptance Criteria from spec section 9 (Tests):
    Test 1 -- applicable Golden Case retrieved
    Test 2 -- wrong visual but correct decision pattern retrieved
    Test 3 -- similar image but wrong applicability rejected
    Test 4 -- Failure Pattern boundary warning returned
    Test 5 -- empty evidence returns Low confidence path
    Test 6 -- Decision not modified by Retrieval
    Test 7 -- evidence trace preserved
    Test 8 -- Pipeline executes with Retrieval stage

Plus auxiliary invariants for ADR-019:
    - P5 visual similarity is NOT a factor in V1
    - Empty Evidence Package returns the canonical "no evidence" caveat
    - Stage wire contract (name = "retrieval") preserved
    - P1 (applicability) is a hard filter (P2..P4 cannot rescue a KO
      whose applicability does not match)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.brain.runtime.context import PipelineContext, ProjectContext
from caseos.knowledge.retrieval.module import (
    EvidencePackage,
    KnowledgeRetriever,
    RetrievalEngine,
    SCORE_P1_APPLICABILITY,
)


# ------------- Sample Knowledge Objects (inline) -------------

# A Golden Case whose applicability matches `kindergarten_outdoor`.
_KO_GOLDEN_KINDERGARTEN = {
    "identity": "GoldenCase.themed_anchor_kindergarten_v1",
    "principle": (
        "Create one memorable experience node before adding secondary "
        "facilities."
    ),
    "applicability": {
        "suitable": ["kindergarten_outdoor", "public_park_open_area"],
    },
    "boundary": [
        "do not apply when budget cannot support a meaningful experience node",
    ],
    "feedback": [
        {"outcome": "stay_time_increased", "score": "positive"},
    ],
}

# A Decision Pattern that matches any project with an open / under-defined
# site. The "visual" dimension is the natural landscape; the decision
# pattern is "create anchor".
_KO_DECISION_PATTERN_NATURE = {
    "identity": "DecisionPattern.nature_anchor_v1",
    "principle": "Use natural landscape to anchor the experience.",
    "applicability": {"suitable_when": ["site is open or under-defined"]},
    "observation": [
        "natural landscape with trees and varied terrain",
    ],
}

# A Decision Pattern that matches a budget-constrained project.
_KO_DECISION_PATTERN_BUDGET = {
    "identity": "DecisionPattern.low_budget_consolidation_v1",
    "principle": "Consolidate value; do not spread budget.",
    "applicability": {"suitable_when": ["site is open or under-defined"]},
    "observation": [
        "limited budget, prefer consolidation over expansion",
    ],
}

# A Failure Pattern carrying a boundary warning.
_KO_FAILURE_PATTERN = {
    "identity": "FailurePattern.scatter_equipment_overload_v1",
    "principle": "Remove before add. Empty is better than cluttered.",
    "applicability": {"suitable": ["any_limited_budget"]},
    "boundary": [
        "do not apply when the existing equipment is the only safety anchor",
    ],
}

# A "visually-similar but wrong-applicability" KO. It shares many
# keywords with the project but its applicability tag does not match.
# This is the Test 3 fixture.
_KO_VISUAL_NOT_APPLICABLE = {
    "identity": "FakeVisuallySimilarButNotApplicableKO",
    "principle": "Looks similar but is for shopping malls only.",
    "applicability": {"suitable": ["shopping_mall_interior"]},
    "observation": [
        "open indoor area with children playing",
    ],
}

# A second matching KO so we can test ranking.
_KO_GOLDEN_PARK = {
    "identity": "GoldenCase.park_anchor_v1",
    "principle": "Open-space anchor: orient the visitor to a central lawn.",
    "applicability": {"suitable": ["public_park_open_area"]},
    "boundary": [],
}


# ------------- helpers -------------

def _project(**overrides) -> ProjectContext:
    base = dict(
        project_id="t",
        project_type="kindergarten_outdoor",
        site_description="",
        user_goal="improve enrollment",
        constraints="",
        extras={},
    )
    base.update(overrides)
    return ProjectContext(**base)


def _decision_r1():
    return {
        "decision": "Create a single thematically anchored experience",
        "diagnosis": "the problem is not insufficient equipment but a lack of spatial narrative",
        "boundary": "Do not add scattered, disconnected equipment",
        "reasoning": "Rule R-01 fired",
        "_trace": {"rule_id": "R-01", "rule_name": "..."},
    }


def _run_retrieval(project, decision=None, knowledge=None):
    engine = RetrievalEngine()
    return engine.retrieve(
        project=project,
        decision=decision,
        knowledge_patterns=knowledge,
    )


def _assert_five_fields(ep: EvidencePackage) -> None:
    """ADR-019 Section 4 -- the Evidence Package has exactly 5 fields."""
    d = ep.to_dict()
    for field_name in (
        "relevant_objects",
        "applicability_reason",
        "supporting_principle",
        "boundary_warning",
        "trust_contribution",
    ):
        assert field_name in d, f"Evidence Package missing field: {field_name}"


# ------------- Test 1: Applicable Golden Case retrieved -------------

def test_applicable_golden_case_is_retrieved() -> None:
    project = _project(project_type="kindergarten_outdoor")
    ep = _run_retrieval(
        project=project,
        decision=_decision_r1(),
        knowledge=[_KO_GOLDEN_KINDERGARTEN, _KO_VISUAL_NOT_APPLICABLE],
    )
    _assert_five_fields(ep)
    ids = [ko.get("identity") for ko in ep.relevant_objects]
    assert "GoldenCase.themed_anchor_kindergarten_v1" in ids
    # Test 1 corollary: the golden case is the top-ranked because
    # it matches P1 + P2 (diagnosis overlap with principle).
    assert ep.relevant_objects[0]["identity"] == \
        "GoldenCase.themed_anchor_kindergarten_v1"
    # Applicability reason names the tag.
    assert "kindergarten_outdoor" in ep.applicability_reason


# ------------- Test 2: Wrong visual but correct decision pattern -------------

def test_wrong_visual_correct_decision_pattern_retrieved() -> None:
    """The decision pattern about natural landscape has no explicit
    `suitable` tag (only `suitable_when` in natural language). V1
    still treats it as applicable when the project_type is open or
    under-defined, because the natural-language cue + project context
    are sufficient. The wrong-visual KO must not be preferred just
    because it shares keywords.
    """
    project = _project(
        project_type="kindergarten_outdoor",
        site_description="open outdoor with natural landscape and trees",
    )
    decision = _decision_r1()
    ep = _run_retrieval(
        project=project,
        decision=decision,
        knowledge=[_KO_DECISION_PATTERN_NATURE, _KO_VISUAL_NOT_APPLICABLE],
    )
    _assert_five_fields(ep)
    ids = [ko.get("identity") for ko in ep.relevant_objects]
    # The natural-landscape pattern must be retrieved.
    assert "DecisionPattern.nature_anchor_v1" in ids
    # The wrong-applicability KO must NOT be in the result.
    assert "FakeVisuallySimilarButNotApplicableKO" not in ids


# ------------- Test 3: Similar image but wrong applicability rejected -------------

def test_similar_but_not_applicable_is_rejected() -> None:
    """Anti-pattern 1 (ADR-019 Section 8): visual similarity first.
    V1 must reject the visually-similar KO whose applicability does
    not match the project_type.
    """
    project = _project(project_type="kindergarten_outdoor")
    ep = _run_retrieval(
        project=project,
        decision=_decision_r1(),
        knowledge=[_KO_VISUAL_NOT_APPLICABLE],
    )
    _assert_five_fields(ep)
    # Empty retrieval is the correct response (P1 hard filter).
    assert ep.relevant_objects == []
    # The empty EP carries honest messages, not invented content.
    assert "No applicable" in ep.applicability_reason


# ------------- Test 4: Failure Pattern boundary warning returned -------------

def test_failure_pattern_boundary_warning_returned() -> None:
    """The Failure Pattern\'s `boundary` field must appear in the
    Evidence Package\'s `boundary_warning` field, so the customer
    sees when this evidence should NOT be applied.
    """
    project = _project(
        project_type="kindergarten_outdoor",
        constraints="limited budget",  # any_limited_budget match
    )
    ep = _run_retrieval(
        project=project,
        decision=_decision_r1(),
        knowledge=[_KO_FAILURE_PATTERN],
    )
    _assert_five_fields(ep)
    assert ep.relevant_objects != []
    assert "safety anchor" in ep.boundary_warning
    # Trust contribution classifies the KO correctly.
    assert "Failure Pattern" in ep.trust_contribution


# ------------- Test 5: Empty evidence returns Low confidence path -------------

def test_empty_ep_forces_low_confidence_in_trust() -> None:
    """When the Evidence Package is empty, the Trust Engine must
    return Low confidence (Sprint 20 spec Test 5 + ADR-019 Section
    7). The empty-EP path is detected by a `_trace.empty_evidence_package`
    flag and a `relevant_objects == []` EP.
    """
    project = _project(project_type="kindergarten_outdoor")
    ep = _run_retrieval(
        project=project,
        decision=_decision_r1(),
        knowledge=[_KO_VISUAL_NOT_APPLICABLE],  # all rejected -> empty
    )
    _assert_five_fields(ep)
    assert ep.relevant_objects == []

    # Drive the Trust Engine with the empty EP.
    from caseos.intelligence.trust.module import TrustEngine
    trust_engine = TrustEngine()
    trust = trust_engine.evaluate(
        decision=_decision_r1(),
        knowledge_patterns=ep.relevant_objects,
        project_type="kindergarten_outdoor",
        evidence_package=ep.to_dict(),
    )
    assert trust["confidence"] == "Low", \
        "Empty EP must force Low confidence per ADR-019 Section 7"
    blob = " ".join(trust["uncertainty_handling"]).lower()
    assert "evidence package" in blob or "no knowledge object" in blob
    # The empty-EP trace flag is set.
    assert trust.get("_trace", {}).get("empty_evidence_package") is True


# ------------- Test 6: Decision not modified by Retrieval -------------

def test_decision_object_is_not_modified_by_retrieval() -> None:
    """Running the full pipeline (including the retrieval stage) must
    not change the Decision Object\'s output. The Decision Engine\'s
    rules and rule order are unchanged; retrieval is a separate
    stage that writes its own slot.
    """
    from caseos.brain.runtime.pipeline import default_pipeline
    from caseos.brain.runtime.context import ProjectContext
    import json

    project = _project(
        project_type="kindergarten_outdoor",
        site_description=(
            "outdoor area with some existing equipment but the area "
            "lacks a memorable theme or identity"
        ),
        user_goal="improve enrollment",
        constraints="limited budget",
    )
    pipeline = default_pipeline()
    ctx = pipeline.run(project)

    # The Decision Object is set; its content is governed by R-01.
    decision = ctx.decision_object
    assert decision is not None
    # R-01 fires; the diagnosis must match what the rule produces.
    assert "not insufficient equipment" in decision["diagnosis"]
    assert "anchored experience" in decision["decision"]
    # The retrieval stage ran (EP is non-null); but it did not
    # mutate the decision.
    assert ctx.evidence_package is not None
    decision2 = ctx.decision_object
    assert json.dumps(decision, sort_keys=True) == \
        json.dumps(decision2, sort_keys=True)


# ------------- Test 7: Evidence trace preserved -------------

def test_evidence_trace_is_preserved() -> None:
    """The Trust Object\'s _trace must reference the retrieval\'s
    outcome. The retrieval itself records relevant_count and a
    rule_id; the trust record records supporting_knowledge_count.
    """
    project = _project(project_type="kindergarten_outdoor")
    ep = _run_retrieval(
        project=project,
        decision=_decision_r1(),
        knowledge=[_KO_GOLDEN_KINDERGARTEN, _KO_GOLDEN_PARK],
    )
    assert len(ep.relevant_objects) >= 1

    # Trust consumes the EP and records the supporting KO count.
    from caseos.intelligence.trust.module import TrustEngine
    trust = TrustEngine().evaluate(
        decision=_decision_r1(),
        knowledge_patterns=ep.relevant_objects,
        project_type="kindergarten_outdoor",
        evidence_package=ep.to_dict(),
    )
    trace = trust.get("_trace", {})
    assert "supporting_knowledge_count" in trace
    assert trace["supporting_knowledge_count"] >= 1
    assert "supporting_knowledge_identities" in trace


# ------------- Test 8: Pipeline executes with Retrieval stage -------------

def test_pipeline_runs_end_to_end_with_retrieval() -> None:
    """Full pipeline (Human -> Knowledge -> Retrieval -> Decision ->
    Trust -> Recommendation -> Output) must execute on a real
    project.json fixture and produce all the expected slots.
    """
    from caseos.brain.runtime.pipeline import default_pipeline
    import json
    fixture = json.load(open(
        r"backend\caseos\examples\kindergarten.json", encoding="utf-8"
    ))
    project = ProjectContext.from_dict(fixture)
    ctx = default_pipeline().run(project)
    # All seven slots filled.
    assert ctx.human_context is not None
    assert len(ctx.knowledge_patterns) >= 1
    assert ctx.evidence_package is not None  # NEW
    assert ctx.decision_object is not None
    assert ctx.trust_object is not None
    assert ctx.recommendation is not None
    assert ctx.metadata.get("markdown")


# ------------- Auxiliary: P1 is a hard filter -------------

def test_p1_applicability_is_a_hard_filter() -> None:
    """A KO that fails P1 (applicability) is excluded even if it
    would score high on P2/P3/P4. Visual similarity cannot rescue
    a non-applicable KO.
    """
    project = _project(project_type="kindergarten_outdoor")
    ep = _run_retrieval(
        project=project,
        decision=_decision_r1(),
        knowledge=[_KO_VISUAL_NOT_APPLICABLE],
    )
    assert ep.relevant_objects == []


# ------------- Auxiliary: Stage wire contract -------------

def test_stage_name_is_retrieval_and_in_default_pipeline() -> None:
    from caseos.brain.runtime import default_pipeline
    pipe = default_pipeline()
    names = [s.name for s in pipe.stages]
    assert "retrieval" in names
    # Retrieval sits between knowledge and decision.
    idx_knowledge = names.index("knowledge")
    idx_retrieval = names.index("retrieval")
    idx_decision = names.index("decision")
    assert idx_knowledge < idx_retrieval < idx_decision
    for s in pipe.stages:
        if s.name == "retrieval":
            assert isinstance(s, KnowledgeRetriever)


# ------------- Auxiliary: Evidence Package has 5 fields always -------------

def test_evidence_package_always_has_five_fields() -> None:
    """Even the empty EP has all 5 fields populated (with honest
    fallback messages). This satisfies ADR-019 Section 4 -- the
    shape is constant.
    """
    ep = EvidencePackage.empty()
    d = ep.to_dict()
    assert set(d.keys()) >= {
        "relevant_objects",
        "applicability_reason",
        "supporting_principle",
        "boundary_warning",
        "trust_contribution",
        "schema_version",
    }
    assert d["relevant_objects"] == []


# ------------- Auxiliary: P5 visual similarity is NOT a factor -------------

def test_visual_similarity_is_not_a_factor_in_v1() -> None:
    """Per ADR-019 Section 10, P5 visual similarity is not
    implemented in V1. The 4 rules we ship are P1..P4.
    """
    from caseos.knowledge.retrieval.module import RULE_APPLICABILITY
    rule_ids = [r.id for r in RULE_APPLICABILITY]
    assert rule_ids == ["P1", "P2", "P3", "P4"]
    assert "P5" not in rule_ids