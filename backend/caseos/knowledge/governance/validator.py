"""Governance-level validation for Knowledge Objects (Sprint 20.6).

This module extends the Sprint 20.5 ADR-015 contract validator
(	ools.corpus_migration.validator) with the additional checks
called out in Sprint 20.6 spec section 2:

  * identity type is one of the 5 ADR-015 types
  * applicability is meaningful (not just a tag dump)
  * boundary is non-empty
  * principle is not empty
  * feedback field exists (empty list is acceptable: no recorded feedback)

Architecture: this validator re-uses the existing ADR-015
verdict as the base, then layers the governance checks on top.
The base result is preserved in the returned dataclass so a
single object carries the full picture.

Rejections carry a human-readable reason so a human reviewer can
fix the underlying Knowledge Object and re-submit it."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Reuse the existing ADR-015 validator; do not duplicate its logic.
from tools.corpus_migration.validator import (
    REQUIRED_FIELDS,
    validate_knowledge_object,
    validate_corpus,
)


# The 5 IdentityType prefixes defined in ADR-015 section
# "Knowledge Object Types V1".
VALID_IDENTITY_TYPES = frozenset({
    "GoldenCase",
    "DecisionPattern",
    "FailurePattern",
    "ExpertPrinciple",
    "UserPreference",
})


def _identity_type(identity: str) -> str:
    return identity.split(".", 1)[0] if "." in identity else ""


@dataclass
class GovernanceValidationResult:
    "Result of running governance checks on a single KO.",

    identity: str
    valid: bool
    base_missing: list[str] = field(default_factory=list)  # ADR-015 missing
    base_errors: list[str] = field(default_factory=list)   # ADR-015 errors
    governance_errors: list[str] = field(default_factory=list)  # new for 20.6

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "valid": self.valid,
            "base_missing": list(self.base_missing),
            "base_errors": list(self.base_errors),
            "governance_errors": list(self.governance_errors),
        }


def _check_identity_type(ko: dict, errors: list[str]) -> None:
    identity = str(ko.get("identity") or "")
    if not identity:
        return  # missing identity is reported by the base validator
    itype = _identity_type(identity)
    if itype not in VALID_IDENTITY_TYPES:
        errors.append(
            "identity type " + repr(itype) +
            " is not one of " + repr(sorted(VALID_IDENTITY_TYPES)),
        )


def _check_applicability_meaningful(ko: dict, errors: list[str]) -> None:
    "Applicability must declare at least one suitable context",
    "and should not be a tag dump (e.g. all empty strings).",
    app = ko.get("applicability")
    if not isinstance(app, dict):
        return  # base validator already raised this
    suitable = app.get("suitable") or app.get("suitable_when")
    if isinstance(suitable, list):
        non_empty = [s for s in suitable if isinstance(s, str) and s.strip()]
        if not non_empty:
            errors.append("applicability.suitable contains no meaningful entry")


def _check_boundary_nonempty(ko: dict, errors: list[str]) -> None:
    "Boundary is mandatory; the ADR-015 base check already",
    "rejects an absent field. Here we also reject a present",
    "field that is only whitespace or only an empty list.",
    b = ko.get("boundary", "__missing__")
    if b == "__missing__":
        return  # base validator already flagged it
    if isinstance(b, list):
        if not any(isinstance(x, str) and x.strip() for x in b):
            errors.append("boundary list has no non-empty string entry")
    elif isinstance(b, str):
        if not b.strip():
            errors.append("boundary is a blank string")
    else:
        errors.append("boundary must be a list or string")


def _check_principle_nonempty(ko: dict, errors: list[str]) -> None:
    p = ko.get("principle")
    if not isinstance(p, str) or not p.strip():
        errors.append("principle must be a non-empty string")


def _check_feedback_present(ko: dict, errors: list[str]) -> None:
    "Feedback is required to be present. Empty list is OK:",
    "it means no recorded feedback yet. The field MUST exist",
    "so downstream governance can iterate it.",
    if "feedback" not in ko:
        errors.append("feedback field is missing")
        return
    f = ko["feedback"]
    if f is None:
        errors.append("feedback field is null")
        return
    if not isinstance(f, list):
        errors.append("feedback must be a list")


def validate_for_governance(ko: Any) -> GovernanceValidationResult:
    "Run the full governance check on a single Knowledge Object.",
    " Returns a GovernanceValidationResult. An invalid object has",
    "valid=False and at least one base_missing / base_errors /",
    "governance_errors entry.",
    if not isinstance(ko, dict):
        base = validate_knowledge_object(ko)
        return GovernanceValidationResult(
            identity=base.identity,
            valid=base.valid,
            base_missing=base.missing,
            base_errors=base.errors,
        )

    base = validate_knowledge_object(ko)
    governance_errors: list[str] = []
    if base.valid:
        _check_identity_type(ko, governance_errors)
        _check_applicability_meaningful(ko, governance_errors)
        _check_boundary_nonempty(ko, governance_errors)
        _check_principle_nonempty(ko, governance_errors)
        _check_feedback_present(ko, governance_errors)

    valid = base.valid and not governance_errors
    return GovernanceValidationResult(
        identity=base.identity,
        valid=valid,
        base_missing=base.missing,
        base_errors=base.errors,
        governance_errors=governance_errors,
    )


def _load_one(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}


def validate_corpus_for_governance(
    corpus_dir: Path | str,
) -> list[GovernanceValidationResult]:
    "Run governance validation on every JSON file in the corpus.",
    "Walks recursively (matches Sprint 20.5 load_corpus).",
    corpus_dir = Path(corpus_dir)
    out: list[GovernanceValidationResult] = []
    if not corpus_dir.exists():
        return out
    for path in sorted(corpus_dir.rglob("*.json")):
        data = _load_one(path)
        if not data:
            out.append(GovernanceValidationResult(
                identity="<" + path.name + ">",
                valid=False,
                base_errors=["failed to parse JSON"],
            ))
            continue
        out.append(validate_for_governance(data))
    return out


__all__ = [
    "VALID_IDENTITY_TYPES",
    "GovernanceValidationResult",
    "validate_for_governance",
    "validate_corpus_for_governance",
]
