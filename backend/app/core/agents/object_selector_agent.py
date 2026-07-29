"""Object Selector Agent: pick concrete Objects that implement the Strategies.

Algorithm (V1):
  1. Build the union of all kept Strategies' ``Typical_Implementations``.
     These are object *categories* (e.g. "Landmark", "Theme Sculpture").
  2. Scan the Object Library (knowledge/objects/*.md) and score each
     Object whose Category overlaps the desired categories. Matching is
     case-insensitive and substring-based, so strategy-side vocabulary
     like ``"Theme Sculpture"`` matches object-side ``"SCULPTURE"`` etc.
  3. The top N (default 5) become Recommendations; the rest are kept as
     ObjectCandidates for transparency.

V1 does not call any LLM. It is a deterministic, explainable heuristic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.agents.base import Agent, AgentRegistry
from app.core.decision.models import ObjectCandidate, Recommendation

if TYPE_CHECKING:
    from app.core.decision.context import DecisionContext


TOP_N_DEFAULT = 5


def _norm(s: str) -> str:
    """Lowercase + collapse separators so 'Theme Sculpture' == 'SCULPTURE'."""
    return s.lower().replace("_", " ").replace("/", " ").strip()


def _categories_match(want_norm: str, obj_cat_norm: str) -> bool:
    """Either substring containment in either direction is enough."""
    tokens_want = [t for t in want_norm.split() if t]
    return any(t in obj_cat_norm for t in tokens_want)


@AgentRegistry.register
class ObjectSelectorAgent(Agent):
    name = "object_selector"
    display_name = "Object Selector Agent"
    top_n: int = TOP_N_DEFAULT

    def run(self, context) -> None:
        if not context.strategies:
            context.object_candidates = []
            context.top_recommendations = []
            return
        if self.knowledge is None:
            raise RuntimeError("ObjectSelectorAgent requires a KnowledgeBase")

        # 1. Collect categories desired by kept strategies.
        wanted_categories: dict[str, list[str]] = {}
        for s in context.strategies:
            entry = self.knowledge.strategy(s.strategy_id)
            if entry is None:
                continue
            for cat in entry.typical_implementations:
                wanted_categories.setdefault(cat, []).append(s.strategy_id)

        if not wanted_categories:
            context.object_candidates = []
            context.top_recommendations = []
            return

        wanted_norm = {_norm(cat): sids for cat, sids in wanted_categories.items()}
        space_domain = (context.space_summary.domain if context.space_summary else "")
        goal_ids = {g.goal_id for g in context.goals}

        # 2. Score each object whose categories intersect wanted categories.
        candidates: list[ObjectCandidate] = []
        for obj in self.knowledge.objects.values():
            obj_cats = [c.strip() for c in obj.category.split("/") if c.strip()]
            obj_cats_norm = [_norm(c) for c in obj_cats]

            matched_strategies: list[str] = []
            matched_categories: list[str] = []
            for cat, cat_norm in zip(obj_cats, obj_cats_norm):
                for want, sids in wanted_norm.items():
                    if _categories_match(want, cat_norm):
                        matched_strategies.extend(sids)
                        matched_categories.append(cat)

            if not matched_strategies:
                continue
            score = 0.0
            score += 3.0 * len(set(matched_strategies))
            if space_domain and space_domain in obj.domain_affinity:
                score += 1.0
            best_priority = 0
            for sid in set(matched_strategies):
                e = self.knowledge.strategy(sid)
                if e is not None and e.priority > best_priority:
                    best_priority = e.priority
            score += 0.5 * (best_priority / 5.0)

            candidates.append(ObjectCandidate(
                object_id=obj.object_id,
                name=obj.name,
                category=obj.category,
                score=round(score, 3),
                serves_goals=sorted(goal_ids),
                serves_strategies=sorted(set(matched_strategies)),
                notes=(
                    f"Categories {matched_categories} matched "
                    f"{sorted(set(matched_strategies))}"
                ),
            ))

        # 3. Stable rank: score desc, then id asc.
        candidates.sort(key=lambda c: (-c.score, c.object_id))

        context.object_candidates = candidates
        top = candidates[: self.top_n]
        context.top_recommendations = [
            Recommendation(
                rank=i + 1,
                object_id=c.object_id,
                name=c.name,
                score=c.score,
                categories=[c.category],
                serves_goals=list(c.serves_goals),
                serves_strategies=list(c.serves_strategies),
                rationale_short=(
                    f"Served by {len(c.serves_strategies)} strategy(s): "
                    f"{', '.join(c.serves_strategies)}."
                ),
            )
            for i, c in enumerate(top)
        ]
        context.add_metadata("candidates_total", len(candidates))
        context.add_metadata(
            "top_recommendation_ids",
            [r.object_id for r in context.top_recommendations],
        )


__all__ = ["ObjectSelectorAgent", "TOP_N_DEFAULT"]