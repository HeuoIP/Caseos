"""Ingestion contract rules (Sprint 25.0-A inferred).

This module declares the **rule table** that a
``CaseKnowledge`` record must satisfy to be considered
"valid for ingestion". The rules are pure constants + a
lightweight ``IngestionContract`` value object so that:

    * Different ingestion backends (file, API, manual) can
      pick a contract variant.
    * Tests can assert against the rules without invoking
      the runtime validator.
    * Future sprints may add new contracts (e.g. "strict"
      vs. "lenient") without changing the data model.

Rules V1
--------

    I1   source_kind is in SOURCE_KIND_ALLOW_LIST
    I2   knowledge_version is a positive int
    I3   tags count is in [MIN_TAG_COUNT, MAX_TAG_COUNT]
    I4   linked_assets count is in
         [MIN_ASSET_COUNT, MAX_ASSET_COUNT]
    I5   when knowledge_id is non-empty, title is non-empty
    I6   requires_human_review is True (V1 invariant)

The numeric bounds are intentionally generous; they exist
to keep the contract **enumerable** and to prevent footgun
inputs (10,000 tags, etc.). Domain-level validation (e.g.
"a kindergarten KO must declare theme") lives elsewhere.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Tuple

from .object import (
    SOURCE_KIND_ALLOW_LIST,
    CaseKnowledge,
    CaseKnowledgeError,
)


# ---------------------------------------------------------------------------
# Numeric bounds
# ---------------------------------------------------------------------------


MIN_TAG_COUNT: int = 0
MAX_TAG_COUNT: int = 64

MIN_ASSET_COUNT: int = 0
MAX_ASSET_COUNT: int = 50


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class IngestionContractError(ValueError):
    """Base error for the Ingestion Contract."""


# ---------------------------------------------------------------------------
# IngestionContract
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class IngestionContract:
    """The V1 Ingestion Contract rule table.

    The dataclass is frozen; callers may freely pass it
    around. The validator (``IngestionValidator``) consumes
    this contract to decide whether a ``CaseKnowledge``
    record is acceptable.
    """

    source_kind_allow_list: FrozenSet[str] = SOURCE_KIND_ALLOW_LIST
    min_tag_count: int = MIN_TAG_COUNT
    max_tag_count: int = MAX_TAG_COUNT
    min_asset_count: int = MIN_ASSET_COUNT
    max_asset_count: int = MAX_ASSET_COUNT
    require_title_when_knowledge_id: bool = True
    require_human_review: bool = True

    def __post_init__(self) -> None:
        if self.min_tag_count < 0:
            raise IngestionContractError(
                "min_tag_count must be >= 0; got " + repr(self.min_tag_count)
            )
        if self.max_tag_count < self.min_tag_count:
            raise IngestionContractError(
                "max_tag_count must be >= min_tag_count; got "
                + repr(self.max_tag_count) + " < " + repr(self.min_tag_count)
            )
        if self.min_asset_count < 0:
            raise IngestionContractError(
                "min_asset_count must be >= 0; got "
                + repr(self.min_asset_count)
            )
        if self.max_asset_count < self.min_asset_count:
            raise IngestionContractError(
                "max_asset_count must be >= min_asset_count; got "
                + repr(self.max_asset_count) + " < "
                + repr(self.min_asset_count)
            )
        if not isinstance(self.source_kind_allow_list, frozenset):
            # Be liberal: accept any iterable, but freeze.
            object.__setattr__(
                self,
                "source_kind_allow_list",
                frozenset(self.source_kind_allow_list),
            )

    # --------------------------------------------------------------
    # Convenience predicates -- pure, no I/O
    # --------------------------------------------------------------

    def accepts_source_kind(self, source_kind: str) -> bool:
        return source_kind in self.source_kind_allow_list

    def tag_count_in_range(self, count: int) -> bool:
        return self.min_tag_count <= count <= self.max_tag_count

    def asset_count_in_range(self, count: int) -> bool:
        return self.min_asset_count <= count <= self.max_asset_count

    def summary(self) -> Tuple[str, ...]:
        """Return a stable tuple of rule names for reporting."""
        return (
            "I1_source_kind_allow_list",
            "I2_knowledge_version_positive",
            "I3_tag_count_in_range",
            "I4_asset_count_in_range",
            "I5_title_required_when_knowledge_id",
            "I6_human_review_required",
        )

    def describe(self) -> dict:
        """Return a JSON-safe description of the contract."""
        return {
            "source_kind_allow_list": sorted(self.source_kind_allow_list),
            "min_tag_count": self.min_tag_count,
            "max_tag_count": self.max_tag_count,
            "min_asset_count": self.min_asset_count,
            "max_asset_count": self.max_asset_count,
            "require_title_when_knowledge_id":
                self.require_title_when_knowledge_id,
            "require_human_review": self.require_human_review,
            "rules": list(self.summary()),
        }


# ---------------------------------------------------------------------------
# Default contract singleton
# ---------------------------------------------------------------------------


DEFAULT_INGESTION_CONTRACT: IngestionContract = IngestionContract()


def default_contract() -> IngestionContract:
    """Return the default V1 contract.

    Returns the module-level singleton. Tests may construct
    their own ``IngestionContract`` to exercise variants.
    """
    return DEFAULT_INGESTION_CONTRACT
