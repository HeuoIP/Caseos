"""User-facing output for the CaseOS Product Layer.

``ProductResponse`` is a flat, serialisation-friendly view of what the
Decision Engine produced, with one extra slice (the resolved
``decision_goal``) that the user explicitly supplied. The future Web
UI or CLI consumer should depend only on this dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.decision.models import (
    DecisionMaker,
    Explanation,
    GoalRef,
    Recommendation,
    SpaceSummary,
    StrategyRef,
)


@dataclass
class DecisionGoalView:
    """The user-facing decision goal slice.

    Composed from:
      * the user's ``primary_goal`` (translated to a Goal_ID), and
      * the inferred DecisionMaker profile.
    """

    project_type: str
    project_description: str
    primary_goal_label: str  # e.g. "Increase visitors"
    primary_goal_id: str  # e.g. "BUSINESS.TRAFFIC"
    inferred_profile: str  # e.g. "PUBLIC_ADMIN"
    profile_description: str
    extra_goals: list[GoalRef] = field(default_factory=list)


@dataclass
class ProductResponse:
    """One product-layer run's output.

    Required slices (acceptance criteria):
      * ``space_summary``
      * ``decision_goal``
      * ``strategies``
      * ``recommended_objects``
      * ``explanations``
      * ``markdown_report``
    """

    # 1. Space Summary
    space_summary: SpaceSummary | None

    # 2. Decision Goal
    decision_goal: DecisionGoalView | None

    # 3. Strategies selected
    strategies: list[StrategyRef]

    # 4. Top recommended objects
    recommended_objects: list[Recommendation]

    # 5. Explanations (Chinese reasoning per top object)
    explanations: list[Explanation]

    # 6. Full Markdown report
    markdown_report: str

    # Underlying decision context (kept for downstream consumers/tests)
    decision_maker: DecisionMaker | None = None
    all_goals: list[GoalRef] = field(default_factory=list)

    # Pipeline trace + metadata (durations, error info, ...)
    stages: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def top_object_ids(self) -> list[str]:
        return [r.object_id for r in self.recommended_objects]

    @property
    def primary_recommendation(self) -> Recommendation | None:
        return self.recommended_objects[0] if self.recommended_objects else None


__all__ = ["DecisionGoalView", "ProductResponse"]