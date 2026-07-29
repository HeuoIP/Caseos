"""Knowledge Retriever: deterministic, local, ranked retrieval.

Given a Vision JSON (or a partial Space summary + decision context), the
retriever returns a RelevantKnowledgeContext with the top-N entries in each
knowledge slice (themes, objects, rules, handbook, reasoning patterns).

V1 is pure local. No vector database. No LLM. The retriever ranks by
overlap of taxonomy tokens, file-name keywords, and library-side
cross-references. It is meant to be replaceable by a vector-based
retriever later without changing the Agent interface.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from app.core.knowledge.knowledge_context import (
    KnowledgeSnippet,
    RelevantKnowledgeContext,
)
from app.core.knowledge.knowledge_loader import (
    KnowledgeLoader,
    ObjectEntry,
    ThemeEntry,
)


# Per-slice retrieval caps. Tweakable but kept conservative for V1.

TOP_THEMES = 5
TOP_OBJECTS = 8
TOP_RULES = 3
TOP_HANDBOOK = 4
TOP_REASONING = 5


_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _norm(s: str) -> str:
    """Lowercase, collapse separators, strip whitespace."""
    return s.lower().replace("_", " ").replace("/", " ").replace("-", " ").strip()


def _tokens(s: str) -> set:
    return {t for t in _norm(s).split() if len(t) >= 2}


def _jaccard(a: set, b: set) -> float:
    """Jaccard similarity between two token sets."""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _contains_any(haystack: str, needles: set) -> bool:
    h = _norm(haystack)
    return any(_norm(n) in h for n in needles if n)


class KnowledgeRetriever:
    """Build a RelevantKnowledgeContext for one decision run.


    The retriever reads from ``KnowledgeLoader`` (theme / object / rule /

    handbook) and a ``KnowledgeBase`` (reasoning patterns, goals,

    strategies). It is deterministic and offline.

    """

    def __init__(self, loader: KnowledgeLoader, knowledge_base=None):
        self.loader = loader
        self.kb = knowledge_base

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def retrieve(self, vision_json: dict, decision_context: Optional[dict] = None) -> RelevantKnowledgeContext:
        """Build a RelevantKnowledgeContext for one Vision JSON.

        

        Args:

            vision_json: parsed Vision JSON (CaseOS_Output_Schema_V3).

            decision_context: optional dict with DecisionContext metadata

                (project_type, primary_goal, user_constraints).

        """
        ctx = RelevantKnowledgeContext()
        ctx.trigger_keywords = self._extract_keywords(vision_json)
        ctx.primary_theme, ctx.secondary_themes = self._extract_themes(vision_json)
        ctx.domain = (vision_json.get("basic_info", {}) or {}).get("site_type", "")

        ctx.related_cases = self._retrieve_cases(vision_json)
        ctx.related_themes = self._retrieve_themes(vision_json)
        ctx.related_objects = self._retrieve_objects(vision_json, decision_context)
        ctx.related_rules = self._retrieve_rules(vision_json)
        ctx.related_handbook = self._retrieve_handbook(vision_json)
        ctx.related_reasoning = self._retrieve_reasoning(vision_json, decision_context)

        ctx.stats = {
            "cases": len(ctx.related_cases),
            "themes": len(ctx.related_themes),
            "objects": len(ctx.related_objects),
            "rules": len(ctx.related_rules),
            "handbook": len(ctx.related_handbook),
            "reasoning": len(ctx.related_reasoning),
        }
        return ctx

    # ------------------------------------------------------------------
    # Helpers to extract query tokens from the Vision JSON
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_keywords(vision_json):
        ai = (vision_json.get("ai_analysis") or {}) if isinstance(vision_json, dict) else {}
        kws = list(ai.get("keywords") or [])
        return [str(k) for k in kws if k]

    @staticmethod
    def _extract_themes(vision_json):
        design = (vision_json.get("design") or {}) if isinstance(vision_json, dict) else {}
        themes = design.get("theme", []) or []
        primary = ""
        secondary = []
        for t in themes:
            if isinstance(t, dict):
                if t.get("role") == "primary" and not primary:
                    primary = str(t.get("id", ""))
                elif t.get("role") == "secondary":
                    secondary.append(str(t.get("id", "")))
        return primary, secondary

    def _query_tokens(self, vision_json) -> set:
        """Flat token set that any library entry may match against."""
        tokens: set = set()
        if not isinstance(vision_json, dict):
            return tokens
        ai = vision_json.get("ai_analysis") or {}
        for k in (ai.get("keywords") or []):
            tokens |= _tokens(str(k))
        summary = ai.get("vision_summary", "")
        if isinstance(summary, str):
            tokens |= _tokens(summary)
        design = vision_json.get("design") or {}
        for k in (design.get("design_language") or []):
            tokens |= _tokens(str(k))
        for h in (design.get("design_highlights") or []):
            tokens |= _tokens(str(h))
        return tokens

    # ------------------------------------------------------------------
    # Per-slice retrievers
    # ------------------------------------------------------------------

    def _retrieve_cases(self, vision_json) -> list:
        """Find similar cases in data/analysis/cases/."""
        # Cases are owned by the data folder, not the knowledge library.
        # We look on disk relative to the loader root (knowledge/..).

        cases_root = self.loader.root.parent / "data" / "analysis" / "cases"
        if not cases_root.exists():
            return []
        query_tokens = self._query_tokens(vision_json)
        out = []
        for path in sorted(cases_root.glob("*.json")):
            try:
                payload = self._read_json(path)
            except Exception:
                continue
            if not payload:
                continue
            score = self._case_score(payload, query_tokens)
            if score <= 0:
                continue
            ai = (payload.get("ai_analysis") or {}) if isinstance(payload, dict) else {}
            basic = (payload.get("basic_info") or {}) if isinstance(payload, dict) else {}
            name = str(basic.get("project_name", path.stem))
            site = str(basic.get("site_type", ""))
            out.append(KnowledgeSnippet(
                kind="case",
                ref_id=path.stem,
                title=name or path.stem,
                score=round(score, 4),
                summary=(str(ai.get("vision_summary", ""))[:140]),
                file=str(path),
                extra={"site_type": site},
            ))
        out.sort(key=lambda s: (-s.score, s.ref_id))
        return out[:5]

    def _case_score(self, payload: dict, query_tokens: set) -> float:
        if not isinstance(payload, dict) or not query_tokens:
            return 0.0
        ai = payload.get("ai_analysis") or {}
        cand_tokens = set()
        for k in (ai.get("keywords") or []):
            cand_tokens |= _tokens(str(k))
        summary = ai.get("vision_summary", "")
        if isinstance(summary, str):
            cand_tokens |= _tokens(summary)
        return _jaccard(query_tokens, cand_tokens)

    def _retrieve_themes(self, vision_json) -> list:
        """Match the primary theme first, then fallback to keyword overlap."""
        primary, secondary = self._extract_themes(vision_json)
        out = []
        seen = set()
        for theme_id in [primary] + secondary + [""]:
            if not theme_id or theme_id in seen:
                continue
            entry = self.loader.theme(theme_id)
            if entry is None:
                continue
            seen.add(theme_id)
            out.append(KnowledgeSnippet(
                kind="theme",
                ref_id=entry.theme_id,
                title=entry.name,
                score=1.0 if entry.theme_id == primary else 0.6,
                summary=entry.summary,
                file=entry.file,
                extra={
                    "recommended_objects": list(entry.recommended_objects),
                    "unsuitable_objects": list(entry.unsuitable_objects),
                },
            ))
        # Pad with keyword-overlap themes
        if len(out) < TOP_THEMES:
            query_tokens = self._query_tokens(vision_json)
            for entry in self.loader.themes.values():
                if entry.theme_id in seen:
                    continue
                score = _jaccard(query_tokens, _tokens(" ".join([entry.name, entry.summary])))
                if score > 0:
                    out.append(KnowledgeSnippet(
                        kind="theme",
                        ref_id=entry.theme_id,
                        title=entry.name,
                        score=round(score, 4),
                        summary=entry.summary,
                        file=entry.file,
                    ))
                    seen.add(entry.theme_id)
                    if len(out) >= TOP_THEMES:
                        break
        out.sort(key=lambda s: (-s.score, s.ref_id))
        return out[:TOP_THEMES]

    def _retrieve_objects(self, vision_json, decision_context) -> list:
        """Match objects by category + theme alignment + goal suitability."""
        primary, _ = self._extract_themes(vision_json)
        theme_entry = self.loader.theme(primary) if primary else None
        theme_rec = set(_norm(x) for x in (theme_entry.recommended_objects if theme_entry else []))
        theme_excl = set(_norm(x) for x in (theme_entry.unsuitable_objects if theme_entry else []))
        query_tokens = self._query_tokens(vision_json)
        equip = (vision_json.get("equipment") or {}) if isinstance(vision_json, dict) else {}
        equip_units = [_norm(x) for x in (equip.get("functional_units") or [])]
        out = []
        for obj in self.loader.objects.values():
            score = 0.0
            text = " ".join([obj.name, obj.summary, obj.category])
            score += _jaccard(query_tokens, _tokens(text)) * 2.0
            if theme_rec:
                cat = _norm(obj.category)
                if any(_norm(t) in cat or _norm(t) in _norm(obj.name) for t in theme_rec):
                    score += 1.0
                if any(_norm(t) in cat or _norm(t) in _norm(obj.name) for t in theme_excl):
                    score -= 1.5
            if equip_units:
                if any(_norm(u) in _norm(obj.category) for u in equip_units):
                    score += 0.5
            if score <= 0:
                continue
            out.append(KnowledgeSnippet(
                kind="object",
                ref_id=obj.object_id,
                title=obj.name,
                score=round(score, 4),
                summary=obj.summary,
                file=obj.file,
                extra={
                    "category": obj.category,
                    "serves_goals": list(obj.serves_goals),
                },
            ))
        out.sort(key=lambda s: (-s.score, s.ref_id))
        return out[:TOP_OBJECTS]

    def _retrieve_rules(self, vision_json) -> list:
        """Match decision rules by keyword overlap."""
        query_tokens = self._query_tokens(vision_json)
        out = []
        for entry in self.loader.rules.values():
            text = " ".join([entry.title, entry.summary, " ".join(entry.keywords)])
            score = _jaccard(query_tokens, _tokens(text))
            if score <= 0:
                continue
            out.append(KnowledgeSnippet(
                kind="rule",
                ref_id=entry.rule_id,
                title=entry.title,
                score=round(score, 4),
                summary=entry.summary,
                file=entry.file,
            ))
        out.sort(key=lambda s: (-s.score, s.ref_id))
        return out[:TOP_RULES]

    def _retrieve_handbook(self, vision_json) -> list:
        """Match expert handbook docs by keyword overlap."""
        query_tokens = self._query_tokens(vision_json)
        out = []
        for entry in self.loader.handbook.values():
            text = " ".join([entry.title, entry.summary, " ".join(entry.keywords)])
            score = _jaccard(query_tokens, _tokens(text))
            if score <= 0:
                continue
            out.append(KnowledgeSnippet(
                kind="handbook",
                ref_id=entry.handbook_id,
                title=entry.title,
                score=round(score, 4),
                summary=entry.summary,
                file=entry.file,
            ))
        out.sort(key=lambda s: (-s.score, s.ref_id))
        return out[:TOP_HANDBOOK]

    def _retrieve_reasoning(self, vision_json, decision_context) -> list:
        """Pick reasoning patterns that apply to the inferred goals."""
        if self.kb is None:
            return []
        goal_ids = set()
        if isinstance(decision_context, dict):
            for g in (decision_context.get("goals") or []):
                gid = (g.get("goal_id") if isinstance(g, dict) else None)
                if gid:
                    goal_ids.add(str(gid))
        if not goal_ids:
            # Fall back to inferring goals from the Goal Library by keyword.
            query_tokens = self._query_tokens(vision_json)
            for entry in self.kb.goals:
                if _jaccard(query_tokens, _tokens(entry.name + " " + entry.name_en)) > 0:
                    goal_ids.add(entry.goal_id)
        out = []
        for r in self.kb.reasonings:
            uses_goals = set(r.uses_goals or [])
            if uses_goals and uses_goals != {"*"}:
                if not (uses_goals & goal_ids):
                    continue
            out.append(KnowledgeSnippet(
                kind="reasoning",
                ref_id=r.reason_id,
                title=r.name or r.name_en,
                score=round(float(r.priority), 4),
                summary=r.example_zh or r.template_zh or r.name_en,
                file=r.file,
                extra={"uses_goals": list(r.uses_goals), "uses_strategies": list(r.uses_strategies)},
            ))
        out.sort(key=lambda s: (-s.score, s.ref_id))
        return out[:TOP_REASONING]

    @staticmethod
    def _read_json(path: Path):
        import json
        return json.loads(path.read_text(encoding="utf-8"))


__all__ = [
    "KnowledgeRetriever",
    "TOP_HANDBOOK",
    "TOP_OBJECTS",
    "TOP_REASONING",
    "TOP_RULES",
    "TOP_THEMES",
]
