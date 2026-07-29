"""
Data models for the CaseOS Agent Framework.

Every dataclass here is plain Python (no Pydantic dependency) so that the
framework stays a thin orchestrator and can be reused by scripts, tests,
and the future FastAPI surface without coupling to a schema layer.

Naming conventions:
  * ``*Ref``     -- a reference into the knowledge library (carries an ID).
  * ``*Candidate`` -- something the engine considered but not yet chosen.
  * ``*Summary``  -- a structured view derived from raw input.
  * ``Recommendation`` -- the final top-N output of a decision run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ----------------------------------------------------------------------
# Stage 1: Space Agent -> SpaceSummary
# ----------------------------------------------------------------------

@dataclass
class SpaceSummary:
    """Structured view of the physical space, derived from Vision JSON."""

    # Raw taxonomy fields (stable IDs)
    site_type: str
    primary_theme: str
    secondary_themes: list[str] = field(default_factory=list)
    age_groups: list[str] = field(default_factory=list)
    play_behaviors: list[str] = field(default_factory=list)
    functional_units: list[str] = field(default_factory=list)
    materials: list[str] = field(default_factory=list)
    colors: list[str] = field(default_factory=list)
    design_language: list[str] = field(default_factory=list)

    # Free-text fields from Vision JSON
    vision_summary: str = ""
    design_interpretation: str = ""
    design_story: str = ""
    design_highlights: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    # Inferred / metadata
    confidence: float = 0.0
    domain: str = ""  # inferred from site_type, e.g. "COMMERCIAL"
    inclusive_design: bool = False
    risk_level: str = ""


# ----------------------------------------------------------------------
# Stage 2: Decision Maker Agent -> DecisionMaker
# ----------------------------------------------------------------------

@dataclass
class DecisionMaker:
    """The inferred profile of the person who will own the decision."""

    profile: str  # stable ID, e.g. "COMMERCIAL_OPERATOR"
    description: str
    typical_goals: list[str] = field(default_factory=list)
    rationale: str = ""


@dataclass
class GoalRef:
    """A goal that the engine believes applies to this space."""

    goal_id: str
    name: str
    name_en: str
    priority: int  # 1..5
    confidence: float  # 0..1
    rationale: str
    domain_affinity: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)


# ----------------------------------------------------------------------
# Stage 3: Strategy Agent -> StrategyRef
# ----------------------------------------------------------------------

@dataclass
class StrategyRef:
    """A strategy selected to address one or more goals."""

    strategy_id: str
    name: str
    name_en: str
    priority: int
    addresses_goals: list[str]
    serves_strategies: list[str] = field(default_factory=list)  # synergy partners kept
    conflicts_with: list[str] = field(default_factory=list)
    rationale: str = ""
    mechanism: str = ""


# ----------------------------------------------------------------------
# Stage 3.5: Strategy Analysis (Sprint 9)
# ----------------------------------------------------------------------

@dataclass
class StrategyAnalysis:
    """LLM-style structured reasoning produced by StrategyAgent.

    The fields map 1:1 to the ADR-005 output contract. The agent is
    rule-based but emits text that an LLM reviewer would write.
    """
    space_positioning: str = ""
    core_problem: str = ""
    design_direction: str = ""
    investment_logic: str = ""
    confidence: float = 0.0
    related_strategy_ids: list = field(default_factory=list)
    related_goal_ids: list = field(default_factory=list)
    knowledge_refs: list = field(default_factory=list)


# ----------------------------------------------------------------------
# Stage 4: Object Selector Agent -> ObjectCandidate + Recommendation
# ----------------------------------------------------------------------

@dataclass
class ObjectCandidate:
    """An object considered by the engine. Not necessarily chosen."""

    object_id: str
    name: str
    category: str
    score: float
    serves_goals: list[str] = field(default_factory=list)
    serves_strategies: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Recommendation:
    """A final top-N recommendation for the proposal."""

    rank: int
    object_id: str
    name: str
    score: float
    categories: list[str] = field(default_factory=list)
    serves_goals: list[str] = field(default_factory=list)
    serves_strategies: list[str] = field(default_factory=list)
    rationale_short: str = ""


# ----------------------------------------------------------------------
# Stage 5: Explain Agent -> Explanation
# ----------------------------------------------------------------------

@dataclass
class Explanation:
    """Human-readable reasoning for one recommendation."""

    object_id: str
    patterns: list[str]  # Reason_IDs applied
    text: str  # Chinese reasoning paragraph
    factors: dict[str, str] = field(default_factory=dict)


# ----------------------------------------------------------------------
# Pipeline-level
# ----------------------------------------------------------------------

@dataclass
class StageRecord:
    """One agent's execution summary."""

    agent: str
    status: str  # "ok" | "skipped" | "error"
    started_at: str = ""
    finished_at: str = ""
    note: str = ""