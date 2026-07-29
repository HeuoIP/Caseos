"""Space Agent: derive a SpaceSummary from the Vision JSON.

This agent does not call VisionAnalyzer -- it expects Vision JSON that has
already been produced by the upstream vision pipeline. Its job is to
restructure the raw analysis into a clean view the rest of the framework
can consume.

It also infers a coarse "domain" from the site_type so downstream agents
can do quick domain matching.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.agents.base import Agent, AgentRegistry
from app.core.decision.models import SpaceSummary

if TYPE_CHECKING:
    from app.core.decision.context import DecisionContext


# Domain inference table. Stable site_type prefix -> domain tag.
# Keep this small and obvious; the framework must never invent knowledge.
_SITE_TYPE_TO_DOMAIN: dict[str, str] = {
    "SITE.COMMERCIAL": "COMMERCIAL",
    "SITE.SHOPPING_MALL": "COMMERCIAL",
    "SITE.RESIDENTIAL": "RESIDENTIAL",
    "SITE.PUBLIC_PARK": "PUBLIC_PARK",
    "SITE.URBAN_PLAZA": "URBAN_PLAZA",
    "SITE.TOURIST": "TOURISM",
    "SITE.KINDERGARTEN": "EDUCATION",
    "SITE.SCHOOL": "EDUCATION",
    "SITE.MUSEUM": "MUSEUM",
    "SITE.INDOOR_CENTER": "INDOOR_PLAY",
}


@AgentRegistry.register
class SpaceAgent(Agent):
    name = "space"
    display_name = "Space Agent"

    def run(self, context) -> None:
        v = context.vision_json or {}
        basic = v.get("basic_info", {}) or {}
        design = v.get("design", {}) or {}
        target = v.get("target_users", {}) or {}
        play = v.get("play_experience", {}) or {}
        equip = v.get("equipment", {}) or {}
        materials = v.get("materials", {}) or {}
        color = v.get("color", {}) or {}
        safety = v.get("safety", {}) or {}
        ai = v.get("ai_analysis", {}) or {}

        site_type = str(basic.get("site_type", "") or "")
        themes = design.get("theme", []) or []
        primary_theme = ""
        secondary: list[str] = []
        for t in themes:
            if isinstance(t, dict):
                if t.get("role") == "primary" and not primary_theme:
                    primary_theme = str(t.get("id", ""))
                elif t.get("role") == "secondary":
                    secondary.append(str(t.get("id", "")))

        space = SpaceSummary(
            site_type=site_type,
            primary_theme=primary_theme,
            secondary_themes=secondary,
            age_groups=list(target.get("age_group", []) or []),
            play_behaviors=list(play.get("play_behaviors", []) or []),
            functional_units=list(equip.get("functional_units", []) or []),
            materials=list(materials.get("main_materials", []) or []),
            colors=list(color.get("colors", []) or []),
            design_language=list(design.get("design_language", []) or []),
            vision_summary=str(ai.get("vision_summary", "") or ""),
            design_interpretation=str(ai.get("design_interpretation", "") or ""),
            design_story=str(design.get("design_story", "") or ""),
            design_highlights=list(design.get("design_highlights", []) or []),
            keywords=list(ai.get("keywords", []) or []),
            confidence=float(ai.get("confidence", 0.0) or 0.0),
            domain=self._infer_domain(site_type),
            inclusive_design=bool(safety.get("inclusive_design", False)),
            risk_level=str(safety.get("risk_level", "") or ""),
        )
        context.space_summary = space
        context.add_metadata("site_type", site_type)
        context.add_metadata("primary_theme", primary_theme)
        context.add_metadata("domain", space.domain)

    @staticmethod
    def _infer_domain(site_type: str) -> str:
        if not site_type:
            return ""
        if site_type in _SITE_TYPE_TO_DOMAIN:
            return _SITE_TYPE_TO_DOMAIN[site_type]
        # Fallback: try prefix match
        for prefix, domain in _SITE_TYPE_TO_DOMAIN.items():
            if site_type.startswith(prefix):
                return domain
        return "PLAYGROUND"  # safe default for unknown sites


__all__ = ["SpaceAgent"]