"""Stage 3: Vision Engine output -> CKO Draft (sections 0-6).

The extractor is **deterministic** -- it does not call any LLM. It
maps Vision V3 taxonomy fields onto the CKO V1.2 schema using a
small set of rules:

  * Section 0.case_id is always "PENDING" until the Reviewer
    approves.
  * Section 0.knowledge_source is locked to
    ``external_excellent_case`` per ADR-011 V1.
  * Sections 7 / 8 / 9 are intentionally NOT touched (Section 7 and
    8 are filled by the Reviewer / Librarian; Section 9 by the
    Evaluator).
  * When a Vision V3 field is empty, the extractor substitutes a
    safe default drawn from the project_types and CKO taxonomies;
    the Reviewer can fix it later.

The defaulting is the V1 behaviour. V2 may add an LLM-based
draft-fill that the Reviewer overwrites.
"""

from __future__ import annotations

from typing import Any

from .models import CKODraft, CaseInput, RawCaseUnderstanding


# Maps V3 site_type IDs onto the CKO ``project_types`` vocabulary.
# Conservative: unknown IDs fall back to ``other`` (per ADR-011).
_PROJECT_TYPE_MAP: dict[str, str] = {
    "KINDERGARTEN": "kindergarten",
    "SCHOOL": "school",
    "PUBLIC_PARK": "public_park",
    "MALL": "malls_retail",
    "HOTEL": "hospitality_hotel",
    "MUSEUM": "cultural_tourism",
    "RESIDENTIAL": "family_residential",
    "PLAZA": "real_estate_commercial",
    "ROOFTOP": "real_estate_commercial",
    "POCKET_PARK": "public_park",
    "STREET": "real_estate_commercial",
    "INNER_COURTYARD": "school",
    "GROUND_PLAYGROUND": "public_park",
}


def _project_type_from(vision: dict[str, Any], default: str | None) -> str:
    """Resolve a CKO project_type from the Vision payload + input hint."""
    if default:
        return default
    basic = vision.get("basic_info", {}) or {}
    site = str(basic.get("site_type") or "")
    if not site:
        return "other"
    # site is expected to look like "SITE.KINDERGARTEN".
    leaf = site.split(".", 1)[-1]
    return _PROJECT_TYPE_MAP.get(leaf.upper(), "other")


class CKODraftExtractor:
    """Stage 3 of the Golden Case pipeline.

    Usage::

        extractor = CKODraftExtractor()
        draft = extractor.extract(raw_understanding, case_input)
    """

    def extract(
        self,
        raw: RawCaseUnderstanding,
        case_input: CaseInput,
    ) -> CKODraft:
        """Build a CKO Draft from a Vision Engine response.

        Sections 0 to 6 are populated. Sections 7 / 8 / 9 stay None;
        the Reviewer / Evaluator fills them.
        """
        v = raw.vision_payload
        basic = v.get("basic_info", {}) or {}
        design = v.get("design", {}) or {}

        title = str(basic.get("project_name") or "").strip() or "Untitled case"
        project_type = _project_type_from(v, case_input.project_type)

        return CKODraft(
            # Section 0
            case_id="PENDING",
            title=title,
            source=case_input.source,
            image_reference=raw.image_path,
            project_type=project_type,
            knowledge_source="external_excellent_case",

            # Section 1 -- Project Context
            client_goal=_join_goal(design),
            project_background=_join_background(v),
            target_users=_age_groups_to_users(v),
            site_condition=raw.environmental_relationship
            or "site condition not visible",
            budget_level=None,

            # Section 2 -- Space Cognition
            spatial_role=_spatial_role(v),
            spatial_position="edge",
            spatial_scale="medium",
            existing_elements=raw.visible_elements,
            environmental_relationship=raw.environmental_relationship,

            # Section 3 -- Experience Analysis
            atmosphere=_atmosphere(v),
            emotional_response=_emotional_response(v),
            child_behavior=raw.possible_user_behavior,
            interaction_type="active",
            stay_value="mid",

            # Section 4 -- Diagnosis
            problem_type="positive_throughline",
            diagnosis=_diagnosis_one_line(title, v),
            evidence=raw.visible_elements[:3],
            key_observation=_key_observation(title),

            # Section 5 -- Strategy
            strategy_type="anchor",
            design_principles=_default_principles(),
            spatial_organization=_spatial_org(title, raw),
            theme_logic=_theme_logic(v),

            # Section 6 -- Recommendation Logic
            applicable_conditions=_applicable_conditions(project_type),
            recommended_for=_recommended_for(project_type),
            not_recommended_for=_not_recommended_for(project_type),
            risk_warning=None,

            # Sections 7, 8, 9 stay None
            professional_evaluation=None,
            learning_value=None,
            case_evaluation=None,
        )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _join_goal(design: dict[str, Any]) -> str:
    highlights = design.get("design_highlights") or []
    if isinstance(highlights, list) and highlights:
        return f"Demonstrates the following: {'; '.join(str(h) for h in highlights[:2])}."
    return "Document site context, user group and intended outcome (pending reviewer)."


def _join_background(v: dict[str, Any]) -> str:
    basic = v.get("basic_info", {}) or {}
    parts: list[str] = []
    if basic.get("city"):
        parts.append(f"Located in {basic['city']}")
    if basic.get("country"):
        parts.append(basic["country"])
    if basic.get("site_type"):
        parts.append(f"site type {basic['site_type']}")
    return (", ".join(parts) or "Background not available from Vision Engine") + "."


def _age_groups_to_users(v: dict[str, Any]) -> list[str]:
    target = v.get("target_users", {}) or {}
    raw_ages = target.get("age_group") or []
    out: list[str] = []
    for a in raw_ages:
        s = str(a)
        if s.startswith("AGE."):
            leaf = s.split(".", 1)[-1]
            out.append(f"age_{leaf.lower().replace('-', '_').replace('+', 'plus')}")
        else:
            out.append(s.lower())
    return out or ["general_visitor"]


def _spatial_role(v: dict[str, Any]) -> str:
    """Pick a CKO spatial_role from the Vision site_type group."""
    basic = v.get("basic_info", {}) or {}
    site = str(basic.get("site_type") or "").upper()
    if site.startswith("SITE.PARK") or "PARK" in site:
        return "play"
    if site.startswith("SITE.SCHOOL") or "KINDERGARTEN" in site:
        return "play"
    if "MALL" in site or "PLAZA" in site:
        return "gathering"
    if "MUSEUM" in site:
        return "contemplative"
    return "play"


def _atmosphere(v: dict[str, Any]) -> str:
    """Build a single-sentence atmosphere sentence from keywords + style."""
    ai = v.get("ai_analysis", {}) or {}
    design = v.get("design", {}) or {}
    keywords = ai.get("keywords") or []
    style = design.get("style") or []
    bits = (", ".join(str(k) for k in keywords[:3]) + " from keywords").strip()
    if style and isinstance(style, list):
        bits = bits + "; style cues: " + ", ".join(str(s) for s in style[:2])
    if not bits:
        bits = "atmosphere pending reviewer input"
    return bits


def _emotional_response(v: dict[str, Any]) -> list[str]:
    ai = v.get("ai_analysis", {}) or {}
    keywords = ai.get("keywords") or []
    out = [str(k) for k in keywords[:3] if k] or ["wonder", "explore"]
    # Enforce non-empty
    if not out:
        out = ["wonder"]
    return out


def _diagnosis_one_line(title: str, v: dict[str, Any]) -> str:
    design = v.get("design", {}) or {}
    theme = design.get("theme") or []
    if isinstance(theme, list) and theme:
        first = theme[0]
        if isinstance(first, dict):
            t = first.get("id", "themed space")
        else:
            t = str(first)
        return f"A {t}-led project whose spatial decisions justify the theme."
    return "A space whose composition reads as one coherent move."


def _key_observation(title: str) -> str:
    return f"The single move that holds the {title or 'site'} together."


def _default_principles() -> list[str]:
    """Default to Constitution Principle 004 + DP-002."""
    return [
        "Constitution Principle 004 -- Amplify the strengths of a space.",
        "DP-002 -- Space First, Object Second.",
    ]


def _spatial_org(title: str, raw: RawCaseUnderstanding) -> str:
    if raw.visible_elements:
        return "The space is organised around: " + ", ".join(raw.visible_elements[:3]) + "."
    return "Spatial organisation pending reviewer input."


def _theme_logic(v: dict[str, Any]) -> str | None:
    design = v.get("design", {}) or {}
    theme = design.get("theme") or []
    if isinstance(theme, list) and theme:
        first = theme[0]
        if isinstance(first, dict):
            return f"Theme {first.get('id', '')} binds the visible elements into one story."
    return None


def _applicable_conditions(project_type: str) -> list[str]:
    return [
        f"Project type {project_type} or similar.",
        "Vision-derived evidence available; case requires expert review.",
    ]


def _recommended_for(project_type: str) -> list[str]:
    return [
        f"{project_type} designers and operators",
        "research and inspiration cases with review",
    ]


def _not_recommended_for(project_type: str) -> list[str]:
    return [
        "production-grade adoption before reviewer approval",
        "use in contexts outside the documented project_type",
    ]


__all__ = ["CKODraftExtractor"]
