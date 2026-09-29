"""Ingestion contract report (Sprint 25.0-A inferred).

Produces a Markdown report describing:

    * the CaseKnowledge record under review,
    * the IngestionContract rule table,
    * the validator outcome (rule_id + reason),
    * the V1 architecture boundary.

This module is **pure** -- it formats strings only; it does
not perform any validation itself.
"""
from __future__ import annotations

from typing import Optional

from .contract import (
    IngestionContract,
    default_contract,
)
from .object import CaseKnowledge
from .validator import (
    IngestionValidationResult,
    IngestionValidator,
)


def _md_section(title: str, body: str) -> str:
    return "## " + title + "\n\n" + body.rstrip() + "\n\n"


def _format_record(record: Optional[CaseKnowledge]) -> str:
    if record is None:
        return "_No record provided._\n"
    if not isinstance(record, CaseKnowledge):
        return "_Not a CaseKnowledge instance._\n"
    return (
        "- case_id: `" + record.case_id + "`\n"
        "- source: `" + record.source + "`\n"
        "- source_kind: `" + record.source_kind + "`\n"
        "- knowledge_id: `" + record.knowledge_id + "`\n"
        "- knowledge_version: `" + str(record.knowledge_version) + "`\n"
        "- title: `" + record.title + "`\n"
        "- tags: " + str(len(record.tags)) + " items\n"
        "- linked_assets: " + str(len(record.linked_assets)) + " items\n"
        "- requires_human_review: `"
        + str(record.requires_human_review) + "`\n"
        "- created_at: `" + record.created_at + "`\n"
        "- created_by: `" + record.created_by + "`\n"
    )


def _format_contract(contract: IngestionContract) -> str:
    d = contract.describe()
    return (
        "- source_kind_allow_list: "
        + ", ".join("`" + s + "`" for s in d["source_kind_allow_list"])
        + "\n"
        "- tag_count range: ["
        + str(d["min_tag_count"]) + ", " + str(d["max_tag_count"]) + "]\n"
        "- asset_count range: ["
        + str(d["min_asset_count"]) + ", "
        + str(d["max_asset_count"]) + "]\n"
        "- require_title_when_knowledge_id: `"
        + str(d["require_title_when_knowledge_id"]) + "`\n"
        "- require_human_review: `"
        + str(d["require_human_review"]) + "`\n"
        "- rules: " + ", ".join("`" + r + "`" for r in d["rules"]) + "\n"
    )


def _format_result(result: Optional[IngestionValidationResult]) -> str:
    if result is None:
        return "_No validator result provided._\n"
    return (
        "- valid: `" + str(result.valid) + "`\n"
        "- rule_id: `" + result.rule_id + "`\n"
        "- reason: `" + result.reason + "`\n"
        "- checked_at: `" + result.checked_at + "`\n"
        "- case_id: `" + result.case_id + "`\n"
    )


def generate_report(
    *,
    record: Optional[CaseKnowledge] = None,
    contract: Optional[IngestionContract] = None,
    result: Optional[IngestionValidationResult] = None,
    title: str = "Case Knowledge Ingestion Report",
) -> str:
    """Build a Markdown report for a Case Knowledge ingestion.

    Parameters
    ----------
    record:
        The CaseKnowledge under review (may be None).
    contract:
        The contract applied (defaults to the V1 contract).
    result:
        The validator output (may be None).
    title:
        Optional report title.
    """
    if contract is None:
        contract = default_contract()
    if result is None and record is not None:
        result = IngestionValidator(contract).validate(record)

    parts: list = []
    parts.append("# " + title + "\n\n")
    parts.append(
        "This report describes a single Case Knowledge record "
        "and its ingestion-contract check (Sprint 25.0-A).\n\n"
    )
    parts.append(_md_section("Record", _format_record(record)))
    parts.append(_md_section("Contract", _format_contract(contract)))
    parts.append(_md_section("Validator Result", _format_result(result)))

    parts.append("## Safety Boundary\n\n")
    parts.append(
        "The ingestion contract layer is **schema-level** only. "
        "It does not move data along the pipeline; it does not "
        "mutate any existing Knowledge Object; it does not "
        "import from retrieval, evolution, governance, "
        "intake, intelligence, or brain modules.\n\n"
    )
    return "".join(parts)
