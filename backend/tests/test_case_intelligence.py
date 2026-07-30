"""Sprint 18 acceptance test -- Golden Case Intelligence Pipeline V1.

Acceptance::

    A single external case image can complete:
        Image -> CKO Draft -> Evaluation -> Review -> Golden Case

Plus the six required scenarios:

    1. create CKO draft
    2. evaluation data validation
    3. reviewer approve
    4. reviewer reject
    5. invalid case handling
    6. pipeline failure handling

No network. No real Vision API. No real LLM. Pure local pipeline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import pytest  # isort: skip  -- intentionally local-imported

from app.core.case_intelligence import (
    CaseEvaluator,
    CaseImageAnalyzer,
    CaseInput,
    CaseReviewer,
    CKODraft,
    CKODraftExtractor,
    CaseEvaluation,
    EvaluationValidationError,
    GoldenCasePipeline,
    ReviewNote,
    ReviewStateError,
    ReviewStatus,
    ReviewVerdict,
    Transferability,
)
from app.services.vision.analyzer import VisionAnalyzer


# ---------------------------------------------------------------------------
# Stub VisionAnalyzer (no network / no LLM)
# ---------------------------------------------------------------------------


class StubVisionAnalyzer(VisionAnalyzer):
    """A vision analyzer that returns a pre-canned V3 payload.

    Used by every test so we never hit a network or model.
    """

    PAYLOAD = {
        "basic_info": {
            "project_name": "Forest Adventure Park",
            "case_id": "STUB-001",
            "site_type": "SITE.PUBLIC_PARK",
            "country": "NL",
            "city": "Utrecht",
        },
        "design": {
            "theme": [
                {"id": "NATURE.FOREST", "role": "primary", "confidence": 0.92}
            ],
            "style": ["STYLE.ORGANIC"],
            "design_highlights": [
                "Treehouse with rope bridge",
                "Sensory garden path",
            ],
        },
        "target_users": {"age_group": ["AGE.3_6", "AGE.6_9"]},
        "play_experience": {"play_behaviors": ["PLAY.CLIMB", "PLAY.EXPLORE"]},
        "equipment": {"functional_units": ["UNIT.CLIMBING", "UNIT.SLIDE"]},
        "materials": {"main_materials": ["MATERIAL.WOOD", "MATERIAL.ROPE"]},
        "color": {"colors": ["COLOR.NATURAL"]},
        "ai_analysis": {
            "keywords": ["forest", "treehouse", "nature"],
        },
    }

    def analyze(self, image_path: str) -> dict:
        # Pretend we ran vision. Return a copy so callers cannot mutate
        # the shared stub payload.
        return json.loads(json.dumps(self.PAYLOAD))


def _write_dummy_image(tmp_path: Path, name: str = "case.jpg") -> Path:
    """Write a tiny file so ``analyzer`` sees a real file on disk.

    The Stub does not read the bytes; it just needs the file to exist.
    """
    p = tmp_path / name
    p.write_bytes(b"\xff\xd8\xff\xe0stub-jpeg")  # JPEG magic-like bytes
    return p


def _eval_payload(**overrides):
    """A valid ADR-012 payload for the Forest park (Candidate Golden)."""
    payload = CaseEvaluator.payload_from_scores(
        space=22,
        experience=23,
        theme=16,
        user=13,
        commercial=7,  # 22+23+16+13+7 = 81 -> Candidate Golden
        level="high",
        applicable_project_types=["public_park", "school", "kindergarten"],
        limitations=["requires mature trees", "rope needs maintenance"],
    )
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# Acceptance -- end-to-end
# ---------------------------------------------------------------------------


def test_acceptance_image_to_golden_case(tmp_path):
    """Acceptance: Image -> CKO Draft -> Evaluation -> Review -> Golden Case."""
    image = _write_dummy_image(tmp_path)
    pipeline = GoldenCasePipeline(vision_analyzer=StubVisionAnalyzer())

    result = pipeline.start(
        CaseInput(
            image_path=str(image),
            source="CaseOS stub archive (test)",
            project_type="public_park",
        ),
        evaluation_payload=_eval_payload(),
    )

    # Stages 1-4 complete; the review is opened automatically.
    assert result.success, f"start() failed: {result.errors}"
    assert result.stage_reached == GoldenCasePipeline.STAGE_REVIEW
    assert result.raw_understanding is not None
    assert result.cko_draft is not None
    assert result.evaluation is not None
    assert result.evaluation.tier == "candidate_golden"
    assert result.review is not None
    assert result.review.status == ReviewStatus.REVIEWING
    assert result.golden_case is None  # not approved yet

    # Stage 5/6: the reviewer approves.
    verdict = pipeline.approve(
        result,
        case_id="CKO-0042",
        reviewer="alice",
        note="Spot on.",
    )
    assert verdict.status == ReviewStatus.APPROVED
    assert result.success
    assert result.golden_case is not None
    assert result.golden_case.case_id == "CKO-0042"

    # Sections 0-9 are all populated.
    cko = result.golden_case.cko
    assert cko["case_identity"]["case_id"] == "CKO-0042"
    assert cko["case_identity"]["knowledge_source"] == "external_excellent_case"
    assert cko["case_evaluation"]["total_score"] == 81
    assert cko["case_evaluation"]["transferability"]["level"] == "high"
    # Sections 7 and 8 are stubbed (pending reviewer completion).
    assert cko["professional_evaluation"]["_pending_reviewer_completion"] is True
    assert cko["learning_value"]["_pending_reviewer_completion"] is True

    # Persistence helper writes a file we can re-load.
    target = tmp_path / "CKO-0042.json"
    written = GoldenCasePipeline.save_golden_case(result.golden_case, target)
    assert written.exists()
    on_disk = json.loads(written.read_text(encoding="utf-8"))
    assert on_disk["case_id"] == "CKO-0042"


# ---------------------------------------------------------------------------
# Scenario 1 -- create CKO draft
# ---------------------------------------------------------------------------


def test_create_cko_draft_from_vision_payload(monkeypatch):
    """The extractor turns a V3 payload into a populated CKODraft."""
    # Skip the file-existence check so this test does not need a tmp image.
    monkeypatch.setattr(
        "app.core.case_intelligence.analyzer.Path.is_file",
        lambda self: True,
    )
    vision = StubVisionAnalyzer()
    raw_obj = CaseImageAnalyzer(vision).analyze(
        CaseInput(image_path="/tmp/x.jpg", source="manual", project_type="public_park")
    )
    draft = CKODraftExtractor().extract(
        raw_obj,
        CaseInput(image_path="/tmp/x.jpg", source="manual", project_type="public_park"),
    )

    # Section 0
    assert draft.case_id == "PENDING"
    assert draft.knowledge_source == "external_excellent_case"
    assert draft.project_type == "public_park"
    assert draft.title == "Forest Adventure Park"

    # Section 2
    assert draft.existing_elements  # equipment.functional_units
    assert draft.environmental_relationship == "SITE.PUBLIC_PARK"

    # Section 3
    assert "wonder" in draft.emotional_response or "forest" in draft.atmosphere

    # Sections 7-9 are intentionally None.
    assert draft.professional_evaluation is None
    assert draft.learning_value is None
    assert draft.case_evaluation is None

    # to_cko_dict serialises sections 0-6.
    blob = draft.to_cko_dict()
    assert "case_identity" in blob
    assert "recommendation_logic" in blob
    assert blob["case_identity"]["case_id"] == "PENDING"


# ---------------------------------------------------------------------------
# Scenario 2 -- evaluation data validation
# ---------------------------------------------------------------------------


def test_evaluation_validation_rejects_out_of_range_and_mismatch():
    """The evaluator rejects bad scores and total mismatches."""
    evaluator = CaseEvaluator()

    # Out of range -> rejected.
    bad = _eval_payload(space_logic_score=99)  # bigger than 25 allowed
    with pytest.raises(EvaluationValidationError):
        evaluator.evaluate({k: v for k, v in bad.items() if k != "total_score"} | {"total_score": 99})

    # Mismatched total -> rejected.
    mismatched = _eval_payload()
    mismatched["total_score"] = 999  # 81 vs 999
    with pytest.raises(EvaluationValidationError):
        evaluator.evaluate(mismatched)

    # Happy path -> accepted.
    good = _eval_payload()
    evaluation = evaluator.evaluate(good)
    assert evaluation.total_score == 81
    assert evaluation.tier == "candidate_golden"


def test_evaluation_validation_rejects_empty_transferability_lists():
    evaluator = CaseEvaluator()
    bad = _eval_payload()
    bad["transferability"]["limitations"] = []  # required non-empty
    with pytest.raises(EvaluationValidationError):
        evaluator.evaluate(bad)

    bad = _eval_payload()
    bad["transferability"]["applicable_project_types"] = []
    with pytest.raises(EvaluationValidationError):
        evaluator.evaluate(bad)

    bad = _eval_payload()
    bad["transferability"]["level"] = "ULTRA"
    with pytest.raises(EvaluationValidationError):
        evaluator.evaluate(bad)


# ---------------------------------------------------------------------------
# Scenario 3 -- reviewer approve
# ---------------------------------------------------------------------------


def test_reviewer_approve_produces_golden_case(tmp_path):
    reviewer = CaseReviewer()
    verdict = ReviewVerdict(status=ReviewStatus.DRAFT)
    reviewer.start_review(verdict, reviewer="alice", note="Go.")

    # Build a CKODraft and an evaluation manually.
    raw = CaseImageAnalyzer(StubVisionAnalyzer()).analyze(
        CaseInput(image_path=str(_write_dummy_image(tmp_path)), source="t")
    )
    draft = CKODraftExtractor().extract(raw, CaseInput(image_path=str(_write_dummy_image(tmp_path)), source="t"))
    evaluation = CaseEvaluator().evaluate(_eval_payload())

    final, golden = reviewer.approve(
        verdict,
        cko_draft=draft,
        evaluation=evaluation,
        case_id="CKO-0100",
        reviewer="alice",
    )
    assert final.status == ReviewStatus.APPROVED
    assert golden.case_id == "CKO-0100"
    assert golden.cko["case_identity"]["case_id"] == "CKO-0100"
    assert golden.evaluation.total_score == 81


def test_reviewer_approve_rejects_invalid_case_id(tmp_path):
    reviewer = CaseReviewer()
    verdict = ReviewVerdict(status=ReviewStatus.DRAFT)
    reviewer.start_review(verdict, reviewer="alice")

    raw = CaseImageAnalyzer(StubVisionAnalyzer()).analyze(
        CaseInput(image_path=str(_write_dummy_image(tmp_path)), source="t")
    )
    draft = CKODraftExtractor().extract(raw, CaseInput(image_path=str(_write_dummy_image(tmp_path)), source="t"))
    evaluation = CaseEvaluator().evaluate(_eval_payload())

    with pytest.raises(ReviewStateError):
        reviewer.approve(
            verdict,
            cko_draft=draft,
            evaluation=evaluation,
            case_id="bad-id",
            reviewer="alice",
        )


# ---------------------------------------------------------------------------
# Scenario 4 -- reviewer reject
# ---------------------------------------------------------------------------


def test_reviewer_reject_terminates_review():
    reviewer = CaseReviewer()
    verdict = ReviewVerdict(status=ReviewStatus.DRAFT)
    reviewer.start_review(verdict, reviewer="bob", note="Starting.")

    final = reviewer.reject(verdict, reviewer="bob", note="Image too low-res.")
    assert final.status == ReviewStatus.REJECTED
    assert final.reviewed_at is not None
    # Notes are append-only.
    assert any("Starting" in n.note for n in final.notes)
    assert any("too low-res" in n.note for n in final.notes)


def test_reviewer_cannot_approve_from_draft(monkeypatch):
    # Skip the file-existence check so this test does not need a tmp image.
    monkeypatch.setattr(
        "app.core.case_intelligence.analyzer.Path.is_file",
        lambda self: True,
    )
    reviewer = CaseReviewer()
    verdict = ReviewVerdict(status=ReviewStatus.DRAFT)

    raw = CaseImageAnalyzer(StubVisionAnalyzer()).analyze(
        CaseInput(image_path="/tmp/x.jpg", source="t")
    )
    draft = CKODraftExtractor().extract(raw, CaseInput(image_path="/tmp/x.jpg", source="t"))
    evaluation = CaseEvaluator().evaluate(_eval_payload())

    with pytest.raises(ReviewStateError):
        reviewer.approve(
            verdict,
            cko_draft=draft,
            evaluation=evaluation,
            case_id="CKO-0001",
            reviewer="bob",
        )


# ---------------------------------------------------------------------------
# Scenario 5 -- invalid case handling
# ---------------------------------------------------------------------------


def test_invalid_case_handling_missing_image():
    """A missing image must surface as a recorded error, not a crash."""
    pipeline = GoldenCasePipeline(vision_analyzer=StubVisionAnalyzer())
    result = pipeline.start(
        CaseInput(
            image_path="/tmp/__definitely_does_not_exist__.jpg",
            source="manual",
            project_type="public_park",
        ),
        evaluation_payload=_eval_payload(),
    )
    assert result.success is False
    assert any("Image not found" in e for e in result.errors)
    assert result.golden_case is None


def test_invalid_case_handling_empty_source():
    """The dataclass refuses an empty source at construction."""
    with pytest.raises(ValueError):
        CaseInput(image_path="/tmp/x.jpg", source="")


def test_invalid_case_handling_empty_image_path():
    with pytest.raises(ValueError):
        CaseInput(image_path="", source="manual")


# ---------------------------------------------------------------------------
# Scenario 6 -- pipeline failure handling
# ---------------------------------------------------------------------------


class BrokenVisionAnalyzer(VisionAnalyzer):
    """A vision analyzer that raises a generic exception."""

    def analyze(self, image_path: str) -> dict:
        raise RuntimeError("simulated vision outage")


class BuggyEvaluator:
    """An evaluator that succeeds validation but raises a generic error.

    We bypass ``CaseEvaluator.evaluate`` to simulate a model/system
    failure mid-stage.
    """

    def evaluate(self, payload):  # noqa: D401 -- test stub
        raise RuntimeError("simulated evaluator crash")


def test_pipeline_failure_handling_vision_outage(tmp_path):
    pipeline = GoldenCasePipeline(vision_analyzer=BrokenVisionAnalyzer())
    image = _write_dummy_image(tmp_path)
    result = pipeline.start(
        CaseInput(image_path=str(image), source="t"),
        evaluation_payload=_eval_payload(),
    )
    assert result.success is False
    assert result.stage_reached == GoldenCasePipeline.STAGE_VISION
    assert any("Vision Engine failed" in e for e in result.errors)


def test_pipeline_failure_handling_bad_evaluation_payload(tmp_path):
    pipeline = GoldenCasePipeline(vision_analyzer=StubVisionAnalyzer())
    image = _write_dummy_image(tmp_path)
    bad = _eval_payload()
    bad["total_score"] = 999  # mismatch

    result = pipeline.start(
        CaseInput(image_path=str(image), source="t"),
        evaluation_payload=bad,
    )
    assert result.success is False
    assert result.stage_reached == GoldenCasePipeline.STAGE_EVALUATE
    assert any("Evaluation invalid" in e for e in result.errors)


def test_pipeline_failure_handling_evaluator_crash(tmp_path):
    pipeline = GoldenCasePipeline(
        vision_analyzer=StubVisionAnalyzer(),
        evaluator=BuggyEvaluator(),
    )
    image = _write_dummy_image(tmp_path)
    result = pipeline.start(
        CaseInput(image_path=str(image), source="t"),
        evaluation_payload=_eval_payload(),
    )
    assert result.success is False
    assert result.stage_reached == GoldenCasePipeline.STAGE_EVALUATE
    assert any("Evaluator errored" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Modifications (sanity, not part of the six required scenarios)
# ---------------------------------------------------------------------------


def test_modify_cko_logs_changes_through_reviewer(tmp_path):
    pipeline = GoldenCasePipeline(vision_analyzer=StubVisionAnalyzer())
    image = _write_dummy_image(tmp_path)

    result = pipeline.start(
        CaseInput(image_path=str(image), source="t"),
        evaluation_payload=_eval_payload(),
    )
    assert result.success

    pipeline.modify_cko(
        result,
        changes={"strategy": {"strategy_type": "journey", "spatial_organization": "updated."}},
        reviewer="alice",
        note="Switched to journey strategy.",
    )
    assert result.cko_draft.strategy_type == "journey"  # type: ignore[union-attr]
    assert any("Switched to journey" in n.note for n in result.review.notes)  # type: ignore[union-attr]
    assert any(m.get("kind") == "cko" for m in result.review.modifications)  # type: ignore[union-attr]
