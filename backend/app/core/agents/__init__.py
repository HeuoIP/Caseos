"""Public agent exports.

Importing this package registers every agent in ``AgentRegistry`` as a
side effect. Always import the package -- never the individual agent
modules directly -- so the registry is fully populated before the
engine resolves names.
"""

from app.core.agents.base import Agent, AgentRegistry
from app.core.agents.decision_maker_agent import DecisionMakerAgent
from app.core.agents.explain_agent import ExplainAgent
from app.core.agents.knowledge_retriever_agent import KnowledgeRetrieverAgent
from app.core.agents.object_selector_agent import (
    ObjectSelectorAgent,
    TOP_N_DEFAULT,
)
from app.core.agents.space_agent import SpaceAgent
from app.core.agents.strategy_agent import StrategyAgent

__all__ = [
    "Agent",
    "AgentRegistry",
    "DecisionMakerAgent",
    "ExplainAgent",
    "KnowledgeRetrieverAgent",
    "ObjectSelectorAgent",
    "SpaceAgent",
    "StrategyAgent",
    "TOP_N_DEFAULT",
]