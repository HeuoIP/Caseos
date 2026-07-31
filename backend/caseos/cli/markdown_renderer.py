"""Render the CaseOS recommendation into a Markdown report.

The format follows ADR-017 Section 2.2 (seven sections per
recommendation) and the Sprint 19.4 spec section 8 worked example.

    # Project Understanding
    # Human Understanding        (Sprint 21 / ADR-013)
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

from caseos.brain.runtime.context import PipelineContext, ProjectContext


def _safe(value: Any, fallback: str = "n/a") -> str:
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    # Sentinel UNKNOWN stringified.
    if isinstance(value, str) and value.strip() == "__UNKNOWN__":
        return fallback
    return str(value)


def _human_understanding_block(
    human_context: dict | None,
    validation: dict | None = None,
) -> list[str]:
    """Render the Sprint 21 Human Understanding section.

    `validation` is the optional dict produced by HumanModule and
    recorded under `ctx.metadata["human_validation"]`. When None,
    the renderer still produces a Human Understanding section but
    omits the validation verdict line.
    """
    lines: list[str] = []
    lines.append("# Human Understanding")
    lines.append("")
    if not human_context:
        lines.append("_No HumanContext was produced by the human understanding stage._")
        lines.append("")
        return lines

    def _v(key: str) -> str:
        val = human_context.get(key)
        if val is None:
            return "n/a"
        if isinstance(val, str) and (not val.strip() or val.strip() == "__UNKNOWN__"):
            return "n/a"
        if isinstance(val, list):
            return "; ".join(str(x) for x in val if x) if val else "n/a"
        return str(val)

    lines.append(f"- User Goal: {_v('user_goal')}")
    lines.append(f"- Business Context: {_v('business_context')}")
    lines.append(f"- Emotional Preference: {_v('emotional_preference')}")
    lines.append(f"- Budget Context: {_v('budget_context')}")
    constraints = human_context.get("constraints") or []
    if isinstance(constraints, list) and constraints:
        lines.append("- Constraints:")
        for c in constraints:
            lines.append(f"  - {c}")
    else:
        lines.append("- Constraints: (none provided)")
    lines.append(f"- Success Definition: {_v('success_definition')}")
    lines.append(f"- Risk Tolerance: {_v('risk_tolerance')}")
    lines.append(f"- Decision Priority: {_v('decision_priority')}")

    unknowns = human_context.get("unknowns") or []
    if unknowns:
        lines.append(f"- Unknowns: {', '.join(str(u) for u in unknowns)}")
    else:
        lines.append("- Unknowns: (none -- all fields supplied)")

    if validation:
        verdict = "VALID" if validation.get("valid") else "INVALID"
        warnings = validation.get("warnings") or []
        errors = validation.get("errors") or []
        lines.append(
            f"- Validation: {verdict} "
            f"(warnings={len(warnings)}, errors={len(errors)})"
        )
        for w in warnings:
            lines.append(f"  - WARN: {w}")
        for e in errors:
            lines.append(f"  - ERROR: {e}")
    lines.append("")
    return lines


def _format_confidence_and_caveats(block: dict | None, trust: dict | None) -> tuple[str, list[str]]:
    block = block or {}
    confidence = _safe(block.get("confidence"), fallback="Unknown")
    caveats: list[str] = list(block.get("caveats") or [])
    if trust:
        trust_conf = _safe(trust.get("confidence"), fallback="")
        if trust_conf:
            confidence = trust_conf
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
    human_context: dict | None = None,
    human_validation: dict | None = None,
) -> str:
    """Render the Markdown report.

    Sprint 21 update: `human_context` carries the Sprint 21 Human
    Understanding output; `human_validation` carries the validation
    result recorded under `ctx.metadata["human_validation"]`.
    """
    sections = recommendation.get("sections") or {}
    confidence, caveats = _format_confidence_and_caveats(
        sections.get("confidence_and_caveats"), trust
    )

    lines: list[str] = []

    # 1. Project Understanding
    lines.append("# Project Understanding")
    lines.append("")
    lines.append(f"- Project ID: `{project.project_id or 'n/a'}`")
    lines.append(f"- Project Type: {_safe(project.project_type)}")
    lines.append(f"- User Goal: {_safe(project.user_goal)}")
    lines.append(f"- Site Description: {_safe(project.site_description)}")
    lines.append(f"- Constraints: {_safe(project.constraints)}")
    lines.append("")

    # 2. Human Understanding (Sprint 21 / ADR-013)
    lines.extend(_human_understanding_block(human_context, human_validation))

    # 3-9. The seven ADR-017 sections
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

    # 10. Evidence Package (Sprint 20 / ADR-019)
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

    # 11. Confidence & Caveats
    lines.append("# Confidence & Caveats")
    lines.append("")
    lines.append(f"- Confidence Level: **{confidence}**")
    if caveats:
        lines.append("- Caveats:")
        for c in caveats:
            lines.append(f"  - {c}")
    lines.append("")

    # 12. Recommendation
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
        "_Sprint 21 (ADR-013) full intelligence loop: Human -> Knowledge -> "
        "Retrieval -> Decision -> Trust -> Recommendation. All stages "
        "wired end-to-end._"
    )
    lines.append("")
    return "\n".join(lines)


__all__ = ["render_markdown"]
