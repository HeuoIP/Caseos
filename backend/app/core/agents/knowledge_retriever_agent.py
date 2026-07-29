"""Knowledge Retriever Agent: pulls relevant knowledge into the
DecisionContext so downstream agents (Strategy, Object Selector, Explain)
can reason with concrete references.

Pipeline slot: between DecisionMaker and Strategy.

Pipeline state flow after this agent runs:
  context.knowledge_context.related_themes      --> Theme refs
  context.knowledge_context.related_objects     --> Object refs
  context.knowledge_context.related_rules       --> Rule refs
  context.knowledge_context.related_handbook     --> Expert refs
  context.knowledge_context.related_reasoning   --> Reasoning refs
  context.knowledge_context.related_cases       --> Similar cases

The agent reuses the existing KnowledgeLoader and KnowledgeBase to build
a deterministic, local RelevantKnowledgeContext. No vector DB. No LLM.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.agents.base import Agent, AgentRegistry
from app.core.knowledge.knowledge_context import RelevantKnowledgeContext
from app.core.knowledge.knowledge_loader import KnowledgeLoader
from app.core.knowledge.retriever import KnowledgeRetriever

if TYPE_CHECKING:
    from app.core.decision.context import DecisionContext
    from app.core.decision.knowledge import KnowledgeBase


@AgentRegistry.register

class KnowledgeRetrieverAgent(Agent):
    """Reads Vision JSON + decision context, returns a RelevantKnowledgeContext.

    The agent is sensible to both the older YAML-based KnowledgeBase (used

    by Sprint 7 agents) and the new Markdown-based KnowledgeLoader (used by

    the retriever). If neither is wired in, the agent produces an empty

    context and the pipeline continues -- the engine never crashes.

    """

    name = "knowledge_retriever"
    display_name = "Knowledge Retriever"

    def __init__(self, knowledge="", knowledge_loader=None):
        super().__init__(knowledge=knowledge)
        self._loader = knowledge_loader
        self._retriever = None

    def _ensure_retriever(self):
        if self._retriever is not None:
            return self._retriever
        if self._loader is None:
            # Lazily derive a loader from the parent knowledge path if we can.
            kb_root = getattr(self.knowledge, "root", None)
            if kb_root is not None:
                self._loader = KnowledgeLoader(kb_root)
            else:
                return None
        self._retriever = KnowledgeRetriever(self._loader, knowledge_base=self.knowledge)
        return self._retriever

    def run(self, context: "DecisionContext") -> None:
        """Populate ``context.knowledge_context`` for this run.

        

        The agent is read-only with respect to the knowledge library. It

        only reads Vision JSON and the existing DecisionContext fields.

        """
        retriever = self._ensure_retriever()
        if retriever is None:
            context.knowledge_context = RelevantKnowledgeContext()
            context.add_metadata("knowledge_retriever.status", "skipped")
            return

        decision_context = self._decision_context_dict(context)
        ctx = retriever.retrieve(context.vision_json or {}, decision_context=decision_context)
        context.knowledge_context = ctx
        context.add_metadata("knowledge_retriever.status", "ok")
        context.add_metadata("knowledge_retriever.snippets", ctx.total_snippets())
        context.add_metadata("knowledge_retriever.stats", dict(ctx.stats))

    @staticmethod
    def _decision_context_dict(context: "DecisionContext") -> dict:
        """Project the context into a dict the retriever can consume."""
        out = {}
        if context.goals:
            out["goals"] = [{"goal_id": g.goal_id, "priority": g.priority} for g in context.goals]
        if context.strategies:
            out["strategies"] = [{"strategy_id": s.strategy_id, "priority": s.priority} for s in context.strategies]
        if context.space_summary:
            out["site_type"] = context.space_summary.site_type
            out["domain"] = context.space_summary.domain
        return out


__all__ = ["KnowledgeRetrieverAgent"]
