"""Adapter Validator V1 (Sprint 23.0-B, ADR-020).

The validator is the **input guard** for the
``KnowledgeObjectAdapter``. It is stateless: every call is a
pure function of the input ``AdapterRequest``.

Rules (Sprint 23.0-B spec):

    A1  request_id is a non-empty string
    A2  transaction_id is a non-empty string
    A3  change_intent_id is a non-empty string
    A4  target_identity is a non-empty string
    A5  target_version is an int >= 1
    A6  change_type is in the V1 allow-list
        (EvolutionChangeType.BOUNDARY_UPDATE |
         EvolutionChangeType.PRINCIPLE_UPDATE |
         EvolutionChangeType.APPLICABILITY_UPDATE)
    A7  before_snapshot is a non-empty dict
    A8  reviewer is a non-empty string
    A9  requested_change, when present, is a non-empty string

The validator collects ALL failures (it does NOT short-circuit
on the first error). The caller decides whether to treat a
non-valid result as a hard rejection.

Architecture boundary (Sprint 23.0-B spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.evolution (sibling packages)
        * caseos.knowledge.evolution.contracts
        * caseos.knowledge.object (KO V1 schema)
        * stdlib
"""
from __future__ import annotations

import dataclasses
from typing import Any, Optional, Tuple

from ..contracts.change_type import EvolutionChangeType
from .mapping import CHANGE_TYPE_TO_KO_FIELD
from .object import AdapterRequest


@dataclasses.dataclass(frozen=True)
class AdapterValidationResult:
    """The outcome of an ``AdapterValidator.validate`` call.

    Fields:
        valid: True iff every rule passed.
        errors: a tuple of human-readable error messages.
            Empty when ``valid`` is True.
    """

    valid: bool
    errors: Tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


_ALLOWED_CHANGE_TYPES: frozenset = frozenset(CHANGE_TYPE_TO_KO_FIELD.keys())


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


class AdapterValidator:
    """Stateless validator for ``AdapterRequest``.

    Validation is a pure function. The validator collects
    every rule failure and reports them in one pass; the
    caller decides how to react.
    """

    def validate(
        self,
        request: Optional[AdapterRequest],
    ) -> AdapterValidationResult:
        errors: list[str] = []

        if request is None:
            return AdapterValidationResult(
                valid=False,
                errors=("request is None",),
            )

        # A1
        if not _is_nonempty_str(getattr(request, "request_id", "")):
            errors.append("request_id must be a non-empty string")

        # A2
        if not _is_nonempty_str(getattr(request, "transaction_id", "")):
            errors.append("transaction_id must be a non-empty string")

        # A3
        if not _is_nonempty_str(getattr(request, "change_intent_id", "")):
            errors.append("change_intent_id must be a non-empty string")

        # A4
        if not _is_nonempty_str(getattr(request, "target_identity", "")):
            errors.append("target_identity must be a non-empty string")

        # A5 -- target_version must be int >= 1
        version = getattr(request, "target_version", None)
        if not isinstance(version, int) or isinstance(version, bool):
            errors.append(
                "target_version must be an int; got "
                + type(version).__name__
            )
        elif version < 1:
            errors.append(
                "target_version must be >= 1; got " + str(version)
            )

        # A6 -- change_type must be in the V1 allow-list
        ct = getattr(request, "change_type", None)
        if isinstance(ct, str):
            try:
                ct = EvolutionChangeType(ct)
            except ValueError:
                ct = None
        if not isinstance(ct, EvolutionChangeType):
            errors.append(
                "change_type must be an EvolutionChangeType enum; got "
                + repr(getattr(request, "change_type", None))
            )
        elif ct not in _ALLOWED_CHANGE_TYPES:
            errors.append(
                "change_type not in V1 allow-list: "
                + (ct.value if isinstance(ct, EvolutionChangeType) else str(ct))
            )

        # A7 -- before_snapshot must be a non-empty dict
        snapshot = getattr(request, "before_snapshot", None)
        if not isinstance(snapshot, dict):
            errors.append(
                "before_snapshot must be a dict; got "
                + type(snapshot).__name__
            )
        elif len(snapshot) == 0:
            errors.append("before_snapshot must be a non-empty dict")

        # A8 -- reviewer must be a non-empty string
        if not _is_nonempty_str(getattr(request, "reviewer", "")):
            errors.append("reviewer must be a non-empty string")

        # A9 -- requested_change must be a non-empty string.
        # V1 has no notion of a 'null change' -- the adapter
        # is invoked only when there is a proposed new value
        # to apply. None, empty string, or non-string types
        # are all rejected.
        rc = getattr(request, "requested_change", None)
        if not _is_nonempty_str(rc):
            errors.append(
                "requested_change must be a non-empty string; got "
                + repr(rc)
            )

        return AdapterValidationResult(
            valid=(len(errors) == 0),
            errors=tuple(errors),
        )


__all__ = [
    "AdapterValidator",
    "AdapterValidationResult",
]
