"""Promotion eligibility checker (Sprint 25.2-A).

Pure, deterministic runtime guard. Consumes a
``PromotionCandidate`` and a ``PromotionPolicy``, returns an
``EligibilityResult`` and an updated candidate whose
``status`` reflects the outcome.

Algorithm V1 (fail-fast, first-failure-wins):

    P1  case_id is non-empty
    P2  case_source_kind in allowed_source_kinds
    P3  len(provenance_chain) >= min_provenance_steps
    P4  every required_provenance_step is present
    P5  proposed_version is a positive int
    P6  if require_justification: justification non-empty
    P7  if require_proposed_knowledge_id: id non-empty
    P8  if require_human_review: justification contains
        human_review_marker (case-insensitive)

The checker NEVER mutates the input candidate; it returns
``updated_candidate`` as a new ``PromotionCandidate`` with
``status`` and ``failure_reason`` set. The input record's
``status`` defaults to ``DRAFT``; after the check it is
either ``ELIGIBLE`` or ``NOT_ELIGIBLE``.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .object import (
    DRAFT,
    ELIGIBLE,
    NOT_ELIGIBLE,
    PROMOTION_STATUS_ALLOW_LIST,
    PromotionCandidate,
    PromotionCandidateError,
)
from .policy import (
    DEFAULT_PROMOTION_POLICY,
    PromotionPolicy,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# EligibilityResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EligibilityResult:
    """Outcome of an eligibility check."""

    valid: bool = False
    rule_id: str = ""
    reason: str = ""
    missing_steps: tuple = ()
    checked_at: str = field(default_factory=_now_iso)
    candidate_id: str = ""

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "missing_steps": list(self.missing_steps),
            "checked_at": self.checked_at,
            "candidate_id": self.candidate_id,
        }


# ---------------------------------------------------------------------------
# Checker
# ---------------------------------------------------------------------------


class PromotionEligibilityChecker:
    """V1 deterministic gate."""

    ENGINE_NAME: str = "PromotionEligibilityChecker V1"

    def __init__(
        self,
        policy: Optional[PromotionPolicy] = None,
    ) -> None:
        if policy is None:
            policy = DEFAULT_PROMOTION_POLICY
        if not isinstance(policy, PromotionPolicy):
            raise PromotionCandidateError(
                "policy must be a PromotionPolicy or None; got "
                + type(policy).__name__
            )
        self.policy: PromotionPolicy = policy

    # ---- public ----------------------------------------------------

    def check(
        self, candidate: PromotionCandidate
    ) -> tuple:
        """Run the gate.

        Returns a ``(EligibilityResult, PromotionCandidate)``
        tuple. The returned candidate carries the new
        ``status`` (``ELIGIBLE`` or ``NOT_ELIGIBLE``) plus a
        ``failure_reason`` when not eligible. The input
        candidate is never mutated.
        """
        if not isinstance(candidate, PromotionCandidate):
            result = EligibilityResult(
                valid=False,
                rule_id="P0_type",
                reason=(
                    "candidate must be a PromotionCandidate; got "
                    + type(candidate).__name__
                ),
            )
            return result, candidate

        policy = self.policy

        # P1 -- case_id
        if not candidate.case_id or not candidate.case_id.strip():
            result = EligibilityResult(
                valid=False,
                rule_id="P1_case_id_present",
                reason="case_id is empty",
                candidate_id=candidate.candidate_id,
            )
            return result, self._stamp(candidate, result)

        # P2 -- source kind allowed
        if not policy.accepts_source_kind(candidate.case_source_kind):
            result = EligibilityResult(
                valid=False,
                rule_id="P2_source_kind_allowed",
                reason=(
                    "case_source_kind="
                    + repr(candidate.case_source_kind)
                    + " not in allow list "
                    + repr(sorted(policy.allowed_source_kinds))
                ),
                candidate_id=candidate.candidate_id,
            )
            return result, self._stamp(candidate, result)

        # P3 -- min provenance steps
        steps_present = {r.step for r in candidate.provenance_chain}
        if len(candidate.provenance_chain) < policy.min_provenance_steps:
            result = EligibilityResult(
                valid=False,
                rule_id="P3_min_provenance_steps",
                reason=(
                    "provenance_chain has "
                    + str(len(candidate.provenance_chain))
                    + " step(s); minimum is "
                    + str(policy.min_provenance_steps)
                ),
                candidate_id=candidate.candidate_id,
            )
            return result, self._stamp(candidate, result)

        # P4 -- required steps present
        missing = tuple(
            s for s in policy.required_provenance_steps
            if s not in steps_present
        )
        if missing:
            result = EligibilityResult(
                valid=False,
                rule_id="P4_required_provenance_steps",
                reason=(
                    "missing required provenance steps: "
                    + ", ".join(missing)
                ),
                missing_steps=missing,
                candidate_id=candidate.candidate_id,
            )
            return result, self._stamp(candidate, result)

        # P5 -- proposed_version positive
        if (
            not isinstance(candidate.proposed_version, int)
            or candidate.proposed_version < 1
        ):
            result = EligibilityResult(
                valid=False,
                rule_id="P5_proposed_version_positive",
                reason=(
                    "proposed_version must be a positive int; got "
                    + repr(candidate.proposed_version)
                ),
                candidate_id=candidate.candidate_id,
            )
            return result, self._stamp(candidate, result)

        # P6 -- justification required
        if (
            policy.require_justification
            and not candidate.justification.strip()
        ):
            result = EligibilityResult(
                valid=False,
                rule_id="P6_justification_required",
                reason="justification is required and is empty",
                candidate_id=candidate.candidate_id,
            )
            return result, self._stamp(candidate, result)

        # P7 -- proposed_knowledge_id required (when on)
        if (
            policy.require_proposed_knowledge_id
            and not candidate.proposed_knowledge_id.strip()
        ):
            result = EligibilityResult(
                valid=False,
                rule_id="P7_proposed_knowledge_id_required",
                reason=(
                    "proposed_knowledge_id is required by policy "
                    "but is empty"
                ),
                candidate_id=candidate.candidate_id,
            )
            return result, self._stamp(candidate, result)

        # P8 -- human review marker present
        if policy.require_human_review:
            marker = policy.human_review_marker.lower()
            if marker not in candidate.justification.lower():
                result = EligibilityResult(
                    valid=False,
                    rule_id="P8_human_review_marker_required",
                    reason=(
                        "justification must contain the marker "
                        + repr(policy.human_review_marker)
                        + " (case-insensitive)"
                    ),
                    candidate_id=candidate.candidate_id,
                )
                return result, self._stamp(candidate, result)

        # ---- all checks passed ------------------------------------
        result = EligibilityResult(
            valid=True,
            rule_id="OK",
            reason="all V1 promotion policy rules satisfied",
            candidate_id=candidate.candidate_id,
        )
        updated = self._stamp(candidate, result)
        return result, updated

    # ---- private helpers ------------------------------------------

    @staticmethod
    def _stamp(
        candidate: PromotionCandidate,
        result: EligibilityResult,
    ) -> PromotionCandidate:
        new_status = ELIGIBLE if result.valid else NOT_ELIGIBLE
        return dataclasses.replace(
            candidate,
            status=new_status,
            failure_reason="" if result.valid else result.reason,
        )
