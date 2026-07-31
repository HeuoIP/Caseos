"""Stage interface for the Brain pipeline.

A `Stage` is the smallest runnable unit in the runtime. The Pipeline
(Sprint 19.1 spec section "Pipeline Execution") chains stages; each
stage returns nothing (it mutates `PipelineContext` in place) so the
type signature is uniform regardless of what the stage does.

Real intelligence modules from Sprint 20+ will be Stages that fulfil
this interface exactly. The placeholder modules in
`caseos.intelligence.*` are already written as Stage subclasses.
"""

from __future__ import annotations

import abc
from typing import Callable

from .context import PipelineContext, ProjectContext


class Stage(abc.ABC):
    """Base class for any pipeline stage.

    Attributes:
        name: short identifier used in logs and the stage registry.
    """

    name: str = "unnamed"

    @abc.abstractmethod
    def run(self, ctx: PipelineContext) -> PipelineContext:
        """Execute the stage.

        Implementations MUST mutate `ctx` in place and return it.
        Returning the context makes call sites readable:
            ctx = stage.run(ctx)
        """
        raise NotImplementedError


# A convenience type: any callable that takes a context and returns it.
StageCallable = Callable[[PipelineContext], PipelineContext]


def call(stage_name: str, fn: StageCallable) -> Stage:
    """Adapter that turns a plain function into a `Stage` instance.

    Useful when a stage is only one or two lines. The standard
    modules in `caseos.intelligence.*` are full classes; ad-hoc tests
    and experiment scripts use this helper.
    """

    class _FnStage(Stage):
        def run(self, ctx: PipelineContext) -> PipelineContext:
            return fn(ctx)

    _FnStage.name = stage_name
    return _FnStage()


def run_stage(stage: Stage, ctx: PipelineContext) -> PipelineContext:
    """Run a single stage with error wrapping.

    A Stage that raises is logged into `ctx.stage_log` then re-raised.
    The pipeline uses this so that one bad stage does not corrupt
    later stages silently.
    """

    try:
        out = stage.run(ctx)
    except Exception as exc:  # pragma: no cover - defensive
        ctx.stage_log(stage.name, status="error", error=str(exc))
        raise
    else:
        ctx.stage_log(stage.name, status="ok")
        return out


__all__ = ["Stage", "StageCallable", "call", "run_stage"]


def new_pipeline_context(project: ProjectContext) -> PipelineContext:
    """Convenience factory."""
    return PipelineContext(project=project)