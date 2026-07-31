"""Decision Module (placeholder).

Real implementation lands in ADR-014. The placeholder synthesises a
`Decision Object` shaped like the 7-field template (problem / diagnosis
/ priority / strategy / experience_logic / boundaries / reasoning).

Contract:
    Input  : ctx.project
             ctx.human_context
             ctx.knowledge_patterns
    Output : ctx.decision_object (dict with 7 fields)
"""

from __future__ import annotations

from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext


class DecisionModule(Stage):
    """Placeholder Decision Intelligence stage."""

    name = "decision"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        project = ctx.project
        goal = project.user_goal or "improve space suitability"
        problem = project.site_description or "space lacks identity"
        ctx.decision_object = {
            "schema_version": "decision_object_v0_placeholder",
            "problem": problem,
            "diagnosis": "no memorable experience anchor",
            "priority": "create one anchored experience before adding secondary facilities",
            "strategy": "build a single thematically anchored experience node",
            "experience_logic": "enter -> explore -> interact -> stay -> repeat",
            "boundaries": [
                "do not recommend equipment stacking",
                "do not propose a luxury finish under budget constraints",
            ],
            "reasoning": (
                "Placeholder reasoning. Real Decision Intelligence is "
                "wired in Sprint 20 via ADR-014."
            ),
        }
        return ctx


__all__ = ["DecisionModule"]