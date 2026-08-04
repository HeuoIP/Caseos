"""Knowledge Object Evolution Adapter Engine V1 (Sprint 23.0-B, ADR-020).

The ``KnowledgeObjectAdapter`` is the **safe bridge** between
the Evolution Runtime and the Knowledge Object V1 schema.

Inputs:

    AdapterRequest  --  an immutable contract that bundles the
                        EvolutionTransaction fields the adapter
                        needs (``change_type``, ``target_version``,
                        ``before_snapshot``, ``requested_change``,
                        ``reviewer``, ``target_identity``) and
                        the parent ``change_intent_id`` /
                        ``transaction_id``.

Output:

    AdapterResult   --  ``success=True`` carries ``new_snapshot``
                        (a dict candidate compatible with
                        ``KnowledgeObject.from_dict``) plus a
                        ``FieldMapping`` describing which KO
                        field was targeted. ``success=False``
                        carries a ``rejection_reason``.

Hard invariants (Sprint 23.0-B spec):

    * The adapter NEVER mutates the input request.
    * The adapter NEVER mutates the input before_snapshot.
    * The adapter NEVER appends to VersionStore or AuditStore.
    * ``mutation_executed`` is always False in V1.
    * The output ``new_snapshot`` is validated against the KO
      V1 schema (``KnowledgeObjectValidator``) on success.
    * On success, ``next_version == before_version + 1``.
    * The adapter is fully deterministic for a given input.

Architecture boundary (Sprint 23.0-B spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.evolution (sibling packages)
        * caseos.knowledge.evolution.contracts
        * caseos.knowledge.object (KO V1 schema + validator)
        * stdlib
"""
from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from ...object import KnowledgeObject, KnowledgeObjectValidator
from ..contracts.change_type import EvolutionChangeType
from .mapping import CHANGE_TYPE_TO_KO_FIELD, resolve_target_field
from .object import (
    AdapterRequest,
    AdapterResult,
    FieldMapping,
)
from .validator import AdapterValidator, AdapterValidationResult


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_mapping_id() -> str:
    return "fmap-" + str(uuid.uuid4())


class KnowledgeObjectAdapter:
    """Stateless adapter between Evolution Runtime and KO V1.

    Construction-time configuration:

        mapping_table    optional override of
                         ``CHANGE_TYPE_TO_KO_FIELD``
                         (defaults to the V1 canonical mapping)
        validator        optional ``AdapterValidator`` instance
                         (defaults to a fresh one)

    The adapter holds no runtime state. The ``adapt`` method
    is a pure function of the input ``AdapterRequest``.
    """

    def __init__(
        self,
        *,
        mapping_table: Optional[Dict[EvolutionChangeType, str]] = None,
        validator: Optional[AdapterValidator] = None,
        knowledge_object_validator: Optional[KnowledgeObjectValidator] = None,
    ) -> None:
        self.mapping_table: Dict[EvolutionChangeType, str] = (
            mapping_table if mapping_table is not None else CHANGE_TYPE_TO_KO_FIELD
        )
        self.validator: AdapterValidator = validator or AdapterValidator()
        self.ko_validator: KnowledgeObjectValidator = (
            knowledge_object_validator or KnowledgeObjectValidator()
        )

    # -------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------

    def adapt(
        self,
        request: AdapterRequest,
    ) -> AdapterResult:
        """Translate an ``AdapterRequest`` into an ``AdapterResult``.

        Returns a frozen ``AdapterResult``. ``success=True``
        carries ``new_snapshot`` and ``mapping``. ``success=False``
        carries ``rejection_reason``.
        """
        # Step 1: input validation
        validation: AdapterValidationResult = self.validator.validate(request)
        if not validation.valid:
            return self._reject(
                request=request,
                reason="; ".join(validation.errors),
            )

        # Step 2: resolve change_type -> KO V1 field
        resolved_field = resolve_target_field(
            request.change_type,
            mapping_table=self.mapping_table,
        )
        if resolved_field is None:
            return self._reject(
                request=request,
                reason=(
                    "change_type "
                    + (
                        request.change_type.value
                        if isinstance(request.change_type, EvolutionChangeType)
                        else str(request.change_type)
                    )
                    + " has no mapping in the V1 KO schema"
                ),
            )

        # Step 3: deep-copy before_snapshot (NEVER mutate input)
        try:
            new_snapshot = copy.deepcopy(request.before_snapshot)
        except Exception as exc:
            return self._reject(
                request=request,
                reason="before_snapshot is not deep-copyable: "
                + repr(exc),
            )

        if not isinstance(new_snapshot, dict):
            return self._reject(
                request=request,
                reason="before_snapshot is not a dict",
            )

        # Step 4: apply the requested change to the resolved field.
        # The adapter consumes ``requested_change`` as a string.
        # The KO V1 schema accepts ``str`` for ``category``,
        # ``theme``, ``interaction_type``, and other simple text
        # fields; we therefore set the field to ``requested_change``.
        # If the resolved field is a list field, we wrap the
        # string in a single-element list to preserve the
        # schema invariant.
        applied = self._apply_change(
            new_snapshot=new_snapshot,
            resolved_field=resolved_field,
            requested_change=request.requested_change,
        )
        if not applied:
            return self._reject(
                request=request,
                reason=(
                    "resolved target field '"
                    + resolved_field
                    + "' is not present in the before_snapshot"
                ),
            )

        # Step 5: bump version (always before_version + 1).
        # We update ``version`` if it exists in the snapshot,
        # otherwise we add it. KO V1 requires ``version``.
        try:
            current_version = int(new_snapshot.get("version", 0))
        except (TypeError, ValueError):
            current_version = 0
        next_version = current_version + 1
        new_snapshot["version"] = next_version

        # KO V1 requires ``knowledge_id``. We set it from
        # ``target_identity`` when missing.
        if not new_snapshot.get("knowledge_id"):
            new_snapshot["knowledge_id"] = request.target_identity

        # Step 6: validate the produced snapshot against KO V1.
        try:
            candidate_ko = KnowledgeObject.from_dict(new_snapshot)
        except Exception as exc:
            return self._reject(
                request=request,
                reason=(
                    "produced snapshot is incompatible with "
                    "KnowledgeObject V1 schema: " + repr(exc)
                ),
            )
        ko_validation = self.ko_validator.validate(candidate_ko)
        if not ko_validation.valid:
            return self._reject(
                request=request,
                reason=(
                    "produced snapshot fails KnowledgeObjectValidator: "
                    + "; ".join(ko_validation.errors)
                ),
            )

        # Step 7: emit the success result.
        mapping = FieldMapping(
            change_type=request.change_type,
            requested_target_field=(
                request.target_identity + ":requested"
                if False
                else _inferred_requested_target_field(request)
            ),
            resolved_target_field=resolved_field,
            applied=True,
            note=(
                "change_type "
                + (
                    request.change_type.value
                    if isinstance(request.change_type, EvolutionChangeType)
                    else str(request.change_type)
                )
                + " mapped to KO V1 field '" + resolved_field + "'"
            ),
        )

        return AdapterResult(
            success=True,
            request_id=request.request_id,
            transaction_id=request.transaction_id,
            target_identity=request.target_identity,
            before_version=int(request.target_version),
            next_version=next_version,
            new_snapshot=new_snapshot,
            mapping=mapping,
            rejection_reason="",
            mutation_executed=False,
            created_at=_now(),
        )

    # -------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------

    def _reject(
        self,
        *,
        request: AdapterRequest,
        reason: str,
    ) -> AdapterResult:
        return AdapterResult(
            success=False,
            request_id=request.request_id,
            transaction_id=request.transaction_id,
            target_identity=request.target_identity,
            before_version=int(request.target_version),
            next_version=None,
            new_snapshot=None,
            mapping=None,
            rejection_reason=reason,
            mutation_executed=False,
            created_at=_now(),
        )

    def _apply_change(
        self,
        *,
        new_snapshot: dict,
        resolved_field: str,
        requested_change: Optional[str],
    ) -> bool:
        """Apply ``requested_change`` to ``resolved_field``.

        Returns ``True`` when the field exists in the snapshot
        and was set, ``False`` otherwise.

        KO V1 list fields: ``function_tags``, ``image_refs``,
        ``document_refs``. For these we wrap ``requested_change``
        in a single-element list to keep type safety.

        KO V1 string fields: everything else (e.g. ``category``,
        ``theme``, ``interaction_type``). For these we set the
        value directly.
        """
        if resolved_field not in new_snapshot:
            return False
        existing = new_snapshot[resolved_field]
        if isinstance(existing, list):
            new_snapshot[resolved_field] = [
                requested_change if requested_change is not None else "",
            ]
        else:
            new_snapshot[resolved_field] = (
                requested_change if requested_change is not None else ""
            )
        return True


# -----------------------------------------------------------------
# Helper for the FieldMapping metadata
# -----------------------------------------------------------------


_KO_V1_LIST_FIELDS: frozenset[str] = frozenset({
    "function_tags", "image_refs", "document_refs",
})


def _inferred_requested_target_field(request: AdapterRequest) -> str:
    """Return a short label of the upstream target field.

    The upstream ChangeIntent may or may not carry a
    ``target_field``; the adapter never assumes it does.
    We use the resolved KO V1 field as the canonical label
    when the upstream intent is opaque. When the adapter is
    invoked through a wrapper that supplies the upstream
    target_field, callers can override this via the
    ``mapping_table`` argument.
    """
    # The adapter receives ``requested_change`` (the value to
    # apply) and the ``change_type``. The conceptual upstream
    # target_field for each change_type is fixed by the V1
    # mapping. We surface it as a human-readable label.
    if isinstance(request.change_type, EvolutionChangeType):
        return _CONCEPTUAL_TARGET_FIELDS.get(request.change_type, "")
    return ""


_CONCEPTUAL_TARGET_FIELDS: Dict[EvolutionChangeType, str] = {
    EvolutionChangeType.BOUNDARY_UPDATE: "boundary",
    EvolutionChangeType.PRINCIPLE_UPDATE: "principle",
    EvolutionChangeType.APPLICABILITY_UPDATE: "applicability",
}


__all__ = ["KnowledgeObjectAdapter"]
