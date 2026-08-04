"""Knowledge Mutation Runtime V1 (Sprint 22.4-H, ADR-020).

This package implements the **first** real mutation runtime for
CaseOS Knowledge Evolution. It consumes:

    * MutationRequest
    * EvolutionTransaction (status == "APPROVED")
    * GovernanceResult (approved == True)
    * VersionStore
    * AuditStore
    * (optional) ChangeIntent

and produces:

    * A new immutable ``KnowledgeVersion`` appended to the
      VersionStore (the OLD version is never mutated).
    * An immutable ``EvolutionAuditRecord`` appended to the
      AuditStore (before/after snapshots).
    * A frozen ``MutationResult`` reporting the outcome.

Architecture boundary (Sprint 22.4-H spec):

    This package does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * caseos.knowledge.objects
        * stdlib

Forbidden:

    The mutation runtime does NOT expose:

        * restore()
        * rollback()
        * apply()
        * undo()

    Old KnowledgeVersions are NEVER overwritten. The runtime
    is purely additive.

Sprint chain:

    ChangeIntent (22.3.2)
        |
        v
    EvolutionTransaction (22.4-A)
        |
        v
    EvolutionGovernanceGate (22.4-B)
        |
        v
    KnowledgeMutationEngine (22.4-H) <-- this package
        |
        v
    KnowledgeVersion (22.4-D)  +  EvolutionAuditRecord (22.4-E)
"""
from __future__ import annotations

from .engine import KnowledgeMutationEngine
from .object import (
    MUTATION_ALLOWED_CHANGE_TYPES,
    MutationRequest,
    MutationValidationResult,
)
from .result import MutationResult
from .validator import MutationValidator

__all__ = [
    "KnowledgeMutationEngine",
    "MUTATION_ALLOWED_CHANGE_TYPES",
    "MutationRequest",
    "MutationResult",
    "MutationValidationResult",
    "MutationValidator",
]
