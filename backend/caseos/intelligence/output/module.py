"""Output Stage -- renders the Markdown report.

Sprint 21 update: forwards `ctx.human_context` AND the
`ctx.metadata["human_validation"]` block to the renderer so the
Human Understanding section appears in the Markdown report with
its validation verdict.

The pipeline wire contract (the stage\'s `name` and the slot it
populates, `ctx.metadata["markdown"]`) is unchanged.
"""
from __future__ import annotations

from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext
from caseos.cli.markdown_renderer import render_markdown


class OutputModule(Stage):
    name = "output"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        recommendation = ctx.recommendation or {"sections": {}}
        validation = None
        if isinstance(ctx.metadata, dict):
            v = ctx.metadata.get("human_validation")
            if isinstance(v, dict):
                validation = v
        ctx.metadata["markdown"] = render_markdown(
            project=ctx.project,
            recommendation=recommendation,
            trust=ctx.trust_object or {},
            evidence_package=ctx.evidence_package,
            human_context=ctx.human_context,
            human_validation=validation,
        )
        return ctx


__all__ = ["OutputModule"]
