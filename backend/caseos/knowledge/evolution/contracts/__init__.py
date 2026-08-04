"""Evolution Change Type Contract (Sprint 22.4-I, ADR-020).

This package owns the single source of truth for the
``change_type`` taxonomy used across the CaseOS Knowledge
Evolution pipeline:

    LearningProposal   (proposal_type, with _candidate suffix)
        |
        v
    InterpretationPolicy
        |
        v
    ChangeIntent               <-- uses EvolutionChangeType
        |
        v
    EvolutionTransaction       <-- uses EvolutionChangeType
        |
        v
    EvolutionGovernanceGate
        |
        v
    KnowledgeMutationEngine    <-- uses EvolutionChangeType

The values are the bare taxonomy strings (no ``_candidate``
suffix). The ``_candidate`` suffix belongs to the upstream
proposal vocabulary and is consumed by the Interpretation
Policy before reaching the evolution layer.

Architecture boundary (Sprint 22.4-I spec):

    This package does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This package MAY import from:
        * stdlib
"""
from .change_type import EvolutionChangeType

__all__ = ["EvolutionChangeType"]
