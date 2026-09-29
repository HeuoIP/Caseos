"""Ingestion validator (Sprint 25.0-A inferred).

The validator is the runtime guard that decides whether a
``CaseKnowledge`` record satisfies a given ``IngestionContract``.

Algorithm V1 (deterministic, fail-fast, first-failure-wins):

    1. I1: source_kind in source_kind_allow_list
    2. I2: knowledge_version is a positive int
    3. I3: len(tags) in [min_tag_count, max_tag_count]
    4. I4: len(linked_assets) in [min_asset_count, max_asset_count]
    5. I5: when knowledge_id is non-empty, title must be non-empty
    6. I6: requires_human_review is True (when contract demands)

The result is a frozen ``IngestionValidationResult`` that
records:

    * ``valid``           -- overall pass/fail
    * ``rule_id``         -- the rule that failed (or "OK")
    * ``reason``          -- human-readable explanation
    * ``checked_at``      -- ISO timestamp

The validator NEVER mutates the input record. It only reads.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .contract import (
    DEFAULT_INGESTION_CONTRACT,
    IngestionContract,
)
from .object import (
    SOURCE_KIND_ALLOW_LIST,
    CaseKnowledge,
    CaseKnowledgeError,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IngestionValidationResult:
    """Outcome of validating a CaseKnowledge record."""

    valid: bool = False
    rule_id: str = ""
    reason: str = ""
    checked_at: str = field(default_factory=_now_iso)
    case_id: str = ""

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "checked_at": self.checked_at,
            "case_id": self.case_id,
        }


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class IngestionValidator:
    """Runtime guard for CaseKnowledge ingestion."""

    ENGINE_NAME: str = "IngestionValidator V1"

    def __init__(
        self,
        contract: Optional[IngestionContract] = None,
    ) -> None:
        if contract is None:
            contract = DEFAULT_INGESTION_CONTRACT
        if not isinstance(contract, IngestionContract):
            raise CaseKnowledgeError(
                "contract must be an IngestionContract or None; got "
                + type(contract).__name__
            )
        self.contract: IngestionContract = contract

    # ---- public ----------------------------------------------------

    def validate(
        self, record: Any
    ) -> IngestionValidationResult:
        """Validate ``record`` against the contract.

        ``record`` must be a ``CaseKnowledge`` instance.
        Anything else is treated as an immediate failure
        with ``rule_id="I0_type"``.
        """
        if not isinstance(record, CaseKnowledge):
            return IngestionValidationResult(
                valid=False,
                rule_id="I0_type",
                reason=(
                    "record must be a CaseKnowledge; got "
                    + type(record).__name__
                ),
            )

        contract = self.contract

        # I1 -- source_kind
        if not contract.accepts_source_kind(record.source_kind):
            return IngestionValidationResult(
                valid=False,
                rule_id="I1_source_kind_allow_list",
                reason=(
                    "source_kind=" + repr(record.source_kind)
                    + " not in allow list "
                    + repr(sorted(contract.source_kind_allow_list))
                ),
                case_id=record.case_id,
            )

        # I2 -- knowledge_version positive
        if (
            not isinstance(record.knowledge_version, int)
            or record.knowledge_version < 1
        ):
            return IngestionValidationResult(
                valid=False,
                rule_id="I2_knowledge_version_positive",
                reason=(
                    "knowledge_version must be a positive int; got "
                    + repr(record.knowledge_version)
                ),
                case_id=record.case_id,
            )

        # I3 -- tags count in range
        tag_count = len(record.tags)
        if not contract.tag_count_in_range(tag_count):
            return IngestionValidationResult(
                valid=False,
                rule_id="I3_tag_count_in_range",
                reason=(
                    "tags count=" + str(tag_count)
                    + " not in ["
                    + str(contract.min_tag_count) + ", "
                    + str(contract.max_tag_count) + "]"
                ),
                case_id=record.case_id,
            )

        # I4 -- asset count in range
        asset_count = len(record.linked_assets)
        if not contract.asset_count_in_range(asset_count):
            return IngestionValidationResult(
                valid=False,
                rule_id="I4_asset_count_in_range",
                reason=(
                    "linked_assets count=" + str(asset_count)
                    + " not in ["
                    + str(contract.min_asset_count) + ", "
                    + str(contract.max_asset_count) + "]"
                ),
                case_id=record.case_id,
            )

        # I5 -- title required when knowledge_id non-empty
        if (
            contract.require_title_when_knowledge_id
            and record.knowledge_id
            and not record.title.strip()
        ):
            return IngestionValidationResult(
                valid=False,
                rule_id="I5_title_required_when_knowledge_id",
                reason=(
                    "title is required when knowledge_id="
                    + repr(record.knowledge_id) + " is set"
                ),
                case_id=record.case_id,
            )

        # I6 -- requires_human_review must be True
        if contract.require_human_review and not record.requires_human_review:
            return IngestionValidationResult(
                valid=False,
                rule_id="I6_human_review_required",
                reason=(
                    "requires_human_review must be True under V1 contract; "
                    "got False"
                ),
                case_id=record.case_id,
            )

        return IngestionValidationResult(
            valid=True,
            rule_id="OK",
            reason="all V1 contract rules satisfied",
            case_id=record.case_id,
        )
