"""Writer Validator V1 (Sprint 23.0-C, ADR-020).

The validator is the **input guard** for the
``KnowledgeObjectWriter``. It is stateless: every call is a
pure function of the input ``WriteRequest``.

Rules (Sprint 23.0-C spec):

    W1  write_id is a non-empty string
    W2  transaction_id is a non-empty string
    W3  proposal_id is a non-empty string
    W4  change_intent_id is a non-empty string
    W5  target_identity is a non-empty string
    W6  change_type is in the V1 allow-list
        (EvolutionChangeType.BOUNDARY_UPDATE |
         EvolutionChangeType.PRINCIPLE_UPDATE |
         EvolutionChangeType.APPLICABILITY_UPDATE)
    W7  before_version is an int >= 1
    W8  before_snapshot is a non-empty dict
    W9  new_snapshot is a non-empty dict
    W10 reviewer is a non-empty string
    W11 change_reason is a non-empty string
    W12 new_snapshot["version"] == before_version + 1
    W13 new_snapshot["knowledge_id"] == target_identity
    W14 new_snapshot != before_snapshot (a real change is
        required; an empty write is rejected)

The validator collects ALL failures (it does NOT short-circuit
on the first error).

Architecture boundary (Sprint 23.0-C spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.evolution (sibling packages)
        * caseos.knowledge.evolution.contracts
        * caseos.knowledge.object (the KO V1 schema)
        * stdlib
"""
from __future__ import annotations

import dataclasses
from typing import Any, Optional, Tuple

from ..contracts.change_type import EvolutionChangeType
from .object import WriteRequest


@dataclasses.dataclass(frozen=True)
class WriterValidationResult:
    """The outcome of a ``WriterValidator.validate`` call.

    Fields:
        valid: True iff every rule passed.
        errors: a tuple of human-readable error messages.
            Empty when ``valid`` is True.
    """

    valid: bool
    errors: Tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


_ALLOWED_CHANGE_TYPES: frozenset = frozenset({
    EvolutionChangeType.BOUNDARY_UPDATE,
    EvolutionChangeType.PRINCIPLE_UPDATE,
    EvolutionChangeType.APPLICABILITY_UPDATE,
})


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


class WriterValidator:
    """Stateless validator for ``WriteRequest``."""

    def validate(
        self,
        request: Optional[WriteRequest],
    ) -> WriterValidationResult:
        errors: list[str] = []

        if request is None:
            return WriterValidationResult(
                valid=False,
                errors=("request is None",),
            )

        # W1
        if not _is_nonempty_str(getattr(request, "write_id", "")):
            errors.append("write_id must be a non-empty string")

        # W2
        if not _is_nonempty_str(getattr(request, "transaction_id", "")):
            errors.append("transaction_id must be a non-empty string")

        # W3
        if not _is_nonempty_str(getattr(request, "proposal_id", "")):
            errors.append("proposal_id must be a non-empty string")

        # W4
        if not _is_nonempty_str(getattr(request, "change_intent_id", "")):
            errors.append("change_intent_id must be a non-empty string")

        # W5
        if not _is_nonempty_str(getattr(request, "target_identity", "")):
            errors.append("target_identity must be a non-empty string")

        # W6 -- change_type must be in the V1 allow-list
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

        # W7 -- before_version must be int >= 1
        version = getattr(request, "before_version", None)
        if not isinstance(version, int) or isinstance(version, bool):
            errors.append(
                "before_version must be an int; got "
                + type(version).__name__
            )
        elif version < 1:
            errors.append(
                "before_version must be >= 1; got " + str(version)
            )

        # W8 -- before_snapshot must be a non-empty dict
        before_snap = getattr(request, "before_snapshot", None)
        if not isinstance(before_snap, dict):
            errors.append(
                "before_snapshot must be a dict; got "
                + type(before_snap).__name__
            )
        elif len(before_snap) == 0:
            errors.append("before_snapshot must be a non-empty dict")

        # W9 -- new_snapshot must be a non-empty dict
        new_snap = getattr(request, "new_snapshot", None)
        if not isinstance(new_snap, dict):
            errors.append(
                "new_snapshot must be a dict; got "
                + type(new_snap).__name__
            )
        elif len(new_snap) == 0:
            errors.append("new_snapshot must be a non-empty dict")

        # W10 -- reviewer must be a non-empty string
        if not _is_nonempty_str(getattr(request, "reviewer", "")):
            errors.append("reviewer must be a non-empty string")

        # W11 -- change_reason must be a non-empty string
        if not _is_nonempty_str(getattr(request, "change_reason", "")):
            errors.append("change_reason must be a non-empty string")

        # W12 -- new_snapshot["version"] == before_version + 1
        if isinstance(new_snap, dict):
            new_version = new_snap.get("version", None)
            if isinstance(version, int) and not isinstance(version, bool):
                if not isinstance(new_version, int) or isinstance(new_version, bool):
                    errors.append(
                        "new_snapshot.version must be an int; got "
                        + type(new_version).__name__
                    )
                elif new_version != version + 1:
                    errors.append(
                        "new_snapshot.version must be before_version + 1; got "
                        + str(new_version) + " expected " + str(version + 1)
                    )

        # W13 -- new_snapshot["knowledge_id"] == target_identity
        if isinstance(new_snap, dict):
            new_kid = new_snap.get("knowledge_id", None)
            target_kid = getattr(request, "target_identity", "")
            if new_kid != target_kid:
                errors.append(
                    "new_snapshot.knowledge_id must equal target_identity; got "
                    + repr(new_kid) + " expected " + repr(target_kid)
                )

        # W14 -- new_snapshot != before_snapshot
        if isinstance(before_snap, dict) and isinstance(new_snap, dict):
            if new_snap == before_snap:
                errors.append(
                    "new_snapshot must differ from before_snapshot "
                    "(empty write rejected)"
                )

        return WriterValidationResult(
            valid=(len(errors) == 0),
            errors=tuple(errors),
        )


__all__ = [
    "WriterValidator",
    "WriterValidationResult",
]
