"""Strategy Agent: pick Strategies that serve the inferred Goals.

Algorithm (V1):
  1. For each goal, find every Strategy whose ``Addresses_Goals``
     contains it.
  2. Rank by priority and the number of goals served.
  3. Resolve Conflicts: drop the lower-priority strategy of any pair.
  4. Keep synergy partners when they don't conflict with anything kept.

The output is a list of StrategyRef objects. No objects are chosen here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.agents.base import Agent, AgentRegistry
from app.core.decision.models import StrategyRef

if TYPE_CHECKING:
    from app.core.decision.context import DecisionContext


@AgentRegistry.register
class StrategyAgent(Agent):
    name = "strategy"
    display_name = "Strategy Agent"

    def run(self, context) -> None:
        if not context.goals:
            context.strategies = []
            return
        if self.knowledge is None:
            raise RuntimeError("StrategyAgent requires a KnowledgeBase")

        goal_ids = {g.goal_id for g in context.goals}

        # Step 1+2: gather candidates
        candidates: list[tuple[float, StrategyRef]] = []
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
                rationale=(
                    f"Serves {len(serves)} inferred goal(s): "
                    f"{', '.join(serves)}; priority={entry.priority}."
                ),
            )
            candidates.append((score, ref, entry))

        # Higher score first; tie-break by id for determinism.
        candidates.sort(key=lambda x: (-x[0], x[1].strategy_id))

        # Step 3: resolve conflicts. Greedy: keep first, drop conflicting.
        kept: list[StrategyRef] = []
        kept_ids: set[str] = set()
        for _, ref, entry in candidates:
            if any(c in kept_ids for c in ref.conflicts_with):
                ref.rationale += " [dropped: conflicts with kept strategy]"
                continue
            kept.append(ref)
            kept_ids.add(ref.strategy_id)

        # Step 4: attach synergy partners (informational only).
        # Use the original StrategyEntry's synergies list -- this is the
        # canonical knowledge, not the in-memory StrategyRef.
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


__all__ = ["StrategyAgent"]