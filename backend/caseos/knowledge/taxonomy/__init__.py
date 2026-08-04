"""Knowledge Taxonomy Schema V1 (Sprint 23.1-C, ADR-018 / ADR-020).

This package is the **fine-grained categorization layer**
of CaseOS. A ``Taxonomy`` is a named, hierarchical
classification system (e.g. "Design Style Taxonomy", "Color
Taxonomy"). A ``TaxonomyNode`` is a single labelled entry
in a Taxonomy (e.g. "Scandinavian", "Earth-tones",
"Outdoor").

Relationship to other packages:

    KnowledgeObject    (Sprint 23.0-A) -- single record
    KnowledgeDomain    (Sprint 23.1-A) -- coarse-grained scope
    KODomainBinding    (Sprint 23.1-B) -- KO <-> Domain link
    Taxonomy           (Sprint 23.1-C) -- fine-grained tags

V1 ships only the data contract and an append-only
registry. No retrieval, no embedding, no evolution
mutation, no AI.

Taxonomy Schema V1 surface:

    Taxonomy             frozen dataclass (11 fields)
    TaxonomyNode         frozen dataclass (14 fields)
    TaxonomyValidator    runtime guard
    TaxonomyRegistry     append-only container
    generate_taxonomy_report  Markdown report

The Taxonomy NEVER mutates a Knowledge Object, a Domain,
or a Binding. It is a pure data structure that future
Retrieval / Evolution sprints may consume.

Architecture boundary (Sprint 23.1-C spec):

    This package does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This package MAY import from:
        * caseos.knowledge.object (sibling KO schema)
        * caseos.knowledge.domain (sibling Domain schema)
        * caseos.knowledge.binding (sibling Binding)
        * stdlib
"""
from .object import (
    TaxonomyNodeSchemaError,
    IDENTITY_FIELDS as NODE_IDENTITY_FIELDS,
    CONTENT_FIELDS as NODE_CONTENT_FIELDS,
    HIERARCHY_FIELDS as NODE_HIERARCHY_FIELDS,
    METADATA_FIELDS as NODE_METADATA_FIELDS,
    Taxonomy,
    TaxonomyError,
    TaxonomyNode,
    TaxonomyNodeError,
    TaxonomySchemaError,
    TAXONOMY_IDENTITY_FIELDS,
    TAXONOMY_CONTENT_FIELDS,
    TAXONOMY_METADATA_FIELDS,
)
from .schema import (
    ALL_NODE_FIELDS,
    ALL_TAXONOMY_FIELDS,
    FIELD_TYPES,
    NODE_FIELD_TYPES,
    NODE_REQUIRED_FIELDS,
    NODE_TYPE_ALLOW_LIST,
    REQUIRED_FIELDS,
    TAXONOMY_TYPE_ALLOW_LIST,
    VERSION_POLICY,
)
from .registry import TaxonomyRegistry, TaxonomyRegistryError
from .validator import (
    TaxonomyValidator,
    TaxonomyValidationResult,
)
from .report import generate_taxonomy_report

__all__ = [
    # Taxonomy
    "Taxonomy",
    "TaxonomyError",
    "TaxonomySchemaError",
    "TAXONOMY_IDENTITY_FIELDS",
    "TAXONOMY_CONTENT_FIELDS",
    "TAXONOMY_METADATA_FIELDS",
    "REQUIRED_FIELDS",
    "FIELD_TYPES",
    "TAXONOMY_TYPE_ALLOW_LIST",
    "VERSION_POLICY",
    # Node
    "TaxonomyNode",
    "TaxonomyNodeError",
    "TaxonomyNodeSchemaError",
    "NODE_IDENTITY_FIELDS",
    "NODE_CONTENT_FIELDS",
    "NODE_HIERARCHY_FIELDS",
    "NODE_METADATA_FIELDS",
    "NODE_REQUIRED_FIELDS",
    "NODE_FIELD_TYPES",
    "ALL_NODE_FIELDS",
    "NODE_TYPE_ALLOW_LIST",
    "ALL_TAXONOMY_FIELDS",
    # Validator
    "TaxonomyValidator",
    "TaxonomyValidationResult",
    # Registry
    "TaxonomyRegistry",
    "TaxonomyRegistryError",
    # Report
    "generate_taxonomy_report",
]
