"""Rollback Validator V1 (Sprint 22.4-G, ADR-020 Rule 4).

Deterministic validation of a ``RollbackRequest`` against a
``VersionStore``. Pure function; no mutation; no I/O.

Rules (Sprint 22.4-G spec Task 2):

    R1  transaction_id must be a non-empty string.
    R2  target_identity must be a non-empty string.
    R3  from_version must be strictly greater than
        to_version. A rollback must be a reversal.
    R4  both from_version and to_version must exist in
        the version store's history for the target
        identity. A rollback to a non-existent version
        is invalid.
    R5  to_version must be >= 1. Versions start at 1
        (per ADR-020 Rule 2 + Sprint 22.4-D). A rollback
        to "version 0" or negative is invalid. This is
        the "no direct restore" guard: V1 has no path
        to "create" a version; the only valid rollback
        targets are real, prior versions.

Rule evaluation order (first failure wins):

    R1 -> R2 -> R5 -> R4 -> R3

    * R5 fires before R4 so that an obviously invalid
      ``to_version`` (e.g. 0 or negative) is reported
      with its real reason rather than masked by R4.
    * R4 fires before R3 so that a missing version in
      history is reported with its real reason rather
      than masked by an "order" complaint.
    * R3 last: only when both versions exist and
      ``to_version >= 1`` does the validator check
      ``from > to``.

Architecture boundary (Sprint 22.4-G spec Task 6):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Any, Optional

from ..versioning import VersionStore
from .object import RollbackRequest, RollbackValidationResult


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


class RollbackValidator:
    """Stateless validator. ``validate`` is a pure function."""

    def validate(
        self,
        request: Optional[RollbackRequest],
        version_store: Optional[VersionStore] = None,
    ) -> RollbackValidationResult:
        """Validate a request against the V1 rule set.

        Args:
            request: the request to validate. ``None`` is
                rejected with rule ``R0`` (not a numbered
                rule, but a clear failure marker).
            version_store: optional VersionStore. R4 is
                skipped when ``version_store`` is None.

        Returns:
            A ``RollbackValidationResult`` whose ``valid`` is
            True iff every rule passed.
        """
        if request is None:
            return RollbackValidationResult(
                valid=False, rule_id="R0",
                reason="request is None",
            )

        # R1
        if not _is_nonempty_str(request.transaction_id):
            return RollbackValidationResult(
                valid=False, rule_id="R1",
                reason="missing transaction_id",
            )

        # R2
        if not _is_nonempty_str(request.target_identity):
            return RollbackValidationResult(
                valid=False, rule_id="R2",
                reason="missing target_identity",
            )

        # R5 -- check BEFORE R4 because R5 is cheaper
        # and conceptually comes first ("no direct
        # restore to version 0").
        if (
            not isinstance(request.to_version, int)
            or request.to_version < 1
        ):
            return RollbackValidationResult(
                valid=False, rule_id="R5",
                reason=(
                    "to_version must be >= 1; "
                    "rollback cannot target a non-existent version"
                ),
            )

        # R4 -- check BEFORE R3 so that a missing version
        # is reported with its real reason rather than
        # masked by an "order" complaint.
        if version_store is not None:
            history_numbers = {
                v.version_number
                for v in version_store.history(request.target_identity)
            }
            if request.from_version not in history_numbers:
                return RollbackValidationResult(
                    valid=False, rule_id="R4",
                    reason=(
                        "from_version ("
                        + str(request.from_version)
                        + ") not in version store history"
                    ),
                )
            if request.to_version not in history_numbers:
                return RollbackValidationResult(
                    valid=False, rule_id="R4",
                    reason=(
                        "to_version ("
                        + str(request.to_version)
                        + ") not in version store history"
                    ),
                )

        # R3
        if not (
            isinstance(request.from_version, int)
            and request.from_version > request.to_version
        ):
            return RollbackValidationResult(
                valid=False, rule_id="R3",
                reason=(
                    "from_version (" + str(request.from_version)
                    + ") must be strictly greater than to_version ("
                    + str(request.to_version) + ")"
                ),
            )

        return RollbackValidationResult(valid=True)


__all__ = ["RollbackValidator"]
