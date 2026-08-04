"""Feedback Evolution Builder V1 (Sprint 22.5-A, ADR-018/020).

The builder is a **dependency-injection helper**. It assembles
the existing components (FeedbackEvaluator, ContradictionAnalyzer,
InterpretationPolicy, EvolutionExecutor) into a single
``FeedbackEvolutionRuntime`` instance.

The builder does NOT contain business logic. It does NOT decide
whether a feedback event should proceed past the human gate.
It does NOT mutate any state. It only wires collaborators.

This separation keeps ``runtime.py`` focused on orchestration
flow and lets tests build custom runtimes with fakes / mocks /
in-memory stores.

Architecture boundary (Sprint 22.5-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.feedback
        * caseos.knowledge.feedback.evolution_runtime
        * caseos.knowledge.evolution
        * caseos.knowledge.evolution.contracts
        * stdlib
"""
from __future__ import annotations

from typing import Optional

from caseos.knowledge.evolution.audit_v2 import AuditStore
from caseos.knowledge.evolution.runtime_v2.executor import (
    EvolutionExecutor,
)
from caseos.knowledge.evolution.versioning import VersionStore

from caseos.knowledge.feedback.evaluation import FeedbackEvaluator
from caseos.knowledge.feedback.evaluation.analyzer import (
    ContradictionAnalyzer,
)
from caseos.knowledge.feedback.interpretation import (
    InterpretationPolicy,
)

from .runtime import FeedbackEvolutionRuntime


class FeedbackEvolutionBuilder:
    """Assembles a ``FeedbackEvolutionRuntime``.

    Every collaborator is an optional constructor argument.
    Defaults are constructed lazily so the builder has no
    side effects at instantiation time.

    The builder is intentionally **stateless** -- its only
    responsibility is to produce a configured runtime.
    """

    def __init__(
        self,
        *,
        feedback_evaluator: Optional[FeedbackEvaluator] = None,
        contradiction_analyzer: Optional[ContradictionAnalyzer] = None,
        interpretation_policy: Optional[InterpretationPolicy] = None,
        evolution_executor: Optional[EvolutionExecutor] = None,
        version_store: Optional[VersionStore] = None,
        audit_store: Optional[AuditStore] = None,
    ) -> None:
        self._feedback_evaluator = feedback_evaluator
        self._contradiction_analyzer = contradiction_analyzer
        self._interpretation_policy = interpretation_policy
        self._evolution_executor = evolution_executor
        self._version_store = version_store
        self._audit_store = audit_store

    def with_components(
        self,
        *,
        feedback_evaluator: Optional[FeedbackEvaluator] = None,
        contradiction_analyzer: Optional[ContradictionAnalyzer] = None,
        interpretation_policy: Optional[InterpretationPolicy] = None,
        evolution_executor: Optional[EvolutionExecutor] = None,
        version_store: Optional[VersionStore] = None,
        audit_store: Optional[AuditStore] = None,
    ) -> "FeedbackEvolutionBuilder":
        """Return a new builder with the given overrides.

        The builder pattern is fluent: ``builder.with_components(
        ...).build()`` produces a fully configured runtime.
        The original builder instance is NOT mutated.
        """
        return FeedbackEvolutionBuilder(
            feedback_evaluator=feedback_evaluator or self._feedback_evaluator,
            contradiction_analyzer=(
                contradiction_analyzer or self._contradiction_analyzer
            ),
            interpretation_policy=(
                interpretation_policy or self._interpretation_policy
            ),
            evolution_executor=evolution_executor or self._evolution_executor,
            version_store=version_store or self._version_store,
            audit_store=audit_store or self._audit_store,
        )

    def build(self) -> FeedbackEvolutionRuntime:
        """Produce a ``FeedbackEvolutionRuntime`` instance.

        Defaults are filled in lazily:

            * FeedbackEvaluator        -- no-arg constructor
            * ContradictionAnalyzer    -- no-arg constructor
            * InterpretationPolicy     -- no-arg constructor
            * VersionStore / AuditStore -- empty append-only stores
            * EvolutionExecutor        -- wires the above stores
        """
        feedback_evaluator = (
            self._feedback_evaluator or FeedbackEvaluator()
        )
        contradiction_analyzer = (
            self._contradiction_analyzer or ContradictionAnalyzer()
        )
        interpretation_policy = (
            self._interpretation_policy or InterpretationPolicy()
        )
        version_store = self._version_store or VersionStore()
        audit_store = self._audit_store or AuditStore()
        evolution_executor = self._evolution_executor or EvolutionExecutor(
            version_store=version_store,
            audit_store=audit_store,
        )
        return FeedbackEvolutionRuntime(
            feedback_evaluator=feedback_evaluator,
            contradiction_analyzer=contradiction_analyzer,
            interpretation_policy=interpretation_policy,
            evolution_executor=evolution_executor,
            version_store=version_store,
            audit_store=audit_store,
        )


__all__ = ["FeedbackEvolutionBuilder"]
