"""
Tests for the corpus governance layer (Sprint 20.6).

Each test corresponds to a Sprint 20.6 spec section 7 bullet:
  1. invalid object without boundary rejected
  2. invalid object without applicability rejected
  3. duplicate objects detected
  4. trust tier assigned correctly
  5. promotion keeps original object
  6. governance report generated

All existing tests remain green (60/60 prior + 6 new).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.knowledge.governance import (
    DuplicateCandidate,
    GovernanceValidationResult,
    PromotionError,
    PromotionEvent,
    TrustTier,
    assign_trust_tier,
    detect_duplicates,
    generate_report,
    promote,
    validate_for_governance,
    verify_original_preserved,
)


def _valid_ko(**overrides) -> dict:
    "A minimal ADR-015 + governance-valid KO.",
    base = {
        "identity": "GoldenCase.theme_anchor_v1",
        "situation_context": {"project_type": "kindergarten_outdoor"},
        "observation": ["children pass through without lingering"],
        "diagnosis": "no emotional anchor",
        "decision": {"strategy": "create a single thematically anchored experience"},
        "principle": "create one memorable experience node before adding facilities",
        "applicability": {"suitable": ["kindergarten_outdoor"]},
        "boundary": ["do not apply when budget cannot support a meaningful anchor"],
        "feedback": [{"outcome": "stay_time_increased", "score": "positive"}],
    }
    base.update(overrides)
    return base


# ------------- Test 1: missing boundary rejected -------------

def test_invalid_object_without_boundary_is_rejected() -> None:
    ko = _valid_ko()
    del ko["boundary"]
    result = validate_for_governance(ko)
    assert result.valid is False
    assert "boundary" in result.base_missing
    assert any("mandatory" in e and "boundary" in e for e in result.base_errors)


# ------------- Test 2: missing applicability rejected -------------

def test_invalid_object_without_applicability_is_rejected() -> None:
    ko = _valid_ko()
    del ko["applicability"]
    result = validate_for_governance(ko)
    assert result.valid is False
    assert "applicability" in result.base_missing
    assert any("mandatory" in e and "applicability" in e for e in result.base_errors)



# ------------- Test 3: duplicate objects detected -------------

def test_duplicate_objects_are_detected() -> None:
    "Same identity string is a duplicate.",
    a = _valid_ko(identity="GoldenCase.theme_anchor_v1")
    b = _valid_ko(identity="GoldenCase.theme_anchor_v1")
    cands = detect_duplicates([a, b])
    assert len(cands) == 1
    cand = cands[0]
    assert isinstance(cand, DuplicateCandidate)
    assert cand.object_a == cand.object_b == "GoldenCase.theme_anchor_v1"
    assert "identity-collision" in cand.similarity_basis

    "Shared situation + decision keywords are flagged.",
    a2 = _valid_ko(
        identity="GoldenCase.alpha_v1",
        situation_context={"project_type": "kindergarten_outdoor"},
        decision={"strategy": "create an anchor"},
    )
    b2 = _valid_ko(
        identity="GoldenCase.beta_v1",
        situation_context={"project_type": "kindergarten_outdoor"},
        decision={"strategy": "create an anchor"},
    )
    overlap_cands = detect_duplicates([a2, b2])
    assert overlap_cands, "expected duplicate from keyword overlap"

    "Completely different KOs are not flagged.",
    c1 = _valid_ko(
        identity="GoldenCase.zoo_v1",
        situation_context={"project_type": "public_park"},
        decision={"strategy": "remove some pieces"},
    )
    c2 = _valid_ko(
        identity="GoldenCase.cinema_v1",
        situation_context={"project_type": "cultural_tourism"},
        decision={"strategy": "build a path"},
    )
    assert detect_duplicates([c1, c2]) == []


# ------------- Test 4: trust tier assigned correctly -------------

def test_trust_tier_is_assigned_correctly() -> None:
    ko_a = _valid_ko(source_reliability=["real-project-completed", "expert-verified"])
    a = assign_trust_tier(ko_a)
    assert a.tier is TrustTier.TIER_A, repr(a)
    assert a.is_default is False

    ko_b = _valid_ko(source_reliability=["real-project-completed"])
    b = assign_trust_tier(ko_b)
    assert b.tier is TrustTier.TIER_B, repr(b)

    ko_c = _valid_ko(source_reliability=["professional-case-reference"])
    c = assign_trust_tier(ko_c)
    assert c.tier is TrustTier.TIER_C, repr(c)

    for label in ("inspiration", "conceptual", "theoretical-assumption"):
        ko_d = _valid_ko(source_reliability=[label])
        d = assign_trust_tier(ko_d)
        assert d.tier is TrustTier.TIER_D, label + " -> " + repr(d)

    "No declared source_reliability -> identity-type default.",
    ko_default_gc = _valid_ko()
    default = assign_trust_tier(ko_default_gc)
    assert default.is_default is True
    assert default.tier is TrustTier.TIER_B

    ko_default_up = _valid_ko(identity="UserPreference.natural_v1")
    default_up = assign_trust_tier(ko_default_up)
    assert default_up.is_default is True
    assert default_up.tier is TrustTier.TIER_D



# ------------- Test 5: promotion keeps original object -------------

def test_promotion_preserves_original_object() -> None:
    source = _valid_ko()
    snapshot_identity = source["identity"]
    snapshot_principle = source["principle"]

    event = promote(source, "DecisionPattern", note="abstract the pattern")
    assert isinstance(event, PromotionEvent)
    assert event.source_type == "GoldenCase"
    assert event.target_type == "DecisionPattern"
    assert event.source_identity == snapshot_identity
    assert event.target_identity.startswith("DecisionPattern.")
    assert event.target_ko is not source
    assert source["identity"] == snapshot_identity
    assert source["principle"] == snapshot_principle
    assert verify_original_preserved(source, event) is True

    "A forbidden promotion raises PromotionError.",
    try:
        promote(source, "UserPreference")
    except PromotionError:
        pass
    else:
        raise AssertionError("expected PromotionError for UserPreference target")


# ------------- Test 6: governance report generated -------------

def test_governance_report_is_generated() -> None:
    from caseos.knowledge.objects.loader import DEFAULT_CORPUS_DIR
    md = generate_report(DEFAULT_CORPUS_DIR)
    assert isinstance(md, str)
    assert "# Sprint 20.6 -- Corpus Governance Report V1" in md
    assert "## 1. Objects by Identity Type" in md
    assert "## 2. Objects by Trust Tier" in md
    assert "## 3. Validation Result" in md
    assert "## 4. Duplicate Candidates" in md
    assert "## 5. Promotion Candidates" in md
    assert "## 6. Summary" in md
    assert "GoldenCase" in md
    assert "Tier_B" in md

    "When output_path is provided, the report is also written to disk.",
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "report.md"
        md2 = generate_report(DEFAULT_CORPUS_DIR, output_path=out)
        assert out.exists()
        assert out.read_text(encoding="utf-8") == md2


# ------------- Architectural invariant -------------

def test_governance_modules_do_not_import_retrieval_or_decision() -> None:
    "Governance is memory protection, not retrieval, not recommendation.",
    import importlib
    for mod_name in (
        "caseos.knowledge.governance",
        "caseos.knowledge.governance.validator",
        "caseos.knowledge.governance.duplicate",
        "caseos.knowledge.governance.trust_tier",
        "caseos.knowledge.governance.promotion",
        "caseos.knowledge.governance.report",
    ):
        mod = importlib.import_module(mod_name)
        source = Path(mod.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "caseos.knowledge.retrieval",
            "caseos.brain.intelligence.decision",
            "caseos.brain.intelligence.recommendation",
        ):
            assert forbidden not in source, ("forbidden: " + forbidden + " in " + mod_name + "")

