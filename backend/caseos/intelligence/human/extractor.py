"""HumanContext Extractor -- Sprint 21 (ADR-013 Section 3).

The extractor takes *structured* project input and produces a
`HumanContext`. It is intentionally trivial:

    * map existing fields by name
    * keep the original meaning
    * missing fields become UNKNOWN
    * never invent content

Rules (Sprint 21 spec section 3):

    * Input may be a `ProjectContext` (frozen dataclass) or the
      raw project dict from `project.json`.
    * Field names follow the spec example:
          user_goal, business_context, emotional_preference,
          budget_context, constraints, success_definition,
          risk_tolerance, decision_priority
    * Conventional names from the existing `ProjectContext`
      (`project_type`, `site_description`, `user_goal`,
      `constraints`) are mapped as follows:
          project.user_goal            -> human.user_goal
          project.extras["budget"]     -> human.budget_context
          project.extras["preference"] -> human.emotional_preference
          project.extras["business"]   -> human.business_context
          project.extras["success"]    -> human.success_definition
          project.extras["risk"]       -> human.risk_tolerance
          project.extras["priority"]   -> human.decision_priority
          project.extras["user_goal"]  -> human.user_goal
          project.extras["emotional_preference"] -> human.emotional_preference
          project.extras["budget_context"]      -> human.budget_context
          project.extras["success_definition"]  -> human.success_definition
          project.extras["risk_tolerance"]      -> human.risk_tolerance
          project.extras["decision_priority"]   -> human.decision_priority
    * Anything not mapped -> UNKNOWN.
    * `constraints` may be a string or a list[str]; it is normalised
      to `list[str]`.

Important: `site_description` is NOT mapped to `business_context`.
Site description belongs to Spatial Understanding (Sprint 16,
Space Cognition), not Human Understanding. ADR-013 explicitly
defines `business_context` as "who they are / what kind of
project this is". Mixing the two would be a semantic
mismatch, and the Sprint 21 spec section 3 says the extractor
must "preserve original meaning".

`UNKNOWN` is preserved. We never replace it with a guess.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from caseos.brain.runtime.context import ProjectContext

from .object import HumanContext, UNKNOWN


def _string_or_unknown(value: Any) -> str:
    """Return a string value, or UNKNOWN when the input is empty.

    Empty strings and whitespace-only strings are treated as unknown
    so downstream rules see the same signal regardless of whether
    the user wrote `""` or omitted the field.
    """
    if value is None:
        return UNKNOWN
    if isinstance(value, str):
        s = value.strip()
        return s if s else UNKNOWN
    # Lists / numbers / dicts should not normally land here; coerce
    # to string but only if non-empty.
    s = str(value).strip()
    return s if s and s.lower() != "none" else UNKNOWN


def _coerce_constraints(value: Any) -> list[str]:
    """Normalise constraints to a list of strings.

    Accepts:
      * list[str | other] -> keep only the strings; drop empties
      * str               -> split on `;` then `,`
      * None / missing    -> []
    """
    if value is None:
        return []
    if isinstance(value, list):
        out: list[str] = []
        for v in value:
            if v is None:
                continue
            s = str(v).strip()
            if s:
                out.append(s)
        return out
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        # Split on semicolon first, then on commas.
        parts: list[str] = []
        for chunk in s.split(";"):
            chunk = chunk.strip()
            if not chunk:
                continue
            for piece in chunk.split(","):
                piece = piece.strip()
                if piece:
                    parts.append(piece)
        return parts
    s = str(value).strip()
    return [s] if s else []


def _pick(src: dict[str, Any], *keys: str) -> str:
    """Return the first non-empty value across the candidate keys."""
    for k in keys:
        v = _string_or_unknown(src.get(k))
        if v != UNKNOWN:
            return v
    return UNKNOWN


@dataclass
class ExtractionResult:
    """The extractor returns a HumanContext plus a small trace.

    The trace is used by the report and tests to verify that no
    information was invented. `mapped_fields` carries the names
    that the extractor successfully pulled from the input.
    """

    human_context: HumanContext
    mapped_fields: list[str]
    skipped_fields: list[str]


def extract_human_context(
    project: ProjectContext | Mapping[str, Any] | None,
) -> ExtractionResult:
    """Build a HumanContext from a project-shaped input.

    Accepts a `ProjectContext`, a raw dict, or None. Returns an
    `ExtractionResult` so callers can inspect what was mapped.
    """
    if project is None:
        empty = HumanContext()
        return ExtractionResult(
            human_context=empty,
            mapped_fields=[],
            skipped_fields=list(HumanContext().__dataclass_fields__.keys()),
        )

    # Normalise to a dict to keep the mapping table flat.
    if isinstance(project, ProjectContext):
        src: dict[str, Any] = {
            "project_id": project.project_id,
            "project_type": project.project_type,
            "site_description": project.site_description,
            "user_goal": project.user_goal,
            "constraints": project.constraints,
        }
        if isinstance(project.extras, dict):
            for k, v in project.extras.items():
                src.setdefault(str(k), v)
    elif isinstance(project, Mapping):
        src = dict(project)
    else:
        raise TypeError(
            "extract_human_context expects ProjectContext, mapping, or None; "
            f"got {type(project).__name__}"
        )

    mapped: list[str] = []
    skipped: list[str] = []

    # ------------------------------------------------------------------
    # Required fields
    # ------------------------------------------------------------------

    user_goal = _pick(src, "user_goal")
    if user_goal != UNKNOWN:
        mapped.append("user_goal")
    else:
        skipped.append("user_goal")

    # business_context: explicit only. site_description is NOT a
    # fallback because it belongs to Spatial Understanding.
    business_context = _pick(src, "business_context", "business")
    if business_context != UNKNOWN:
        mapped.append("business_context")
    else:
        skipped.append("business_context")

    emotional_preference = _pick(
        src, "emotional_preference", "preference",
    )
    if emotional_preference != UNKNOWN:
        mapped.append("emotional_preference")
    else:
        skipped.append("emotional_preference")

    budget_context = _pick(src, "budget_context", "budget")
    if budget_context != UNKNOWN:
        mapped.append("budget_context")
    else:
        skipped.append("budget_context")

    constraints = _coerce_constraints(src.get("constraints"))
    if constraints:
        mapped.append("constraints")
    else:
        skipped.append("constraints")

    success_definition = _pick(src, "success_definition", "success")
    if success_definition != UNKNOWN:
        mapped.append("success_definition")
    else:
        skipped.append("success_definition")

    # ------------------------------------------------------------------
    # Optional fields
    # ------------------------------------------------------------------

    risk_tolerance = _pick(src, "risk_tolerance", "risk")
    if risk_tolerance != UNKNOWN:
        mapped.append("risk_tolerance")
    else:
        skipped.append("risk_tolerance")

    decision_priority = _pick(src, "decision_priority", "priority")
    if decision_priority != UNKNOWN:
        mapped.append("decision_priority")
    else:
        skipped.append("decision_priority")

    ctx = HumanContext(
        user_goal=user_goal,
        business_context=business_context,
        emotional_preference=emotional_preference,
        budget_context=budget_context,
        constraints=constraints,
        success_definition=success_definition,
        risk_tolerance=risk_tolerance,
        decision_priority=decision_priority,
        project_id=str(src.get("project_id") or ""),
    )

    return ExtractionResult(
        human_context=ctx,
        mapped_fields=mapped,
        skipped_fields=skipped,
    )


__all__ = [
    "ExtractionResult",
    "extract_human_context",
    "_string_or_unknown",
    "_coerce_constraints",
]
