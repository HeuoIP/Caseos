"""
Pipeline definition for the CaseOS Agent Framework.

The pipeline is just an ordered list of agent names. The order is
sensible but configurable -- a custom pipeline (or a future DAG) is
just a list subclass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.core.agents.base import AgentRegistry

if TYPE_CHECKING:
    from app.core.agents.base import Agent
    from app.core.decision.knowledge import KnowledgeBase


# The default agent order. Any future agent can be inserted here without
# touching the engine.
DEFAULT_PIPELINE: list[str] = [
    "space",
    "decision_maker",
    "strategy",
    "object_selector",
    "explain",
]


@dataclass
class Pipeline:
    """An ordered list of agent names that the engine will execute."""

    agent_names: list[str] = field(default_factory=lambda: list(DEFAULT_PIPELINE))

    def __post_init__(self) -> None:
        unknown = [n for n in self.agent_names if not AgentRegistry.has(n)]
        if unknown:
            # Defer to runtime so the registry can be populated by import
            # order. We re-check at build() time.
            pass

    def build(self, knowledge: "KnowledgeBase | None" = None) -> list["Agent"]:
        """Resolve names to Agent instances. Raises on unknown names."""
        agents: list[Agent] = []
        for n in self.agent_names:
            agents.append(AgentRegistry.build(n, knowledge=knowledge))
        return agents


__all__ = ["DEFAULT_PIPELINE", "Pipeline"]