"""
Knowledge loader for the CaseOS Agent Framework.

This module is the single place where the agent framework touches the
on-disk knowledge library (Goal / Strategy / Reasoning / Object indexes).
It loads indexes lazily so that constructing an agent does not pay the
cost of reading every YAML file unless that agent actually needs it.

Design rules:
  * The framework never edits knowledge files.
  * The framework never invents IDs that do not exist in the library.
  * Every lookup is by stable ID; if the ID is missing we surface it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Stable ID header used in object/theme MD files:
#   > **Object ID:** `OBJECT.TREEHOUSE`
#   > **Stable ID:** `NATURE.FOREST`
_STABLE_ID_RE = re.compile(r"`([A-Z][A-Z0-9_]*\.[A-Z0-9][A-Z0-9_]*)`")


@dataclass
class GoalEntry:
    goal_id: str
    name: str
    name_en: str
    priority: int
    domain_affinity: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)
    related_goals: list[str] = field(default_factory=list)
    suitable_objects: list[str] = field(default_factory=list)
    unsuitable_objects: list[str] = field(default_factory=list)
    file: str = ""


@dataclass
class StrategyEntry:
    strategy_id: str
    name: str
    name_en: str
    priority: int
    addresses_goals: list[str] = field(default_factory=list)
    conflicts_with: list[str] = field(default_factory=list)
    synergies: list[str] = field(default_factory=list)
    typical_implementations: list[str] = field(default_factory=list)
    file: str = ""


@dataclass
class ReasoningEntry:
    reason_id: str
    name: str
    name_en: str
    priority: int
    required_factors: list[str] = field(default_factory=list)
    optional_factors: list[str] = field(default_factory=list)
    uses_goals: list[str] = field(default_factory=list)
    uses_strategies: list[str] = field(default_factory=list)
    template_zh: str = ""
    example_zh: str = ""
    file: str = ""


@dataclass
class ObjectEntry:
    object_id: str
    name: str
    name_en: str
    category: str
    domain_affinity: list[str] = field(default_factory=list)
    file: str = ""


class KnowledgeBase:
    """Lazy, read-only view of the CaseOS knowledge library."""

    def __init__(self, root: Path | str):
        self.root = Path(root)
        self._goals: list[GoalEntry] | None = None
        self._strategies: list[StrategyEntry] | None = None
        self._reasonings: list[ReasoningEntry] | None = None
        self._objects: dict[str, ObjectEntry] | None = None

    # ---- paths --------------------------------------------------

    @property
    def goals_dir(self) -> Path:
        return self.root / "goals"

    @property
    def strategies_dir(self) -> Path:
        return self.root / "strategies"

    @property
    def reasoning_dir(self) -> Path:
        return self.root / "reasoning"

    @property
    def objects_dir(self) -> Path:
        return self.root / "objects"

    # ---- loaders ------------------------------------------------

    def _load_goals(self) -> list[GoalEntry]:
        index = self.goals_dir / "_index.yaml"
        if not index.exists():
            return []
        raw = yaml.safe_load(index.read_text(encoding="utf-8")) or {}
        out: list[GoalEntry] = []
        for g in raw.get("Goals", []):
            yaml_file = self.goals_dir / g.get("File", "")
            details = self._load_goal_details(yaml_file) if yaml_file.exists() else {}
            out.append(GoalEntry(
                goal_id=g["Goal_ID"],
                name=g.get("Name", ""),
                name_en=g.get("Name_EN", ""),
                priority=int(g.get("Priority", 0)),
                domain_affinity=list(g.get("Domain_Affinity", []) or []),
                conflicts_with=list(g.get("Conflicts_With", []) or []),
                related_goals=list(g.get("Related_Goals", []) or []),
                suitable_objects=details.get("suitable_objects", []),
                unsuitable_objects=details.get("unsuitable_objects", []),
                file=g.get("File", ""),
            ))
        return out

    def _load_goal_details(self, path: Path) -> dict[str, list[str]]:
        """Read a Goal YAML and extract just the lists the agents need."""
        d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return {
            "suitable_objects": list(d.get("Suitable_Objects", []) or []),
            "unsuitable_objects": list(d.get("Unsuitable_Objects", []) or []),
        }

    def _load_strategies(self) -> list[StrategyEntry]:
        index = self.strategies_dir / "_index.yaml"
        if not index.exists():
            return []
        raw = yaml.safe_load(index.read_text(encoding="utf-8")) or {}
        out: list[StrategyEntry] = []
        for s in raw.get("Strategies", []):
            yaml_file = self.strategies_dir / s.get("File", "")
            details = self._load_strategy_details(yaml_file) if yaml_file.exists() else {}
            out.append(StrategyEntry(
                strategy_id=s["Strategy_ID"],
                name=s.get("Name", ""),
                name_en=s.get("Name_EN", ""),
                priority=int(s.get("Priority", 0)),
                addresses_goals=list(s.get("Addresses_Goals", []) or []),
                conflicts_with=list(s.get("Conflicts_With", []) or []),
                synergies=list(s.get("Synergies", []) or []),
                typical_implementations=details.get("typical_implementations", []),
                file=s.get("File", ""),
            ))
        return out

    def _load_strategy_details(self, path: Path) -> dict[str, list[str]]:
        d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return {
            "typical_implementations": list(d.get("Typical_Implementations", []) or []),
        }

    def _load_reasonings(self) -> list[ReasoningEntry]:
        index = self.reasoning_dir / "_index.yaml"
        if not index.exists():
            return []
        raw = yaml.safe_load(index.read_text(encoding="utf-8")) or {}
        out: list[ReasoningEntry] = []
        for r in raw.get("Reasons", []):
            yaml_file = self.reasoning_dir / r.get("File", "")
            details = self._load_reasoning_details(yaml_file) if yaml_file.exists() else {}
            out.append(ReasoningEntry(
                reason_id=r["Reason_ID"],
                name=r.get("Name", ""),
                name_en=r.get("Name_EN", ""),
                priority=int(r.get("Priority", 0)),
                required_factors=list(r.get("Required_Factors", []) or []),
                uses_goals=list(r.get("Uses_Goals", []) or []),
                uses_strategies=list(r.get("Uses_Strategies", []) or []),
                template_zh=details.get("template_zh", ""),
                example_zh=details.get("example_zh", ""),
                file=r.get("File", ""),
            ))
        return out

    def _load_reasoning_details(self, path: Path) -> dict[str, str]:
        d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return {
            "template_zh": str(d.get("Template_Chinese", "") or ""),
            "example_zh": str(d.get("Example_Output", "") or ""),
        }

    def _load_objects(self) -> dict[str, ObjectEntry]:
        out: dict[str, ObjectEntry] = {}
        if not self.objects_dir.exists():
            return out
        for path in sorted(self.objects_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            m_id = re.search(r"\*\*Object ID:\*\*\s*`([A-Z][A-Z0-9_.]+)`", text)
            if not m_id:
                continue
            object_id = m_id.group(1)
            m_cat = re.search(r"\*\*Category:\*\*\s*([^\n\r]+)", text)
            category = m_cat.group(1).strip() if m_cat else ""
            m_dom = re.search(r"\*\*Domain Affinity:\*\*\s*([^\n\r]+)", text)
            domain = []
            if m_dom:
                domain = [p.strip() for p in re.split(r"[,;\u3001]", m_dom.group(1)) if p.strip()]
            # Name is the first H1
            name = path.stem
            m_name = re.match(r"#\s+(.+)", text)
            if m_name:
                name = m_name.group(1).strip()
            out[object_id] = ObjectEntry(
                object_id=object_id,
                name=name,
                name_en=path.stem.replace("_", " "),
                category=category,
                domain_affinity=domain,
                file=path.name,
            )
        return out

    # ---- accessors ----------------------------------------------

    @property
    def goals(self) -> list[GoalEntry]:
        if self._goals is None:
            self._goals = self._load_goals()
        return self._goals

    @property
    def strategies(self) -> list[StrategyEntry]:
        if self._strategies is None:
            self._strategies = self._load_strategies()
        return self._strategies

    @property
    def reasonings(self) -> list[ReasoningEntry]:
        if self._reasonings is None:
            self._reasonings = self._load_reasonings()
        return self._reasonings

    @property
    def objects(self) -> dict[str, ObjectEntry]:
        if self._objects is None:
            self._objects = self._load_objects()
        return self._objects

    # ---- lookups ------------------------------------------------

    def goal(self, goal_id: str) -> GoalEntry | None:
        for g in self.goals:
            if g.goal_id == goal_id:
                return g
        return None

    def strategy(self, strategy_id: str) -> StrategyEntry | None:
        for s in self.strategies:
            if s.strategy_id == strategy_id:
                return s
        return None

    def reasoning(self, reason_id: str) -> ReasoningEntry | None:
        for r in self.reasonings:
            if r.reason_id == reason_id:
                return r
        return None

    def object(self, object_id: str) -> ObjectEntry | None:
        return self.objects.get(object_id)

    # ---- summaries ----------------------------------------------

    def summary(self) -> dict[str, int]:
        return {
            "goals": len(self.goals),
            "strategies": len(self.strategies),
            "reasonings": len(self.reasonings),
            "objects": len(self.objects),
        }


__all__ = [
    "GoalEntry",
    "KnowledgeBase",
    "ObjectEntry",
    "ReasoningEntry",
    "StrategyEntry",
]