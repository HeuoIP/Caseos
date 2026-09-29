"""Promotion contract objects (Sprint 25.2-A).

Defines the three V1 data carriers:

    * ``PromotionStatus``    -- three-state enum
                                 DRAFT / ELIGIBLE / NOT_ELIGIBLE
    * ``ProvenanceRecord``   -- one entry in the audit chain
    * ``PromotionCandidate`` -- the gating record that pairs
                                 a CaseKnowledge with its
                                 provenance chain

All three are frozen dataclasses. Collection fields are
deep-copied on entry so caller mutations cannot leak in.
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Tuple


# ---------------------------------------------------------------------------
# PromotionStatus
# ---------------------------------------------------------------------------


class PromotionStatus(str, Enum):
    """Three-state promotion lifecycle.

    DRAFT          -- candidate is being assembled
    ELIGIBLE       -- passed every policy rule
    NOT_ELIGIBLE   -- failed at least one rule
    """

    DRAFT = "DRAFT"
    ELIGIBLE = "ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


DRAFT: str = PromotionStatus.DRAFT.value
ELIGIBLE: str = PromotionStatus.ELIGIBLE.value
NOT_ELIGIBLE: str = PromotionStatus.NOT_ELIGIBLE.value

PROMOTION_STATUS_ALLOW_LIST: frozenset = frozenset(
    {DRAFT, ELIGIBLE, NOT_ELIGIBLE}
)


class PromotionStatusError(ValueError):
    """Raised when an unknown status string is supplied."""


def _coerce_status(value: Any) -> str:
    if isinstance(value, PromotionStatus):
        return value.value
    if isinstance(value, str) and value in PROMOTION_STATUS_ALLOW_LIST:
        return value
    raise PromotionStatusError(
        "status must be one of "
        + ", ".join(sorted(PROMOTION_STATUS_ALLOW_LIST))
        + "; got " + repr(value)
    )


# ---------------------------------------------------------------------------
# Default factories
# ---------------------------------------------------------------------------


def _empty_tuple() -> tuple:
    return ()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_candidate_id() -> str:
    return "PC-" + uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Default provenance steps (V1 contract)
# ---------------------------------------------------------------------------


STEP_INTAKE: str = "intake"
STEP_CASE_KNOWLEDGE_VALIDATION: str = "case_knowledge_validation"

DEFAULT_PROVENANCE_STEPS: Tuple[str, ...] = (
    STEP_INTAKE,
    STEP_CASE_KNOWLEDGE_VALIDATION,
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class PromotionCandidateError(ValueError):
    """Base error for the Promotion Candidate contract."""


# ---------------------------------------------------------------------------
# ProvenanceRecord
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProvenanceRecord:
    """One entry in a candidate's audit chain.

    Fields
    ------
    step        -- canonical step name, e.g. ``"intake"``
    actor       -- who/what performed the step (free-form)
    timestamp   -- ISO timestamp (defaults to now)
    reference   -- optional pointer (review id, transition id,
                   file path, ...)
    notes       -- free-form operator notes
    """

    step: str = ""
    actor: str = ""
    timestamp: str = field(default_factory=_now_iso)
    reference: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.step, str) or not self.step.strip():
            raise PromotionCandidateError(
                "ProvenanceRecord.step must be a non-empty string"
            )
        if not isinstance(self.actor, str):
            raise PromotionCandidateError(
                "ProvenanceRecord.actor must be a string; got "
                + type(self.actor).__name__
            )

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "reference": self.reference,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: dict) -> "ProvenanceRecord":
        if not isinstance(data, dict):
            raise PromotionCandidateError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict = {}
        for fname in ("step", "actor", "timestamp", "reference", "notes"):
            if fname in data:
                kwargs[fname] = data[fname]
        return ProvenanceRecord(**kwargs)


# ---------------------------------------------------------------------------
# PromotionCandidate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PromotionCandidate:
    """The V1 promotion candidate contract.

    Pairs a CaseKnowledge (referenced by ``case_id``) with
    the audit chain that justifies its promotion. The
    ``status`` field is **set by the eligibility checker**;
    constructors default it to ``DRAFT``.
    """

    # ---- Identity --------------------------------------------------
    candidate_id: str = field(default_factory=_new_candidate_id)

    # ---- Source binding -------------------------------------------
    case_id: str = ""
    case_source_kind: str = ""

    # ---- Target preview -------------------------------------------
    proposed_knowledge_id: str = ""
    proposed_version: int = 1

    # ---- Audit chain ----------------------------------------------
    provenance_chain: Tuple[ProvenanceRecord, ...] = field(
        default_factory=_empty_tuple
    )

    # ---- Justification --------------------------------------------
    justification: str = ""

    # ---- Runtime ---------------------------------------------------
    status: str = DRAFT
    failure_reason: str = ""
    created_at: str = field(default_factory=_now_iso)
    created_by: str = ""

    # ---- Post-init -------------------------------------------------
    def __post_init__(self) -> None:
        # Defensive copy of the provenance chain.
        raw = self.provenance_chain
        if isinstance(raw, list):
            object.__setattr__(
                self,
                "provenance_chain",
                tuple(copy.deepcopy(raw)),
            )
        elif isinstance(raw, tuple):
            object.__setattr__(
                self,
                "provenance_chain",
                tuple(copy.deepcopy(raw)),
            )
        elif raw is None:
            object.__setattr__(self, "provenance_chain", ())

        # Status guard (uses the typed enum coercion).
        object.__setattr__(self, "status", _coerce_status(self.status))

        # ID guard.
        if not isinstance(self.candidate_id, str) or not self.candidate_id:
            raise PromotionCandidateError(
                "candidate_id must be a non-empty string"
            )
        if not isinstance(self.case_id, str) or not self.case_id:
            raise PromotionCandidateError(
                "case_id must be a non-empty string; "
                "PromotionCandidate must reference a CaseKnowledge"
            )
        if (
            not isinstance(self.proposed_version, int)
            or self.proposed_version < 1
        ):
            raise PromotionCandidateError(
                "proposed_version must be a positive integer (>= 1); got "
                + repr(self.proposed_version)
            )

    # ---- Serialization --------------------------------------------
    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "case_id": self.case_id,
            "case_source_kind": self.case_source_kind,
            "proposed_knowledge_id": self.proposed_knowledge_id,
            "proposed_version": self.proposed_version,
            "provenance_chain": [
                r.to_dict() for r in self.provenance_chain
            ],
            "justification": self.justification,
            "status": self.status,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at,
            "created_by": self.created_by,
        }

    @staticmethod
    def from_dict(data: dict) -> "PromotionCandidate":
        if not isinstance(data, dict):
            raise PromotionCandidateError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict = {}
        for fname in (
            "candidate_id", "case_id", "case_source_kind",
            "proposed_knowledge_id", "proposed_version",
            "provenance_chain", "justification", "status",
            "failure_reason", "created_at", "created_by",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        raw_chain = kwargs.get("provenance_chain")
        if isinstance(raw_chain, list):
            kwargs["provenance_chain"] = [
                ProvenanceRecord.from_dict(r)
                if isinstance(r, dict)
                else r
                for r in raw_chain
            ]
        return PromotionCandidate(**kwargs)


# ---------------------------------------------------------------------------
# Convenience builder
# ---------------------------------------------------------------------------


def new_promotion_candidate(
    *,
    case_id: str,
    provenance_chain=None,
    case_source_kind: str = "",
    proposed_knowledge_id: str = "",
    proposed_version: int = 1,
    justification: str = "",
    created_by: str = "",
) -> PromotionCandidate:
    """Construct a ``PromotionCandidate`` with DRAFT status.

    The eligibility checker is responsible for promoting
    ``status`` to ELIGIBLE or NOT_ELIGIBLE.
    """
    if not case_id or not case_id.strip():
        raise PromotionCandidateError(
            "case_id must be a non-empty string"
        )
    return PromotionCandidate(
        case_id=case_id,
        case_source_kind=case_source_kind,
        proposed_knowledge_id=proposed_knowledge_id,
        proposed_version=proposed_version,
        provenance_chain=tuple(provenance_chain or ()),
        justification=justification,
        created_by=created_by,
    )
