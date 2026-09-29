"""Promotion report (Sprint 25.2-A).

Produces a Markdown report for a single promotion
eligibility check. Pure formatting; does not call the
checker itself.
"""
from __future__ import annotations

from typing import Optional

from .eligibility import (
    EligibilityResult,
    PromotionEligibilityChecker,
)
from .object import (
    ELIGIBLE,
    NOT_ELIGIBLE,
    PromotionCandidate,
)
from .policy import (
    PromotionPolicy,
    default_policy,
)


def _md_section(title: str, body: str) -> str:
    return "## " + title + "\n\n" + body.rstrip() + "\n\n"


def _format_candidate(candidate: Optional[PromotionCandidate]) -> str:
    if candidate is None:
        return "_No candidate provided._\n"
    return (
        "- candidate_id: `" + candidate.candidate_id + "`\n"
        "- case_id: `" + candidate.case_id + "`\n"
        "- case_source_kind: `" + candidate.case_source_kind + "`\n"
        "- proposed_knowledge_id: `"
        + candidate.proposed_knowledge_id + "`\n"
        "- proposed_version: `"
        + str(candidate.proposed_version) + "`\n"
        "- status: `" + candidate.status + "`\n"
        "- failure_reason: `" + candidate.failure_reason + "`\n"
        "- provenance_chain: "
        + str(len(candidate.provenance_chain)) + " step(s)\n"
        "- justification: `" + candidate.justification + "`\n"
        "- created_at: `" + candidate.created_at + "`\n"
        "- created_by: `" + candidate.created_by + "`\n"
    )


def _format_provenance(candidate: Optional[PromotionCandidate]) -> str:
    if candidate is None or not candidate.provenance_chain:
        return "_No provenance records._\n"
    lines = []
    for i, r in enumerate(candidate.provenance_chain, start=1):
        lines.append(
            str(i) + ". `" + r.step + "` by `" + r.actor
            + "` at `" + r.timestamp + "`"
            + (" ref=`" + r.reference + "`" if r.reference else "")
            + (" notes=`" + r.notes + "`" if r.notes else "")
        )
    return "\n".join(lines) + "\n"


def _format_policy(policy: PromotionPolicy) -> str:
    d = policy.describe()
    return (
        "- allowed_source_kinds: "
        + ", ".join("`" + s + "`" for s in d["allowed_source_kinds"])
        + "\n"
        "- min_provenance_steps: `" + str(d["min_provenance_steps"])
        + "`\n"
        "- required_provenance_steps: "
        + ", ".join("`" + s + "`" for s in d["required_provenance_steps"])
        + "\n"
        "- require_justification: `"
        + str(d["require_justification"]) + "`\n"
        "- require_proposed_knowledge_id: `"
        + str(d["require_proposed_knowledge_id"]) + "`\n"
        "- require_human_review: `"
        + str(d["require_human_review"]) + "`\n"
        "- human_review_marker: `"
        + str(d["human_review_marker"]) + "`\n"
        "- rules: " + ", ".join("`" + r + "`" for r in d["rules"]) + "\n"
    )


def _format_result(result: Optional[EligibilityResult]) -> str:
    if result is None:
        return "_No eligibility result provided._\n"
    return (
        "- valid: `" + str(result.valid) + "`\n"
        "- rule_id: `" + result.rule_id + "`\n"
        "- reason: `" + result.reason + "`\n"
        "- missing_steps: "
        + (", ".join("`" + s + "`" for s in result.missing_steps)
           if result.missing_steps else "[]")
        + "\n"
        "- checked_at: `" + result.checked_at + "`\n"
        "- candidate_id: `" + result.candidate_id + "`\n"
    )


def generate_promotion_report(
    *,
    candidate: Optional[PromotionCandidate] = None,
    policy: Optional[PromotionPolicy] = None,
    result: Optional[EligibilityResult] = None,
    title: str = "Promotion Eligibility Report",
) -> str:
    """Build a Markdown report for a single promotion check."""
    if policy is None:
        policy = default_policy()
    if result is None and candidate is not None:
        result, _ = PromotionEligibilityChecker(policy).check(candidate)

    parts: list = []
    parts.append("# " + title + "\n\n")
    parts.append(
        "This report describes a single PromotionCandidate "
        "and its eligibility decision (Sprint 25.2-A).\n\n"
    )
    parts.append(_md_section("Candidate", _format_candidate(candidate)))
    parts.append(_md_section(
        "Provenance Chain", _format_provenance(candidate)
    ))
    parts.append(_md_section("Policy", _format_policy(policy)))
    parts.append(_md_section("Eligibility Result", _format_result(result)))

    parts.append("## Safety Boundary\n\n")
    parts.append(
        "The promotion eligibility layer is **gating only**. "
        "It does NOT write to the Knowledge Corpus, does NOT "
        "mutate any KnowledgeObject, does NOT touch the "
        "Intake layer, and does NOT invoke intelligence / AI. "
        "Actual promotion is reserved for a later Sprint.\n\n"
    )
    return "".join(parts)
