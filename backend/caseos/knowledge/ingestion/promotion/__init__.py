"""Case Knowledge Promotion Contract V1 (Sprint 25.2-A).

This subpackage defines the **promotion eligibility contract**
for Case Knowledge records. It answers the question:

    "Given a CaseKnowledge + provenance chain, is this record
     eligible to be promoted into the Knowledge Corpus?"

V1 is purely a **gate**: it decides pass / fail and records
the reason. It does NOT write to the corpus, does NOT mutate
the KnowledgeObject, does NOT touch the Intake layer, and
does NOT invoke any AI / intelligence machinery.

Pipeline position (V1):

    CaseKnowledge          (from Sprint 25.0-A)
        |
        v
    ProvenanceRecord[]     (audit chain)
        |
        v
    PromotionEligibilityChecker  <-- THIS package
        |
        +-- ELIGIBLE       -> caller decides what to do next
        +-- NOT_ELIGIBLE   -> caller surfaces the reason

The actual corpus mutation is reserved for a later sprint
(e.g. 25.3-A Ingestion Backend / 25.4-A Promotion Writer).

Architecture boundary (Sprint 25.2-A spec):

    This package does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.corpus
        * caseos.knowledge.object     (KnowledgeObject schema)
        * caseos.brain.*
    This package MAY import from:
        * caseos.knowledge.ingestion.object   (CaseKnowledge)
        * stdlib
"""
from .object import (
    DEFAULT_PROVENANCE_STEPS,
    ELIGIBLE,
    NOT_ELIGIBLE,
    DRAFT,
    PROMOTION_STATUS_ALLOW_LIST,
    ProvenanceRecord,
    PromotionCandidate,
    PromotionCandidateError,
    PromotionStatus,
    PromotionStatusError,
    STEP_CASE_KNOWLEDGE_VALIDATION,
    STEP_INTAKE,
    new_promotion_candidate,
)
from .policy import (
    DEFAULT_PROMOTION_POLICY,
    PromotionPolicy,
    PromotionPolicyError,
)
from .eligibility import (
    EligibilityResult,
    PromotionEligibilityChecker,
)
from .report import generate_promotion_report

__all__ = [
    # Object
    "PromotionCandidate",
    "PromotionCandidateError",
    "ProvenanceRecord",
    "PromotionStatus",
    "PromotionStatusError",
    "PROMOTION_STATUS_ALLOW_LIST",
    "DRAFT",
    "ELIGIBLE",
    "NOT_ELIGIBLE",
    "DEFAULT_PROVENANCE_STEPS",
    "STEP_INTAKE",
    "STEP_CASE_KNOWLEDGE_VALIDATION",
    "new_promotion_candidate",
    # Policy
    "PromotionPolicy",
    "PromotionPolicyError",
    "DEFAULT_PROMOTION_POLICY",
    # Eligibility
    "PromotionEligibilityChecker",
    "EligibilityResult",
    # Report
    "generate_promotion_report",
]
