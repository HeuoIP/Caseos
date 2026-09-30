"""Knowledge Admission Contract V1 (Sprint 25.3-A).

This subpackage defines the **first-entry admission contract**
for knowledge. It answers the question:

    "Given an ELIGIBLE PromotionCandidate, what is the
     immutable handoff a future Writer Sprint can consume
     to register a brand-new Knowledge Object (version=1)
     in the Knowledge Corpus?"

V1 is a **contract**, not a writer:

    * It does NOT mutate any KnowledgeObject.
    * It does NOT write to the VersionStore.
    * It does NOT call the Evolution runtime.
    * It does NOT register anything in the Corpus.
    * It does NOT invoke AI / LLM / VLM / Embedding /
      Retrieval.

Pipeline position (V1):

    PromotionCandidate (ELIGIBLE)
          |
          v
    AdmissionCandidate  <-- THIS package: contract
          |
          v
    (Future Writer Sprint, 25.4+)
          |
          v
    KnowledgeObject v1 written into Corpus + VersionStore

Semantic boundary
-----------------

    * Admission owns version 1 only.
    * Evolution owns version 2 and above.
    * Promotion owns the eligibility decision (25.2-A).
    * Admission owns the first-entry decision (this Sprint).

Architecture boundary (Sprint 25.3-A spec):

    This package does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution   (including versioning / mutation)
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.corpus
        * caseos.knowledge.object      (KnowledgeObject schema)
        * caseos.brain.*
    This package MAY import from:
        * caseos.knowledge.ingestion.object       (CaseKnowledge)
        * caseos.knowledge.ingestion.promotion    (PromotionCandidate)
        * stdlib
"""
from .object import (
    ADMISSIBLE,
    DRAFT,
    NOT_ADMISSIBLE,
    ADMISSION_STATUS_ALLOW_LIST,
    ADMISSION_TARGET_VERSION,
    AdmissionCandidate,
    AdmissionCandidateError,
    AdmissionProvenanceRef,
    AdmissionStatus,
    AdmissionStatusError,
    new_admission_candidate,
)
from .policy import (
    ADMISSION_HUMAN_REVIEW_MARKER,
    DEFAULT_ADMISSION_POLICY,
    AdmissionPolicy,
    AdmissionPolicyError,
)
from .checker import (
    AdmissionChecker,
    AdmissionResult,
)
from .boundary import (
    ADMISSION_OWNED_VERSIONS,
    EVOLUTION_OWNED_MIN_VERSION,
    SEMANTIC_BOUNDARY_TABLE,
    is_admission_owned_version,
    is_evolution_owned_version,
)
from .report import generate_admission_report
from .writer import (
    CREATED,
    IDEMPOTENT,
    REJECTED,
    WRITE_STATUS_ALLOW_LIST,
    AdmissionWriteResult,
    AdmissionWriter,
    AdmissionWriterError,
    DuplicateAdmissionError,
)

__all__ = [
    # Object
    "AdmissionCandidate",
    "AdmissionCandidateError",
    "AdmissionProvenanceRef",
    "AdmissionStatus",
    "AdmissionStatusError",
    "ADMISSION_STATUS_ALLOW_LIST",
    "ADMISSION_TARGET_VERSION",
    "DRAFT",
    "ADMISSIBLE",
    "NOT_ADMISSIBLE",
    "new_admission_candidate",
    # Policy
    "AdmissionPolicy",
    "AdmissionPolicyError",
    "DEFAULT_ADMISSION_POLICY",
    "ADMISSION_HUMAN_REVIEW_MARKER",
    # Checker
    "AdmissionChecker",
    "AdmissionResult",
    # Boundary
    "ADMISSION_OWNED_VERSIONS",
    "EVOLUTION_OWNED_MIN_VERSION",
    "SEMANTIC_BOUNDARY_TABLE",
    "is_admission_owned_version",
    "is_evolution_owned_version",
    # Report
    "generate_admission_report",
    # Writer
    "AdmissionWriter",
    "AdmissionWriteResult",
    "AdmissionWriterError",
    "DuplicateAdmissionError",
    "CREATED",
    "IDEMPOTENT",
    "REJECTED",
    "WRITE_STATUS_ALLOW_LIST",
]