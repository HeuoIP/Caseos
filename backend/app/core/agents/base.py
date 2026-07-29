"""
Base interface and registry for CaseOS decision agents.

Every agent is a small class with a stable ``name`` and a single
``run(context)`` method that mutates the shared ``DecisionContext``.
The framework never inspects the agent's internal state -- it just
calls ``run`` in pipeline order and records the stage.

To add a new agent (Budget, Fengshui, Psychology, Safety, Commercial...):

    1. Subclass ``Agent`` and set ``name = "budget"`` (or similar).
    2. Implement ``run(self, context)``.
    3. The agent auto-registers at import time via ``@AgentRegistry.register``.
    4. Insert the name into ``DEFAULT_PIPELINE`` (or a custom Pipeline).

The engine does not need to change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from app.core.decision.context import DecisionContext
    from app.core.decision.knowledge import KnowledgeBase


class Agent(ABC):
    """Abstract base for every CaseOS decision agent."""

    # Subclasses MUST set this to a unique short identifier.
    name: ClassVar[str] = ""

    # Optional human-readable label for logs and reports.
    display_name: ClassVar[str] = ""

    def __init__(self, knowledge: "KnowledgeBase | None" = None):
        self.knowledge = knowledge

    @abstractmethod
    def run(self, context: "DecisionContext") -> None:
        """Read from context, mutate context in place."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"


class AgentRegistry:
    """Process-wide registry of agent classes, keyed by ``Agent.name``."""

    _agents: dict[str, type[Agent]] = {}

    @classmethod
    def register(cls, agent_cls: type[Agent]) -> type[Agent]:
        """Decorator that adds an Agent subclass to the registry."""
        if not agent_cls.name:
            raise ValueError(
                f"{agent_cls.__name__} must define a non-empty `name` class var"
            )
        cls._agents[agent_cls.name] = agent_cls
        return agent_cls

    @classmethod
    def get(cls, name: str) -> type[Agent]:
        if name not in cls._agents:
            raise KeyError(f"Unknown agent: {name!r}. Known: {sorted(cls._agents)}")
        return cls._agents[name]

    @classmethod
    def has(cls, name: str) -> bool:
        return name in cls._agents

    @classmethod
    def names(cls) -> list[str]:
        return sorted(cls._agents)

    @classmethod
    def build(cls, name: str, knowledge: "KnowledgeBase | None" = None) -> Agent:
        return cls.get(name)(knowledge=knowledge)

    @classmethod
    def reset(cls) -> None:
        """Test helper: clear the registry."""
        cls._agents.clear()


__all__ = ["Agent", "AgentRegistry"]