"""
Decision Engine: orchestrates the agent pipeline.

Public API:

    engine = DecisionEngine()                  # default pipeline
    engine = DecisionEngine(pipeline=custom)   # custom pipeline

    ctx = engine.run(vision_json_dict)
    ctx = engine.run(vision_json_dict, context=existing_ctx)  # resume
    markdown = engine.run_report(vision_json_dict)

The engine never inspects agent internals -- it just walks the pipeline
list and invokes each agent's ``run(context)``. Any future agent can be
added by registering it and inserting its name into a Pipeline.
"""

from __future__ import annotations

import time
import traceback
from typing import Any

from app.core.decision.context import DecisionContext
from app.core.decision.knowledge import KnowledgeBase
from app.core.decision.pipeline import DEFAULT_PIPELINE, Pipeline


class DecisionEngine:
    """Run a sequence of agents against a single Vision JSON input."""

    def __init__(
        self,
        knowledge: KnowledgeBase | None = None,
        pipeline: Pipeline | None = None,
        repo_root: Any = None,
    ):
        # Default knowledge base lives at <repo_root>/knowledge/
        if knowledge is None and repo_root is not None:
            knowledge = KnowledgeBase(repo_root / "knowledge")
        self.knowledge = knowledge
        self.pipeline = pipeline or Pipeline(agent_names=list(DEFAULT_PIPELINE))
        self._agents = self.pipeline.build(knowledge=self.knowledge)

    @property
    def agent_names(self) -> list[str]:
        return [a.name for a in self._agents]

    def run(
        self,
        vision_json: dict[str, Any],
        context: DecisionContext | None = None,
    ) -> DecisionContext:
        """Execute the full pipeline against one Vision JSON dict.

        If ``context`` is provided it is used as the starting state;
        otherwise a fresh ``DecisionContext`` is created.
        """
        ctx = context if context is not None else DecisionContext(vision_json=vision_json)
        if ctx.vision_json is None and vision_json is not None:
            ctx.vision_json = vision_json
        ctx.add_metadata("pipeline", list(self.agent_names))

        for agent in self._agents:
            rec = ctx.record_stage(agent.name, status="running")
            t0 = time.perf_counter()
            try:
                agent.run(ctx)
                rec.status = "ok"
            except Exception as exc:  # surface to context, do not crash
                rec.status = "error"
                rec.note = f"{type(exc).__name__}: {exc}"
                ctx.add_metadata(
                    f"error.{agent.name}", traceback.format_exc()
                )
            finally:
                rec.finished_at = _now_iso()
                ctx.metadata[f"duration.{agent.name}"] = round(
                    time.perf_counter() - t0, 4
                )

        return ctx


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


__all__ = ["DecisionEngine"]