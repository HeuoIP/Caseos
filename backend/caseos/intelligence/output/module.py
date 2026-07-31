"""Output Stage -- renders the Markdown report."""
from __future__ import annotations
from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext
from caseos.cli.markdown_renderer import render_markdown


class OutputModule(Stage):
    name = "output"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        recommendation = ctx.recommendation or {"sections": {}}
        ctx.metadata["markdown"] = render_markdown(
            project=ctx.project,
            recommendation=recommendation,
            trust=ctx.trust_object or {},
        )
        return ctx


__all__ = ["OutputModule"]