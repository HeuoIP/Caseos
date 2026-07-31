"""Human Understanding Module (placeholder).

Real implementation is owned by ADR-013. This skeleton only proves
that the pipeline can call the module and that the module writes
a structured object into `ctx.human_context`.

Contract:
    Input  : ctx.project  (ProjectContext)
    Output : ctx.human_context (dict)
"""

from __future__ import annotations

from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext


class HumanModule(Stage):
    """Placeholder that derives a HumanContext from the ProjectContext."""

    name = "human_understanding"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        project = ctx.project
        ctx.human_context = {
            "schema_version": "human_context_v0_placeholder",
            "project_id": project.project_id,
            "user_goal": project.user_goal,
            "decision_style": "supportive",  # stub
            "language_preference": "zh-CN",  # stub
        }
        return ctx


__all__ = ["HumanModule"]