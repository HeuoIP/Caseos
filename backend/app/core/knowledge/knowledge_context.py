"""Knowledge Context module."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class KnowledgeSnippet:
    kind: str
    ref_id: str
    title: str
    score: float = 0.0
    summary: str = ""
    file: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class RelevantKnowledgeContext:
    related_cases: list = field(default_factory=list)
    related_themes: list = field(default_factory=list)
    related_objects: list = field(default_factory=list)
    related_rules: list = field(default_factory=list)
    related_handbook: list = field(default_factory=list)
    related_reasoning: list = field(default_factory=list)
    primary_theme: str = ""
    secondary_themes: list = field(default_factory=list)
    domain: str = ""
    trigger_keywords: list = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def is_empty(self) -> bool:
        return not (
            self.related_cases
            or self.related_themes
            or self.related_objects
            or self.related_rules
            or self.related_handbook
            or self.related_reasoning
        )

    def total_snippets(self) -> int:
        return (
            len(self.related_cases)
            + len(self.related_themes)
            + len(self.related_objects)
            + len(self.related_rules)
            + len(self.related_handbook)
            + len(self.related_reasoning)
        )

    def by_kind(self, kind: str) -> list:
        bag = {
            "case": self.related_cases,
            "theme": self.related_themes,
            "object": self.related_objects,
            "rule": self.related_rules,
            "handbook": self.related_handbook,
            "reasoning": self.related_reasoning,
        }
        return list(bag.get(kind, ()))


__all__ = ["KnowledgeSnippet", "RelevantKnowledgeContext"]