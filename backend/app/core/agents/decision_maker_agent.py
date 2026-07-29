"""Decision Maker Agent: infer who decides + what they likely want.

V1 is a transparent rule-based heuristic. There is no LLM in this
agent -- the framework is an architecture first, intelligence later.

Heuristic:
  1. Use the SpaceAgent.domain to pick a profile.
  2. From that profile, pick 2-4 default goals (highest priority that
     fit the domain).
  3. Optionally fold in user_age / site_type hints for finer ranking.

The output is a DecisionMaker + a ranked list of GoalRef.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.agents.base import Agent, AgentRegistry
from app.core.decision.models import DecisionMaker, GoalRef

if TYPE_CHECKING:
    from app.core.decision.context import DecisionContext


# Profile table: domain -> (profile_id, description, default_goal_ids)
_PROFILE_BY_DOMAIN: dict[str, tuple[str, str, list[str]]] = {
    "COMMERCIAL": (
        "COMMERCIAL_OPERATOR",
        "Owner or operator of a commercial venue (mall, plaza, brand space). "
        "Cares about foot traffic, dwell time, brand perception, and revenue.",
        ["BUSINESS.TRAFFIC", "PHOTO.SHARING", "BUSINESS.BRAND"],
    ),
    "TOURISM": (
        "TOURISM_OPERATOR",
        "Operator of a tourist destination (theme park, scenic site, cultural venue). "
        "Cares about distinctiveness, social sharing, repeat visits.",
        ["BUSINESS.TRAFFIC", "BUSINESS.DIFFERENTIATION", "PHOTO.SHARING"],
    ),
    "EDUCATION": (
        "EDUCATOR",
        "Educator or institution (kindergarten, school, museum). "
        "Cares about child development, learning outcomes, and parent trust.",
        ["EDU.LEARNING", "CHILD.DEVELOPMENT", "EDU.ENROLLMENT"],
    ),
    "MUSEUM": (
        "CULTURAL_CURATOR",
        "Curator or museum operator. Cares about cultural authenticity, "
        "learning, and visitor engagement.",
        ["EDU.LEARNING", "CULTURAL.HERITAGE", "EDU.DISCOVERY"],
    ),
    "PUBLIC_PARK": (
        "PUBLIC_ADMIN",
        "Municipal or community administrator. Cares about inclusion, "
        "community activity, and broad usability.",
        ["COMMUNITY.ACTIVITY", "COMMUNITY.INCLUSION", "COMMUNITY.BONDING"],
    ),
    "URBAN_PLAZA": (
        "URBAN_OPERATOR",
        "Operator of a public urban space (plaza, square). Cares about "
        "activation, identity, and footfall.",
        ["COMMUNITY.ACTIVITY", "PHOTO.SHARING", "BUSINESS.DIFFERENTIATION"],
    ),
    "RESIDENTIAL": (
        "RESIDENTIAL_OPERATOR",
        "Residential community manager or developer. Cares about family "
        "experience, parent-child bonding, and quiet enjoyment.",
        ["COMMUNITY.BONDING", "CHILD.PLAY_VALUE", "PERSONAL.RELAXATION"],
    ),
    "INDOOR_PLAY": (
        "INDOOR_OPERATOR",
        "Operator of an indoor play / family entertainment center. Cares "
        "about play value, weather-proof revenue, repeat visits.",
        ["BUSINESS.REVENUE", "CHILD.PLAY_VALUE", "COMMUNITY.BONDING"],
    ),
    "PLAYGROUND": (
        "PLAYGROUND_OPERATOR",
        "Operator of a public or private playground. Cares about child "
        "development, play value, and family experience.",
        ["CHILD.PLAY_VALUE", "CHILD.DEVELOPMENT", "COMMUNITY.BONDING"],
    ),
}


@AgentRegistry.register
class DecisionMakerAgent(Agent):
    name = "decision_maker"
    display_name = "Decision Maker Agent"

    def run(self, context) -> None:
        if context.space_summary is None:
            raise RuntimeError(
                "DecisionMakerAgent requires space_summary; run SpaceAgent first."
            )

        domain = context.space_summary.domain or "PLAYGROUND"
        profile_id, description, default_goal_ids = _PROFILE_BY_DOMAIN.get(
            domain,
            _PROFILE_BY_DOMAIN["PLAYGROUND"],
        )

        rationale = (
            f"Site domain is {domain!r}; mapping to profile {profile_id!r} "
            f"with default goals {default_goal_ids}."
        )
        context.decision_maker = DecisionMaker(
            profile=profile_id,
            description=description,
            typical_goals=default_goal_ids,
            rationale=rationale,
        )

        # Resolve goal refs from knowledge base, ranked by priority.
        inferred: list[GoalRef] = []
        if self.knowledge is not None:
            for gid in default_goal_ids:
                entry = self.knowledge.goal(gid)
                if entry is None:
                    continue
                inferred.append(GoalRef(
                    goal_id=entry.goal_id,
                    name=entry.name,
                    name_en=entry.name_en,
                    priority=entry.priority,
                    confidence=1.0,
                    rationale=f"Default goal for profile {profile_id}.",
                    domain_affinity=list(entry.domain_affinity),
                    conflicts_with=list(entry.conflicts_with),
                ))
            # Sort highest priority first
            inferred.sort(key=lambda g: (-g.priority, g.goal_id))

        # Merge: keep any pre-existing goals (e.g. user-supplied primary
        # goal injected by the product layer) and append inferred ones
        # that are not already present.
        existing_ids = {g.goal_id for g in context.goals}
        merged: list[GoalRef] = list(context.goals)
        for g in inferred:
            if g.goal_id not in existing_ids:
                merged.append(g)
                existing_ids.add(g.goal_id)
        context.goals = merged
        context.add_metadata("decision_maker_profile", profile_id)


__all__ = ["DecisionMakerAgent"]