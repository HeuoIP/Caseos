"""Admission Writer V1 (Sprint 25.4-A).

The single, deterministic write boundary for first-time
admission of a Case Knowledge into the formal Knowledge
Base. After AdmissionChecker has signed an
``AdmissionCandidate`` as ``ADMISSIBLE``, this writer is
the only legal path to create:

    * a ``KnowledgeObject`` (version = 1)
    * a ``KnowledgeVersion`` baseline in the VersionStore
    * an ``EvolutionAuditRecord`` with action = "admission"

Pipeline position (V1):

    PromotionCandidate (ELIGIBLE)
          |
          v
    AdmissionCandidate (ADMISSIBLE)   <-- Sprint 25.3-A
          |
          v
    AdmissionWriter                  <-- THIS module
          |
          +--> KnowledgeObject v1
          +--> KnowledgeVersion baseline (v1, previous=None)
          +--> EvolutionAuditRecord

Semantic boundary (Sprint 25.3-A + 25.4-A):

    * V1   -> Admission-owned (this writer)
    * V2+  -> Evolution-owned (NOT this writer)
    * Rollback -> Evolution-owned (NOT this writer)

This writer NEVER calls Evolution mutation paths. It ONLY
calls the append-only ``VersionStore.append`` and
``EvolutionAuditStore.append`` primitives.

Idempotency
-----------

Calling ``write()`` twice with the same candidate yields:

    * first call:  CREATED  (KnowledgeObject v1 + baseline + audit)
    * second call: IDEMPOTENT (no mutation; returns the existing
                              KO + a duplicate-of-record audit
                              entry tagged with action
                              "admission_idempotent")

A second constructor option (``on_duplicate="strict"``) makes
the writer raise ``DuplicateAdmissionError`` instead.

Existing KO protection
----------------------

If the target identity already has ANY version in the
``VersionStore`` (regardless of which Sprint wrote it), the
writer treats this as "already admitted" and either returns
IDEMPOTENT or raises, never overwrites.

Architecture boundary (Sprint 25.4-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
        * caseos.knowledge.intake
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * caseos.brain.*
    This module MAY import from:
        * caseos.knowledge.ingestion.object
        * caseos.knowledge.ingestion.promotion
        * caseos.knowledge.ingestion.admission
        * caseos.knowledge.object
        * caseos.knowledge.evolution.versioning
        * caseos.knowledge.evolution.audit
        * stdlib
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from caseos.knowledge.evolution.audit import (
    EvolutionAuditRecord,
    EvolutionAuditStore,
)
from caseos.knowledge.evolution.versioning import (
    KnowledgeVersion,
    VersionStore,
    VersionStoreError,
)

from caseos.knowledge.ingestion.admission.object import (
    ADMISSIBLE,
    ADMISSION_TARGET_VERSION,
    AdmissionCandidate,
    AdmissionCandidateError,
)

from caseos.knowledge.object.object import (
    KnowledgeObject,
    KnowledgeObjectError,
)
from caseos.knowledge.object.object import (
    KnowledgeObject,
    KnowledgeObjectError,
)


# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------


CREATED: str = "CREATED"
IDEMPOTENT: str = "IDEMPOTENT"
REJECTED: str = "REJECTED"

WRITE_STATUS_ALLOW_LIST: frozenset = frozenset(
    {CREATED, IDEMPOTENT, REJECTED}
)


# ---------------------------------------------------------------------------
# Default factories
# ---------------------------------------------------------------------------


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_version_id() -> str:
    return "V-" + uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class AdmissionWriterError(Exception):
    """Base error for the Admission Writer."""


class DuplicateAdmissionError(AdmissionWriterError):
    """Raised when ``on_duplicate="strict"`` and the writer
    detects an already-admitted identity."""


# ---------------------------------------------------------------------------
# AdmissionWriteResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdmissionWriteResult:
    """The V1 writer output contract.

    Fields
    ------
    success             -- True iff the write completed
    status              -- CREATED / IDEMPOTENT / REJECTED
    knowledge_object    -- the resulting KO (None on REJECTED)
    knowledge_id        -- echoed target identity
    version             -- 1 on success; 0 on REJECTED
    admission_id        -- echoed AdmissionCandidate.admission_id
    audit_record        -- the audit row that was appended
                           (None on REJECTED)
    failure_reason      -- human-readable explanation when
                           status == REJECTED
    created_at          -- ISO timestamp at write time
    """

    success: bool = False
    status: str = REJECTED
    knowledge_object: Optional[KnowledgeObject] = None
    knowledge_id: str = ""
    version: int = 0
    admission_id: str = ""
    audit_record: Optional[EvolutionAuditRecord] = None
    failure_reason: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        out: dict = {
            "success": self.success,
            "status": self.status,
            "knowledge_object": (
                self.knowledge_object.to_dict()
                if self.knowledge_object is not None
                else None
            ),
            "knowledge_id": self.knowledge_id,
            "version": self.version,
            "admission_id": self.admission_id,
            "audit_record": (
                {
                    "audit_id": self.audit_record.audit_id,
                    "transaction_id": self.audit_record.transaction_id,
                    "action": self.audit_record.action,
                    "actor": self.audit_record.actor,
                    "reason": self.audit_record.reason,
                }
                if self.audit_record is not None
                else None
            ),
            "failure_reason": self.failure_reason,
            "created_at": self.created_at,
        }
        return out


# ---------------------------------------------------------------------------
# Field mapping (deterministic, no LLM)
# ---------------------------------------------------------------------------


# Map from AdmissionCandidate.admission_proposal keys to
# KnowledgeObject field names. Anything not listed here is
# read directly from the proposal if present (caller may
# provide custom keys).
_KO_PROPOSAL_KEY_MAP: Mapping[str, str] = {
    "title": "title",
    "description": "description",
    "category": "category",
    "project_type": "project_type",
    "site_type": "site_type",
    "location_type": "location_type",
    "space_size": "space_size",
    "theme": "theme",
    "style": "style",
    "color_system": "color_system",
    "interaction_type": "interaction_type",
    "function_tags": "function_tags",
    "image_refs": "image_refs",
    "document_refs": "document_refs",
    "source": "source",
}


# Default values for KO fields when the proposal is silent.
# These are intentionally conservative; we never invent
# business data, only neutral placeholders.
_KO_FIELD_DEFAULTS: Mapping[str, Any] = {
    "title": "",
    "description": "",
    "category": "case",
    "project_type": "",
    "site_type": "",
    "location_type": "",
    "space_size": "",
    "theme": "",
    "style": "",
    "color_system": "",
    "interaction_type": "",
    "function_tags": [],
    "image_refs": [],
    "document_refs": [],
    "source": "admission",
}


def _coerce_collection(value: Any) -> list:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    return [value]


# ---------------------------------------------------------------------------
# AdmissionWriter
# ---------------------------------------------------------------------------


class AdmissionWriter:
    """V1 first-entry admission writer.

    Constructor parameters
    ----------------------
    version_store:
        Existing ``VersionStore`` from
        ``caseos.knowledge.evolution.versioning``. The writer
        appends a v1 baseline to this store.
    audit_store:
        Existing ``EvolutionAuditStore`` from
        ``caseos.knowledge.evolution.audit``. The writer
        appends an audit record per successful / idempotent
        write.
    existing_kos:
        Optional mapping ``knowledge_id -> KnowledgeObject``
        that the writer treats as an additional source of
        identity truth. If provided and the identity is
        present, the writer returns IDEMPOTENT (or raises in
        strict mode) WITHOUT consulting VersionStore.
        When ``None``, VersionStore is the single source of
        truth (per spec: "如果系统已有 identity registry /
        VersionStore 能提供幂等判断，优先复用").
    actor:
        Free-form operator/system name attached to every
        audit record the writer emits.
    on_duplicate:
        "idempotent" (default) -> return AdmissionWriteResult
                                  with status=IDEMPOTENT.
        "strict"               -> raise
                                  DuplicateAdmissionError on
                                  duplicate detection.
    """

    ENGINE_NAME: str = "AdmissionWriter V1"

    def __init__(
        self,
        *,
        version_store: VersionStore,
        audit_store: EvolutionAuditStore,
        existing_kos: Optional[Mapping[str, KnowledgeObject]] = None,
        actor: str = "admission_writer",
        on_duplicate: str = "idempotent",
    ) -> None:
        if not isinstance(version_store, VersionStore):
            raise AdmissionWriterError(
                "version_store must be a VersionStore; got "
                + type(version_store).__name__
            )
        if not isinstance(audit_store, EvolutionAuditStore):
            raise AdmissionWriterError(
                "audit_store must be an EvolutionAuditStore; got "
                + type(audit_store).__name__
            )
        if on_duplicate not in ("idempotent", "strict"):
            raise AdmissionWriterError(
                "on_duplicate must be 'idempotent' or 'strict'; got "
                + repr(on_duplicate)
            )
        if existing_kos is not None and not isinstance(
            existing_kos, Mapping
        ):
            raise AdmissionWriterError(
                "existing_kos must be a Mapping or None; got "
                + type(existing_kos).__name__
            )

        self.version_store: VersionStore = version_store
        self.audit_store: EvolutionAuditStore = audit_store
        self.existing_kos: Optional[Mapping[str, KnowledgeObject]] = (
            existing_kos
        )
        self.actor: str = actor
        self.on_duplicate: str = on_duplicate

    # ---- public ----------------------------------------------------

    def write(
        self, candidate: AdmissionCandidate
    ) -> AdmissionWriteResult:
        """Run the admission write.

        The candidate MUST already be ``ADMISSIBLE``. The
        writer does NOT re-run the AdmissionChecker.

        Returns an ``AdmissionWriteResult``. Never mutates the
        candidate or any of its referenced records.
        """
        # ---- input validation ------------------------------------
        if not isinstance(candidate, AdmissionCandidate):
            return AdmissionWriteResult(
                success=False,
                status=REJECTED,
                failure_reason=(
                    "candidate must be an AdmissionCandidate; got "
                    + type(candidate).__name__
                ),
                admission_id="",
            )

        if candidate.status != ADMISSIBLE:
            return AdmissionWriteResult(
                success=False,
                status=REJECTED,
                failure_reason=(
                    "candidate.status must be "
                    + repr(ADMISSIBLE)
                    + " for the writer; got "
                    + repr(candidate.status)
                ),
                admission_id=candidate.admission_id,
            )

        if candidate.target_version != ADMISSION_TARGET_VERSION:
            return AdmissionWriteResult(
                success=False,
                status=REJECTED,
                failure_reason=(
                    "candidate.target_version must be "
                    + str(ADMISSION_TARGET_VERSION)
                    + "; got " + repr(candidate.target_version)
                ),
                admission_id=candidate.admission_id,
            )

        if (
            not candidate.target_knowledge_id
            or not candidate.target_knowledge_id.strip()
        ):
            return AdmissionWriteResult(
                success=False,
                status=REJECTED,
                failure_reason="target_knowledge_id is empty",
                admission_id=candidate.admission_id,
            )

        target_id = candidate.target_knowledge_id

        # ---- duplicate / existing-KO detection ------------------
        existing_v = self._find_existing_version(target_id)
        if existing_v is not None or (
            self.existing_kos is not None
            and target_id in self.existing_kos
        ):
            return self._handle_duplicate(
                candidate, target_id, existing_v,
            )

        # ---- build KO + version + audit -------------------------
        try:
            ko = self._create_knowledge_object(candidate)
        except (KnowledgeObjectError, AdmissionCandidateError) as exc:
            return AdmissionWriteResult(
                success=False,
                status=REJECTED,
                failure_reason=(
                    "KnowledgeObject build failed: " + str(exc)
                ),
                admission_id=candidate.admission_id,
            )

        version = self._build_version_record(ko, candidate)
        try:
            self.version_store.append(version)
        except VersionStoreError as exc:
            return AdmissionWriteResult(
                success=False,
                status=REJECTED,
                failure_reason=(
                    "VersionStore.append failed: " + str(exc)
                ),
                admission_id=candidate.admission_id,
                knowledge_id=target_id,
            )

        audit = self._build_audit_record(
            candidate, ko, version, action="admission",
        )
        self.audit_store.append(audit)

        return AdmissionWriteResult(
            success=True,
            status=CREATED,
            knowledge_object=ko,
            knowledge_id=target_id,
            version=ADMISSION_TARGET_VERSION,
            admission_id=candidate.admission_id,
            audit_record=audit,
            failure_reason="",
        )

    # ---- private helpers ------------------------------------------

    def _find_existing_version(
        self, target_id: str
    ) -> Optional[KnowledgeVersion]:
        history = self.version_store.history(target_id)
        return history[-1] if history else None

    def _handle_duplicate(
        self,
        candidate: AdmissionCandidate,
        target_id: str,
        existing_version: Optional[KnowledgeVersion],
    ) -> AdmissionWriteResult:
        if self.on_duplicate == "strict":
            raise DuplicateAdmissionError(
                "AdmissionCandidate " + repr(candidate.admission_id)
                + " targets an already-admitted identity "
                + repr(target_id)
                + "; refusing to overwrite"
            )
        # idempotent mode
        audit = self._build_audit_record(
            candidate,
            knowledge_object=None,
            version=existing_version,
            action="admission_idempotent",
        )
        self.audit_store.append(audit)
        return AdmissionWriteResult(
            success=True,
            status=IDEMPOTENT,
            knowledge_object=None,
            knowledge_id=target_id,
            version=(
                existing_version.version_number
                if existing_version is not None else 0
            ),
            admission_id=candidate.admission_id,
            audit_record=audit,
            failure_reason="",
        )

    def _create_knowledge_object(
        self, candidate: AdmissionCandidate
    ) -> KnowledgeObject:
        proposal = candidate.admission_proposal
        kwargs: dict = {
            "knowledge_id": candidate.target_knowledge_id,
            "version": ADMISSION_TARGET_VERSION,
        }
        for ko_field, proposal_key in _KO_PROPOSAL_KEY_MAP.items():
            if proposal_key in proposal:
                value = proposal[proposal_key]
            else:
                value = _KO_FIELD_DEFAULTS.get(ko_field, "")
            # Coerce list/tuple collections.
            if ko_field in (
                "function_tags", "image_refs", "document_refs",
            ):
                value = _coerce_collection(value)
            kwargs[ko_field] = value

        now = _now_iso()
        kwargs.setdefault("created_at", now)
        kwargs.setdefault("updated_at", now)

        return KnowledgeObject(**kwargs)

    def _build_version_record(
        self,
        ko: KnowledgeObject,
        candidate: AdmissionCandidate,
    ) -> KnowledgeVersion:
        return KnowledgeVersion(
            version_id=_new_version_id(),
            target_identity=ko.knowledge_id,
            version_number=ADMISSION_TARGET_VERSION,
            previous_version=None,
            snapshot=ko.to_dict(),
            created_at=_now(),
            created_by=self.actor,
            change_reason="admission baseline (target_version=1)",
            proposal_id=candidate.admission_id,
        )

    def _build_audit_record(
        self,
        candidate: AdmissionCandidate,
        knowledge_object: Optional[KnowledgeObject],
        version: Optional[KnowledgeVersion],
        action: str,
    ) -> EvolutionAuditRecord:
        provenance_payload = [
            r.to_dict() for r in candidate.source.provenance_chain
        ]
        after: dict = {
            "knowledge_id": candidate.target_knowledge_id,
            "version": ADMISSION_TARGET_VERSION,
            "admission_id": candidate.admission_id,
            "candidate_id": candidate.source.promotion_candidate_id,
            "case_id": candidate.source.case_id,
            "source_kind": candidate.source.case_source_kind,
            "provenance": provenance_payload,
            "requires_human_review": candidate.requires_human_review,
        }
        if knowledge_object is not None:
            after["knowledge_id"] = knowledge_object.knowledge_id
        if version is not None:
            after["version"] = version.version_number
        return EvolutionAuditRecord(
            audit_id=str(uuid.uuid4()),
            transaction_id=candidate.admission_id,
            action=action,
            actor=self.actor,
            before=None,
            after=after,
            reason=candidate.justification,
        )