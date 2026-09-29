"""Admission report (Sprint 25.3-A).

Produces a Markdown report for a single admission check.
Includes the Semantic Boundary table from
``caseos.knowledge.ingestion.admission.boundary``.
Pure formatting; no mutation.
"""
from __future__ import annotations

from typing import Optional

from .boundary import (
    EVOLUTION_OWNED_MIN_VERSION,
    SEMANTIC_BOUNDARY_TABLE,
    is_admission_owned_version,
)
from .checker import (
    AdmissionChecker,
    AdmissionResult,
)
from .object import (
    ADMISSION_TARGET_VERSION,
    AdmissionCandidate,
    AdmissionProvenanceRef,
)
from .policy import (
    AdmissionPolicy,
    default_policy,
)


def _md_section(title: str, body: str) -> str:
    return "## " + title + "\n\n" + body.rstrip() + "\n\n"


def _format_source(source: AdmissionProvenanceRef) -> str:
    if source is None:
        return "_No source provenance._\n"
    return (
        "- promotion_candidate_id: `"
        + source.promotion_candidate_id + "`\n"
        "- case_id: `" + source.case_id + "`\n"
        "- case_source_kind: `" + source.case_source_kind + "`\n"
        "- provenance_chain: "
        + str(len(source.provenance_chain)) + " step(s)\n"
    )


def _format_provenance(source: AdmissionProvenanceRef) -> str:
    if source is None or not source.provenance_chain:
        return "_No provenance records._\n"
    lines = []
    for i, r in enumerate(source.provenance_chain, start=1):
        lines.append(
            str(i) + ". `" + r.step + "` by `"
            + r.actor + "` at `" + r.timestamp + "`"
            + (" ref=`" + r.reference + "`" if r.reference else "")
        )
    return "\n".join(lines) + "\n"


def _format_candidate(candidate: Optional[AdmissionCandidate]) -> str:
    if candidate is None:
        return "_No candidate provided._\n"
    return (
        "- admission_id: `" + candidate.admission_id + "`\n"
        "- target_knowledge_id: `"
        + candidate.target_knowledge_id + "`\n"
        "- target_version: `" + str(candidate.target_version) + "`\n"
        "- status: `" + candidate.status + "`\n"
        "- failure_reason: `" + candidate.failure_reason + "`\n"
        "- requires_human_review: `"
        + str(candidate.requires_human_review) + "`\n"
        "- admission_proposal: "
        + str(len(candidate.admission_proposal)) + " field(s)\n"
        "- justification: `" + candidate.justification + "`\n"
        "- created_at: `" + candidate.created_at + "`\n"
        "- created_by: `" + candidate.created_by + "`\n"
    )


def _format_policy(policy: AdmissionPolicy) -> str:
    d = policy.describe()
    return (
        "- target_version: `" + str(d["target_version"]) + "`\n"
        "- require_human_review: `"
        + str(d["require_human_review"]) + "`\n"
        "- require_non_empty_proposal: `"
        + str(d["require_non_empty_proposal"]) + "`\n"
        "- require_non_empty_provenance: `"
        + str(d["require_non_empty_provenance"]) + "`\n"
        "- human_review_marker: `"
        + str(d["human_review_marker"]) + "`\n"
        "- rules: "
        + ", ".join("`" + r + "`" for r in d["rules"]) + "\n"
    )


def _format_result(result: Optional[AdmissionResult]) -> str:
    if result is None:
        return "_No admission result provided._\n"
    return (
        "- valid: `" + str(result.valid) + "`\n"
        "- rule_id: `" + result.rule_id + "`\n"
        "- reason: `" + result.reason + "`\n"
        "- checked_at: `" + result.checked_at + "`\n"
        "- admission_id: `" + result.admission_id + "`\n"
    )


def _format_boundary() -> str:
    rows = ["| Version | Owner | Responsibility |",
            "|---------|-------|----------------|"]
    for ver, owner, desc in SEMANTIC_BOUNDARY_TABLE:
        # Escape pipes inside description so the table stays valid.
        safe = desc.replace("|", "\\|")
        rows.append("| " + ver + " | " + owner + " | " + safe + " |")
    rows.append("")
    rows.append(
        "Admission target version: `" + str(ADMISSION_TARGET_VERSION)
        + "`; Evolution minimum owned version: `"
        + str(EVOLUTION_OWNED_MIN_VERSION) + "`."
    )
    return "\n".join(rows) + "\n"


def generate_admission_report(
    *,
    candidate: Optional[AdmissionCandidate] = None,
    policy: Optional[AdmissionPolicy] = None,
    result: Optional[AdmissionResult] = None,
    title: str = "Knowledge Admission Report",
) -> str:
    """Build a Markdown report for a single admission check."""
    if policy is None:
        policy = default_policy()
    if result is None and candidate is not None:
        result, _ = AdmissionChecker(policy).check(candidate)

    parts: list = []
    parts.append("# " + title + "\n\n")
    parts.append(
        "This report describes a single AdmissionCandidate "
        "and its first-entry admission decision (Sprint 25.3-A).\n\n"
    )
    parts.append(_md_section("Candidate", _format_candidate(candidate)))
    if candidate is not None:
        parts.append(_md_section(
            "Source Provenance", _format_source(candidate.source),
        ))
        parts.append(_md_section(
            "Provenance Chain", _format_provenance(candidate.source),
        ))
    parts.append(_md_section("Policy", _format_policy(policy)))
    parts.append(_md_section("Admission Result", _format_result(result)))
    parts.append(_md_section("Semantic Boundary", _format_boundary()))

    parts.append("## Safety Boundary\n\n")
    parts.append(
        "The admission layer is **contract-only**. It does NOT "
        "mutate any KnowledgeObject, does NOT write to the "
        "VersionStore, does NOT call the Evolution runtime, "
        "does NOT touch the Corpus, and does NOT invoke any "
        "AI / LLM / VLM / Embedding / Retrieval / Brain module. "
        "The actual first-entry write is reserved for a future "
        "Writer Sprint.\n\n"
    )
    return "".join(parts)
