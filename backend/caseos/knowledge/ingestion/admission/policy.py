"""Admission policy rules (Sprint 25.3-A).

V1 rule table that the admission checker consumes:

    A1  target_knowledge_id is a non-empty string
    A2  target_version equals ADMISSION_TARGET_VERSION (1)
    A3  source.promotion_candidate_id is a non-empty string
    A4  source.case_id is a non-empty string
    A5  source.provenance_chain is non-empty
    A6  admission_proposal is a non-empty mapping
    A7  requires_human_review is True (V1 invariant)
    A8  justification contains ADMISSION_HUMAN_REVIEW_MARKER
        (case-insensitive substring search)

The policy is intentionally separate from the candidate
so that future sprints (25.4+) can introduce stricter or
looser variants without touching the data shape.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .object import (
    ADMISSION_TARGET_VERSION,
    AdmissionCandidateError,
)


class AdmissionPolicyError(ValueError):
    """Base error for the Admission Policy module."""


# Default marker (substring) the justification must contain.
ADMISSION_HUMAN_REVIEW_MARKER: str = "human_review"


# ---------------------------------------------------------------------------
# AdmissionPolicy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdmissionPolicy:
    """The V1 admission policy rule table.

    Frozen dataclass. All fields have defaults so callers
    can construct the V1 policy with no arguments.
    """

    target_version: int = ADMISSION_TARGET_VERSION
    require_human_review: bool = True
    require_non_empty_proposal: bool = True
    require_non_empty_provenance: bool = True
    human_review_marker: str = ADMISSION_HUMAN_REVIEW_MARKER

    def __post_init__(self) -> None:
        if not isinstance(self.target_version, int):
            raise AdmissionPolicyError(
                "target_version must be an int; got "
                + type(self.target_version).__name__
            )
        if self.target_version < 1:
            raise AdmissionPolicyError(
                "target_version must be >= 1; got "
                + repr(self.target_version)
            )

    # ---- Convenience predicates ----------------------------------

    def summary(self) -> Tuple[str, ...]:
        return (
            "A1_target_knowledge_id_present",
            "A2_target_version_is_v1",
            "A3_promotion_candidate_id_present",
            "A4_case_id_present",
            "A5_provenance_chain_non_empty",
            "A6_admission_proposal_non_empty",
            "A7_requires_human_review_true",
            "A8_human_review_marker_present",
        )

    def describe(self) -> dict:
        return {
            "target_version": self.target_version,
            "require_human_review": self.require_human_review,
            "require_non_empty_proposal": self.require_non_empty_proposal,
            "require_non_empty_provenance": self.require_non_empty_provenance,
            "human_review_marker": self.human_review_marker,
            "rules": list(self.summary()),
        }


# ---------------------------------------------------------------------------
# Default singleton
# ---------------------------------------------------------------------------


DEFAULT_ADMISSION_POLICY: AdmissionPolicy = AdmissionPolicy()


def default_policy() -> AdmissionPolicy:
    return DEFAULT_ADMISSION_POLICY
