"""Explain Agent: turn the decision context into customer-facing
language for each top recommendation.

Sprint 9 upgrade:
  * Consumes the StrategyAnalysis emitted by StrategyAgent (the
    LLM-style positioning + direction text) and the KnowledgeContext
    from the retriever. The output reads like a senior designer
    explained the choice to a paying client, not like an AI.
  * Avoids jargon: it should never read as marketing fluff OR
    technical AI language. Avoid words like striking / amazing /
    iconic / world-class. Use concrete physical features instead.

V1 is rule-based. An LLM can replace the text-generation step later
without changing the agent interface.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.core.agents.base import Agent, AgentRegistry
from app.core.decision.models import Explanation

if TYPE_CHECKING:
    from app.core.decision.context import DecisionContext


_VAR_RE = re.compile("{(.+?)}")


def _fill(template, factors):
    def repl(m):
        key = m.group(1)
        return factors.get(key, "{" + key + "}")
    return _VAR_RE.sub(repl, template)


AUTO_EXCLUDE = set()


def _object_benefit_zh(object_id):
    table = {
        "OBJECT.TREEHOUSE": "child-scale height and exploration.",
        "OBJECT.SLIDE": "a clear movement payoff at the end of a climb.",
        "OBJECT.READING_CORNER": "a quiet sit-down zone close to the action.",
        "OBJECT.INTERACTIVE_WALL": "low-height play that does not queue.",
        "OBJECT.IP_SCULPTURE": "a memorable landmark readable from the entrance.",
    }
    return table.get(object_id, "a concrete, visible feature that fits the scene.")

def _site_feature_zh(space):
    if space is None:
        return "the site"
    if space.vision_summary:
        return space.vision_summary.split(",")[0]
    if space.primary_theme:
        return "the " + (space.primary_theme or "") + " theme"
    return "the site"

def _age_group_zh(space):
    if space is None or not space.age_groups:
        return "children"
    return " / ".join(space.age_groups)

def _join_zh(items):
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return " and ".join(items)

def _strategy_direction_zh(context):
    """Pick the cleanest one-sentence direction from the strategy analysis."""
    if context.strategy_analysis and context.strategy_analysis.design_direction:
        return context.strategy_analysis.design_direction
    if not context.strategies:
        return "a coherent experience"
    names = [s.name for s in context.strategies[:3]]
    return _join_zh(names)

def _theme_benefit_zh(context):
    """Pick the most relevant theme from the retrieved knowledge context."""
    if context.knowledge_context and context.knowledge_context.related_themes:
        first = context.knowledge_context.related_themes[0]
        return first.title or first.ref_id
    if context.space_summary and context.space_summary.primary_theme:
        return context.space_summary.primary_theme
    return "the chosen theme"

def _goal_label_zh(context):
    if context.goals:
        return context.goals[0].name or "your goal"
    return "your goal"

@AgentRegistry.register
class ExplainAgent(Agent):
    name = "explain"
    display_name = "Explain Agent"

    def run(self, context):
        if not context.top_recommendations:
            context.explanations = []
            return
        if self.knowledge is None:
            raise RuntimeError("ExplainAgent requires a KnowledgeBase")

        out = []
        for rec in context.top_recommendations:
            factors = self._build_factors(context, rec)
            template = self._select_template(context, rec)
            text = _fill(template, factors)
            patterns = self._pick_patterns(rec)
            out.append(Explanation(
                object_id=rec.object_id,
                patterns=patterns,
                text=text,
                factors=factors,
            ))
        context.explanations = out
        context.add_metadata("explain_count", len(out))

    def _build_factors(self, context, rec):
        space = context.space_summary
        goal_names = {g.goal_id: g.name for g in context.goals}
        strategy_names = {s.strategy_id: s.name for s in context.strategies}
        factors = {
            "goal": _join_zh([goal_names[g] for g in rec.serves_goals if g in goal_names]) or "your goal",
            "strategy": _join_zh([strategy_names[s] for s in rec.serves_strategies if s in strategy_names]) or "the strategy",
            "object": rec.name,
            "benefit": _object_benefit_zh(rec.object_id),
            "site_feature": _site_feature_zh(space),
            "age_group": _age_group_zh(space),
            "theme_benefit": _theme_benefit_zh(context),
            "strategy_direction": _strategy_direction_zh(context),
            "goal_label": _goal_label_zh(context),
            "reason": "matches your goal, scene, and the kept strategies.",
        }
        return factors

    def _select_template(self, context, rec):
        """Pick the customer-friendly template (Sprint 9 default)."""
        return "{object} brings {benefit} It fits {theme_benefit} and serves {goal}, while {strategy_direction}"

    def _pick_patterns(self, rec):
        goal_ids = set(rec.serves_goals)
        strategy_ids = set(rec.serves_strategies)
        chosen = []
        for r in self.knowledge.reasonings:
            if r.reason_id in AUTO_EXCLUDE:
                continue
            if r.uses_goals and set(r.uses_goals) != {"*"} and not (set(r.uses_goals) & goal_ids):
                continue
            if r.uses_strategies and set(r.uses_strategies) != {"*"} and not (set(r.uses_strategies) & strategy_ids):
                continue
            chosen.append((r.priority, r.reason_id))
        chosen.sort(key=lambda x: (-x[0], x[1]))
        return [rid for _, rid in chosen[:3]]


__all__ = ["ExplainAgent"]

