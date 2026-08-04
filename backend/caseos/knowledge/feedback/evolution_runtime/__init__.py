"""Feedback Evolution Runtime V1 (Sprint 22.5-A, ADR-018/020).

This package is the **real integration entry point** between
the Feedback Layer and the Knowledge Evolution Layer. It
orchestrates existing components -- FeedbackEvaluator,
ContradictionAnalyzer, InterpretationPolicy, EvolutionExecutor
-- and returns a single ``FeedbackEvolutionResult``.

Pipeline:

    FeedbackEvent
        |
        v
    Feedback Evaluation
        |
        v
    Contradiction Analysis
        |
        v
    Learning Proposal
        |
        v
    Human Review Gate
        |
        +-- not approved -> WAITING_HUMAN_REVIEW / REJECTED
        |
        v
    Interpretation
        |
        v
    ChangeIntent
        |
        v
    EvolutionTransaction
        |
        v
    EvolutionExecutor
        |
        v
    FeedbackEvolutionResult

Architecture boundary (Sprint 22.5-A spec):

    This package does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.feedback (sibling modules)
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from .builder import FeedbackEvolutionBuilder
from .object import (
    EVOLUTION_STATUS_APPROVED_AND_EXECUTED,
    EVOLUTION_STATUS_APPROVED_BUT_BLOCKED,
    EVOLUTION_STATUS_REJECTED,
    EVOLUTION_STATUS_WAITING_HUMAN_REVIEW,
    EVOLUTION_STATUSES,
    FeedbackEvolutionResult,
)
from .report import generate_report
from .runtime import (
    FeedbackEvolutionRuntime,
    execute_feedback_evolution,
)

__all__ = [
    "FeedbackEvolutionBuilder",
    "FeedbackEvolutionResult",
    "FeedbackEvolutionRuntime",
    "execute_feedback_evolution",
    "generate_report",
    "EVOLUTION_STATUS_WAITING_HUMAN_REVIEW",
    "EVOLUTION_STATUS_REJECTED",
    "EVOLUTION_STATUS_APPROVED_AND_EXECUTED",
    "EVOLUTION_STATUS_APPROVED_BUT_BLOCKED",
    "EVOLUTION_STATUSES",
]
