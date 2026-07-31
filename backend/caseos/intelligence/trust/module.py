"""Trust Module (placeholder).

Real implementation is ADR-016. The placeholder emits a Trust Object
with the 5 fields defined in ADR-016 (evidence, source reliability,
applicability match, confidence level, uncertainty handling).

The default placeholder is HONEST about its low source quality:
`confidence = Low` with caveats. This is the canonical example of
ADR-016's Anti-Hallucination Principle applied at runtime.

Contract:
    Input  : ctx.decision_object
             ctx.knowledge_patterns
    Output : ctx.trust_object (dict with 5 fields)
"""

from __future__ import annotations

from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext


class TrustModule(Stage):
    """Placeholder Trust Model stage."""

    name = "trust"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        decision = ctx.decision_object or {}
        knowledge = ctx.knowledge_patterns or []
        # Honest placeholder: only Low confidence, full caveats.
        ctx.trust_object = {
            "schema_version": "trust_object_v0_placeholder",
            "evidence": {
                "decision_field_present": bool(decision),
                "knowledge_pattern_count": len(knowledge),
            },
            "source_reliability": ["placeholder-stage"],
            "applicability_match": "low",
            "confidence": "Low",
            "uncertainty": [
                "Reasoning was produced by a placeholder stage, not by ADR-014 Decision Intelligence.",
                "Evidence does not include real Golden Cases or Decision Rules yet (Sprint 20).",
            ],
        }
        return ctx


__all__ = ["TrustModule"]