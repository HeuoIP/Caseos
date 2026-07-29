"""Knowledge Loader: lazy aggregated view over the on-disk
knowledge library. It complements the YAML-based KnowledgeBase
by exposing the non-YAML sources that the retriever needs:

  * Theme Library (knowledge/taxonomy/theme/*.md)
  * Object Library (knowledge/objects/*.md)
  * Decision Rules (knowledge/decision_rules/*.md)
  * Expert Handbook (knowledge/expert_handbook/*.md)

The loader never edits files and never invents IDs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Stable IDs we expect to find in MD files.

global _STABLE_ID_RE

_STABLE_ID_RE = re.compile(r'([A-Z][A-Z0-9_]*\.[A-Z0-9][A-Z0-9_]*)')

_HEADING_RE = re.compile(r"# (.+)")


@dataclass
class ThemeEntry:
    theme_id: str
    name: str
    name_en: str = ""
    file: str = ""
    summary: str = ""
    keywords: list = field(default_factory=list)
    recommended_objects: list = field(default_factory=list)
    unsuitable_objects: list = field(default_factory=list)
    alternative_objects: list = field(default_factory=list)


@dataclass
class ObjectEntry:
    object_id: str
    name: str
    name_en: str = ""
    file: str = ""
    summary: str = ""
    serves_goals: list = field(default_factory=list)
    story_role: str = ""
    category: str = ""


@dataclass
class RuleEntry:
    rule_id: str
    title: str
    file: str = ""
    summary: str = ""
    keywords: list = field(default_factory=list)


@dataclass
class HandbookEntry:
    handbook_id: str
    title: str
    file: str = ""
    summary: str = ""
    keywords: list = field(default_factory=list)


class KnowledgeLoader:
    """Aggregate loader over the knowledge library.

    Reading is lazy: each library is only scanned on first access.

    Every entry is a reference, not a fragmentary copy.

    """

    def __init__(self, root):
        self.root = Path(root)
        self._themes = None
        self._objects = None
        self._rules = None
        self._handbook = None

    @property
    def theme_dir(self) -> Path:
        return self.root / "taxonomy" / "theme"

    @property
    def object_dir(self) -> Path:
        return self.root / "objects"

    @property
    def rules_dir(self) -> Path:
        return self.root / "decision_rules"

    @property
    def handbook_dir(self) -> Path:
        return self.root / "expert_handbook"

    @property
    def themes(self) -> dict:
        if self._themes is None:
            self._themes = self._load_themes()
        return self._themes

    @property
    def objects(self) -> dict:
        if self._objects is None:
            self._objects = self._load_objects()
        return self._objects

    @property
    def rules(self) -> dict:
        if self._rules is None:
            self._rules = self._load_rules()
        return self._rules

    @property
    def handbook(self) -> dict:
        if self._handbook is None:
            self._handbook = self._load_handbook()
        return self._handbook

    @staticmethod
    def _first_id(text: str) -> str:
        m = _STABLE_ID_RE.search(text)
        return m.group(1) if m else ""

    @staticmethod
    def _first_summary(text: str, max_lines: int = 3) -> str:
        """Return the first non-heading prose lines as a summary."""
        lines = []
        for line in text.splitlines():
            s = line.strip()
            if not s:
                if lines:
                    break
                continue
            if s.startswith("#"):
                continue
            if s.startswith("**") or s.startswith("=="):
                continue
            lines.append(s)
            if len(lines) >= max_lines:
                break
        return " ".join(lines)

    @staticmethod
    def _section_items(text: str, heading: str) -> list:
        """Extract bullet items under a heading."""
        items = []
        in_section = False
        for line in text.splitlines():
            if line.strip().startswith("#"):
                in_section = heading.lower() in line.lower()
                continue
            if in_section:
                s = line.strip()
                if s.startswith(("- ", "* ")):
                    items.append(s[2:].strip())
                elif s and not items:
                    items.append(s)
                    break
                elif items:
                    break
        return items

    def _load_themes(self) -> dict:
        out = {}
        if not self.theme_dir.exists():
            return out
        for path in sorted(self.theme_dir.glob("*.md")):
            if path.name.lower() == "readme.md":
                continue
            text = path.read_text(encoding="utf-8")
            theme_id = self._first_id(text)
            if not theme_id:
                stem = path.stem.replace(" ", "_").upper()
                theme_id = "NATURE." + stem if "_" in stem else stem
            name = path.stem
            m = _HEADING_RE.match(text)
            if m:
                name = m.group(1).strip()
            out[theme_id] = ThemeEntry(
                theme_id=theme_id,
                name=name,
                name_en=path.stem.replace("_", " "),
                file=path.name,
                summary=self._first_summary(text),
                keywords=self._section_items(text, "Keywords"),
                recommended_objects=self._section_items(text, "Recommended Objects"),
                unsuitable_objects=self._section_items(text, "Unsuitable Objects"),
                alternative_objects=self._section_items(text, "Alternative Objects"),
            )
        return out

    def _load_objects(self) -> dict:
        out = {}
        if not self.object_dir.exists():
            return out
        for path in sorted(self.object_dir.glob("*.md")):
            if path.name.lower() == "readme.md":
                continue
            text = path.read_text(encoding="utf-8")
            object_id = self._first_id(text)
            if not object_id:
                continue
            name = path.stem
            m = _HEADING_RE.match(text)
            if m:
                name = m.group(1).strip()
            story_role_list = self._section_items(text, "Story Role")
            story_role = story_role_list[0] if story_role_list else ""
            category_list = self._section_items(text, "Category")
            category = category_list[0] if category_list else ""
            out[object_id] = ObjectEntry(
                object_id=object_id,
                name=name,
                name_en=path.stem.replace("_", " "),
                file=path.name,
                summary=self._first_summary(text),
                serves_goals=self._section_items(text, "Serves Goals"),
                story_role=story_role,
                category=category,
            )
        return out

    def _load_rules(self) -> dict:
        out = {}
        if not self.rules_dir.exists():
            return out
        for path in sorted(self.rules_dir.glob("*.md")):
            if path.name.lower() == "readme.md":
                continue
            text = path.read_text(encoding="utf-8")
            rule_id = path.stem
            title = path.stem
            m = _HEADING_RE.match(text)
            if m:
                title = m.group(1).strip()
            out[rule_id] = RuleEntry(
                rule_id=rule_id,
                title=title,
                file=path.name,
                summary=self._first_summary(text, max_lines=5),
                keywords=self._section_items(text, "Keywords"),
            )
        return out

    def _load_handbook(self) -> dict:
        out = {}
        if not self.handbook_dir.exists():
            return out
        for path in sorted(self.handbook_dir.glob("*.md")):
            if path.name.lower() == "readme.md":
                continue
            text = path.read_text(encoding="utf-8")
            handbook_id = path.stem
            title = path.stem
            m = _HEADING_RE.match(text)
            if m:
                title = m.group(1).strip()
            out[handbook_id] = HandbookEntry(
                handbook_id=handbook_id,
                title=title,
                file=path.name,
                summary=self._first_summary(text, max_lines=5),
                keywords=self._section_items(text, "Keywords"),
            )
        return out

    def theme(self, theme_id: str) -> Optional[ThemeEntry]:
        return self.themes.get(theme_id)

    def object(self, object_id: str) -> Optional[ObjectEntry]:
        return self.objects.get(object_id)

    def rule(self, rule_id: str) -> Optional[RuleEntry]:
        return self.rules.get(rule_id)

    def handbook_doc(self, handbook_id: str) -> Optional[HandbookEntry]:
        return self.handbook.get(handbook_id)

    def summary(self) -> dict:
        return {
            "themes": len(self.themes),
            "objects": len(self.objects),
            "rules": len(self.rules),
            "handbook": len(self.handbook),
        }


__all__ = [
    "HandbookEntry",
    "KnowledgeLoader",
    "ObjectEntry",
    "RuleEntry",
    "ThemeEntry",
]
