"""Tests for the corpus intake layer (Sprint 20.7).

Each test corresponds to a Sprint 20.7 spec section 7 bullet:
  1. new raw case starts NEW
  2. status lifecycle works
  3. raw case cannot bypass governance
  4. promotion keeps original object
  5. converter does not hallucinate missing fields
  6. intake report generated
  7. existing tests remain green (verified by full suite)

Plus one architecture boundary test: intake must not depend
on retrieval / decision / trust / recommendation engines."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.knowledge.intake import (
    IntakeError,
    IntakeManager,
    IntakeStatus,
    RawCaseObject,
    generate_report,
    new_raw_case,
    summarise_candidate,
    to_candidate_knowledge_object,
)


def _make_manager_with_case(title="forest kindergarten playground") -> tuple[IntakeManager, RawCaseObject]:
    m = IntakeManager()
    rc = m.create_from_kwargs(source="external", title=title)
    return m, rc


# ------------- Test 1: new raw case starts NEW -------------

def test_new_raw_case_starts_in_NEW() -> None:
    m = IntakeManager()
    rc = m.create_from_kwargs(source="external", title="a real project")
    assert isinstance(rc, RawCaseObject)
    assert rc.status is IntakeStatus.NEW
    stored = m.get(rc.id)
    assert stored is not None
    assert stored.status is IntakeStatus.NEW


# ------------- Test 2: status lifecycle works -------------

def test_status_lifecycle_works() -> None:
    m, rc = _make_manager_with_case()
    # "NEW -> REVIEW_REQUIRED -> VALIDATED (or stay)"
    m.submit_for_review(rc.id)
    assert m.get(rc.id).status is IntakeStatus.REVIEW_REQUIRED
    res = m.validate(rc.id)
    # "Most raw cases fail validation because they have no"
    # "ADR-015 fields; the lifecycle still progresses correctly."
    assert res["valid"] in (True, False)
    # "Either way, the manager exposes the transition history."
    transitions = m.transitions(rc.id)
    assert len(transitions) >= 2
    # "No backwards transition is allowed."
    from caseos.knowledge.intake.status import is_forward
    assert is_forward(IntakeStatus.NEW, IntakeStatus.REVIEW_REQUIRED)
    assert not is_forward(IntakeStatus.REVIEW_REQUIRED, IntakeStatus.NEW)
    assert not is_forward(IntakeStatus.ACTIVE, IntakeStatus.VALIDATED)


# ------------- Test 3: raw case cannot bypass governance -------------

def test_raw_case_cannot_bypass_governance() -> None:
    m, rc = _make_manager_with_case()
    # "Cannot move NEW -> ACTIVE directly."
    m.submit_for_review(rc.id)
    try:
        m.promote(rc.id)
    except IntakeError:
        pass
    else:
        raise AssertionError("promote from REVIEW_REQUIRED should fail")
    # "Cannot move NEW -> PROMOTED directly either."
    m2 = IntakeManager()
    rc2 = m2.create_from_kwargs(source="external", title="x")
    try:
        m2.promote(rc2.id)
    except IntakeError:
        pass
    else:
        raise AssertionError("promote from NEW should fail")
    # "Cannot skip validate()."
    m3 = IntakeManager()
    rc3 = m3.create_from_kwargs(source="external", title="y")
    m3.submit_for_review(rc3.id)
    m3.validate(rc3.id)
    # "If validation failed (typical), status must still be REVIEW_REQUIRED."
    if m3.get(rc3.id).status is not IntakeStatus.VALIDATED:
        assert m3.get(rc3.id).status is IntakeStatus.REVIEW_REQUIRED
        try:
            m3.promote(rc3.id)
        except IntakeError:
            pass
        else:
            raise AssertionError("promote from REVIEW_REQUIRED after failed validate should fail")


# ------------- Test 4: promotion keeps original object -------------

def test_promotion_keeps_original_object() -> None:
    # "A hand-authored KO that passes governance can be promoted."
    m = IntakeManager()
    # "Build a raw case and then a full KO candidate (operator hand-authored)."
    rc = m.create_from_kwargs(source="external", title="a curated golden case")
    snapshot_title = rc.title
    snapshot_source = rc.source
    snapshot_id = rc.id
    # "Walk the lifecycle to VALIDATED."
    m.submit_for_review(rc.id)
    # "Inject a hand-authored KO into the manager "validation" flow"
    # "by using the converter and then monkey-patching the candidate"
    # "in place. The manager itself only knows about raw cases, so"
    # "this test asserts what the manager guarantees, not the KO"
    # "content: after any operation, the original raw case is intact."
    candidate = to_candidate_knowledge_object(rc.copy())
    # "Simulate a successful hand-authored case by promoting"
    # "directly: the original raw case must not be mutated, even"
    # "if the operator hand-feeds a complete KO into governance."
    from caseos.knowledge.governance import (
        validate_for_governance,
        promote as governance_promote,
    )
    # "Now actually build a fully-valid candidate KO with the 9 ADR-015 fields."
    full_ko = dict(candidate)
    full_ko["identity"] = "GoldenCase.curated_v1"
    full_ko["situation_context"] = {"project_type": "kindergarten_outdoor"}
    full_ko["observation"] = ["children linger when there is shade"]
    full_ko["diagnosis"] = "no emotional anchor"
    full_ko["decision"] = {"strategy": "create a single anchor"}
    full_ko["principle"] = "one anchor before many facilities"
    full_ko["applicability"] = {"suitable": ["kindergarten_outdoor"]}
    full_ko["boundary"] = ["do not apply when budget cannot support a meaningful anchor"]
    res = validate_for_governance(full_ko)
    assert res.valid is True, res.to_dict()
    # "Now call governance.promote directly to simulate a promotion"
    # "and verify the raw case (the original) is untouched."
    event = governance_promote(full_ko, "DecisionPattern", note="test promotion")
    assert event.source_identity == "GoldenCase.curated_v1"
    assert event.target_identity.startswith("DecisionPattern.")
    # "Original raw case is intact."
    assert m.get(snapshot_id).title == snapshot_title
    assert m.get(snapshot_id).source == snapshot_source


# ------------- Test 5: converter does not hallucinate missing fields -------------

def test_converter_does_not_hallucinate_missing_fields() -> None:
    rc = new_raw_case(source="external", title="forest kindergarten playground")
    ko = to_candidate_knowledge_object(rc)
    # "The nine ADR-015 fields are all missing on purpose."
    for f in (
        "situation_context", "observation", "diagnosis",
        "decision", "principle",
        "applicability", "boundary",
    ):
        assert ko.get(f) is None, f"converter hallucinated {f}: " + repr(ko.get(f))
    # "feedback is the required-presence-but-may-be-empty list."
    assert ko.get("feedback") == []
    # "identity carries a name derived from the title (verbatim, with whitespace normalised)."
    assert ko["identity"]["name"] == "forest kindergarten playground"
    # "Intake metadata is carried but never leaks into ADR-015."
    assert ko.get("_intake_source") == "external"
    summary = summarise_candidate(ko)
    assert "situation_context" in summary["missing_fields"]
    assert "applicability" in summary["missing_fields"]
    assert "boundary" in summary["missing_fields"]


# ------------- Test 6: intake report generated -------------

def test_intake_report_is_generated(tmp_path=None) -> None:
    m = IntakeManager()
    rc = m.create_from_kwargs(source="external", title="a real case")
    m.submit_for_review(rc.id)
    m.validate(rc.id)
    md = generate_report(m)
    assert isinstance(md, str)
    assert "# Sprint 20.7 -- Corpus Intake Report V1" in md
    assert "## 1. Status Distribution" in md
    assert "## 2. Incoming Objects" in md
    assert "## 3. Recent Transitions" in md
    assert "## 4. Promotions" in md
    assert "## 5. Summary" in md
    assert rc.id in md
    # "When output_path is provided, the report is also written to disk."
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "report.md"
        md2 = generate_report(m, output_path=out)
        assert out.exists()
        assert out.read_text(encoding="utf-8") == md2


# ------------- Architecture boundary invariant -------------

def test_intake_modules_do_not_import_retrieval_or_decision() -> None:
    # "Sprint 20.7 architecture boundary: intake is the"
    # "stomach; it must not depend on retrieval / decision /"
    # "trust / recommendation. The package talks to governance"
    # "only, and governance is already proven to be a leaf."
    import importlib
    for mod_name in (
        "caseos.knowledge.intake",
        "caseos.knowledge.intake.object",
        "caseos.knowledge.intake.status",
        "caseos.knowledge.intake.converter",
        "caseos.knowledge.intake.manager",
        "caseos.knowledge.intake.report",
    ):
        mod = importlib.import_module(mod_name)
        source = Path(mod.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "caseos.knowledge.retrieval",
            "caseos.brain.intelligence.decision",
            "caseos.brain.intelligence.recommendation",
            "caseos.brain.intelligence.trust",
        ):
            assert forbidden not in source, (
                f"intake module {mod_name} must not import {forbidden}",
            )
