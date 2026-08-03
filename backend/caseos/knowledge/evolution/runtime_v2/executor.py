"""Evolution Executor V2 -- Full Simulation (Sprint 22.4-F, ADR-020).

The ``EvolutionExecutor`` wires the Sprint 22.4-A through 22.4-E
modules into a single simulation pipeline. It composes:

    EvolutionValidator           (Sprint 22.4-A)
        +
    EvolutionGovernanceGate     (Sprint 22.4-B)
        +
    VersionStore                 (Sprint 22.4-D)
        +
    AuditStore (V2)              (Sprint 22.4-E)
        =
    EvolutionExecutor.execute(transaction, change_intent, reviewer)

The executor is **stateless with respect to the Knowledge
Object**. It is allowed to write only to its own version
store and audit store. It is forbidden from touching the
Knowledge Object, the corpus, the retrieval engine, or
any intelligence engine.

V1 hard rule: ``mutation_executed`` is **always False**.
A future Sprint 22.4.x will flip this single boolean from
False to True when a real mutation runtime is wired in.

Version + Audit integration (Sprint 22.4-F spec Task 4):

    On full pass (validator + governance), the executor:

        1. Computes the next version_number for the
           target_identity by inspecting the version store.
        2. Builds a ``KnowledgeVersion`` with the
           transaction's ``before_snapshot`` (honest: "no
           real change yet") and a UUID ``version_id``.
        3. Appends the version record.
        4. Builds a ``EvolutionAuditRecord`` (V2) with
           transaction_id, proposal_id, target_identity,
           reviewer, and ``after_snapshot=None``.
        5. Appends the audit record.

    On any failure, the executor short-circuits: no
    version is created, no audit is created, and the
    result's ``version_created`` and ``audit_created`` are
    both False.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ..audit_v2 import (
    AuditStore,
    EvolutionAuditRecord,
)
from ..governance import EvolutionGovernanceGate
from ..object import EvolutionTransaction
from ..validator import EvolutionValidator, ValidationResult
from ..versioning import KnowledgeVersion, VersionStore


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class EvolutionExecutionResult:
    """The outcome of a full-simulation ``EvolutionExecutor.execute``.

    Required fields (Sprint 22.4-F spec Task 1):

        transaction_id      the transaction that was executed
        governance_passed   True iff validator + gate both passed
        version_created     True iff a new KnowledgeVersion was appended
        audit_created       True iff a new EvolutionAuditRecord was
                            appended
        mutation_executed   ALWAYS False in V1
        created_at          ISO timestamp (datetime)

    The dataclass is **frozen**. The result is the
    operator-facing artifact that ``generate_report``
    renders to Markdown.
    """

    transaction_id: str
    governance_passed: bool
    version_created: bool
    audit_created: bool
    mutation_executed: bool
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = {
            "transaction_id": self.transaction_id,
            "governance_passed": self.governance_passed,
            "version_created": self.version_created,
            "audit_created": self.audit_created,
            "mutation_executed": self.mutation_executed,
            "created_at": _now_iso(),
        }
        return out


def _next_version_number(version_store: VersionStore, identity: str) -> int:
    """Return the next monotonically increasing version_number.

    If no prior version exists for ``identity``, return 1.
    Otherwise return ``latest.version_number + 1``.
    """
    latest = version_store.get(identity)
    if latest is None:
        return 1
    return int(latest.version_number) + 1


def _build_version(
    transaction: EvolutionTransaction,
    version_number: int,
    previous_version: Optional[int],
) -> KnowledgeVersion:
    """Build a ``KnowledgeVersion`` for the simulation.

    The snapshot is taken from the transaction's
    ``before_snapshot``. This is honest: V1 does not
    produce an "after" state, so the recorded snapshot
    is the pre-change state. A future mutation runtime
    will recompute the "after" snapshot.
    """
    return KnowledgeVersion(
        version_id=str(uuid.uuid4()),
        target_identity=transaction.target_identity,
        version_number=version_number,
        previous_version=previous_version,
        snapshot=transaction.before_snapshot,
        created_at=_now(),
        created_by=transaction.reviewer,
        change_reason=(
            transaction.requested_change
            or "evolution simulation v1; no real mutation"
        ),
        proposal_id=transaction.proposal_id,
    )


def _build_audit(
    transaction: EvolutionTransaction,
    version: KnowledgeVersion,
) -> EvolutionAuditRecord:
    """Build a ``EvolutionAuditRecord`` (V2) for the simulation.

    The ``after_snapshot`` is intentionally ``None``: V1
    does not compute an "after" state. A future mutation
    runtime will fill this in.

    The ``rollback_reference`` is also ``None`` in V1:
    a future rollback module under a new ADR will set it.
    """
    return EvolutionAuditRecord(
        audit_id=str(uuid.uuid4()),
        transaction_id=transaction.transaction_id,
        proposal_id=transaction.proposal_id,
        target_identity=transaction.target_identity,
        previous_version=version.previous_version,
        new_version=version.version_number,
        before_snapshot=transaction.before_snapshot,
        after_snapshot=None,  # V1: no real "after"
        change_type=transaction.change_type,
        reason=(
            transaction.requested_change
            or "evolution simulation v1; no real mutation"
        ),
        reviewer=transaction.reviewer,
        created_at=version.created_at,
        rollback_reference=None,
    )


class EvolutionExecutor:
    """Full-simulation executor that wires the evolution pipeline.

    The executor is **composable**: every collaborator is an
    optional constructor argument with a sensible default.
    Tests can inject custom stores; production code can rely
    on the defaults.
    """

    def __init__(
        self,
        *,
        validator: Optional[EvolutionValidator] = None,
        governance_gate: Optional[EvolutionGovernanceGate] = None,
        version_store: Optional[VersionStore] = None,
        audit_store: Optional[AuditStore] = None,
    ) -> None:
        self.validator = validator or EvolutionValidator()
        self.governance_gate = governance_gate or EvolutionGovernanceGate()
        self.version_store = version_store or VersionStore()
        self.audit_store = audit_store or AuditStore()

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(
        self,
        transaction: Optional[EvolutionTransaction],
        change_intent: Any = None,
        reviewer: Optional[str] = None,
    ) -> EvolutionExecutionResult:
        """Run the full simulation pipeline on one transaction.

        Returns an ``EvolutionExecutionResult``. The flow:

            1. validate the transaction (EvolutionValidator),
            2. govern the transaction (EvolutionGovernanceGate),
            3. on full pass: append a KnowledgeVersion,
            4. on full pass: append an EvolutionAuditRecord,
            5. return the result.

        ``mutation_executed`` is always False in V1. The
        executor does not call any KO writer, version bumper,
        or engine mutator. The audit record's ``after_snapshot``
        is None to make the "no mutation" posture explicit.
        """
        if transaction is None:
            return EvolutionExecutionResult(
                transaction_id="",
                governance_passed=False,
                version_created=False,
                audit_created=False,
                mutation_executed=False,
            )

        # ---- Step 1: validate ----
        v_result: ValidationResult = self.validator.validate(transaction)
        if not v_result.is_valid:
            return EvolutionExecutionResult(
                transaction_id=transaction.transaction_id,
                governance_passed=False,
                version_created=False,
                audit_created=False,
                mutation_executed=False,
            )

        # ---- Step 2: govern ----
        gov_result = self.governance_gate.govern(
            transaction, change_intent=change_intent,
        )
        if not gov_result.approved:
            return EvolutionExecutionResult(
                transaction_id=transaction.transaction_id,
                governance_passed=False,
                version_created=False,
                audit_created=False,
                mutation_executed=False,
            )

        # ---- Step 3: version ----
        version_number = _next_version_number(
            self.version_store, transaction.target_identity,
        )
        previous_version = (
            version_number - 1 if version_number > 1 else None
        )
        version = _build_version(
            transaction,
            version_number=version_number,
            previous_version=previous_version,
        )
        self.version_store.append(version)

        # ---- Step 4: audit ----
        audit = _build_audit(transaction, version)
        self.audit_store.append(audit)

        # The ``reviewer`` argument is documented in the spec
        # but not used in V1: the audit record reads the
        # reviewer from the transaction itself. We keep the
        # parameter for future extensibility.
        _ = reviewer

        return EvolutionExecutionResult(
            transaction_id=transaction.transaction_id,
            governance_passed=True,
            version_created=True,
            audit_created=True,
            mutation_executed=False,  # ALWAYS False in V1
        )

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    def version_count(self) -> int:
        return self.version_store.count()

    def audit_count(self) -> int:
        return self.audit_store.count()


__all__ = [
    "EvolutionExecutor",
    "EvolutionExecutionResult",
]
