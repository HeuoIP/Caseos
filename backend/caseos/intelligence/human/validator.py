"""HumanContext Validator -- Sprint 21 (ADR-013 Section 4).

The validator is a pure function: it inspects a `HumanContext`
and returns a `HumanValidationResult` describing whether the
object is acceptable and what is missing.

Rejection rules (Sprint 21 spec section 4):

    * empty user_goal          -> invalid
    * empty success_definition -> invalid

Warning rules (Sprint 21 spec section 4):

    * missing budget           -> warn
    * missing constraints      -> warn
    * missing business_context -> warn

Validation output shape (Sprint 21 spec section 4):

    {
        valid: bool,
        warnings: list[str],
        errors: list[str],
        missing_required: list[str],
        missing_optional: list[str],
    }

Important: the validator NEVER throws on missing fields. It
records the gap. The pipeline still runs -- missing signals
do not abort the analysis, they only reduce the chance that
the Decision Engine can fire a rule.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from .object import HumanContext, UNKNOWN, _is_unknown


@dataclass
class HumanValidationResult:
    """Outcome of validating a HumanContext.

    Attributes:
        valid: True when no required field is missing.
        warnings: human-readable warnings (optional fields).
        errors: human-readable errors (required fields).
        missing_required: list of required field names that are missing.
        missing_optional: list of optional field names that are missing.
        validated_at: ISO timestamp.
    """

    valid: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    missing_optional: list[str] = field(default_factory=list)
    validated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _required_missing(ctx: HumanContext) -> list[str]:
    out: list[str] = []
    if _is_unknown(ctx.user_goal):
        out.append("user_goal")
    if _is_unknown(ctx.success_definition):
        out.append("success_definition")
    return out


def _optional_missing(ctx: HumanContext) -> list[str]:
    out: list[str] = []
    if _is_unknown(ctx.budget_context):
        out.append("budget_context")
    if _is_unknown(ctx.business_context):
        out.append("business_context")
    if not ctx.constraints:
        out.append("constraints")
    if _is_unknown(ctx.emotional_preference):
        out.append("emotional_preference")
    if _is_unknown(ctx.risk_tolerance):
        out.append("risk_tolerance")
    if _is_unknown(ctx.decision_priority):
        out.append("decision_priority")
    return out


def validate_human_context(ctx: HumanContext) -> HumanValidationResult:
    """Validate a HumanContext.

    Returns a `HumanValidationResult`. The function never raises;
    missing information is reported as warnings or errors.

    The validator deliberately does NOT call any external system --
    it is a pure function of the HumanContext.
    """
    missing_required = _required_missing(ctx)
    missing_optional = _optional_missing(ctx)

    errors: list[str] = []
    for name in missing_required:
        errors.append(f"required field missing: {name}")

    warnings: list[str] = []
    for name in missing_optional:
        warnings.append(f"optional field missing: {name}")

    return HumanValidationResult(
        valid=not missing_required,
        warnings=warnings,
        errors=errors,
        missing_required=missing_required,
        missing_optional=missing_optional,
        validated_at=_now_iso(),
    )


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


__all__ = [
    "HumanValidationResult",
    "validate_human_context",
]
