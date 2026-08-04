"""Knowledge Graph Validation Runtime V1 (Sprint 23.2-A).

This package is the **cross-layer consistency checker**
for the CaseOS knowledge graph. It reads the V1 data
contracts produced by the 23.0 / 23.1 sprints:

    KnowledgeObject      (Sprint 23.0-A)
    KnowledgeDomain      (Sprint 23.1-A)
    KODomainBinding      (Sprint 23.1-B)
    Taxonomy             (Sprint 23.1-C)
    TaxonomyNode         (Sprint 23.1-C)
    KnowledgeAttribute   (Sprint 23.1-D)

and reports consistency violations as a structured
``ValidationResult``. The runtime NEVER mutates any of
the supplied graph components; it is a pure reader.

V1 ships only the runtime contract:

    ValidationRequest     frozen dataclass (input)
    ValidationResult      frozen dataclass (output)
    GraphIssue            frozen dataclass (single issue)
    KnowledgeGraphValidator  cross-layer checker
    generate_graph_report   Markdown report

Architecture boundary (Sprint 23.2-A spec):

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
        * caseos.knowledge.attribute (sibling Attribute)
        * stdlib
"""
from .object import (
    GraphIssue,
    GraphIssueError,
    GraphValidationResult,
    GraphValidationRequest,
    GraphValidationError,
    SEVERITY_ALLOW_LIST,
    TARGET_KIND_ALLOW_LIST,
)
from .validator import KnowledgeGraphValidator
from .report import generate_graph_report

__all__ = [
    # Objects
    "GraphIssue",
    "GraphIssueError",
    "GraphValidationRequest",
    "GraphValidationResult",
    "GraphValidationError",
    "SEVERITY_ALLOW_LIST",
    "TARGET_KIND_ALLOW_LIST",
    # Validator
    "KnowledgeGraphValidator",
    # Report
    "generate_graph_report",
]
