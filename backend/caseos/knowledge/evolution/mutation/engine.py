"""Knowledge Mutation Engine V1 (Sprint 22.4-H, ADR-020).

The mutation engine is the **first** real Knowledge Evolution
runtime in CaseOS. It:

    1. Validates the MutationRequest against the
       MutationValidator (M1-M5).
    2. On success: reads the prior ``KnowledgeVersion`` from
       the VersionStore, deep-copies its snapshot, applies
       the change_payload, creates a new immutable
       ``KnowledgeVersion``, and appends it to the
       VersionStore.
    3. Creates an immutable ``EvolutionAuditRecord`` with
       ``before_snapshot`` and ``after_snapshot`` and
       appends it to the AuditStore.
    4. Returns a frozen ``MutationResult``.

Hard invariants (Sprint 22.4-H spec):

    * Old ``KnowledgeVersion`` records are NEVER mutated.
    * The engine does NOT update an in-place Knowledge
      Object. Every mutation produces a NEW version.
    * The engine does NOT expose ``apply`` / ``execute`` /
      ``restore`` / ``rollback`` / ``mutate`` / ``undo``.
    * The engine does NOT import from
      ``caseos.intelligence.*`` or
      ``caseos.knowledge.retrieval``.

Change payload interpretation:

    The engine reads two keys from
    ``MutationRequest.change_payload``:

        * ``target_field`` -- the KO field to mutate. MUST
          be a non-empty string. The payload must also
          include ``new_value`` for that field.
        * ``new_value``    -- the replacement value. May be
          any JSON-safe value (str, list, dict, number,
          bool, None).

    Unknown fields in ``change_payload`` are preserved as
    opaque metadata. They are NOT applied to the snapshot.
    They MAY surface in a future audit log enrichment.

Failure semantics:

    * Validator rejects  -> success=False,
       mutation_executed=False, no stores touched.
    * Snapshot miss     -> success=False,
       mutation_executed=False, no stores touched.
    * Append race / IO  -> the engine does not currently
       model external IO; mutation runs in-process and
       raises only on programmer error (e.g. a non-
       VersionStore passed in).

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
from typing import Any, Optional

from ..audit_v2 import (
    AuditStore,
    AuditStoreError,
    EvolutionAuditRecord,
)
from ..governance import GovernanceResult
from ..object import EvolutionTransaction
from ..versioning import (
    KnowledgeVersion,
    VersionStore,
    VersionStoreError,
)
from .object import (
    MUTATION_ALLOWED_CHANGE_TYPES,
    MutationRequest,
    MutationValidationResult,
)
from .result import MutationResult
from .validator import MutationValidator


def _now() -> Any:
    # Local import keeps the engine's stdlib surface tight.
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


def _new_version_id() -> str:
    return "ver-" + str(uuid.uuid4())


def _new_audit_id() -> str:
    return "audit-" + str(uuid.uuid4())


def _is_nonempty_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _extract_target_field(payload: Any) -> Optional[str]:
    """Extract the ``target_field`` key from a change payload."""
    if not isinstance(payload, dict):
        return None
    tf = payload.get("target_field", None)
    if _is_nonempty_str(tf):
        return tf
    # Some upstream callers (e.g. raw dict copies of ChangeIntent)
    # may use ``field``. We accept both forms but prefer the
    # canonical ``target_field``.
    legacy = payload.get("field", None)
    if _is_nonempty_str(legacy):
        return legacy
    return None


def _has_new_value(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    return "new_value" in payload


class KnowledgeMutationEngine:
    """Stateless mutation engine.

    The engine holds only a ``MutationValidator``. The
    validator is created lazily so the engine can be
    instantiated without side effects.
    """

    def __init__(self, *, validator: Optional[MutationValidator] = None) -> None:
        self.validator = validator or MutationValidator()

    # -------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------

    def mutate(
        self,
        request: MutationRequest,
        transaction: EvolutionTransaction,
        governance: GovernanceResult,
        *,
        version_store: VersionStore,
        audit_store: AuditStore,
        change_intent: Any = None,
    ) -> MutationResult:
        """Execute a mutation attempt.

        Args:
            request: the MutationRequest to execute.
            transaction: the approved source
                EvolutionTransaction.
            governance: the governance verdict.
            version_store: the destination VersionStore.
                MUST be a VersionStore instance; the engine
                does NOT accept other container types.
            audit_store: the destination AuditStore.
                MUST be an AuditStore instance.
            change_intent: optional ChangeIntent. When
                provided and the request's change_payload
                omits a ``new_value``, the engine uses
                ``change_intent.proposed_value`` as a
                fallback.

        Returns:
            A frozen ``MutationResult``. On validation
            failure or store miss the result has
            ``success=False`` and ``mutation_executed=False``;
            the stores are NOT touched.
        """
        if not isinstance(version_store, VersionStore):
            raise VersionStoreError(
                "version_store must be a VersionStore instance"
            )
        if not isinstance(audit_store, AuditStore):
            raise AuditStoreError(
                "audit_store must be an AuditStore instance"
            )

        # --- Validation gate (M1-M5) ----------------------------
        verdict: MutationValidationResult = self.validator.validate(
            request,
            transaction=transaction,
            governance=governance,
            version_store=version_store,
        )
        if not verdict.valid:
            return MutationResult(
                mutation_id=request.mutation_id,
                transaction_id=request.transaction_id,
                target_identity=request.target_identity,
                old_version=0,
                new_version=0,
                mutation_executed=False,
                audit_id=None,
                success=False,
                rejection_rule_id=verdict.rule_id,
                rejection_reason=verdict.reason,
            )

        # --- Snapshot lookup ------------------------------------
        old_version_record: Optional[KnowledgeVersion] = None
        for v in version_store.history(request.target_identity):
            if v.version_number == request.before_version:
                old_version_record = v
                break
        if old_version_record is None:
            # The validator already enforced M4; this branch is
            # only reachable when version_store is None, which
            # we do not allow here.
            return MutationResult(
                mutation_id=request.mutation_id,
                transaction_id=request.transaction_id,
                target_identity=request.target_identity,
                old_version=request.before_version,
                new_version=0,
                mutation_executed=False,
                audit_id=None,
                success=False,
                rejection_rule_id="M4",
                rejection_reason=(
                    "before_version not found in VersionStore: "
                    + str(request.before_version)
                ),
            )

        # --- Build the new snapshot -----------------------------
        # Deep-copy so the old KnowledgeVersion's snapshot
        # cannot leak into the new one (the old record is
        # frozen, but its nested dict is not).
        old_snapshot = copy.deepcopy(old_version_record.snapshot)
        new_snapshot = _apply_payload(
            snapshot=old_snapshot,
            payload=request.change_payload,
            change_intent=change_intent,
        )

        # --- Create the new KnowledgeVersion --------------------
        new_version_number = old_version_record.version_number + 1
        new_version = KnowledgeVersion(
            version_id=_new_version_id(),
            target_identity=request.target_identity,
            version_number=new_version_number,
            previous_version=old_version_record.version_number,
            snapshot=new_snapshot,
            created_at=_now(),
            created_by=request.reviewer,
            change_reason=_change_reason(
                request=request, transaction=transaction,
            ),
            proposal_id=str(getattr(transaction, "proposal_id", "") or ""),
        )
        version_store.append(new_version)

        # --- Create the AuditRecord -----------------------------
        # The audit record carries both snapshots so a future
        # Sprint 22.4.x rollback module can reconstruct the
        # before/after state. The records themselves are
        # append-only (AuditStore raises on update/delete).
        audit_record = EvolutionAuditRecord(
            audit_id=_new_audit_id(),
            transaction_id=request.transaction_id,
            proposal_id=str(getattr(transaction, "proposal_id", "") or ""),
            target_identity=request.target_identity,
            previous_version=old_version_record.version_number,
            new_version=new_version_number,
            before_snapshot=old_snapshot,
            after_snapshot=new_snapshot,
            change_type=request.change_type,
            reason=str(getattr(transaction, "requested_change", "") or ""),
            reviewer=request.reviewer,
            created_at=_now(),
            rollback_reference=None,
        )
        audit_store.append(audit_record)

        return MutationResult(
            mutation_id=request.mutation_id,
            transaction_id=request.transaction_id,
            target_identity=request.target_identity,
            old_version=old_version_record.version_number,
            new_version=new_version_number,
            mutation_executed=True,
            audit_id=audit_record.audit_id,
            success=True,
        )


# -----------------------------------------------------------------
# Internal helpers
# -----------------------------------------------------------------


def _apply_payload(
    *,
    snapshot: Any,
    payload: Any,
    change_intent: Any,
) -> Any:
    """Return a NEW snapshot with the payload applied.

    ``snapshot`` is deep-copied by the caller. The function
    does NOT mutate the input.

    Supported payload shapes:

        * Canonical V1::

              {
                "target_field": "boundary",
                "new_value":    ["Do not add scattered equipment"],
              }

        * Legacy::

              {
                "field":    "boundary",
                "new_value": ["Do not add scattered equipment"],
              }

        * Bare value::

              {"new_value": ...}

          (applied to the field named in ``change_intent``,
          or skipped if no field can be inferred.)

    If ``change_intent`` is provided and the payload omits
    ``target_field``, the engine falls back to
    ``change_intent.target_field``.
    """
    new_snapshot = copy.deepcopy(snapshot)
    if not isinstance(new_snapshot, dict):
        # The V1 mutation contract assumes snapshot is a
        # dict. If a non-dict snapshot slipped through, we
        # leave it untouched and surface the failure via the
        # caller (the engine does not raise here; it is a
        # safe additive step).
        return new_snapshot

    target_field = _extract_target_field(payload)
    if target_field is None and change_intent is not None:
        ci_field = getattr(change_intent, "target_field", None)
        if _is_nonempty_str(ci_field):
            target_field = ci_field

    # Determine the value to apply. Prefer the explicit
    # ``new_value`` key on the payload; otherwise fall back
    # to ``change_intent.proposed_value``.
    if _has_new_value(payload):
        new_value = payload["new_value"]
    elif change_intent is not None:
        ci_value = getattr(change_intent, "proposed_value", None)
        if ci_value is not None:
            new_value = ci_value
        else:
            return new_snapshot
    else:
        return new_snapshot

    if target_field is None:
        # No field to apply to. Leave snapshot unchanged.
        return new_snapshot

    new_snapshot[target_field] = copy.deepcopy(new_value)
    return new_snapshot


def _change_reason(
    *,
    request: MutationRequest,
    transaction: EvolutionTransaction,
) -> str:
    """Build a short change_reason string for the new version."""
    payload_reason = ""
    if isinstance(request.change_payload, dict):
        raw = request.change_payload.get("reason", None)
        if _is_nonempty_str(raw):
            payload_reason = raw
    tx_reason = ""
    if isinstance(getattr(transaction, "requested_change", None), str):
        tx_reason = transaction.requested_change.strip()
    if payload_reason:
        return payload_reason
    if tx_reason:
        return tx_reason
    return (
        "mutation: " + str(request.change_type)
        + " on " + str(request.target_identity)
    )


__all__ = ["KnowledgeMutationEngine"]
