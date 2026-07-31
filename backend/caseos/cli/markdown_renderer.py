"""Render the CaseOS recommendation into a Markdown report.

The format follows the worked example in ADR-017 Section 4 and the
Sprint 19.1 spec example output structure:

    # Project Understanding
    # Spatial Diagnosis
    # Decision
    # Evidence
    # Confidence
    # Recommendation

The renderer is deliberately conservative: a missing field becomes an
explicit "n/a" rather than a fabricated sentence. ADR-016's
Anti-Hallucination Principle says we prefer incomplete to invented.
"""

from __future__ import annotations

from typing import Any

from caseos.brain.runtime.context import ProjectContext


def _safe(value: Any, fallback: str = "n/a") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return str(value)


def render_markdown(
    project: ProjectContext,
    recommendation: dict,
    trust: dict | None,
) -> str:
    sections = recommendation.get("sections") or {}
    confidence_block = sections.get("confidence_and_caveats") or {}
    confidence = _safe(confidence_block.get("confidence"), fallback="Unknown")
    caveats: list[str] = list(confidence_block.get("caveats") or [])
    if trust:
        trust_conf = _safe(trust.get("confidence"), fallback="")
        if trust_conf:
            confidence = trust_conf  # trust always overrides
        extra_caveats = list(trust.get("uncertainty") or [])
        for c in extra_caveats:
            if c not in caveats:
                caveats.append(c)

    lines = []
    lines.append(f"# Project Understanding")
    lines.append("")
    lines.append(
        f"- Project ID: `{project.project_id or 'n/a'}`"
    )
    lines.append(f"- Project Type: {_safe(project.project_type)}")
    lines.append(f"- User Goal: {_safe(project.user_goal)}")
    lines.append(f"- Site Description: {_safe(project.site_description)}")
    lines.append(f"- Constraints: {_safe(project.constraints)}")
    lines.append("")
    lines.append(f"# Spatial Diagnosis")
    lines.append("")
    lines.append(_safe(sections.get("problem_diagnosis"), fallback="n/a (placeholder stage)"))
    lines.append("")
    lines.append(f"# Decision")
    lines.append("")
    strategy = _safe(sections.get("strategic_direction"), fallback="n/a")
    experience = _safe(sections.get("experience_concept"), fallback="n/a")
    implementation = _safe(sections.get("implementation_direction"), fallback="n/a")
    lines.append(f"- Strategy: {strategy}")
    lines.append(f"- Experience Logic: {experience}")
    lines.append(f"- Implementation Direction: {implementation}")
    lines.append("")
    lines.append(f"# Evidence")
    lines.append("")
    ev = sections.get("evidence")
    if isinstance(ev, dict) and ev:
        for k, v in ev.items():
            lines.append(f"- **{k}**: {_safe(v)}")
    else:
        lines.append("_n/a (placeholder stage)_")
    lines.append("")
    lines.append(f"# Confidence")
    lines.append("")
    lines.append(f"- Confidence Level: **{confidence}**")
    lines.append("")
    if caveats:
        lines.append("Caveats:")
        for c in caveats:
            lines.append(f"- {c}")
        lines.append("")
    lines.append(f"# Recommendation")
    lines.append("")
    lines.append(_safe(sections.get("strategic_direction"),
                       fallback="n/a (placeholder recommendation)"))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "_Sprint 19.1 skeleton output. Real reasoning is wired in Sprint 20+._"
    )
    lines.append("")
    return "\n".join(lines)


__all__ = ["render_markdown"]