"""Knowledge Graph Validation Markdown Report V1 (Sprint 23.2-A).

The report module emits a human-readable Markdown summary
of a ``GraphValidationResult``.

Sections:

    # Knowledge Graph Validation Report
    ## Summary
    ## Request
    ## Result
    ## Issues
    ## Architecture Boundary

The report is purely descriptive.

Architecture boundary (Sprint 23.2-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    This module MAY import from:
        * caseos.knowledge.graph (sibling modules)
        * stdlib
"""
from __future__ import annotations

from typing import Optional

from .object import (
    GraphIssue,
    GraphValidationResult,
    SEVERITY_ALLOW_LIST,
    TARGET_KIND_ALLOW_LIST,
)
from .validator import KnowledgeGraphValidator


def _severity_badge(sev: str) -> str:
    return "`" + sev + "`"


def _fmt_issue(issue: GraphIssue) -> str:
    field_part = (
        " field=`" + issue.field_name + "`"
        if issue.field_name is not None
        else ""
    )
    return (
        "- **"
        + issue.rule_id
        + "** "
        + _severity_badge(issue.severity)
        + " target_kind=`"
        + issue.target_kind
        + "` target_id=`"
        + issue.target_id
        + "`"
        + field_part
        + " -- "
        + issue.message
    )


def generate_graph_report(
    result: Optional[GraphValidationResult] = None,
) -> str:
    """Return a Markdown report describing ``result``."""
    sections: list[str] = []

    # Header
    sections.append("# Knowledge Graph Validation Report")
    sections.append("")
    sections.append(
        "**Sprint**: 23.2-A (Knowledge Graph Validation Runtime V1)"
    )
    sections.append(
        "**ADR**: 018 (Feedback Learning Loop) / 020 (Knowledge Evolution)"
    )
    sections.append("")

    # 1. Summary
    sections.append("## Summary")
    sections.append("")
    sections.append(
        "The graph validator is a **pure reader**: it does NOT"
        " mutate any KnowledgeObject, KnowledgeDomain,"
        " KODomainBinding, Taxonomy / TaxonomyNode, or"
        " KnowledgeAttribute. It cross-checks the V1"
        " contracts and emits a structured list of issues."
    )
    sections.append("")
    sections.append("- **V1 rule set**: "
                    + ", ".join(sorted(KnowledgeGraphValidator.V1_RULES)))
    sections.append("- **Severity levels**: "
                    + ", ".join(sorted(SEVERITY_ALLOW_LIST)))
    sections.append("- **Target kinds**: "
                    + ", ".join(sorted(TARGET_KIND_ALLOW_LIST)))
    sections.append("")

    # 2. Request
    sections.append("## Request")
    sections.append("")
    if result is None:
        sections.append("_no result supplied_")
        sections.append("")
    else:
        sections.append("- **request_id**: `" + result.request_id + "`")
        sections.append(
            "- **knowledge_object_id**: `"
            + result.knowledge_object_id
            + "`"
        )
        sections.append("")

    # 3. Result
    sections.append("## Result")
    sections.append("")
    if result is None:
        sections.append("_no result supplied_")
        sections.append("")
    else:
        sections.append("- **success**: `" + str(result.success) + "`")
        sections.append("- **total issues**: " + str(len(result.issues)))
        sections.append("- **errors**: " + str(len(result.errors)))
        sections.append("- **warnings**: " + str(len(result.warnings)))
        sections.append("")

    # 4. Issues
    sections.append("## Issues")
    sections.append("")
    if result is None:
        sections.append("_no result supplied_")
    elif len(result.issues) == 0:
        sections.append("_no issues emitted_")
    else:
        for issue in result.issues:
            sections.append(_fmt_issue(issue))
    sections.append("")

    # 5. Architecture Boundary
    sections.append("## Architecture Boundary")
    sections.append("")
    sections.append(
        "- The graph validator does NOT import from"
        " `caseos.intelligence.*` or `caseos.knowledge.retrieval`."
    )
    sections.append(
        "- The graph validator does NOT mutate any"
        " KnowledgeObject, KnowledgeDomain, KODomainBinding,"
        " Taxonomy / TaxonomyNode, or KnowledgeAttribute."
    )
    sections.append(
        "- The graph validator does NOT consume the Evolution"
        " pipeline; it is a pure reader / consistency checker."
    )
    sections.append(
        "- The graph validator does NOT introduce LLM,"
        " embedding, or auto-learning logic."
    )
    sections.append("")

    return "\n".join(sections)


__all__ = ["generate_graph_report"]
