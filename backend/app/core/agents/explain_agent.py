"""Explain Agent: fill Reasoning templates for the top recommendations.

V1 does not call an LLM. For each top Recommendation, the agent:

  1. Picks 1-3 Reasoning patterns whose Uses_Goals intersect the
     inferred goals OR whose Uses_Strategies intersect served strategies.
     Patterns explicitly marked ``auto=False`` are excluded from the
     automatic top-3 (e.g. NEGATIVE_REASON is reserved for excluded items).
  2. Substitutes concrete {variable}s into Template_Chinese.
  3. Concatenates the filled templates into one Chinese paragraph.

If the framework is later wired to an LLM, this agent becomes the
adapter: same inputs, LLM-generated prose.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from app.core.agents.base import Agent, AgentRegistry
from app.core.decision.models import Explanation

if TYPE_CHECKING:
    from app.core.decision.context import DecisionContext


_VAR_RE = re.compile(r"\{(\w+)\}")


def _fill(template: str, factors: dict[str, str]) -> str:
    def repl(m: "re.Match[str]") -> str:
        key = m.group(1)
        return factors.get(key, "{" + key + "}")
    return _VAR_RE.sub(repl, template)


# Patterns excluded from automatic top-N. They are reserved for special
# contexts (e.g. explaining *why something was dropped*, *on request*).
_AUTO_EXCLUDE: set[str] = {
    "REASON.NEGATIVE_REASON",
}


@AgentRegistry.register
class ExplainAgent(Agent):
    name = "explain"
    display_name = "Explain Agent"

    def run(self, context) -> None:
        if context.top_recommendations is None:
            context.explanations = []
            return
        if self.knowledge is None:
            raise RuntimeError("ExplainAgent requires a KnowledgeBase")

        goal_names = {g.goal_id: g.name for g in context.goals}
        strategy_names = {s.strategy_id: s.name for s in context.strategies}
        space = context.space_summary

        explanations: list[Explanation] = []
        for rec in context.top_recommendations:
            factors = self._build_factors(
                rec=rec,
                goal_names=goal_names,
                strategy_names=strategy_names,
                space=space,
            )

            chosen = self._pick_patterns(rec)
            texts: list[str] = []
            for reason_id in chosen:
                entry = self.knowledge.reasoning(reason_id)
                if entry is None:
                    continue
                text = _fill(entry.template_zh, factors)
                if "{" in text:  # skip templates we could not fully fill
                    continue
                texts.append(text)

            paragraph = "\n".join(t for t in texts if t) or (
                f"\u56e0\u4e3a\u300c{rec.name}\u300d\u80fd\u591f\u670d\u52a1\u4e8e\u4f60\u7684\u76ee\u6807\u4e0e\u7b56\u7565\uff0c\u56e0\u6b64\u63a8\u8350\u3002"
            )
            explanations.append(Explanation(
                object_id=rec.object_id,
                patterns=chosen,
                text=paragraph,
                factors=factors,
            ))

        context.explanations = explanations
        context.add_metadata("explanation_count", len(explanations))

    # ----- helpers -----

    def _build_factors(self, *, rec, goal_names, strategy_names, space) -> dict[str, str]:
        return {
            "goal": _join_zh([goal_names[g] for g in rec.serves_goals if g in goal_names]) or "\u4f60\u7684\u76ee\u6807",
            "strategy": _join_zh([strategy_names[s] for s in rec.serves_strategies if s in strategy_names]) or "\u4f60\u7684\u7b56\u7565",
            "object": rec.name,
            "benefit": _object_benefit_zh(rec.object_id),
            "site_feature": _site_feature_zh(space),
            "age_group": _age_group_zh(space),
            "budget": "\u4e2d\u7b49\u9884\u7b97",
            "option": rec.name,
            "reason": "\u4e0e\u4f60\u7684\u573a\u666f\u3001\u76ee\u6807\u3001\u4ee5\u53ca\u4fdd\u7559\u7684\u7b56\u7565\u9ad8\u5ea6\u543b\u5408",
            "risk": "\u5b89\u5168\u4e0e\u5bb6\u957f\u4fdd\u969c",
            "case_reference": "\u540c\u7c7b\u6210\u529f\u6848\u4f8b",
            "outcome_metric": "\u80b2\u4e50\u5bb6\u53cd\u9988\u63d0\u5347",
            "mitigation": "\u53cc\u91cd\u4fdd\u62a4\u4e0e\u8def\u5f84\u8bbe\u8ba1",
            # NEW: fill in the remaining placeholders the templates use.
            "cost_ratio": "\u4e2d\u7b49\u4ef7\u683c",
            "expected_return": "\u9ad8\u9891\u8bbf\u5ba2\u91cf",
            "payback": "6-9 \u4e2a\u6708",
            "metric": "\u65e5\u5747\u62cd\u7167\u4eba\u6b21",
            "priority_a": "\u4f60\u7684\u4e3b\u8981\u76ee\u6807",
            "priority_b": "\u4f60\u7684\u6b21\u8981\u76ee\u6807",
            "choice": "\u4f60\u7684\u4e3b\u8981\u76ee\u6807",
            "rejected": "\u5176\u4ed6\u9009\u9879",
            "context": "\u4f60\u7684\u9879\u76ee\u573a\u666f",
            "constraint": "\u9884\u7b97\u4e0e\u73af\u5883",
            "time_horizon": "\u4e2d\u671f",
            "alternative": "\u5176\u4ed6\u53ef\u9009\u5bf9\u8c61",
            "conflict_a": "\u63d0\u4f9b\u8212\u9002",
            "conflict_b": "\u4e92\u52a8\u4f53\u9a8c",
            "resolution": "\u63d0\u4f9b\u8212\u9002",
            "culture": "\u672c\u5730\u6587\u5316",
            "heritage": "\u6587\u5316\u9057\u4ea7",
            "community": "\u793e\u533a",
            "expression": "\u73b0\u4ee3\u8bd1\u91ca",
            "pitfall": "\u7b26\u53f7\u5806\u780c",
            "amplification": "\u5b69\u5b50\u7684\u63a2\u7d22\u4f53\u9a8c",
            "preference": "\u63a2\u7d22\u4e0e\u89d2\u8272\u626e\u6f14",
            "developmental_stage": "\u8ba4\u77e5\u4e0e\u793e\u4ea4\u53d1\u5c55",
            "need": "\u5171\u540c\u60f3\u8c61\u4e0e\u8eab\u4f53\u53c2\u4e0e",
            "developmental_goal": "\u8eab\u4f53\u4e0e\u8ba4\u77e5\u53d1\u5c55",
            "safety": "\u5b89\u5168\u53ef\u63a7",
            "domain": "\u4f60\u7684\u9879\u76ee\u573a\u666f",
            "size": "\u9002\u5ea6\u89c4\u6a21",
            "existing_elements": "\u73b0\u6709\u8d44\u6e90",
            "climate": "\u9002\u7528\u6c14\u5019",
            "scale": "\u4e2d\u7b49\u89c4\u6a21",
        }

    def _pick_patterns(self, rec) -> list[str]:
        goal_ids = set(rec.serves_goals)
        strategy_ids = set(rec.serves_strategies)
        chosen: list[tuple[int, str]] = []
        for r in self.knowledge.reasonings:
            if r.reason_id in _AUTO_EXCLUDE:
                continue
            if r.uses_goals and set(r.uses_goals) != {"*"} and not (set(r.uses_goals) & goal_ids):
                continue
            if r.uses_strategies and set(r.uses_strategies) != {"*"} and not (set(r.uses_strategies) & strategy_ids):
                continue
            chosen.append((r.priority, r.reason_id))
        chosen.sort(key=lambda x: (-x[0], x[1]))
        return [rid for _, rid in chosen[:3]]


def _join_zh(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return "\u300c" + "\u300d\u4e0e\u300c".join(items[:-1]) + "\u300d\u4ee5\u53ca\u300c" + items[-1] + "\u300d"


def _object_benefit_zh(object_id: str) -> str:
    table = {
        "OBJECT.TREEHOUSE": "\u63d0\u4f9b\u9ad8\u5ea6\u4e0e\u63a2\u7d22\u4f53\u9a8c",
        "OBJECT.SLIDE": "\u63d0\u4f9b\u523a\u6fc0\u4e0e\u4e50\u8da3",
        "OBJECT.READING_CORNER": "\u63d0\u4f9b\u5b81\u9759\u4e0e\u5b66\u4e60\u7a7a\u95f4",
        "OBJECT.INTERACTIVE_WALL": "\u63d0\u4f9b\u4e92\u52a8\u4e0e\u53d1\u73b0",
        "OBJECT.IP_SCULPTURE": "\u63d0\u4f9b\u8bb0\u5fc6\u70b9\u4e0e\u54c1\u724c\u8bc6\u522b",
    }
    return table.get(object_id, "\u63d0\u4f9b\u4e0e\u4f60\u573a\u666f\u76f8\u5339\u914d\u7684\u4ef7\u503c")


def _site_feature_zh(space) -> str:
    if space is None:
        return "\u4f60\u7684\u573a\u5730"
    if space.vision_summary:
        return space.vision_summary.split("\uff0c")[0]
    if space.primary_theme:
        return f"\u4e3b\u9898\u300c{space.primary_theme}\u300d"
    return "\u4f60\u7684\u573a\u5730"


def _age_group_zh(space) -> str:
    if space is None or not space.age_groups:
        return "\u5b69\u7ae5"
    return "\u300c" + "\u300d\u3001\u300c".join(space.age_groups) + "\u300d"


__all__ = ["ExplainAgent"]