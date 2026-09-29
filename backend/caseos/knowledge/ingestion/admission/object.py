"""Admission contract objects (Sprint 25.3-A).

V1 data carriers:

    * ``AdmissionStatus``       -- DRAFT / ADMISSIBLE / NOT_ADMISSIBLE
    * ``AdmissionProvenanceRef``-- back-reference to the source
                                   PromotionCandidate (preserves
                                   the full provenance chain)
    * ``AdmissionCandidate``    -- the immutable first-entry
                                   handoff a future Writer
                                   Sprint can consume

All three are frozen dataclasses. Collection fields are
deep-copied on entry so caller mutations cannot leak in.
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Tuple

from caseos.knowledge.ingestion.promotion.object import ProvenanceRecord


# ---------------------------------------------------------------------------
# AdmissionStatus
# ---------------------------------------------------------------------------


class AdmissionStatus(str, Enum):
    """Three-state admission lifecycle.

    DRAFT           -- candidate is being assembled
    ADMISSIBLE      -- passed every admission policy rule
    NOT_ADMISSIBLE  -- failed at least one rule
    """

    DRAFT = "DRAFT"
    ADMISSIBLE = "ADMISSIBLE"
    NOT_ADMISSIBLE = "NOT_ADMISSIBLE"


DRAFT: str = AdmissionStatus.DRAFT.value
ADMISSIBLE: str = AdmissionStatus.ADMISSIBLE.value
NOT_ADMISSIBLE: str = AdmissionStatus.NOT_ADMISSIBLE.value

ADMISSION_STATUS_ALLOW_LIST: frozenset = frozenset(
    {DRAFT, ADMISSIBLE, NOT_ADMISSIBLE}
)


# V1 invariant: the first and only version a fresh
# AdmissionCandidate may target. Future Sprints may
# introduce multi-version admission, but V1 is single-
# version (version=1, the baseline) only.
ADMISSION_TARGET_VERSION: int = 1


class AdmissionStatusError(ValueError):
    """Raised when an unknown status string is supplied."""


def _coerce_status(value: Any) -> str:
    if isinstance(value, AdmissionStatus):
        return value.value
    if isinstance(value, str) and value in ADMISSION_STATUS_ALLOW_LIST:
        return value
    raise AdmissionStatusError(
        "status must be one of "
        + ", ".join(sorted(ADMISSION_STATUS_ALLOW_LIST))
        + "; got " + repr(value)
    )


# ---------------------------------------------------------------------------
# Default factories
# ---------------------------------------------------------------------------


def _empty_tuple() -> tuple:
    return ()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_admission_id() -> str:
    return "AD-" + uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class AdmissionCandidateError(ValueError):
    """Base error for the Admission Candidate contract."""


# ---------------------------------------------------------------------------
# AdmissionProvenanceRef
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdmissionProvenanceRef:
    """Back-reference to the source PromotionCandidate.

    The ref MUST preserve the full provenance chain so that
    later audits can reconstruct how the candidate got into
    the admission pipeline.

    Fields
    ------
    promotion_candidate_id     -- PC-* id of the source
    case_id                    -- CK-* id of the source CaseKnowledge
    case_source_kind           -- one of "intake" / "external" / "operator"
    provenance_chain           -- full tuple of ProvenanceRecord
                                  (deep-copied on entry)
    """

    promotion_candidate_id: str = ""
    case_id: str = ""
    case_source_kind: str = ""
    provenance_chain: Tuple[ProvenanceRecord, ...] = field(
        default_factory=_empty_tuple
    )

    def __post_init__(self) -> None:
        # Defensive deep-copy of the chain.
        raw = self.provenance_chain
        if isinstance(raw, list):
            object.__setattr__(
                self, "provenance_chain",
                tuple(copy.deepcopy(raw)),
            )
        elif isinstance(raw, tuple):
            object.__setattr__(
                self, "provenance_chain",
                tuple(copy.deepcopy(raw)),
            )
        elif raw is None:
            object.__setattr__(self, "provenance_chain", ())

        if not isinstance(self.promotion_candidate_id, str) \
                or not self.promotion_candidate_id.strip():
            raise AdmissionCandidateError(
                "AdmissionProvenanceRef.promotion_candidate_id "
                "must be a non-empty string"
            )
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise AdmissionCandidateError(
                "AdmissionProvenanceRef.case_id must be a "
                "non-empty string"
            )

    def to_dict(self) -> dict:
        return {
            "promotion_candidate_id": self.promotion_candidate_id,
            "case_id": self.case_id,
            "case_source_kind": self.case_source_kind,
            "provenance_chain": [
                r.to_dict() for r in self.provenance_chain
            ],
        }

    @staticmethod
    def from_dict(data: dict) -> "AdmissionProvenanceRef":
        if not isinstance(data, dict):
            raise AdmissionCandidateError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict = {}
        for fname in (
            "promotion_candidate_id", "case_id",
            "case_source_kind", "provenance_chain",
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
        return AdmissionProvenanceRef(**kwargs)


# ---------------------------------------------------------------------------
# AdmissionCandidate
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdmissionCandidate:
    """The V1 admission contract.

    An ``AdmissionCandidate`` is the immutable handoff that
    a future Writer Sprint (e.g. 25.4-A) consumes to register
    a brand-new Knowledge Object (version=1) in the Knowledge
    Corpus. The candidate carries:

        * ``source``              -- back-reference to the
                                     PromotionCandidate (with full
                                     provenance chain)
        * ``target_knowledge_id`` -- the KO id this admission
                                     will create
        * ``target_version``      -- V1 invariant: 1
        * ``admission_proposal``  -- a frozen mapping of the
                                     fields the Writer should
                                     emit (no KO instance, just
                                     a value snapshot)
        * ``justification``       -- human-readable rationale
                                     (must contain the human
                                     review marker in V1)
        * ``requires_human_review``-- V1 invariant: True
        * ``status``              -- DRAFT / ADMISSIBLE /
                                     NOT_ADMISSIBLE; the checker
                                     flips DRAFT to ADMISSIBLE or
                                     NOT_ADMISSIBLE
        * ``failure_reason``      -- populated on NOT_ADMISSIBLE

    The candidate NEVER mutates any external state. It is
    a contract, not a writer.
    """

    # ---- Identity --------------------------------------------------
    admission_id: str = field(default_factory=_new_admission_id)

    # ---- Target preview -------------------------------------------
    target_knowledge_id: str = ""
    target_version: int = ADMISSION_TARGET_VERSION

    # ---- Source ref (PromotionCandidate back-reference) ----------
    source: AdmissionProvenanceRef = field(
        default_factory=lambda: AdmissionProvenanceRef(
            promotion_candidate_id="PC-unset",
            case_id="CK-unset",
        )
    )

    # ---- Writer-facing payload ------------------------------------
    admission_proposal: Mapping[str, Any] = field(
        default_factory=dict
    )

    # ---- Justification + human review -----------------------------
    justification: str = ""
    requires_human_review: bool = True

    # ---- Runtime ---------------------------------------------------
    status: str = DRAFT
    failure_reason: str = ""
    created_at: str = field(default_factory=_now_iso)
    created_by: str = ""

    # ---- Post-init -------------------------------------------------
    def __post_init__(self) -> None:
        # Defensive deep-copy of the proposal mapping.
        prop = self.admission_proposal
        if isinstance(prop, dict):
            object.__setattr__(
                self, "admission_proposal", copy.deepcopy(prop)
            )
        elif prop is None:
            object.__setattr__(self, "admission_proposal", {})

        # Status coercion (defends against unknown strings).
        object.__setattr__(self, "status", _coerce_status(self.status))

        # ID guard.
        if not isinstance(self.admission_id, str) or not self.admission_id:
            raise AdmissionCandidateError(
                "admission_id must be a non-empty string"
            )

        # V1 invariant: target_version must equal ADMISSION_TARGET_VERSION.
        if self.target_version != ADMISSION_TARGET_VERSION:
            raise AdmissionCandidateError(
                "V1 AdmissionCandidate.target_version must be "
                + str(ADMISSION_TARGET_VERSION) + "; got "
                + repr(self.target_version)
            )

        # V1 invariant: requires_human_review must be True.
        if not isinstance(self.requires_human_review, bool):
            raise AdmissionCandidateError(
                "requires_human_review must be a bool; got "
                + type(self.requires_human_review).__name__
            )
        if not self.requires_human_review:
            raise AdmissionCandidateError(
                "V1 AdmissionCandidate.requires_human_review must be "
                "True; got False (V1 forbids auto-admission)"
            )
        # target_knowledge_id guard.
        if (
            not isinstance(self.target_knowledge_id, str)
            or not self.target_knowledge_id.strip()
        ):
            raise AdmissionCandidateError(
                "target_knowledge_id must be a non-empty string"
            )

        # source guard: must be the right type.
        if not isinstance(self.source, AdmissionProvenanceRef):
            raise AdmissionCandidateError(
                "source must be an AdmissionProvenanceRef; got "
                + type(self.source).__name__
            )

    # ---- Serialization --------------------------------------------
    def to_dict(self) -> dict:
        return {
            "admission_id": self.admission_id,
            "target_knowledge_id": self.target_knowledge_id,
            "target_version": self.target_version,
            "source": self.source.to_dict(),
            "admission_proposal": dict(self.admission_proposal),
            "justification": self.justification,
            "requires_human_review": self.requires_human_review,
            "status": self.status,
            "failure_reason": self.failure_reason,
            "created_at": self.created_at,
            "created_by": self.created_by,
        }

    @staticmethod
    def from_dict(data: dict) -> "AdmissionCandidate":
        if not isinstance(data, dict):
            raise AdmissionCandidateError(
                "from_dict expects a dict; got " + type(data).__name__
            )
        kwargs: dict = {}
        for fname in (
            "admission_id", "target_knowledge_id", "target_version",
            "admission_proposal", "justification",
            "requires_human_review", "status", "failure_reason",
            "created_at", "created_by",
        ):
            if fname in data:
                kwargs[fname] = data[fname]
        raw_source = data.get("source")
        if isinstance(raw_source, dict):
            kwargs["source"] = AdmissionProvenanceRef.from_dict(raw_source)
        elif isinstance(raw_source, AdmissionProvenanceRef):
            kwargs["source"] = raw_source
        return AdmissionCandidate(**kwargs)


# ---------------------------------------------------------------------------
# Convenience builder
# ---------------------------------------------------------------------------


def new_admission_candidate(
    *,
    promotion_candidate_id: str,
    case_id: str,
    case_source_kind: str,
    provenance_chain,
    target_knowledge_id: str,
    admission_proposal: Mapping[str, Any],
    justification: str,
    requires_human_review: bool = True,
    created_by: str = "",
) -> AdmissionCandidate:
    """Construct an AdmissionCandidate with DRAFT status.

    Convenience builder that wires the AdmissionProvenanceRef
    automatically.
    """
    if not promotion_candidate_id or not promotion_candidate_id.strip():
        raise AdmissionCandidateError(
            "promotion_candidate_id must be a non-empty string"
        )
    if not case_id or not case_id.strip():
        raise AdmissionCandidateError(
            "case_id must be a non-empty string"
        )
    if not target_knowledge_id or not target_knowledge_id.strip():
        raise AdmissionCandidateError(
            "target_knowledge_id must be a non-empty string"
        )
    if not isinstance(admission_proposal, Mapping):
        raise AdmissionCandidateError(
            "admission_proposal must be a mapping; got "
            + type(admission_proposal).__name__
        )
    if not isinstance(requires_human_review, bool):
        raise AdmissionCandidateError(
            "requires_human_review must be a bool; got "
            + type(requires_human_review).__name__
        )

    return AdmissionCandidate(
        target_knowledge_id=target_knowledge_id,
        source=AdmissionProvenanceRef(
            promotion_candidate_id=promotion_candidate_id,
            case_id=case_id,
            case_source_kind=case_source_kind,
            provenance_chain=tuple(provenance_chain or ()),
        ),
        admission_proposal=admission_proposal,
        justification=justification,
        requires_human_review=requires_human_review,
        created_by=created_by,
    )