"""Golden Case Intelligence Pipeline V1 (Sprint 18).

End-to-end orchestration of the six stages::

    Image
        -> CaseInput               (Stage 1, file-level)
        -> RawCaseUnderstanding    (Stage 2, Vision Engine)
        -> CKODraft                (Stage 3, deterministic extraction)
        -> [Reviewable]            (Reviewer enters here)
        -> CaseEvaluation          (Stage 4, manual scoring)
        -> Reviewed                (Stage 5, state machine)
        -> GoldenCase              (Stage 6, persistence-ready JSON)

Acceptance::

    A single external case image can complete:
        Image
        -> CKO Draft
        -> Evaluation
        -> Review
        -> Golden Case

The pipeline deliberately keeps three stages human-driven:

  * Evaluation scoring (Stage 4) -- no AI auto-score.
  * Approval / rejection (Stage 5) -- a human Reviewer decides.
  * Case-id assignment (Stage 6) -- the Reviewer picks it.

The pipeline surfaces failures as ``PipelineResult.errors`` so
callers can decide whether to retry, escalate or drop the case.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .analyzer import CaseImageAnalyzer
from .evaluator import CaseEvaluator, EvaluationValidationError
from .extractor import CKODraftExtractor
from .models import (
    CaseInput,
    CaseEvaluation,
    CKODraft,
    GoldenCase,
    PipelineResult,
    RawCaseUnderstanding,
    ReviewStatus,
    ReviewVerdict,
)
from .reviewer import CaseReviewer, ReviewStateError


class GoldenCasePipeline:
    """The complete V1 pipeline.

    Construct once, reuse for many cases. The Vision analyzer and the
    component objects are passed in so tests can swap them for
    stubs.

    Usage::

        pipeline = GoldenCasePipeline(
            vision_analyzer=build_vision_analyzer(),
        )
        result = pipeline.start(
            CaseInput(image_path="...", source="...", project_type="kindergarten"),
            evaluation_payload={...},
        )
        # result is in REVIEWING status at this point.
        verdict, golden = pipeline.approve(
            result,
            case_id="CKO-0002",
            reviewer="alice",
            note="Looks good.",
        )
    """

    STAGE_INPUT = "stage_1_input"
    STAGE_VISION = "stage_2_vision"
    STAGE_EXTRACT = "stage_3_extract"
    STAGE_EVALUATE = "stage_4_evaluate"
    STAGE_REVIEW = "stage_5_review"
    STAGE_GOLDEN = "stage_6_golden"

    def __init__(
        self,
        vision_analyzer: Any,
        *,
        analyzer: CaseImageAnalyzer | None = None,
        extractor: CKODraftExtractor | None = None,
        evaluator: CaseEvaluator | None = None,
        reviewer: CaseReviewer | None = None,
    ) -> None:
        self._analyzer = analyzer or CaseImageAnalyzer(vision_analyzer)
        self._extractor = extractor or CKODraftExtractor()
        self._evaluator = evaluator or CaseEvaluator()
        self._reviewer = reviewer or CaseReviewer()

    # ------------------------------------------------------------------
    # Stage orchestration
    # ------------------------------------------------------------------

    def start(
        self,
        case_input: CaseInput,
        evaluation_payload: dict[str, Any],
    ) -> PipelineResult:
        """Run Stages 1-4, leaving the case in REVIEWING status.

        The caller then calls ``approve`` (success), ``reject``
        (failure) or ``modify_*`` to make further changes.

        Raises nothing: every error is recorded in
        ``result.errors`` so the caller can decide what to do.
        """
        result = PipelineResult(case_input=case_input)

        # Stage 1 input validation -- the dataclass already validates
        # non-empty fields, but the image existence check is left to
        # the analyzer (Stage 2) to keep one error point.
        result.stage_reached = self.STAGE_INPUT

        # Stage 2 -- Vision.
        try:
            raw = self._analyzer.analyze(case_input)
        except FileNotFoundError as exc:
            return self._fail(
                result,
                stage=self.STAGE_VISION,
                message=f"Image not found: {exc}",
            )
        except Exception as exc:  # noqa: BLE001 -- catch network / model errors
            return self._fail(
                result,
                stage=self.STAGE_VISION,
                message=f"Vision Engine failed: {exc}",
            )
        result.raw_understanding = raw
        result.stage_reached = self.STAGE_VISION

        # Stage 3 -- extraction (deterministic).
        try:
            draft = self._extractor.extract(raw, case_input)
        except Exception as exc:  # noqa: BLE001
            return self._fail(
                result,
                stage=self.STAGE_EXTRACT,
                message=f"Extractor failed: {exc}",
            )
        result.cko_draft = draft
        result.stage_reached = self.STAGE_EXTRACT

        # Stage 4 -- evaluation.
        try:
            evaluation = self._evaluator.evaluate(evaluation_payload)
        except EvaluationValidationError as exc:
            return self._fail(
                result,
                stage=self.STAGE_EVALUATE,
                message=f"Evaluation invalid: {exc}",
            )
        except Exception as exc:  # noqa: BLE001
            return self._fail(
                result,
                stage=self.STAGE_EVALUATE,
                message=f"Evaluator errored: {exc}",
            )
        result.evaluation = evaluation

        # Open the Review (Stage 5) automatically. A reviewer still
        # needs to call ``approve`` / ``reject`` -- the data flows
        # in REVIEWING until the human decides.
        verdict = ReviewVerdict(status=ReviewStatus.DRAFT)
        try:
            self._reviewer.start_review(verdict, reviewer="system")
        except ReviewStateError as exc:
            return self._fail(
                result,
                stage=self.STAGE_REVIEW,
                message=f"Failed to open review: {exc}",
            )
        result.review = verdict
        result.stage_reached = self.STAGE_REVIEW
        result.success = True
        # Keep the evaluation reachable from the verdict for downstream
        # consumers by attaching it on the modifications trail.
        verdict.modifications.append(
            {
                "kind": "evaluation_attached",
                "author": "system",
                "tier": evaluation.tier,
                "total_score": evaluation.total_score,
            }
        )
        return result

    # ------------------------------------------------------------------
    # Human-in-the-loop entry points (operate on an existing result)
    # ------------------------------------------------------------------

    def approve(
        self,
        result: PipelineResult,
        *,
        case_id: str,
        reviewer: str,
        note: str = "Approved.",
    ) -> ReviewVerdict:
        """Approve the case and produce a GoldenCase.

        Mutates ``result.review`` to APPROVED and writes the new
        GoldenCase back into ``result.golden_case``. Returns the
        verdict for caller convenience.
        """
        self._require_ready_for_review(result)
        draft = result.cko_draft
        evaluation = result.evaluation
        assert draft is not None
        assert evaluation is not None
        try:
            verdict, golden = self._reviewer.approve(
                result.review,  # type: ignore[arg-type]
                cko_draft=draft,
                evaluation=evaluation,
                case_id=case_id,
                reviewer=reviewer,
                note=note,
            )
        except ReviewStateError as exc:
            return self._fail(
                result,
                stage=self.STAGE_GOLDEN,
                message=f"Approval failed: {exc}",
            ).review  # type: ignore[return-value]
        result.golden_case = golden
        result.stage_reached = self.STAGE_GOLDEN
        result.success = True
        return verdict

    def reject(
        self,
        result: PipelineResult,
        *,
        reviewer: str,
        note: str = "Rejected.",
    ) -> ReviewVerdict:
        """Reject the case and mark the pipeline as completed-but-not-golden."""
        self._require_ready_for_review(result)
        try:
            verdict = self._reviewer.reject(
                result.review,  # type: ignore[arg-type]
                reviewer=reviewer,
                note=note,
            )
        except ReviewStateError as exc:
            return self._fail(
                result,
                stage=self.STAGE_REVIEW,
                message=f"Rejection failed: {exc}",
            ).review  # type: ignore[return-value]
        result.success = False
        result.stage_reached = self.STAGE_REVIEW
        return verdict

    def modify_cko(
        self,
        result: PipelineResult,
        changes: dict[str, Any],
        reviewer: str,
        note: str = "CKO modified.",
    ) -> CKODraft:
        """Apply a CKO modification through the reviewer."""
        self._require_ready_for_review(result)
        return self._reviewer.modify_cko(
            result.review,  # type: ignore[arg-type]
            result.cko_draft,  # type: ignore[arg-type]
            changes=changes,
            reviewer=reviewer,
            note=note,
        )

    def modify_evaluation(
        self,
        result: PipelineResult,
        new_payload: dict[str, Any],
        reviewer: str,
        note: str = "Evaluation modified.",
    ) -> CaseEvaluation:
        """Replace the evaluation payload after re-validation."""
        self._require_ready_for_review(result)
        new_evaluation = self._evaluator.evaluate(new_payload)
        result.evaluation = self._reviewer.modify_evaluation(
            result.review,  # type: ignore[arg-type]
            new_evaluation,
            reviewer=reviewer,
            note=note,
        )
        return result.evaluation

    # ------------------------------------------------------------------
    # Persistence helpers (Stage 6)
    # ------------------------------------------------------------------

    @staticmethod
    def save_golden_case(golden: GoldenCase, target_path: str | Path) -> Path:
        """Write a Golden Case to disk as UTF-8 JSON (no BOM).

        The output file is the canonical Stage 6 artifact and can be
        loaded directly by the CKO Validator or the future Retrieval
        Engine.
        """
        import json
        from pathlib import Path as _P

        target = _P(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(golden.to_json(), indent=2, ensure_ascii=False)
        target.write_text(text, encoding="utf-8")
        return target

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _require_ready_for_review(result: PipelineResult) -> None:
        if result.review is None or result.cko_draft is None or result.evaluation is None:
            raise RuntimeError(
                "PipelineResult is not ready for review; "
                f"reached stage={result.stage_reached}, "
                f"errors={result.errors}"
            )

    @staticmethod
    def _fail(result: PipelineResult, *, stage: str, message: str) -> PipelineResult:
        # stage_reached is the most recent stage ATTEMPTED,
        # successful or not. On failure that is the failing stage.
        result.success = False
        result.stage_reached = stage
        result.errors.append(f"[{stage}] {message}")
        return result


__all__ = ["GoldenCasePipeline"]
