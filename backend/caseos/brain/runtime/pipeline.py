"""The Brain pipeline.

A `Pipeline` is an ordered list of `Stage`s. The spec (Sprint 19.1
section "Pipeline Execution") requires six stages in this order:

    Input (ProjectContext)
        -> Human Understanding
        -> Knowledge
        -> Retrieval      (Sprint 20 / ADR-019)
        -> Decision
        -> Trust
        -> Recommendation
        -> Output (Markdown render)

The default pipeline (`default_pipeline`) wires the placeholder
implementations from `caseos.intelligence.*`. Sprint 20+ will
substitute real reasoning without changing this skeleton.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .context import PipelineContext, ProjectContext
from .executor import Stage, run_stage


@dataclass
class Pipeline:
    """Ordered sequence of Stages."""

    stages: list[Stage] = field(default_factory=list)

    def add(self, stage: Stage) -> "Pipeline":
        self.stages.append(stage)
        return self

    def run(self, project: ProjectContext) -> PipelineContext:
        """Execute every stage in order. Returns the final context."""
        ctx = PipelineContext(project=project)
        ctx.stage_log("pipeline", stages=[s.name for s in self.stages])
        for stage in self.stages:
            run_stage(stage, ctx)
        return ctx


def default_pipeline(stages: Iterable[Stage] | None = None) -> Pipeline:
    """Build the six-stage default pipeline.

    If `stages` is provided, those stages are used (useful for tests
    that want to mock one or two). Otherwise the placeholder modules
    from `caseos.intelligence.*` are wired in. Importing the
    placeholders is deferred to avoid a circular import.
    """

    if stages is None:
        from caseos.intelligence.human.module import HumanModule
        from caseos.intelligence.knowledge.module import KnowledgeModule
        from caseos.knowledge.retrieval.module import KnowledgeRetriever
        from caseos.intelligence.decision.module import DecisionModule
        from caseos.intelligence.trust.module import TrustModule
        from caseos.intelligence.recommendation.module import (
            RecommendationModule,
        )
        from caseos.intelligence.output.module import OutputModule

        stages = [
            HumanModule(),
            KnowledgeModule(),
            KnowledgeRetriever(),
            DecisionModule(),
            TrustModule(),
            RecommendationModule(),
            OutputModule(),
        ]

    return Pipeline(stages=list(stages))


__all__ = ["Pipeline", "default_pipeline"]