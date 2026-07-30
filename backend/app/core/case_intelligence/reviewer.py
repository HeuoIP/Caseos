"""Stage 5: Expert Review state machine.

A CKO Draft becomes a Golden Case only after a reviewer **approves
it**. The pipeline runs Stages 1-4 automatically; Stage 5 is the
human gate.

Legal state transitions::

    DRAFT       -> REVIEWING
    REVIEWING   -> APPROVED | REJECTED
    APPROVED    -> (terminal)
    REJECTED    -> (terminal)

A reviewer may also **modify** the CKO or the evaluation while in
REVIEWING -- modifications are logged in
``ReviewVerdict.modifications`` for auditability. A modification
does NOT change the status; only ``approve`` / ``reject`` do.

Approval assigns the ``case_id`` (replacing the "PENDING"
placeholder from Stage 3).
"""

from __future__ import annotations

from typing import Any

from .models import (
    CaseEvaluation,
    CKODraft,
    GoldenCase,
    ReviewNote,
    ReviewStatus,
    ReviewVerdict,
)


class ReviewStateError(RuntimeError):
    """Raised when an illegal state transition is attempted."""


class ReviewerIdentityRequiredError(ValueError):
    """Raised when an action is taken without a reviewer name."""


#: Statuses from which ``APPROVED`` and ``REJECTED`` are reachable.
_TERMINAL_FROM = {ReviewStatus.REVIEWING}

#: The legal transitions. Read-only.
_TRANSITIONS: dict[ReviewStatus, set[ReviewStatus]] = {
    ReviewStatus.DRAFT: {ReviewStatus.REVIEWING},
    ReviewStatus.REVIEWING: {
        ReviewStatus.APPROVED,
        ReviewStatus.REJECTED,
        # REVIEWING -> REVIEWING is a no-op for notes; explicit
        # transition is permitted for symmetry.
        ReviewStatus.REVIEWING,
    },
    ReviewStatus.APPROVED: set(),
    ReviewStatus.REJECTED: set(),
}


class CaseReviewer:
    """Stage 5 of the Golden Case pipeline.

    The reviewer is stateless apart from ``assign_case_id`` -- it
    holds no global state; every call is on a fresh ``ReviewVerdict``
    instance. This keeps the surface area small and the audit trail
    clean.

    Usage::

        reviewer = CaseReviewer()
        verdict = ReviewVerdict(status=ReviewStatus.DRAFT)
        verdict = reviewer.start_review(verdict, reviewer="alice")
        verdict = reviewer.modify_cko(verdict, {...}, reviewer="alice")
        verdict, golden = reviewer.approve(
            verdict,
            cko_draft=draft,
            evaluation=evaluation,
            case_id="CKO-0002",
            reviewer="alice",
            note="Looks good.",
        )
    """

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def start_review(
        self,
        verdict: ReviewVerdict,
        reviewer: str,
        note: str = "Review started.",
    ) -> ReviewVerdict:
        """Move DRAFT -> REVIEWING."""
        self._require_reviewer(reviewer)
        self._check_transition(verdict.status, ReviewStatus.REVIEWING)
        verdict.status = ReviewStatus.REVIEWING
        verdict.reviewer = reviewer
        verdict.add_note(ReviewNote.now(reviewer, note))
        return verdict

    def approve(
        self,
        verdict: ReviewVerdict,
        cko_draft: CKODraft,
        evaluation: CaseEvaluation,
        case_id: str,
        reviewer: str,
        note: str = "Approved.",
    ) -> tuple[ReviewVerdict, GoldenCase]:
        """Move REVIEWING -> APPROVED; produce the Golden Case.

        The case_id is validated to match ``^CKO-[0-9]{4,}$`` so it is
        sortable later. Sections 7-9 are attached here.

        Returns:
            A tuple ``(verdict, golden_case)``. ``verdict`` is mutated
            in place; ``golden_case`` is a new instance.
        """
        self._require_reviewer(reviewer)
        self._check_transition(verdict.status, ReviewStatus.APPROVED)

        if not case_id or not case_id.startswith("CKO-"):
            raise ReviewStateError(
                f"case_id must match CKO-<digits>, got {case_id!r}"
            )

        # Finalise verdict.
        verdict.status = ReviewStatus.APPROVED
        verdict.reviewer = reviewer
        verdict.reviewed_at = GoldenCase.now()
        verdict.add_note(
            ReviewNote.now(reviewer, f"Approved as {case_id}. {note}".strip())
        )

        # Assemble the CKO with all 9 sections.
        cko = cko_draft.to_cko_dict()
        cko["case_identity"]["case_id"] = case_id
        cko["professional_evaluation"] = _stub_section_7()
        cko["learning_value"] = _stub_section_8()
        cko["case_evaluation"] = evaluation.to_dict()

        golden = GoldenCase(
            case_id=case_id,
            cko=cko,
            evaluation=evaluation,
            review=verdict,
            approved_at=verdict.reviewed_at,  # type: ignore[assignment]
        )
        return verdict, golden

    def reject(
        self,
        verdict: ReviewVerdict,
        reviewer: str,
        note: str = "Rejected.",
    ) -> ReviewVerdict:
        """Move REVIEWING -> REJECTED."""
        self._require_reviewer(reviewer)
        self._check_transition(verdict.status, ReviewStatus.REJECTED)
        verdict.status = ReviewStatus.REJECTED
        verdict.reviewer = reviewer
        verdict.reviewed_at = GoldenCase.now()
        verdict.add_note(ReviewNote.now(reviewer, note))
        return verdict

    # ------------------------------------------------------------------
    # Modifications (do not change status)
    # ------------------------------------------------------------------

    def modify_cko(
        self,
        verdict: ReviewVerdict,
        cko_draft: CKODraft,
        changes: dict[str, Any],
        reviewer: str,
        note: str = "CKO modified.",
    ) -> CKODraft:
        """Apply ``changes`` to a CKODraft and log the modification.

        ``changes`` is keyed by CKO section ("project_context",
        "space_cognition", ...). Only top-level known sections are
        accepted; unknown keys raise ``ReviewStateError``. To be
        clear about the audit trail, every modification is appended
        to ``verdict.modifications``.
        """
        self._require_reviewer(reviewer)
        if verdict.status not in (ReviewStatus.REVIEWING, ReviewStatus.DRAFT):
            raise ReviewStateError(
                f"Cannot modify CKO from status {verdict.status.value!r}"
            )

        KNOWN_SECTIONS = {
            "case_identity",
            "project_context",
            "space_cognition",
            "experience_analysis",
            "diagnosis",
            "strategy",
            "recommendation_logic",
        }
        for key, value in changes.items():
            if key not in KNOWN_SECTIONS:
                raise ReviewStateError(
                    f"Cannot modify unknown CKO section {key!r}; "
                    f"allowed: {sorted(KNOWN_SECTIONS)}"
                )
            _apply_change(cko_draft, key, value)

        verdict.modifications.append(
            {"kind": "cko", "author": reviewer, "changes": changes}
        )
        verdict.add_note(ReviewNote.now(reviewer, note))
        return cko_draft

    def modify_evaluation(
        self,
        verdict: ReviewVerdict,
        new_evaluation: CaseEvaluation,
        reviewer: str,
        note: str = "Evaluation modified.",
    ) -> CaseEvaluation:
        """Replace the evaluation and log the modification."""
        self._require_reviewer(reviewer)
        if verdict.status not in (ReviewStatus.REVIEWING, ReviewStatus.DRAFT):
            raise ReviewStateError(
                f"Cannot modify evaluation from status {verdict.status.value!r}"
            )
        verdict.modifications.append(
            {
                "kind": "evaluation",
                "author": reviewer,
                "tier": new_evaluation.tier,
                "total_score": new_evaluation.total_score,
            }
        )
        verdict.add_note(ReviewNote.now(reviewer, note))
        return new_evaluation

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _require_reviewer(reviewer: str) -> None:
        if not reviewer or not reviewer.strip():
            raise ReviewerIdentityRequiredError(
                "reviewer must be a non-empty string"
            )

    @staticmethod
    def _check_transition(
        current: ReviewStatus, target: ReviewStatus
    ) -> None:
        allowed = _TRANSITIONS.get(current, set())
        if target not in allowed:
            raise ReviewStateError(
                f"Illegal transition {current.value!r} -> {target.value!r}"
            )


def _apply_change(draft: CKODraft, section: str, value: dict[str, Any]) -> None:
    """Apply a section-level change to a CKODraft in place.

    Only top-level field mapping is supported. Sections whose fields
    map 1:1 to dataclass attributes use the obvious assignment;
    sections with multiple keywords (e.g., target_users, evidence)
    use the dataclass attribute directly.
    """
    # Field name mapping: CKO field name -> CKODraft attribute.
    # Reuse as much as possible.
    field_map = {
        "case_identity": {
            "case_id": "case_id",
            "title": "title",
            "source": "source",
            "image_reference": "image_reference",
            "project_type": "project_type",
            "knowledge_source": "knowledge_source",
        },
        "project_context": {
            "client_goal": "client_goal",
            "project_background": "project_background",
            "target_users": "target_users",
            "site_condition": "site_condition",
            "budget_level": "budget_level",
        },
        "space_cognition": {
            "spatial_role": "spatial_role",
            "spatial_position": "spatial_position",
            "spatial_scale": "spatial_scale",
            "existing_elements": "existing_elements",
            "environmental_relationship": "environmental_relationship",
        },
        "experience_analysis": {
            "atmosphere": "atmosphere",
            "emotional_response": "emotional_response",
            "child_behavior": "child_behavior",
            "interaction_type": "interaction_type",
            "stay_value": "stay_value",
        },
        "diagnosis": {
            "problem_type": "problem_type",
            "diagnosis": "diagnosis",
            "evidence": "evidence",
            "key_observation": "key_observation",
        },
        "strategy": {
            "strategy_type": "strategy_type",
            "design_principles": "design_principles",
            "spatial_organization": "spatial_organization",
            "theme_logic": "theme_logic",
        },
        "recommendation_logic": {
            "applicable_conditions": "applicable_conditions",
            "recommended_for": "recommended_for",
            "not_recommended_for": "not_recommended_for",
            "risk_warning": "risk_warning",
        },
    }
    mapping = field_map[section]
    for cko_field, attr in mapping.items():
        if cko_field in value:
            setattr(draft, attr, value[cko_field])


def _stub_section_7() -> dict[str, Any]:
    """Section 7 -- Project Quality, V1 fields, pending Reviewer fill.

    A real review fills the four 0..10 scores. Until then we
    intentionally keep ``confidence = 0`` so the GoldenCase is
    flagged for Section 7 completion at next touch.
    """
    return {
        "design_quality_score": 0,
        "experience_score": 0,
        "innovation_score": 0,
        "commercial_value_score": 0,
        "confidence": 0.0,
        "_pending_reviewer_completion": True,
    }


def _stub_section_8() -> dict[str, Any]:
    """Section 8 -- Learning Value, pending Reviewer fill."""
    return {
        "space_logic": 0.0,
        "experience_logic": 0.0,
        "theme_logic": 0.0,
        "user_logic": 0.0,
        "commercial_logic": 0.0,
        "_pending_reviewer_completion": True,
    }


__all__ = [
    "CaseReviewer",
    "ReviewStateError",
    "ReviewerIdentityRequiredError",
]

