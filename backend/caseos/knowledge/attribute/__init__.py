"""Knowledge Attribute Schema V1 (Sprint 23.1-D, ADR-018 / ADR-020).

This package is the **typed property slot layer** of CaseOS.
A ``KnowledgeAttribute`` declares the schema for a single
property slot on a ``KnowledgeObject`` (e.g. ``style``,
``theme``, ``color_system``), including:

    * data type (string / number / boolean / enum / list / object)
    * cardinality (single / list / set)
    * whether the attribute is required
    * a default value (serialized as string)
    * numeric range (min_value / max_value)
    * string pattern (regex)
    * value-domain constraint via Taxonomy reference
      (``allowed_taxonomy_id`` + ``allowed_node_ids``)

Relationship to other packages:

    Taxonomy (Sprint 23.1-C)  -- hierarchical label system
    Attribute (Sprint 23.1-D) -- typed property slot  <- this sprint
    KnowledgeObject (23.0-A)   -- uses attribute slots

V1 ships only the data contract and an append-only
registry. No retrieval, no embedding, no evolution
mutation, no AI.

Architecture boundary (Sprint 23.1-D spec):

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
        * caseos.knowledge.taxonomy (sibling Taxonomy)
        * stdlib
"""
from .object import (
    CONTENT_FIELDS,
    CONSTRAINT_FIELDS,
    IDENTITY_FIELDS,
    KnowledgeAttribute,
    KnowledgeAttributeError,
    KnowledgeAttributeSchemaError,
    METADATA_FIELDS,
)
from .schema import (
    ALL_FIELDS,
    ATTRIBUTE_TYPE_ALLOW_LIST,
    CARDINALITY_ALLOW_LIST,
    DATA_TYPE_ALLOW_LIST,
    FIELD_TYPES,
    REQUIRED_FIELDS,
    VERSION_POLICY,
)
from .registry import AttributeRegistry, AttributeRegistryError
from .validator import (
    KnowledgeAttributeValidator,
    AttributeValidationResult,
)
from .report import generate_attribute_report

__all__ = [
    # Object
    "KnowledgeAttribute",
    "KnowledgeAttributeError",
    "KnowledgeAttributeSchemaError",
    "IDENTITY_FIELDS",
    "CONTENT_FIELDS",
    "CONSTRAINT_FIELDS",
    "METADATA_FIELDS",
    # Schema
    "REQUIRED_FIELDS",
    "FIELD_TYPES",
    "VERSION_POLICY",
    "ATTRIBUTE_TYPE_ALLOW_LIST",
    "DATA_TYPE_ALLOW_LIST",
    "CARDINALITY_ALLOW_LIST",
    "ALL_FIELDS",
    # Validator
    "KnowledgeAttributeValidator",
    "AttributeValidationResult",
    # Registry
    "AttributeRegistry",
    "AttributeRegistryError",
    # Report
    "generate_attribute_report",
]
