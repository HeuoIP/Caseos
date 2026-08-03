"""Evolution Validator V1 (Sprint 22.4-A, ADR-020).

The validator is the **safety gate** of the evolution layer. It
is a pure function over an ``EvolutionTransaction``. It does
NOT mutate the transaction or any external state. It returns
a ``ValidationResult`` that the caller can render, queue, or
feed to the audit log.

Mandatory Rules (Sprint 22.4-A spec Task 3):

    Rule 1  proposal_id must exist (non-empty string),
            else reject.
    Rule 2  reviewer must exist (non-empty string),
            else reject.
    Rule 3  before_snapshot must exist (non-empty dict),
            else reject.
    Rule 4  target_identity must exist (non-empty string),
            else reject.
    Rule 5  status == APPLIED is REJECTED. V1 hard-stops
            before APPLIED. This rule is the single
            defence against accidental auto-apply.

The validator does not check the lifecycle transition
ordering; that is ``transaction.is_valid_transition``. The
validator and the lifecycle are intentionally separate
concerns: the lifecycle answers "is this a legal move?" and
the validator answers "is this a safe move?".

Architecture boundary (Sprint 22.4-A spec Task 6):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.objects
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * stdlib
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .object import EvolutionStatus, EvolutionTransaction


@dataclass(frozen=True)
class ValidationResult:
    """The outcome of a validation.

    Attributes:
        is_valid: True iff every rule passed.
        reason: empty string when ``is_valid``; otherwise a
            human-readable reason naming the first failed rule.
        rule: the rule that failed (e.g. ``"R1"``); empty
            string when ``is_valid``.
    """

    is_valid: bool
    reason: str = ""
    rule: str = ""


class EvolutionValidator:
    """Stateless safety gate. ``validate`` is a pure function."""

    def validate(
        self,
        transaction: Optional[EvolutionTransaction],
    ) -> ValidationResult:
        """Return ``ValidationResult`` for a transaction.

        Returns ``ValidationResult(is_valid=False, reason="...")``
        for any rule failure. The function never raises on
        invalid input; a missing transaction is itself a
        validation failure.
        """
        if transaction is None:
            return ValidationResult(
                is_valid=False,
                reason="transaction is None",
                rule="R0",
            )

        # Rule 1: proposal_id must exist
        proposal_id = getattr(transaction, "proposal_id", None)
        if not isinstance(proposal_id, str) or not proposal_id.strip():
            return ValidationResult(
                is_valid=False,
                reason="missing proposal_id",
                rule="R1",
            )

        # Rule 2: reviewer must exist
        reviewer = getattr(transaction, "reviewer", None)
        if not isinstance(reviewer, str) or not reviewer.strip():
            return ValidationResult(
                is_valid=False,
                reason="missing reviewer",
                rule="R2",
            )

        # Rule 3: before_snapshot must exist
        before_snapshot = getattr(transaction, "before_snapshot", None)
        if not isinstance(before_snapshot, dict) or not before_snapshot:
            return ValidationResult(
                is_valid=False,
                reason="missing before_snapshot",
                rule="R3",
            )

        # Rule 4: target_identity must exist
        target_identity = getattr(transaction, "target_identity", None)
        if not isinstance(target_identity, str) or not target_identity.strip():
            return ValidationResult(
                is_valid=False,
                reason="missing target_identity",
                rule="R4",
            )

        # Rule 5: APPLIED status is rejected (no auto-apply)
        status = getattr(transaction, "status", None)
        if status == EvolutionStatus.APPLIED:
            return ValidationResult(
                is_valid=False,
                reason="status is APPLIED; V1 forbids auto-apply",
                rule="R5",
            )

        return ValidationResult(is_valid=True)


__all__ = [
    "EvolutionValidator",
    "ValidationResult",
]
