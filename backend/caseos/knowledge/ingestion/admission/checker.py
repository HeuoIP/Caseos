"""Admission checker (Sprint 25.3-A).

Pure, deterministic runtime guard. Consumes an
``AdmissionCandidate`` and an ``AdmissionPolicy`` and
returns ``(AdmissionResult, updated_candidate)``.

Algorithm V1 (fail-fast, first-failure-wins):

    A1  target_knowledge_id is a non-empty string
    A2  target_version equals ADMISSION_TARGET_VERSION (1)
    A3  source.promotion_candidate_id is a non-empty string
    A4  source.case_id is a non-empty string
    A5  source.provenance_chain is non-empty
    A6  admission_proposal is a non-empty mapping
    A7  requires_human_review is True
    A8  justification contains the human review marker

The checker NEVER mutates the input candidate; it returns
a new candidate whose ``status`` reflects the outcome.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .object import (
    ADMISSIBLE,
    ADMISSION_STATUS_ALLOW_LIST,
    ADMISSION_TARGET_VERSION,
    DRAFT,
    NOT_ADMISSIBLE,
    AdmissionCandidate,
    AdmissionCandidateError,
)
from .policy import (
    ADMISSION_HUMAN_REVIEW_MARKER,
    DEFAULT_ADMISSION_POLICY,
    AdmissionPolicy,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# AdmissionResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdmissionResult:
    """Outcome of an admission check."""

    valid: bool = False
    rule_id: str = ""
    reason: str = ""
    checked_at: str = field(default_factory=_now_iso)
    admission_id: str = ""

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "checked_at": self.checked_at,
            "admission_id": self.admission_id,
        }


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------


class AdmissionChecker:
    """V1 deterministic admission gate."""

    ENGINE_NAME: str = "AdmissionChecker V1"

    def __init__(
        self,
        policy: Optional[AdmissionPolicy] = None,
    ) -> None:
        if policy is None:
            policy = DEFAULT_ADMISSION_POLICY
        if not isinstance(policy, AdmissionPolicy):
            raise AdmissionCandidateError(
                "policy must be an AdmissionPolicy or None; got "
                + type(policy).__name__
            )
        self.policy: AdmissionPolicy = policy

    # ---- public ----------------------------------------------------

    def check(
        self, candidate: AdmissionCandidate
    ) -> tuple:
        """Run the gate.

        Returns ``(AdmissionResult, AdmissionCandidate)``.
        The returned candidate carries the new ``status``
        (ADMISSIBLE or NOT_ADMISSIBLE) and a populated
        ``failure_reason`` when not admissible. The input
        candidate is never mutated.
        """
        if not isinstance(candidate, AdmissionCandidate):
            result = AdmissionResult(
                valid=False,
                rule_id="A0_type",
                reason=(
                    "candidate must be an AdmissionCandidate; got "
                    + type(candidate).__name__
                ),
            )
            return result, candidate

        policy = self.policy

        # A1 -- target_knowledge_id
        if (
            not candidate.target_knowledge_id
            or not candidate.target_knowledge_id.strip()
        ):
            result = AdmissionResult(
                valid=False,
                rule_id="A1_target_knowledge_id_present",
                reason="target_knowledge_id is empty",
                admission_id=candidate.admission_id,
            )
            return result, self._stamp(candidate, result)

        # A2 -- target_version == ADMISSION_TARGET_VERSION (1)
        # The constructor already enforces this; we double-check
        # defensively in case a future variant opens up.
        if candidate.target_version != policy.target_version:
            result = AdmissionResult(
                valid=False,
                rule_id="A2_target_version_is_v1",
                reason=(
                    "target_version must equal "
                    + str(policy.target_version) + "; got "
                    + repr(candidate.target_version)
                ),
                admission_id=candidate.admission_id,
            )
            return result, self._stamp(candidate, result)

        # A3 -- source.promotion_candidate_id
        if (
            not candidate.source.promotion_candidate_id
            or not candidate.source.promotion_candidate_id.strip()
        ):
            result = AdmissionResult(
                valid=False,
                rule_id="A3_promotion_candidate_id_present",
                reason=(
                    "source.promotion_candidate_id is empty; "
                    "AdmissionCandidate must reference a "
                    "PromotionCandidate"
                ),
                admission_id=candidate.admission_id,
            )
            return result, self._stamp(candidate, result)

        # A4 -- source.case_id
        if (
            not candidate.source.case_id
            or not candidate.source.case_id.strip()
        ):
            result = AdmissionResult(
                valid=False,
                rule_id="A4_case_id_present",
                reason="source.case_id is empty",
                admission_id=candidate.admission_id,
            )
            return result, self._stamp(candidate, result)

        # A5 -- provenance_chain non-empty
        if policy.require_non_empty_provenance \
                and len(candidate.source.provenance_chain) == 0:
            result = AdmissionResult(
                valid=False,
                rule_id="A5_provenance_chain_non_empty",
                reason=(
                    "source.provenance_chain is empty; the "
                    "AdmissionCandidate must preserve the "
                    "PromotionCandidate provenance chain"
                ),
                admission_id=candidate.admission_id,
            )
            return result, self._stamp(candidate, result)

        # A6 -- admission_proposal non-empty
        if policy.require_non_empty_proposal \
                and len(candidate.admission_proposal) == 0:
            result = AdmissionResult(
                valid=False,
                rule_id="A6_admission_proposal_non_empty",
                reason="admission_proposal is empty",
                admission_id=candidate.admission_id,
            )
            return result, self._stamp(candidate, result)

        # A7 -- requires_human_review True
        if policy.require_human_review \
                and not candidate.requires_human_review:
            result = AdmissionResult(
                valid=False,
                rule_id="A7_requires_human_review_true",
                reason=(
                    "requires_human_review must be True under "
                    "V1 admission policy; got False"
                ),
                admission_id=candidate.admission_id,
            )
            return result, self._stamp(candidate, result)

        # A8 -- justification contains human_review_marker
        marker = policy.human_review_marker.lower()
        if marker not in candidate.justification.lower():
            result = AdmissionResult(
                valid=False,
                rule_id="A8_human_review_marker_present",
                reason=(
                    "justification must contain the marker "
                    + repr(policy.human_review_marker)
                    + " (case-insensitive)"
                ),
                admission_id=candidate.admission_id,
            )
            return result, self._stamp(candidate, result)

        # ---- all checks passed ------------------------------------
        result = AdmissionResult(
            valid=True,
            rule_id="OK",
            reason="all V1 admission policy rules satisfied",
            admission_id=candidate.admission_id,
        )
        return result, self._stamp(candidate, result)

    # ---- private helpers ------------------------------------------

    @staticmethod
    def _stamp(
        candidate: AdmissionCandidate,
        result: AdmissionResult,
    ) -> AdmissionCandidate:
        new_status = ADMISSIBLE if result.valid else NOT_ADMISSIBLE
        return dataclasses.replace(
            candidate,
            status=new_status,
            failure_reason="" if result.valid else result.reason,
        )
