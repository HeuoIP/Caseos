"""Feedback Validator (Sprint 22.1, ADR-018 Section 4 + Sprint 22.1 spec section 6).

The validator is a **pure function** of the FeedbackObject. It does
not load the corpus, talk to the Decision Engine, or call any
external service. The manager passes the validator a set of
"valid targets" alongside the FeedbackObject.

Validation rules (Sprint 22.1 spec section 6):

    1. source must be one of the four priorities
       (EXPERT > OUTCOME > REASON > PREFERENCE).
    2. feedback_type must be one of the five ADR-018 types.
    3. target_identity must be non-empty AND, if `valid_targets`
       is provided, must be a member of that set.
    4. content must be non-empty.
    5. CONTRADICTION_SIGNAL must require expert review (this
       produces a `requires_expert_review=True` flag on the
       validation result regardless of the source).

Rejection reasons are returned as a list of strings so the
operator can fix the feedback and re-submit it.

The validator is the only layer that decides whether a feedback
event can move from VALIDATING to VALIDATED. The lifecycle gate
is enforced by the manager in ``validate(...)``.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Iterable, Optional

from .object import (
    FeedbackObject,
    FeedbackSource,
    FeedbackType,
    TYPES_REQUIRING_EXPERT_REVIEW,
)


@dataclass
class FeedbackValidationResult:
    """Outcome of validating a FeedbackObject.

    Attributes:
        valid: True when no rule rejected the object.
        warnings: human-readable warnings (non-blocking).
        errors: human-readable errors (blocking).
        missing_required: list of required fields that are missing.
        invalid_sources: list of source values that are not allowed.
        invalid_types: list of feedback_type values that are not allowed.
        unknown_targets: list of target identities that were not
                         found in the supplied `valid_targets` set.
        requires_expert_review: True when the feedback type or
                        source combination demands expert review
                        (CONTRADICTION_SIGNAL is the canonical case).
        validated_at: ISO timestamp.
    """

    valid: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)
    invalid_sources: list[str] = field(default_factory=list)
    invalid_types: list[str] = field(default_factory=list)
    unknown_targets: list[str] = field(default_factory=list)
    requires_expert_review: bool = False
    validated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# The four allowed sources. Declared at module level so the test
# can introspect them.
ALLOWED_SOURCES: frozenset[FeedbackSource] = frozenset({
    FeedbackSource.EXPERT,
    FeedbackSource.OUTCOME,
    FeedbackSource.REASON,
    FeedbackSource.PREFERENCE,
})


# The five allowed feedback types.
ALLOWED_FEEDBACK_TYPES: frozenset[FeedbackType] = frozenset({
    FeedbackType.POSITIVE_CONFIRMATION,
    FeedbackType.NEGATIVE_CORRECTION,
    FeedbackType.PREFERENCE_SIGNAL,
    FeedbackType.UNEXPECTED_DISCOVERY,
    FeedbackType.CONTRADICTION_SIGNAL,
})


class FeedbackValidator:
    """Pure validator for FeedbackObject.

    Stateless -- the same instance can be reused across many
    validations. It does not depend on the store, the manager,
    or the corpus.
    """

    def validate(
        self,
        feedback: FeedbackObject,
        valid_targets: Optional[Iterable[str]] = None,
        require_target_check: bool = False,
    ) -> FeedbackValidationResult:
        """Validate a FeedbackObject.

        Args:
            feedback: the object to validate.
            valid_targets: optional iterable of known target
                identities. When provided AND ``require_target_check``
                is True, the validator rejects feedback whose
                target_identity is not in the set.
            require_target_check: when True, the validator checks
                that ``target_identity`` is in ``valid_targets``.
                When False (default), the validator only checks
                that ``target_identity`` is non-empty.

        Returns:
            ``FeedbackValidationResult`` with a list of errors
            (which block validation) and warnings (which do not).
        """
        errors: list[str] = []
        warnings: list[str] = []
        missing_required: list[str] = []
        invalid_sources: list[str] = []
        invalid_types: list[str] = []
        unknown_targets: list[str] = []
        requires_expert_review = False

        # 1. source check
        src_str = str(feedback.source) if feedback.source is not None else ""
        if src_str not in {s.value for s in ALLOWED_SOURCES}:
            invalid_sources.append(src_str)
            errors.append(f"source not in allow-list: {src_str!r}")

        # 2. feedback_type check
        ftype_str = (
            str(feedback.feedback_type)
            if feedback.feedback_type is not None
            else ""
        )
        if ftype_str not in {t.value for t in ALLOWED_FEEDBACK_TYPES}:
            invalid_types.append(ftype_str)
            errors.append(
                f"feedback_type not in allow-list: {ftype_str!r}"
            )

        # 3. target check
        target = (feedback.target_identity or "").strip()
        if not target:
            missing_required.append("target_identity")
            errors.append("required field missing: target_identity")
        elif require_target_check and valid_targets is not None:
            target_set = set(valid_targets)
            if target not in target_set:
                unknown_targets.append(target)
                errors.append(
                    f"target_identity not found in known corpus: {target!r}"
                )

        # 4. content check
        if not isinstance(feedback.content, str) or not feedback.content.strip():
            missing_required.append("content")
            errors.append("required field missing: content")

        # 5. CONTRADICTION_SIGNAL requires expert review
        try:
            ftype_enum = FeedbackType(ftype_str)
        except ValueError:
            ftype_enum = None
        if ftype_enum is not None and ftype_enum in TYPES_REQUIRING_EXPERT_REVIEW:
            requires_expert_review = True
            warnings.append(
                f"feedback_type={ftype_enum.value} requires "
                "expert review per ADR-018 §4.5"
            )

        # Soft warnings -- not blocking
        try:
            src_enum = FeedbackSource(src_str)
        except ValueError:
            src_enum = None
        if src_enum is not None and src_enum == FeedbackSource.PREFERENCE:
            warnings.append(
                "PREFERENCE source is high-volume and surface-level; "
                "the Loop will pass it through expert review per ADR-018 §1."
            )

        return FeedbackValidationResult(
            valid=not errors,
            warnings=warnings,
            errors=errors,
            missing_required=missing_required,
            invalid_sources=invalid_sources,
            invalid_types=invalid_types,
            unknown_targets=unknown_targets,
            requires_expert_review=requires_expert_review,
            validated_at=_now_iso(),
        )


__all__ = [
    "FeedbackValidationResult",
    "FeedbackValidator",
    "ALLOWED_SOURCES",
    "ALLOWED_FEEDBACK_TYPES",
]
