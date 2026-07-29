"""
Shared mutable state passed between agents.

The ``DecisionContext`` is the only contract that binds agents together.
Each agent reads from it and writes its own slice; the engine never needs
to know agent-internal types.  This keeps the framework decoupled and
makes adding a new agent (Budget, Fengshui, Safety, ...) a matter of
writing one class and inserting its name into the pipeline list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.decision.models import (
    DecisionMaker,
    Explanation,
    GoalRef,
    ObjectCandidate,
    Recommendation,
    SpaceSummary,
    StageRecord,
    StrategyRef,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class DecisionContext:
    """The shared state for one decision run."""

    # ---- Input ----
    vision_json: dict[str, Any]

    # ---- Stage 1: Space ----
    space_summary: SpaceSummary | None = None

    # ---- Stage 2: Decision Maker ----
    decision_maker: DecisionMaker | None = None
    goals: list[GoalRef] = field(default_factory=list)

    # ---- Stage 3: Strategy ----
    strategies: list[StrategyRef] = field(default_factory=list)

    # ---- Stage 4: Object Selector ----
    object_candidates: list[ObjectCandidate] = field(default_factory=list)
    top_recommendations: list[Recommendation] = field(default_factory=list)

    # ---- Stage 5: Explain ----
    explanations: list[Explanation] = field(default_factory=list)

    # ---- Pipeline bookkeeping ----
    stages: list[StageRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    # ---- Helpers used by the engine and agents ----

    def record_stage(self, agent_name: str, status: str = "ok", note: str = "") -> StageRecord:
        """Append a stage record. Engine calls this around each agent."""
        rec = StageRecord(
            agent=agent_name,
            status=status,
            started_at=_now_iso(),
            finished_at=_now_iso(),
            note=note,
        )
        self.stages.append(rec)
        return rec

    def add_metadata(self, key: str, value: Any) -> None:
        self.metadata[key] = value

    def short_id_list(self, refs: list, attr: str = "id") -> list[str]:
        """Helper: extract a list of stable IDs from any *Ref/*Candidate objects."""
        result = []
        for r in refs:
            v = getattr(r, attr, None)
            if v:
                result.append(v)
        return result


__all__ = ["DecisionContext"]