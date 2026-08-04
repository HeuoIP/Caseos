"""Knowledge Domain Schema V1 (Sprint 23.1-A, ADR-020 / ADR-018).

This package is the **higher-level categorization model** that
groups related ``KnowledgeObject`` instances into named
domains. While a ``KnowledgeObject`` describes a single
design / case / pattern, a ``KnowledgeDomain`` describes the
**scope, taxonomy, and applicability rules** of a cluster of
related objects.

V1 ships only the schema. No retrieval, no embedding, no
evolution mutation, no AI.

Domain Schema V1 surface:

    KnowledgeDomain               frozen dataclass (>= 10 fields)
    KnowledgeDomainSchema         required fields + field types
                                  + version policy constants
    KnowledgeDomainValidator      runtime guard
    KnowledgeDomainSnapshot       point-in-time capture for
                                  Evolution (future Sprint)
    generate_domain_report        Markdown report

Architecture boundary (Sprint 23.1-A spec):

    This package does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This package MAY import from:
        * caseos.knowledge.object (sibling KO schema)
        * stdlib

The Domain schema does NOT mutate Knowledge Objects. It is
a pure data contract that future Evolution / Retrieval
sprints may consume.
"""
from .object import (
    IDENTITY_FIELDS,
    METADATA_FIELDS,
    KnowledgeDomain,
    KnowledgeDomainError,
    KnowledgeDomainSchemaError,
    SCOPE_FIELDS,
    TAXONOMY_FIELDS,
)
from .report import generate_domain_report
from .schema import (
    ALL_FIELDS,
    DOMAIN_VERSION_POLICY,
    DOMAIN_TYPE_ALLOW_LIST,
    FIELD_TYPES,
    REQUIRED_FIELDS,
)
from .snapshot import KnowledgeDomainSnapshot
from .validator import KnowledgeDomainValidator, DomainValidationResult

__all__ = [
    # Object
    "KnowledgeDomain",
    "KnowledgeDomainError",
    "KnowledgeDomainSchemaError",
    "IDENTITY_FIELDS",
    "SCOPE_FIELDS",
    "TAXONOMY_FIELDS",
    "METADATA_FIELDS",
    # Schema
    "REQUIRED_FIELDS",
    "FIELD_TYPES",
    "DOMAIN_VERSION_POLICY",
    "DOMAIN_TYPE_ALLOW_LIST",
    "ALL_FIELDS",
    # Validator
    "KnowledgeDomainValidator",
    "DomainValidationResult",
    # Snapshot
    "KnowledgeDomainSnapshot",
    # Report
    "generate_domain_report",
]
