"""Knowledge Object Domain Binding V1 (Sprint 23.1-B, ADR-018 / ADR-020).

This package is the **relationship layer** between
``KnowledgeObject`` (Sprint 23.0-A) and ``KnowledgeDomain``
(Sprint 23.1-A). A ``KODomainBinding`` declares that a
specific Knowledge Object belongs to a specific Domain,
under a particular ``binding_type`` (primary / secondary /
derived).

V1 ships only the data contract and an append-only
registry. No retrieval, no embedding, no evolution
mutation, no AI.

Binding Schema V1 surface:

    KODomainBinding         frozen dataclass (12 fields)
    BINDING_TYPE_ALLOW_LIST primary, secondary, derived
    BindingValidator        runtime guard
    BindingRegistry         append-only container
    generate_binding_report Markdown report

The binding NEVER mutates a Knowledge Object. It NEVER
mutates a Knowledge Domain. It is a pure relationship
record; future Retrieval / Evolution sprints may consume
it.

Architecture boundary (Sprint 23.1-B spec):

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
        * stdlib
"""
from .object import (
    IDENTITY_FIELDS,
    REFERENCE_FIELDS,
    METADATA_FIELDS,
    KODomainBinding,
    KODomainBindingError,
    KODomainBindingSchemaError,
)
from .schema import (
    ALL_FIELDS,
    BINDING_TYPE_ALLOW_LIST,
    BINDING_VERSION_POLICY,
    FIELD_TYPES,
    REQUIRED_FIELDS,
)
from .registry import BindingRegistry, BindingRegistryError
from .validator import BindingValidator, BindingValidationResult
from .report import generate_binding_report

__all__ = [
    # Object
    "KODomainBinding",
    "KODomainBindingError",
    "KODomainBindingSchemaError",
    "IDENTITY_FIELDS",
    "REFERENCE_FIELDS",
    "METADATA_FIELDS",
    # Schema
    "REQUIRED_FIELDS",
    "FIELD_TYPES",
    "BINDING_VERSION_POLICY",
    "BINDING_TYPE_ALLOW_LIST",
    "ALL_FIELDS",
    # Registry
    "BindingRegistry",
    "BindingRegistryError",
    # Validator
    "BindingValidator",
    "BindingValidationResult",
    # Report
    "generate_binding_report",
]
