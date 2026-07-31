"""Intelligence module interfaces (placeholders).

Each submodule exports a Stage subclass. The defaults wired into
`Pipeline` are intentionally replaceable: Sprint 20+ will swap
these for real implementations without changing the pipeline.
"""

from caseos.intelligence.human.module import HumanModule
from caseos.intelligence.knowledge.module import KnowledgeModule
from caseos.intelligence.decision.module import DecisionModule
from caseos.intelligence.trust.module import TrustModule
from caseos.intelligence.recommendation.module import RecommendationModule
from caseos.intelligence.output.module import OutputModule

__all__ = [
    "HumanModule",
    "KnowledgeModule",
    "DecisionModule",
    "TrustModule",
    "RecommendationModule",
    "OutputModule",
]