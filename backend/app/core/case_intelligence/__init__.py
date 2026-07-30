"""Golden Case Intelligence Pipeline V1 (Sprint 18).

Public surface::

    CaseInput                       stage 1  -- raw input
    RawCaseUnderstanding            stage 2  -- Vision Engine output
    CKODraft                        stage 3  -- CKO sections 0-6
    CaseEvaluation                  stage 4  -- ADR-012 weighted score
    ReviewStatus, ReviewVerdict     stage 5  -- state machine
    GoldenCase                      stage 6  -- approved CKO + audit trail
    GoldenCasePipeline              end-to-end orchestrator

Knowledge follows:

    knowledge/cases/schema/cko_schema_v1.md          (V1.2)
    docs/architecture/ADR-011-cko-learning-source-value-model.md
    docs/architecture/ADR-012-case-evaluation-score.md
"""

from .analyzer import CaseImageAnalyzer
from .evaluator import CaseEvaluator, EvaluationValidationError, TOLERANCE
from .extractor import CKODraftExtractor
from .models import (
    GOLDEN_THRESHOLDS,
    WEIGHTS,
    CaseEvaluation,
    CaseInput,
    CKODraft,
    GoldenCase,
    PipelineResult,
    RawCaseUnderstanding,
    ReviewNote,
    ReviewStatus,
    ReviewVerdict,
    Transferability,
)
from .pipeline import GoldenCasePipeline
from .reviewer import CaseReviewer, ReviewStateError, ReviewerIdentityRequiredError

__all__ = [
    # Stages
    "CaseInput",
    "RawCaseUnderstanding",
    "CKODraft",
    "CaseEvaluation",
    "Transferability",
    "ReviewStatus",
    "ReviewNote",
    "ReviewVerdict",
    "GoldenCase",
    "PipelineResult",
    # Engines
    "CaseImageAnalyzer",
    "CKODraftExtractor",
    "CaseEvaluator",
    "CaseReviewer",
    "GoldenCasePipeline",
    # Errors + constants
    "EvaluationValidationError",
    "ReviewStateError",
    "ReviewerIdentityRequiredError",
    "TOLERANCE",
    "WEIGHTS",
    "GOLDEN_THRESHOLDS",
]
