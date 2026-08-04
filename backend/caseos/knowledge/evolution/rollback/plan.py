"""Rollback Planner V1 (Sprint 22.4-G, ADR-020 Rule 4).

The ``RollbackPlanner`` is the **plan producer**. Given a
validated ``RollbackRequest`` and a ``VersionStore``, it
returns a frozen ``RollbackPlan`` that **describes** the
rollback without performing it.

Forbidden methods (Sprint 22.4-G spec Task 4):

    The planner and the plan have NO:
        * apply()
        * execute()
        * restore()
        * rollback()
        * mutate()

    The planner exposes only ``plan(...)``. The plan is
    a frozen dataclass. There is no executor.

    A future Sprint 22.4.x will introduce a separate
    rollback executor under a new ADR; in V1 the planner
    is the only "do something with a request" entry point.

The plan is a **description**, not an action. The plan
field ``mutation_executed`` is always False (see
``RollbackPlan`` docstring). The plan is the
operator-facing audit artifact for the rollback
foundation; it is NOT applied.

Architecture boundary (Sprint 22.4-G spec Task 6):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * stdlib
"""
from __future__ import annotations

import copy
from typing import Any, Iterable, List, Optional, Tuple

from ..versioning import KnowledgeDiffer, VersionStore
from .object import _now, RollbackPlan, RollbackRequest
from .validator import RollbackValidator


# Default ordered list of plan steps. These are
# **descriptions** of what a future executor would do;
# they are not executed in V1.
_DEFAULT_STEPS_V1: Tuple[str, ...] = (
    "verify request against version store history",
    "compute diff between from_version and to_version",
    "queue rollback for human review (future ADR)",
    "awaiting mutation runtime (V1: not executed)",
)


class RollbackPlanner:
    """Stateless plan producer. ``plan`` is a pure function.

    The planner is intentionally not an executor. The
    ``plan`` method returns a frozen ``RollbackPlan`` or
    ``None`` (when the request fails validation).
    """

    def __init__(self, *, validator: Optional[RollbackValidator] = None) -> None:
        self.validator = validator or RollbackValidator()

    def plan(
        self,
        request: Optional[RollbackRequest],
        version_store: Optional[VersionStore] = None,
    ) -> Optional[RollbackPlan]:
        """Produce a frozen ``RollbackPlan`` from a request.

        Returns ``None`` when the request fails validation.
        On success, returns a plan whose
        ``mutation_executed`` is False.
        """
        v = self.validator.validate(request, version_store=version_store)
        if not v.valid:
            return None

        # The validation passed. Build a static description
        # of the rollback. No mutation. No executor.
        diff_summary = _build_diff_summary(
            request=request, version_store=version_store,
        )
        return RollbackPlan(
            rollback_id=request.rollback_id,
            target_identity=request.target_identity,
            source_version=request.from_version,
            destination_version=request.to_version,
            diff_summary=diff_summary,
            steps=_DEFAULT_STEPS_V1,
            created_at=_now(),
            mutation_executed=False,  # ALWAYS False in V1
        )


def _build_diff_summary(
    *,
    request: RollbackRequest,
    version_store: Optional[VersionStore],
) -> str:
    """Compute a short human-readable diff summary.

    Falls back to a stub string when ``version_store`` is
    None. The differ is deterministic and read-only.
    """
    if version_store is None:
        return (
            "rollback from v" + str(request.from_version)
            + " to v" + str(request.to_version)
            + " (no version store provided)"
        )
    history = {
        v.version_number: v
        for v in version_store.history(request.target_identity)
    }
    src = history.get(request.from_version)
    dst = history.get(request.to_version)
    if src is None or dst is None:
        return (
            "rollback from v" + str(request.from_version)
            + " to v" + str(request.to_version)
            + " (one or both versions not found)"
        )
    diff = KnowledgeDiffer.diff(src.snapshot, dst.snapshot)
    changed = (
        ", ".join(diff.changed_fields)
        if diff.changed_fields
        else "(no field-level differences detected)"
    )
    return (
        "fields changing on rollback: " + changed
    )


__all__ = ["RollbackPlanner"]
