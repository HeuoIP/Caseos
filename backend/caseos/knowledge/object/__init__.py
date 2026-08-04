"""Knowledge Object V1 (Sprint 23.0-A).

This package is the **core business knowledge model** of
CaseOS. It defines the canonical shape that:

    * Evolution mutations will write into (Sprint 22.4-H
      and beyond)
    * Retrieval will read from (future sprints; out of
      scope here)
    * AI Design Engine will consume (future sprints; out
      of scope here)

V1 ships only the schema:

    * ``KnowledgeObject``            -- the dataclass
    * ``KnowledgeObjectSchema``      -- required fields,
                                        field types, version
                                        policy constants
    * ``KnowledgeObjectValidator``   -- runtime guard
    * ``KnowledgeObjectSnapshot``    -- point-in-time capture
                                        for Evolution
    * ``generate_schema_report``     -- Markdown report

V1 does NOT introduce retrieval, embedding, vision, OCR,
auto-tagging, AI generation, or Evolution mutation. The
package is a pure data contract.

Architecture boundary (Sprint 23.0-A spec):

    This package does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
    This package MAY import from:
        * stdlib
"""
from .object import (
    ASSET_FIELDS,
    CASE_CONTEXT_FIELDS,
    CONTENT_FIELDS,
    DESIGN_ATTRIBUTE_FIELDS,
    IDENTITY_FIELDS,
    KnowledgeObject,
    KnowledgeObjectError,
    KnowledgeObjectSchemaError,
    METADATA_FIELDS,
)
from .report import generate_schema_report
from .schema import (
    ALL_FIELDS,
    FIELD_TYPES,
    REQUIRED_FIELDS,
    VERSION_POLICY,
)
from .snapshot import KnowledgeObjectSnapshot
from .validator import KnowledgeObjectValidator, ValidationResult

__all__ = [
    # Object
    "KnowledgeObject",
    "KnowledgeObjectError",
    "KnowledgeObjectSchemaError",
    "IDENTITY_FIELDS",
    "CONTENT_FIELDS",
    "CASE_CONTEXT_FIELDS",
    "DESIGN_ATTRIBUTE_FIELDS",
    "ASSET_FIELDS",
    "METADATA_FIELDS",
    # Schema
    "REQUIRED_FIELDS",
    "FIELD_TYPES",
    "VERSION_POLICY",
    "ALL_FIELDS",
    # Validator
    "KnowledgeObjectValidator",
    "ValidationResult",
    # Snapshot
    "KnowledgeObjectSnapshot",
    # Report
    "generate_schema_report",
]
