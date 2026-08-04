"""Mutation Validator V1 (Sprint 22.4-H, ADR-020).

Pure-function validator for ``MutationRequest`` against an
approved ``EvolutionTransaction``, a passed ``GovernanceResult``,
and a ``VersionStore``.

Rules (Sprint 22.4-H spec Task 2):

    M1  Transaction Approved
            EvolutionTransaction.status must be "APPROVED".
    M2  Governance PASS
            GovernanceResult.approved must be True.
    M3  Target Identity Match
            MutationRequest.target_identity must equal
            EvolutionTransaction.target_identity.
    M4  Version Exists
            MutationRequest.before_version must exist in
            the VersionStore history for the target identity.
    M5  Change Type Allow List
            MutationRequest.change_type must be in
            MUTATION_ALLOWED_CHANGE_TYPES.

Rule order (first failure wins):

    M1 -> M2 -> M3 -> M5 -> M4

    * M1 fires first: only an approved transaction may
      ever reach the mutation runtime.
    * M2 fires second: governance is the contractual gate.
    * M3 fires third: the request must target the same KO
      that the transaction is bound to.
    * M5 fires before M4: a wrong change_type is a faster,
      more actionable rejection than a missing version.
    * M4 fires last: only after the request is structurally
      sound do we look up the prior version.

Architecture boundary (Sprint 22.4-H spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, Optional

from ..audit_v2 import EvolutionAuditRecord  # type only
from ..governance import GovernanceResult
from ..object import EvolutionTransaction
from ..versioning import VersionStore
from .object import (
    MUTATION_ALLOWED_CHANGE_TYPES,
    MutationRequest,
    MutationValidationResult,
)


_TRANSACTION_APPROVED = "APPROVED"


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_nonempty_dict(value: Any) -> bool:
    return isinstance(value, dict) and bool(value)


class MutationValidator:
    """Stateless validator. ``validate`` is a pure function."""

    def validate(
        self,
        request: Optional[MutationRequest],
        transaction: Optional[EvolutionTransaction] = None,
        governance: Optional[GovernanceResult] = None,
        version_store: Optional[VersionStore] = None,
    ) -> MutationValidationResult:
        """Validate a mutation request against the V1 rule set.

        Args:
            request: the request to validate. ``None`` is
                rejected with rule ``M0``.
            transaction: the source EvolutionTransaction.
            governance: the governance verdict for the
                transaction.
            version_store: optional VersionStore. When
                provided, M4 is checked; otherwise M4 is
                skipped.

        Returns:
            A ``MutationValidationResult`` whose ``valid`` is
            True iff every rule passed.
        """
        if request is None:
            return MutationValidationResult(
                valid=False, rule_id="M0",
                reason="request is None",
            )

        # M1 -- Transaction Approved
        if transaction is None:
            return MutationValidationResult(
                valid=False, rule_id="M1",
                reason="transaction is None",
            )
        if getattr(transaction, "status", None) != _TRANSACTION_APPROVED:
            return MutationValidationResult(
                valid=False, rule_id="M1",
                reason=(
                    "transaction status must be APPROVED; got "
                    + repr(getattr(transaction, "status", None))
                ),
            )

        # M2 -- Governance PASS
        if governance is None:
            return MutationValidationResult(
                valid=False, rule_id="M2",
                reason="governance result is None",
            )
        if not bool(getattr(governance, "approved", False)):
            return MutationValidationResult(
                valid=False, rule_id="M2",
                reason=(
                    "governance rejected: rule_id="
                    + str(getattr(governance, "rule_id", ""))
                    + " reason=" + str(getattr(governance, "reason", ""))
                ),
            )

        # M3 -- Target Identity Match
        req_identity = getattr(request, "target_identity", None)
        tx_identity = getattr(transaction, "target_identity", None)
        if not _is_nonempty_str(req_identity):
            return MutationValidationResult(
                valid=False, rule_id="M3",
                reason="request.target_identity is missing",
            )
        if not _is_nonempty_str(tx_identity):
            return MutationValidationResult(
                valid=False, rule_id="M3",
                reason="transaction.target_identity is missing",
            )
        if req_identity != tx_identity:
            return MutationValidationResult(
                valid=False, rule_id="M3",
                reason=(
                    "target_identity mismatch: request="
                    + repr(req_identity)
                    + " transaction=" + repr(tx_identity)
                ),
            )

        # M5 -- Change Type Allow List
        ct = getattr(request, "change_type", None)
        if ct not in MUTATION_ALLOWED_CHANGE_TYPES:
            return MutationValidationResult(
                valid=False, rule_id="M5",
                reason=(
                    "change_type not in mutation V1 allow-list: "
                    + repr(ct)
                ),
            )

        # M4 -- Version Exists
        if version_store is not None:
            history_numbers = {
                v.version_number
                for v in version_store.history(req_identity)
            }
            if request.before_version not in history_numbers:
                return MutationValidationResult(
                    valid=False, rule_id="M4",
                    reason=(
                        "before_version ("
                        + str(request.before_version)
                        + ") not in version store history"
                    ),
                )

        return MutationValidationResult(valid=True)


__all__ = ["MutationValidator"]
