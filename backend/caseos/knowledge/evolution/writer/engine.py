"""Knowledge Object Evolution Writer Engine V1 (Sprint 23.0-C, ADR-020).

The ``KnowledgeObjectWriter`` is the **append-only
persistence layer** between the Evolution Adapter (Sprint
23.0-B) and the existing ``VersionStore`` / ``AuditStore``
append-only containers.

    WriteRequest     (Sprint 23.0-C, .object)
        |
        v
    WriterValidator  (W1-W14)
        |
        v
    KnowledgeObjectWriter.write(...)
        |
        +---> VersionStore.append(KnowledgeVersion)
        |
        +---> AuditStore.append(EvolutionAuditRecord)
        |
        v
    WriteResult      (frozen, audit-friendly)

Hard invariants (Sprint 23.0-C spec):

    * The writer NEVER mutates an existing KnowledgeVersion.
    * The writer NEVER overwrites. Both ``VersionStore`` and
      ``AuditStore`` are append-only; the writer only ever
      calls their ``.append()`` method.
    * The writer does NOT touch any intelligence module
      (Decision / Trust / Recommendation) or Retrieval.
    * The writer does NOT touch an in-place Knowledge
      Object. It produces a NEW ``KnowledgeVersion`` whose
      ``version_number`` is ``before_version + 1`` and whose
      ``previous_version`` is the existing latest version's
      number (None when this is the first version).
    * The writer's input ``WriteRequest`` is never mutated.
    * On success, ``mutation_executed=True`` is the first
      meaningful "yes" in the Evolution pipeline. Prior
      layers are candidate-only.

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

import copy
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from ...object import KnowledgeObject, KnowledgeObjectValidator
from ..audit_v2 import AuditStore, EvolutionAuditRecord
from ..contracts.change_type import EvolutionChangeType
from ..versioning import (
    KnowledgeVersion,
    VersionStore,
)
from .object import (
    WriteRequest,
    WriteResult,
)
from .validator import WriterValidator, WriterValidationResult


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_version_id() -> str:
    return "ver-" + str(uuid.uuid4())


def _new_audit_id() -> str:
    return "audit-" + str(uuid.uuid4())


class KnowledgeObjectWriter:
    """Stateless writer. The writer holds only a
    ``WriterValidator``; both stores are passed at call
    time so the writer can be used in tests with fresh
    stores.
    """

    def __init__(
        self,
        *,
        validator: Optional[WriterValidator] = None,
        knowledge_object_validator: Optional[KnowledgeObjectValidator] = None,
    ) -> None:
        self.validator: WriterValidator = validator or WriterValidator()
        self.ko_validator: KnowledgeObjectValidator = (
            knowledge_object_validator or KnowledgeObjectValidator()
        )

    # -------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------

    def write(
        self,
        request: WriteRequest,
        *,
        version_store: VersionStore,
        audit_store: AuditStore,
    ) -> WriteResult:
        """Append a new ``KnowledgeVersion`` and a matching
        ``EvolutionAuditRecord`` to the supplied stores.

        On any rejection neither store is touched.
        """

        # Step 1: input validation
        validation: WriterValidationResult = self.validator.validate(request)
        if not validation.valid:
            return self._reject(
                request=request,
                reason="; ".join(validation.errors),
            )

        # Step 2: confirm the before_version exists in the
        # VersionStore. The writer refuses to write if the
        # caller claims to mutate a version that has no
        # recorded history.
        history = version_store.history(request.target_identity)
        existing_latest = history[-1] if history else None
        if existing_latest is not None:
            existing_version_number = int(existing_latest.version_number)
            if existing_version_number != int(request.before_version):
                return self._reject(
                    request=request,
                    reason=(
                        "before_version "
                        + str(request.before_version)
                        + " does not match the latest recorded version "
                        + str(existing_version_number)
                    ),
                )
        else:
            # No prior history. The writer refuses a write
            # against a non-existent baseline. Sprint 23.0-C
            # spec says the writer's job is to APPEND; the
            # first version must be planted by a separate
            # bootstrap call (out of scope here).
            return self._reject(
                request=request,
                reason=(
                    "no prior KnowledgeVersion found for target_identity "
                    + repr(request.target_identity)
                    + "; the writer cannot bootstrap a first version"
                ),
            )

        # Step 3: confirm new_snapshot is compatible with
        # KnowledgeObject V1 (defence-in-depth; the adapter
        # already does this, but the writer re-checks).
        try:
            candidate_ko = KnowledgeObject.from_dict(request.new_snapshot)
        except Exception as exc:
            return self._reject(
                request=request,
                reason=(
                    "new_snapshot is incompatible with KnowledgeObject V1: "
                    + repr(exc)
                ),
            )
        ko_validation = self.ko_validator.validate(candidate_ko)
        if not ko_validation.valid:
            return self._reject(
                request=request,
                reason=(
                    "new_snapshot fails KnowledgeObjectValidator: "
                    + "; ".join(ko_validation.errors)
                ),
            )

        # Step 4: build the new KnowledgeVersion. The
        # snapshot is deep-copied inside the frozen
        # KnowledgeVersion dataclass, so we do not need an
        # extra copy here.
        new_version_number = int(request.before_version) + 1
        new_version = KnowledgeVersion(
            version_id=_new_version_id(),
            target_identity=request.target_identity,
            version_number=new_version_number,
            previous_version=existing_latest.version_number,
            snapshot=request.new_snapshot,
            created_at=_now(),
            created_by=request.reviewer,
            change_reason=request.change_reason,
            proposal_id=request.proposal_id,
        )

        # Step 5: append the KnowledgeVersion BEFORE the
        # audit record, so the audit can reference the new
        # version_number. Append-only; no mutation of
        # existing versions.
        version_store.append(new_version)

        # Step 6: build the EvolutionAuditRecord. Both
        # snapshots are deep-copied inside the frozen
        # dataclass.
        audit_record = EvolutionAuditRecord(
            audit_id=_new_audit_id(),
            transaction_id=request.transaction_id,
            proposal_id=request.proposal_id,
            target_identity=request.target_identity,
            previous_version=int(request.before_version),
            new_version=new_version_number,
            before_snapshot=request.before_snapshot,
            after_snapshot=request.new_snapshot,
            change_type=request.change_type,
            reason=request.change_reason,
            reviewer=request.reviewer,
            created_at=_now(),
            rollback_reference=None,
        )
        audit_store.append(audit_record)

        # Step 7: emit the success result.
        return WriteResult(
            success=True,
            write_id=request.write_id,
            transaction_id=request.transaction_id,
            target_identity=request.target_identity,
            before_version=int(request.before_version),
            new_version=new_version_number,
            version_id=new_version.version_id,
            audit_id=audit_record.audit_id,
            version_appended=True,
            audit_appended=True,
            mutation_executed=True,
            rejection_reason="",
            created_at=_now(),
        )

    # -------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------

    def _reject(
        self,
        *,
        request: WriteRequest,
        reason: str,
    ) -> WriteResult:
        return WriteResult(
            success=False,
            write_id=request.write_id,
            transaction_id=request.transaction_id,
            target_identity=request.target_identity,
            before_version=int(request.before_version)
                if isinstance(getattr(request, "before_version", None), int)
                else 0,
            new_version=None,
            version_id=None,
            audit_id=None,
            version_appended=False,
            audit_appended=False,
            mutation_executed=False,
            rejection_reason=reason,
            created_at=_now(),
        )


__all__ = ["KnowledgeObjectWriter"]
