"""Rollback Request Builder V1 (Sprint 22.4-G, ADR-020 Rule 4).

A convenience helper to construct a ``RollbackRequest`` from
an ``EvolutionAuditRecord`` (Sprint 22.4-E) and a target
version. The builder is a **pure function**; it does not
mutate the audit record and does not touch the Knowledge
Object.

The builder is provided so the rollback flow has a clean
entry point from the audit log. The V1 audit record carries
``previous_version`` and ``new_version``; rolling back from
``new_version`` to ``to_version`` is the natural use case.

Architecture boundary (Sprint 22.4-G spec Task 6):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

import uuid
from typing import Optional

from ..audit_v2 import EvolutionAuditRecord
from .object import _now, RollbackRequest


def build_request_from_audit(
    audit: EvolutionAuditRecord,
    *,
    to_version: int,
    requested_by: str,
    reason: str,
    rollback_id: Optional[str] = None,
) -> RollbackRequest:
    """Build a ``RollbackRequest`` from an ``EvolutionAuditRecord``.

    Args:
        audit: the audit record describing the version we
            want to roll back FROM. The request's
            ``from_version`` is set to ``audit.new_version``.
        to_version: the version we are rolling back TO. Must
            be a non-negative integer. The builder does not
            validate this; the ``RollbackValidator`` does.
        requested_by: the human or system filing the request.
        reason: short human-readable reason.
        rollback_id: optional explicit id (default: UUID4).

    Returns:
        A ``RollbackRequest`` populated from the audit.
    """
    if not isinstance(audit, EvolutionAuditRecord):
        raise TypeError(
            "audit must be an EvolutionAuditRecord instance"
        )
    if not isinstance(to_version, int):
        raise TypeError("to_version must be an int")
    return RollbackRequest(
        rollback_id=rollback_id or str(uuid.uuid4()),
        transaction_id=audit.transaction_id,
        target_identity=audit.target_identity,
        from_version=audit.new_version,
        to_version=to_version,
        reason=reason,
        requested_by=requested_by,
        created_at=_now(),
    )


__all__ = ["build_request_from_audit"]
