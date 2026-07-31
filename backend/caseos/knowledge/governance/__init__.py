"""Corpus governance layer (Sprint 20.6).

Sprint 20.5 established the Golden Case Corpus V1 (the
5-subdirectory layout in ackend/caseos/knowledge/corpus/).
Sprint 20.6 adds the governance layer that protects memory
quality before the corpus scales further.

This package is intentionally read-only with respect to the
retrieval, decision, trust, and recommendation engines. The
governance modules decide *whether* a Knowledge Object may
live in the corpus and *what trust tier* it occupies; they
never rewrite, re-rank, or override what those engines return.

Submodules:

  validator   -- quality gate (extends ADR-015 checks).
  duplicate   -- deterministic duplicate-candidate detection.
  trust_tier  -- assign ADR-016-aligned TrustTier to a KO.
  promotion   -- lifecycle promotion with original-preservation.
  report      -- generate the governance Markdown report.

Architecture boundary: governance is memory protection, not
retrieval, not recommendation, not AI generation."""

from caseos.knowledge.governance.trust_tier import (
    TrustTier,
    assign_trust_tier,
    assign_tiers,
    distribution,
)
from caseos.knowledge.governance.duplicate import (
    DuplicateCandidate,
    detect_duplicates,
    summarize as duplicate_summarize,
)
from caseos.knowledge.governance.promotion import (
    PromotionEvent,
    PromotionError,
    promote,
    verify_original_preserved,
)
from caseos.knowledge.governance.validator import (
    VALID_IDENTITY_TYPES,
    GovernanceValidationResult,
    validate_for_governance,
    validate_corpus_for_governance,
)
from caseos.knowledge.governance.report import (
    generate_report,
)

__all__ = [
    "TrustTier",
    "assign_trust_tier",
    "assign_tiers",
    "distribution",
    "DuplicateCandidate",
    "detect_duplicates",
    "duplicate_summarize",
    "PromotionEvent",
    "PromotionError",
    "promote",
    "verify_original_preserved",
    "VALID_IDENTITY_TYPES",
    "GovernanceValidationResult",
    "validate_for_governance",
    "validate_corpus_for_governance",
    "generate_report",
]
