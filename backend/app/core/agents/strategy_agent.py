"""Strategy Agent: pick Strategies that serve the inferred Goals,
then emit an LLM-style StrategyAnalysis describing the strategic frame.

Algorithm (V1 rule-based):
  1. For each goal, find every Strategy whose Addresses_Goals contains it.
  2. Rank by priority and the number of goals served.
  3. Resolve Conflicts: drop the lower-priority strategy of any pair.
  4. Keep synergy partners when they do not conflict with anything kept.

Algorithm (Sprint 9 LLM-style reasoning):
  5. Render space + goals + knowledge + chosen strategies into four
     prose fields (space_positioning, core_problem, design_direction,
     investment_logic). The text is deterministic but reads like a
     senior strategist wrote it. A real LLM can replace it later.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.agents.base import Agent, AgentRegistry
from app.core.decision.models import StrategyAnalysis, StrategyRef

if TYPE_CHECKING:
    from app.core.decision.context import DecisionContext


@AgentRegistry.register
class StrategyAgent(Agent):
    name = "strategy"
    display_name = "Strategy Agent"

    def run(self, context) -> None:
        if not context.goals:
            context.strategies = []
            context.strategy_analysis = StrategyAnalysis(
                space_positioning="No goals were inferred; nothing to recommend.",
                confidence=0.0,
            )
            return
        if self.knowledge is None:
            raise RuntimeError("StrategyAgent requires a KnowledgeBase")

        goal_ids = {g.goal_id for g in context.goals}

        # Step 1+2: gather candidates
        candidates = []
        for entry in self.knowledge.strategies:
            serves = sorted(set(entry.addresses_goals) & goal_ids)
            if not serves:
                continue
            score = entry.priority * 10 + len(serves)
            ref = StrategyRef(
                strategy_id=entry.strategy_id,
                name=entry.name,
                name_en=entry.name_en,
                priority=entry.priority,
                addresses_goals=serves,
                conflicts_with=list(entry.conflicts_with),
                rationale=
                    "Serves " + str(len(serves)) + " inferred goal(s): "
                    + ", ".join(serves) + "; priority=" + str(entry.priority) + ".",
            )
            candidates.append((score, ref, entry))

        # Higher score first; tie-break by id for determinism.
        candidates.sort(key=lambda x: (-x[0], x[1].strategy_id))

        # Step 3: resolve conflicts. Greedy: keep first, drop conflicting.
        kept = []
        kept_ids = set()
        for _, ref, entry in candidates:
            if any(c in kept_ids for c in ref.conflicts_with):
                ref.rationale += " [dropped: conflicts with kept strategy]"
                continue
            kept.append(ref)
            kept_ids.add(ref.strategy_id)

        # Step 4: attach synergy partners (informational only).
        for ref in kept:
            entry = self.knowledge.strategy(ref.strategy_id)
            if entry is None:
                continue
            ref.serves_strategies = [
                s.strategy_id for s in kept
                if s.strategy_id != ref.strategy_id
                and s.strategy_id not in ref.conflicts_with
                and ref.strategy_id in entry.synergies
            ]

        context.strategies = kept
        context.add_metadata("strategy_count", len(kept))
        context.add_metadata(
            "strategy_ids",
            [s.strategy_id for s in kept],
        )

        # Sprint 9: emit LLM-style structured reasoning.
        context.strategy_analysis = self._build_analysis(context, kept)

    def _build_analysis(self, context, strategies) -> "StrategyAnalysis":
        """Produce a StrategyAnalysis in the ADR-005 contract.

        

        The agent does not call an LLM. It deterministically renders the

        space + goals + knowledge + chosen strategies into four fields

        that read like a senior strategist wrote them.

        """
        space = context.space_summary
        themes = []
        if context.knowledge_context and context.knowledge_context.related_themes:
            themes = [s.title for s in context.knowledge_context.related_themes[:3]]
        goal_names = [g.name for g in context.goals[:3]]
        strategy_names = [s.name for s in strategies[:5]]
        site_type = (space.site_type if space else "SITE.UNKNOWN") or "SITE.UNKNOWN"
        domain = (space.domain if space else "") or "the site"
        primary_audience = (
            "/".join(space.age_groups[:2]) if space and space.age_groups else "children"
        )
        theme_phrase = themes[0] if themes else "place-based"
        goal_phrase = goal_names[0] if goal_names else "value"
        strategy_phrase = (
            ", ".join(strategy_names[:3]) if strategy_names else "a coherent experience"
        )

        positioning = (
            "A " + domain + " venue at " + site_type
            + " positioned as a " + theme_phrase + " experience for " + primary_audience + "."
        )
        core_problem = (
            "The venue must generate " + goal_phrase
            + " while staying coherent with its " + theme_phrase
            + " narrative and operating within " + domain + " constraints."
        )
        direction = (
            "Pursue " + strategy_phrase
            + " as the lead moves, supported by " + theme_phrase
            + " symbolism and child-scale choreography."
        )
        investment = (
            "Investment concentrates on objects and elements that are "
            + "visible from the entrance, anchored to the " + theme_phrase
            + " and convertible into the user's " + goal_phrase + "."
        )

        refs = []
        if context.knowledge_context:
            for s in context.knowledge_context.related_themes[:3]:
                refs.append("theme:" + s.ref_id)
            for s in context.knowledge_context.related_handbook[:2]:
                refs.append("handbook:" + s.ref_id)

        return StrategyAnalysis(
            space_positioning=positioning,
            core_problem=core_problem,
            design_direction=direction,
            investment_logic=investment,
            confidence=round(0.7 + 0.05 * min(len(strategies), 5), 2),
            related_strategy_ids=[s.strategy_id for s in strategies],
            related_goal_ids=[g.goal_id for g in context.goals],
            knowledge_refs=refs,
        )


__all__ = ["StrategyAgent"]
