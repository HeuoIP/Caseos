"""Render the CaseOS recommendation into a Markdown report.

The format follows ADR-017 Section 2.2 (seven sections per
recommendation) and the Sprint 19.4 spec section 8 worked example.

    # Project Understanding
    # Situation Understanding
    # Problem Diagnosis
    # Strategic Direction
    # Experience Concept
    # Implementation Direction
    # Evidence
    # Confidence & Caveats
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


def _format_confidence_and_caveats(block: dict | None, trust: dict | None) -> tuple[str, list[str]]:
    """Resolve confidence + caveats from the recommendation block
    and/or the trust object. Trust always wins (parity with the
    Sprint 19.3 logic)."""

    block = block or {}
    confidence = _safe(block.get("confidence"), fallback="Unknown")
    caveats: list[str] = list(block.get("caveats") or [])
    if trust:
        trust_conf = _safe(trust.get("confidence"), fallback="")
        if trust_conf:
            confidence = trust_conf
        # ADR-016 contract: caveats live under uncertainty_handling;
        # legacy `uncertainty` is tolerated for forward compat.
        extra_caveats = list(
            trust.get("uncertainty_handling")
            or trust.get("uncertainty")
            or []
        )
        for c in extra_caveats:
            if c not in caveats:
                caveats.append(c)
    return confidence, caveats


def render_markdown(
    project: ProjectContext,
    recommendation: dict,
    trust: dict | None,
    evidence_package: dict | None = None,
) -> str:
    sections = recommendation.get("sections") or {}
    confidence, caveats = _format_confidence_and_caveats(
        sections.get("confidence_and_caveats"), trust
    )

    lines: list[str] = []

    # 1. Project Understanding -- always present, summarises the input
    lines.append("# Project Understanding")
    lines.append("")
    lines.append(f"- Project ID: `{project.project_id or 'n/a'}`")
    lines.append(f"- Project Type: {_safe(project.project_type)}")
    lines.append(f"- User Goal: {_safe(project.user_goal)}")
    lines.append(f"- Site Description: {_safe(project.site_description)}")
    lines.append(f"- Constraints: {_safe(project.constraints)}")
    lines.append("")

    # 2-8. The seven ADR-017 sections
    section_blocks = [
        ("Situation Understanding", sections.get("situation_understanding")),
        ("Problem Diagnosis",       sections.get("problem_diagnosis")),
        ("Strategic Direction",     sections.get("strategic_direction")),
        ("Experience Concept",      sections.get("experience_concept")),
        ("Implementation Direction", sections.get("implementation_direction")),
        ("Evidence",                sections.get("evidence")),
    ]
    for title, body in section_blocks:
        lines.append(f"# {title}")
        lines.append("")
        lines.append(_safe(body, fallback="n/a"))
        lines.append("")

    # 8. Evidence Package (Sprint 20 / ADR-019) -- the 5-component
    #    retrieval output. Rendered with bullet items so the customer
    #    sees (a) which Knowledge Objects were retrieved, (b) why
    #    they apply, (c) the principle they contribute, (d) the
    #    boundary warning, and (e) how this evidence moves trust.
    lines.append("# Evidence Package")
    lines.append("")
    if evidence_package:
        reasons = _safe(evidence_package.get("applicability_reason"),
                       fallback="No applicability reason recorded.")
        lines.append(f"- Applicability Reason: {reasons}")
        principle = _safe(evidence_package.get("supporting_principle"),
                          fallback="No supporting principle available.")
        lines.append(f"- Supporting Principle: {principle}")
        bw = _safe(evidence_package.get("boundary_warning"),
                   fallback="No boundary warning recorded.")
        lines.append(f"- Boundary Warning: {bw}")
        tc = _safe(evidence_package.get("trust_contribution"),
                   fallback="No trust contribution recorded.")
        lines.append(f"- Trust Contribution: {tc}")
        relevant = evidence_package.get("relevant_objects") or []
        if relevant:
            ids = [str(ko.get("identity", "<unknown>")) for ko in relevant
                   if isinstance(ko, dict)]
            lines.append(f"- Relevant Knowledge ({len(ids)}): "
                         + ", ".join(ids))
        else:
            lines.append("- Relevant Knowledge: (none)")
    else:
        lines.append("_No Evidence Package was produced by the retrieval stage._")
    lines.append("")

    # 9. Confidence & Caveats -- rendered with caveats as a bullet list
    lines.append("# Confidence & Caveats")
    lines.append("")
    lines.append(f"- Confidence Level: **{confidence}**")
    if caveats:
        lines.append("- Caveats:")
        for c in caveats:
            lines.append(f"  - {c}")
    lines.append("")

    # 10. Recommendation -- a one-line summary section that points
    # the reader back to the strategic direction. (Per ADR-017
    # Section 2.2.3 the strategic direction already carries the
    # actual recommendation; this section provides the closing
    # signpost.)
    lines.append("# Recommendation")
    lines.append("")
    summary = _safe(
        sections.get("strategic_direction"),
        fallback="n/a (no recommendation available)",
    )
    lines.append(summary)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "_Sprint 20 (ADR-019) full intelligence loop: Human -> Knowledge -> "
        "Retrieval -> Decision -> Trust -> Recommendation. All stages "
        "wired end-to-end._"
    )
    lines.append("")
    return "\n".join(lines)


__all__ = ["render_markdown"]
