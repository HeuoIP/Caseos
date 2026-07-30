"""Data models for the Golden Case Intelligence Pipeline V1.

Stage-mapped to the six pipeline stages from the Sprint 18 task:

  Stage 1  CaseInput                       (input)
  Stage 2  RawCaseUnderstanding            (Vision Engine output, schema-shaped)
  Stage 3  CKODraft                        (sections 0-6 only, sections 7-9 empty)
  Stage 4  CaseEvaluation, Transferability (ADR-012 weighted + transferability)
  Stage 5  ReviewStatus, ReviewVerdict     (state machine)
  Stage 6  GoldenCase                      (approved + persisted output)

Every model is a plain dataclass; no Pydantic. The pipeline stays
re-usable by scripts, tests, and the future FastAPI surface.

The CKO fields here are aligned with:

  ``knowledge/cases/schema/cko_schema_v1.md``          (V1.2, 2026-07-30)
  ``docs/architecture/ADR-011-cko-learning-source-value-model.md``
  ``docs/architecture/ADR-012-case-evaluation-score.md``

Naming conventions
  * ``*Score``      -- a 0..max float per ADR-012 weight.
  * ``Transferability`` -- the separate object, NOT in total_score.
  * ``Review*``     -- the reviewer state machine.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Stage 1 -- Input
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CaseInput:
    """Stage 1 input: a single external case image plus provenance.

    `image_path` must point to a file readable by the Vision Engine.
    `source` is the human-readable provenance string required by
    CKO Section 0.case_identity.source.
    `project_type` is optional; the pipeline accepts None and the
    CKODraft defaults to "other" per ADR-011 / project_types taxonomy.
    """

    image_path: str
    source: str
    project_type: str | None = None

    def __post_init__(self) -> None:
        if not self.image_path:
            raise ValueError("CaseInput.image_path must not be empty")
        if not self.source:
            raise ValueError("CaseInput.source must not be empty")


# ---------------------------------------------------------------------------
# Stage 2 -- Raw Vision Output
# ---------------------------------------------------------------------------


@dataclass
class RawCaseUnderstanding:
    """Structured view of a Vision Engine response.

    The Vision Engine returns a V3 JSON dict. This dataclass holds
    the five "raw understanding" fields required by the Sprint 18
    task plus the original payload for traceability.

    Fields map to the Vision V3 schema values where possible:

        visible_elements            <- design.functional_units
                                       + design.design_highlights
        spatial_features            <- design.style + equipment
        environmental_relationship  <- basic_info.site_type
        possible_user_behavior      <- play_experience.play_behaviors
        visual_characteristics      <- color + design_keywords

    See ``schemas/case_analysis_v3.json``.
    """

    image_path: str
    visible_elements: list[str] = field(default_factory=list)
    spatial_features: list[str] = field(default_factory=list)
    environmental_relationship: str = ""
    possible_user_behavior: list[str] = field(default_factory=list)
    visual_characteristics: list[str] = field(default_factory=list)

    # Original Vision Engine payload, preserved for provenance and
    # later re-extraction as the schema evolves.
    vision_payload: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Stage 3 -- CKO Draft (sections 0-6 only)
# ---------------------------------------------------------------------------


@dataclass
class CKODraft:
    """A Case Knowledge Object filled by the extractor.

    Sections 0-6 are populated by Stage 3 from the Vision Engine
    output. Sections 7 (Project Quality), 8 (Learning Value) and 9
    (Case Evaluation Score) are intentionally left None -- those
    fields are filled by the Librarian / Reviewer, not by the
    extractor.

    Section 0.case_id is set to "PENDING" until the Reviewer
    approves a CKO and assigns a stable id (see ``GoldenCase``).
    """

    # Section 0 -- Case Identity (partial: id pending)
    case_id: str = "PENDING"
    title: str = ""
    source: str = ""
    image_reference: str = ""
    project_type: str = "other"
    knowledge_source: str = "external_excellent_case"  # ADR-011 V1 only

    # Section 1 -- Project Context
    client_goal: str = ""
    project_background: str = ""
    target_users: list[str] = field(default_factory=list)
    site_condition: str = ""
    budget_level: str | None = None

    # Section 2 -- Space Cognition
    spatial_role: str = "play"        # default; populated when known
    spatial_position: str = "edge"
    spatial_scale: str = "small"
    existing_elements: list[str] = field(default_factory=list)
    environmental_relationship: str = ""

    # Section 3 -- Experience Analysis
    atmosphere: str = ""
    emotional_response: list[str] = field(default_factory=list)
    child_behavior: list[str] = field(default_factory=list)
    interaction_type: str = "active"
    stay_value: str = "mid"

    # Section 4 -- Diagnosis
    problem_type: str = "positive_throughline"
    diagnosis: str = ""
    evidence: list[str] = field(default_factory=list)
    key_observation: str = ""

    # Section 5 -- Strategy
    strategy_type: str = "anchor"     # safe default per Brain README
    design_principles: list[str] = field(default_factory=list)
    spatial_organization: str = ""
    theme_logic: str | None = None

    # Section 6 -- Recommendation Logic
    applicable_conditions: list[str] = field(default_factory=list)
    recommended_for: list[str] = field(default_factory=list)
    not_recommended_for: list[str] = field(default_factory=list)
    risk_warning: str | None = None

    # Sections 7 / 8 / 9 -- intentionally NOT populated at Stage 3
    professional_evaluation: dict[str, Any] | None = None
    learning_value: dict[str, Any] | None = None
    case_evaluation: dict[str, Any] | None = None

    def to_cko_dict(self) -> dict[str, Any]:
        """Serialize the populated sections (0-6) into the CKO V1.2 shape.

        Sections 7-9 are NOT included here; the Reviewer / pipeline
        emits them as separate fields in the final GoldenCase JSON.
        """
        return {
            "case_identity": {
                "case_id": self.case_id,
                "title": self.title,
                "source": self.source,
                "image_reference": self.image_reference,
                "project_type": self.project_type,
                "knowledge_source": self.knowledge_source,
            },
            "project_context": {
                "client_goal": self.client_goal,
                "project_background": self.project_background,
                "target_users": self.target_users,
                "site_condition": self.site_condition,
                "budget_level": self.budget_level,
            },
            "space_cognition": {
                "spatial_role": self.spatial_role,
                "spatial_position": self.spatial_position,
                "spatial_scale": self.spatial_scale,
                "existing_elements": self.existing_elements,
                "environmental_relationship": self.environmental_relationship,
            },
            "experience_analysis": {
                "atmosphere": self.atmosphere,
                "emotional_response": self.emotional_response,
                "child_behavior": self.child_behavior,
                "interaction_type": self.interaction_type,
                "stay_value": self.stay_value,
            },
            "diagnosis": {
                "problem_type": self.problem_type,
                "diagnosis": self.diagnosis,
                "evidence": self.evidence,
                "key_observation": self.key_observation,
            },
            "strategy": {
                "strategy_type": self.strategy_type,
                "design_principles": self.design_principles,
                "spatial_organization": self.spatial_organization,
                "theme_logic": self.theme_logic,
            },
            "recommendation_logic": {
                "applicable_conditions": self.applicable_conditions,
                "recommended_for": self.recommended_for,
                "not_recommended_for": self.not_recommended_for,
                "risk_warning": self.risk_warning,
            },
        }


# ---------------------------------------------------------------------------
# Stage 4 -- Case Evaluation (ADR-012)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Transferability:
    """The transferability object from ADR-012.

    NOT part of total_score. Indicates where a case can be applied
    and what to watch out for.

    ``level`` is one of: high / medium / low.
    ``applicable_project_types`` is a non-empty list drawn from
    ``knowledge/cases/taxonomy/project_types.md``.
    ``limitations`` is a non-empty list of caveats.
    """

    level: str
    applicable_project_types: list[str]
    limitations: list[str]

    def __post_init__(self) -> None:
        if self.level not in {"high", "medium", "low"}:
            raise ValueError(
                f"Transferability.level must be high|medium|low, got {self.level!r}"
            )
        if not self.applicable_project_types:
            raise ValueError("Transferability.applicable_project_types must be non-empty")
        if not self.limitations:
            raise ValueError("Transferability.limitations must be non-empty")


# ADR-012 canonical weights (sum to 100).
WEIGHTS: dict[str, int] = {
    "space_logic_score": 25,
    "experience_logic_score": 25,
    "theme_meaning_logic_score": 20,
    "user_value_score": 15,
    "commercial_logic_score": 15,
}

# ADR-012 operational thresholds (NOT schema fields -- informational).
GOLDEN_THRESHOLDS: dict[str, int] = {
    "priority_golden": 90,
    "candidate_golden": 80,
}


@dataclass(frozen=True)
class CaseEvaluation:
    """Stage 4 output: ADR-012 weighted score + transferability.

    ``total_score`` MUST equal the sum of the five weighted
    components within 0.01 tolerance; the evaluator enforces this.
    """

    space_logic_score: float
    experience_logic_score: float
    theme_meaning_logic_score: float
    user_value_score: float
    commercial_logic_score: float
    total_score: float
    transferability: Transferability

    @property
    def tier(self) -> str:
        """Operational tier (per ADR-012 Decision 3)."""
        if self.total_score >= GOLDEN_THRESHOLDS["priority_golden"]:
            return "priority_golden"
        if self.total_score >= GOLDEN_THRESHOLDS["candidate_golden"]:
            return "candidate_golden"
        return "reference_only"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to the V1.2 Section 9 shape."""
        t = self.transferability
        return {
            "space_logic_score": self.space_logic_score,
            "experience_logic_score": self.experience_logic_score,
            "theme_meaning_logic_score": self.theme_meaning_logic_score,
            "user_value_score": self.user_value_score,
            "commercial_logic_score": self.commercial_logic_score,
            "total_score": self.total_score,
            "transferability": {
                "level": t.level,
                "applicable_project_types": t.applicable_project_types,
                "limitations": t.limitations,
            },
        }


# ---------------------------------------------------------------------------
# Stage 5 -- Review (state machine)
# ---------------------------------------------------------------------------


class ReviewStatus(str, enum.Enum):
    """The five legal statuses of a Case under review.

    Allowed transitions (enforced by ``CaseReviewer``):

        DRAFT       -> REVIEWING
        REVIEWING   -> APPROVED | REJECTED | REVIEWING (notes only)
        APPROVED    -> (terminal)
        REJECTED    -> (terminal)
    """

    DRAFT = "DRAFT"
    REVIEWING = "REVIEWING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class ReviewNote:
    """A single timestamped note in the review log."""

    author: str
    timestamp: datetime
    note: str

    @staticmethod
    def now(author: str, note: str) -> "ReviewNote":
        return ReviewNote(author=author, timestamp=datetime.now(timezone.utc), note=note)


@dataclass
class ReviewVerdict:
    """Stage 5 output: the reviewer's verdict plus its history."""

    status: ReviewStatus
    reviewer: str = ""
    reviewed_at: datetime | None = None
    notes: list[ReviewNote] = field(default_factory=list)
    modifications: list[dict[str, Any]] = field(default_factory=list)

    def add_note(self, note: ReviewNote) -> None:
        self.notes.append(note)


# ---------------------------------------------------------------------------
# Stage 6 -- Golden Case
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GoldenCase:
    """Stage 6 output: an approved CKO with evaluation and review.

    A Golden Case is the only stage that is published to the case
    library. Sections 7 (Project Quality), 8 (Learning Value) and
    9 (Case Evaluation) are all populated at this stage.
    """

    case_id: str
    cko: dict[str, Any]               # all 9 sections, V1.2 shape
    evaluation: CaseEvaluation
    review: ReviewVerdict
    approved_at: datetime

    @staticmethod
    def now() -> datetime:
        return datetime.now(timezone.utc)

    def to_json(self) -> dict[str, Any]:
        """Produce a single JSON document (one file = one Golden Case)."""
        return {
            "case_id": self.case_id,
            "approved_at": self.approved_at.isoformat(),
            "review": {
                "status": self.review.status.value,
                "reviewer": self.review.reviewer,
                "reviewed_at": (
                    self.review.reviewed_at.isoformat()
                    if self.review.reviewed_at
                    else None
                ),
                "notes": [
                    {
                        "author": n.author,
                        "timestamp": n.timestamp.isoformat(),
                        "note": n.note,
                    }
                    for n in self.review.notes
                ],
                "modifications": self.review.modifications,
            },
            "cko": self.cko,
        }


# ---------------------------------------------------------------------------
# Pipeline outcome
# ---------------------------------------------------------------------------


@dataclass
class PipelineResult:
    """End-to-end pipeline outcome.

    Stages record their artifacts as they run. On failure, only the
    stages that succeeded are populated and ``errors`` carries the
    failure reason(s). ``stage_reached`` is the human-readable name
    of the last successful stage.
    """

    success: bool = False
    stage_reached: str = "init"

    case_input: CaseInput | None = None
    raw_understanding: RawCaseUnderstanding | None = None
    cko_draft: CKODraft | None = None
    evaluation: CaseEvaluation | None = None
    review: ReviewVerdict | None = None
    golden_case: GoldenCase | None = None

    errors: list[str] = field(default_factory=list)


__all__ = [
    "CaseInput",
    "RawCaseUnderstanding",
    "CKODraft",
    "Transferability",
    "CaseEvaluation",
    "WEIGHTS",
    "GOLDEN_THRESHOLDS",
    "ReviewStatus",
    "ReviewNote",
    "ReviewVerdict",
    "GoldenCase",
    "PipelineResult",
]
