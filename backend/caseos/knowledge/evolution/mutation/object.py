"""Mutation Object Schemas V1 (Sprint 22.4-H, ADR-020).

Frozen dataclasses that constitute the mutation contract:

    MutationRequest              (input)
    MutationValidationResult     (validator output)

Both are **frozen**. The ``change_payload`` dict on the
request is deep-copied in ``__post_init__`` so caller
mutations do not leak into the request.

M5 allow-list (Sprint 22.4-H spec Task 2):

    boundary_update_candidate
    principle_update_candidate
    applicability_update_candidate

Anything outside the allow-list is rejected by the
``MutationValidator``.

Architecture boundary (Sprint 22.4-H spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ..contracts.change_type import EvolutionChangeType


# V1 allow-list (Sprint 22.4-H spec Task 2 M5; Sprint 22.4-I
# contract alignment). The mutation runtime now uses the
# unified ``EvolutionChangeType`` enum (bare names, no
# ``_candidate`` suffix). Anything outside the allow-list
# is rejected by MutationValidator rule M5.
MUTATION_ALLOWED_CHANGE_TYPES = frozenset({
    EvolutionChangeType.BOUNDARY_UPDATE,
    EvolutionChangeType.PRINCIPLE_UPDATE,
    EvolutionChangeType.APPLICABILITY_UPDATE,
})


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_mutation_id() -> str:
    return "mut-" + str(uuid.uuid4())


@dataclass(frozen=True)
class MutationRequest:
    """A single request to mutate a Knowledge Object.

    Required fields (Sprint 22.4-H spec Task 1):

        mutation_id       unique identifier
        transaction_id    the approved EvolutionTransaction
                          this mutation belongs to
        target_identity   the KO this mutation targets
        change_type       must be in MUTATION_ALLOWED_CHANGE_TYPES
        before_version    the version_number we mutate FROM
                          (must exist in the VersionStore)
        change_payload    dict describing the change. The
                          runtime interprets ``target_field``
                          and ``new_value`` keys:
                              {
                                "target_field": "boundary",
                                "new_value": "..."
                              }
                          Other keys are passed through as
                          opaque metadata.
        reviewer          non-empty string (human approver)
        created_at        ISO timestamp (datetime)

    Notes:

        * The request is **immutable** (``frozen=True``).
        * ``change_payload`` is **deep-copied** in
          ``__post_init__`` so caller mutations do not leak
          into the request.
        * ``mutation_id`` defaults to a UUID4 string.
    """

    mutation_id: str
    transaction_id: str
    target_identity: str
    change_type: Any  # EvolutionChangeType (annotation only)
    before_version: int
    change_payload: dict
    reviewer: str
    created_at: datetime = field(default_factory=_now)

    def __post_init__(self) -> None:
        # Defensive copy of the change_payload dict so caller
        # mutations do not leak into the request.
        if isinstance(self.change_payload, dict):
            object.__setattr__(
                self, "change_payload",
                copy.deepcopy(self.change_payload),
            )
        # Coerce string change_type to EvolutionChangeType
        # for Sprint 22.4-I contract alignment. Invalid
        # strings remain strings; rule M5 will then reject
        # the request.
        if isinstance(self.change_type, str):
            try:
                object.__setattr__(
                    self, "change_type",
                    EvolutionChangeType(self.change_type),
                )
            except ValueError:
                pass

    def to_dict(self) -> dict:
        """Return a JSON-safe representation."""
        out = {
            "mutation_id": self.mutation_id,
            "transaction_id": self.transaction_id,
            "target_identity": self.target_identity,
            "change_type": (
                self.change_type.value
                if isinstance(self.change_type, EvolutionChangeType)
                else self.change_type
            ),
            "before_version": self.before_version,
            "change_payload": self.change_payload,
            "reviewer": self.reviewer,
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                if isinstance(self.created_at, datetime)
                else self.created_at,
        }
        return out




@dataclass(frozen=True)
class MutationValidationResult:
    """The outcome of a ``MutationValidator.validate`` call.

    Attributes:
        valid: True iff every rule passed.
        rule_id: The first rule that failed (e.g. ``"M1"``).
            Empty string when ``valid``.
        reason: Human-readable reason for the decision.
            Empty string when ``valid``.
    """

    valid: bool
    rule_id: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


__all__ = [
    "MUTATION_ALLOWED_CHANGE_TYPES",
    "MutationRequest",
    "MutationValidationResult",
]
