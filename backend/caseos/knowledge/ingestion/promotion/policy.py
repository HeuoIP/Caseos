"""Promotion policy rules (Sprint 25.2-A).

V1 rule table that the eligibility checker consumes:

    P1  candidate.case_id is a non-empty string
    P2  candidate.case_source_kind is in allowed_source_kinds
    P3  len(provenance_chain) >= min_provenance_steps
    P4  provenance_chain contains every step in
        required_provenance_steps
    P5  proposed_version is a positive int
    P6  if require_justification then justification is non-empty
    P7  if require_proposed_knowledge_id then
        proposed_knowledge_id is non-empty
    P8  if require_human_review then justification contains a
        human-review marker (case-insensitive substring search)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Tuple

from .object import (
    DEFAULT_PROVENANCE_STEPS,
)


# Promote the typed error from object module under the
# package's error umbrella so importers see a single
# ``PromotionPolicyError`` symbol. We define a tiny alias
# here to avoid circular import risks.
class PromotionPolicyError(ValueError):
    """Base error for the Promotion Policy module."""


HUMAN_REVIEW_MARKER: str = "human_review"


# ---------------------------------------------------------------------------
# Ingestion-side allowed source kinds (kept independent from
# the ingestion core to make the policy self-contained).
# ---------------------------------------------------------------------------


ALLOWED_SOURCE_KINDS: frozenset = frozenset(
    {"intake", "external", "operator"}
)


# ---------------------------------------------------------------------------
# PromotionPolicy
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PromotionPolicy:
    """The V1 promotion policy rule table.

    Frozen dataclass; callers may pass one instance to many
    checks. All numeric defaults are intentionally generous
    so the policy is enumerable and easy to reason about.
    """

    allowed_source_kinds: FrozenSet[str] = field(
        default_factory=lambda: ALLOWED_SOURCE_KINDS
    )
    min_provenance_steps: int = 2
    required_provenance_steps: Tuple[str, ...] = DEFAULT_PROVENANCE_STEPS
    require_justification: bool = True
    require_proposed_knowledge_id: bool = False
    require_human_review: bool = True
    human_review_marker: str = HUMAN_REVIEW_MARKER

    def __post_init__(self) -> None:
        if self.min_provenance_steps < 0:
            raise PromotionPolicyError(
                "min_provenance_steps must be >= 0; got "
                + repr(self.min_provenance_steps)
            )
        if not isinstance(self.required_provenance_steps, tuple):
            object.__setattr__(
                self,
                "required_provenance_steps",
                tuple(self.required_provenance_steps),
            )
        if not isinstance(self.allowed_source_kinds, frozenset):
            object.__setattr__(
                self,
                "allowed_source_kinds",
                frozenset(self.allowed_source_kinds),
            )

    # ---- Convenience predicates ----------------------------------

    def accepts_source_kind(self, kind: str) -> bool:
        return kind in self.allowed_source_kinds

    def required_steps(self) -> Tuple[str, ...]:
        return tuple(self.required_provenance_steps)

    def summary(self) -> Tuple[str, ...]:
        return (
            "P1_case_id_present",
            "P2_source_kind_allowed",
            "P3_min_provenance_steps",
            "P4_required_provenance_steps",
            "P5_proposed_version_positive",
            "P6_justification_required",
            "P7_proposed_knowledge_id_required",
            "P8_human_review_marker_required",
        )

    def describe(self) -> dict:
        return {
            "allowed_source_kinds": sorted(self.allowed_source_kinds),
            "min_provenance_steps": self.min_provenance_steps,
            "required_provenance_steps": list(
                self.required_provenance_steps
            ),
            "require_justification": self.require_justification,
            "require_proposed_knowledge_id":
                self.require_proposed_knowledge_id,
            "require_human_review": self.require_human_review,
            "human_review_marker": self.human_review_marker,
            "rules": list(self.summary()),
        }


# ---------------------------------------------------------------------------
# Default singleton
# ---------------------------------------------------------------------------


DEFAULT_PROMOTION_POLICY: PromotionPolicy = PromotionPolicy()


def default_policy() -> PromotionPolicy:
    return DEFAULT_PROMOTION_POLICY