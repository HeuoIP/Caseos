"""Case Knowledge Ingestion Contract V1 (Sprint 25.0-A, inferred scope).

This package defines the **minimal, validated shape** of a
"Case Knowledge" record -- the form a piece of knowledge
takes **after** intake has produced a RawCaseObject and
**before** it is committed to the Knowledge Corpus.

Pipeline position (V1):

    External source
          |
          v
    intake.RawCaseObject         (pre-knowledge container)
          |
          v
    governance                   (validates and decides)
          |
          v
    ingestion.CaseKnowledge      <-- THIS package: contract
          |
          v
    corpus.KnowledgeObject       (final, mutable under evolution)

V1 ships only the **schema + validation** of the intermediate
form. It does NOT move data along the pipeline; it only
describes what "Case Knowledge" must look like so that:

    * downstream Evolution can verify provenance before
      accepting a mutation
    * downstream Retrieval can rely on a uniform envelope
      when ingesting an out-of-band document
    * future Ingestion Backends (file, API, manual) all
      produce the same shape

Architecture boundary (Sprint 25.0-A inferred scope):

    This package does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.brain.*
    This package MAY import from:
        * caseos.knowledge.object (read-only KO schema)
        * stdlib

The "intake" sibling is intentionally excluded so that
the ingestion contract stays a **schema-level guarantee**,
not a procedural step. Ingestion does not move intake
records forward; it only describes their final shape.
"""
from .object import (
    SOURCE_KIND_ALLOW_LIST,
    SOURCE_KIND_EXTERNAL,
    SOURCE_KIND_INTAKE,
    SOURCE_KIND_OPERATOR,
    CaseKnowledge,
    CaseKnowledgeError,
    new_case_knowledge,
)
from .contract import (
    IngestionContract,
    IngestionContractError,
    MAX_ASSET_COUNT,
    MAX_TAG_COUNT,
    MIN_ASSET_COUNT,
    MIN_TAG_COUNT,
)
from .validator import (
    IngestionValidationResult,
    IngestionValidator,
)
from .report import generate_report

__all__ = [
    # Object
    "CaseKnowledge",
    "CaseKnowledgeError",
    "SOURCE_KIND_ALLOW_LIST",
    "SOURCE_KIND_INTAKE",
    "SOURCE_KIND_EXTERNAL",
    "SOURCE_KIND_OPERATOR",
    "new_case_knowledge",
    # Contract
    "IngestionContract",
    "IngestionContractError",
    "MIN_ASSET_COUNT",
    "MAX_ASSET_COUNT",
    "MIN_TAG_COUNT",
    "MAX_TAG_COUNT",
    # Validator
    "IngestionValidator",
    "IngestionValidationResult",
    # Report
    "generate_report",
]
