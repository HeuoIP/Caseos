"""Recommendation Module (placeholder).

Real implementation is ADR-017. The placeholder assembles the
seven-section output template (Situation / Diagnosis / Strategy /
Experience / Implementation / Evidence / Confidence & Caveats) and
puts it into `ctx.recommendation`.

Contract:
    Input  : ctx.decision_object
             ctx.trust_object
             ctx.human_context
             ctx.knowledge_patterns
    Output : ctx.recommendation (dict with the seven sections)
"""

from __future__ import annotations

from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext


class RecommendationModule(Stage):
    """Placeholder Recommendation Engine stage."""

    name = "recommendation"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        decision = ctx.decision_object or {}
        trust = ctx.trust_object or {}
        human_ctx = ctx.human_context or {}
        ctx.recommendation = {
            "schema_version": "recommendation_v0_placeholder",
            "content_type": "Strategic",
            "audience_variant": "kindergarten_owner",  # placeholder
            "sections": {
                "situation_understanding": human_ctx.get("user_goal") or
                    ctx.project.user_goal,
                "problem_diagnosis": decision.get("diagnosis") or
                    "no obvious diagnosis available",
                "strategic_direction": decision.get("strategy") or
                    "no obvious strategy available",
                "experience_concept": decision.get("experience_logic") or
                    "no experience logic available",
                "implementation_direction":
                    "first move: " + (decision.get("priority") or "n/a"),
                "evidence": trust.get("evidence") or {},
                "confidence_and_caveats": {
                    "confidence": trust.get("confidence") or "Unknown",
                    # ADR-016 / Sprint 19.3: caveats come from
                    # uncertainty_handling (legacy uncertainty is
                    # tolerated for forward compat).
                    "caveats": trust.get("uncertainty_handling") or trust.get("uncertainty") or [],
                },
            },
        }
        return ctx


__all__ = ["RecommendationModule"]