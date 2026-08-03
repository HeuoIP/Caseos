"""Evolution Integration Runtime V1 (Sprint 22.4-C, ADR-020).

The runtime composes four Sprint 22.4-A/B modules into a
single, side-effect-free execution:

    EvolutionValidator     (Sprint 22.4-A)
        +
    EvolutionGovernanceGate (Sprint 22.4-B)
        +
    EvolutionAuditStore    (Sprint 22.4-A)
        =
    EvolutionRuntime.execute(transaction, change_intent, reviewer)
        |
        v
    EvolutionExecutionResult  (frozen dataclass)

The runtime is **stateless with respect to the Knowledge
Object**. It is allowed to write only to its own audit store.
It is forbidden from touching the Knowledge Object, the
corpus, the retrieval engine, or any intelligence engine.

V1 hard rule: ``mutation_executed`` is **always False**.
This field exists so the runtime contract is future-extensible
and so a future Sprint 22.4.x mutation runtime can flip the
single boolean from False to True without changing the schema.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from ..audit import EvolutionAuditRecord, EvolutionAuditStore
from ..governance import EvolutionGovernanceGate, GovernanceResult
from ..object import EvolutionTransaction
from ..validator import EvolutionValidator, ValidationResult


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class EvolutionExecutionResult:
    """The outcome of an ``EvolutionRuntime.execute`` call.

    Required fields (Sprint 22.4-C spec Task 2):

        transaction_id     the transaction that was executed
        success            True iff both validator and gate passed
        governance_result  the GovernanceResult that closed the flow
        audit_created      True iff an audit record was written
        mutation_executed  ALWAYS False in V1
        created_at         ISO timestamp (datetime)

    The dataclass is **frozen**. The result is the operator-facing
    artifact that ``generate_report`` renders to Markdown.
    """

    transaction_id: str
    success: bool
    governance_result: GovernanceResult
    audit_created: bool
    mutation_executed: bool
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        out = {
            "transaction_id": self.transaction_id,
            "success": self.success,
            "governance_result": self.governance_result.to_dict(),
            "audit_created": self.audit_created,
            "mutation_executed": self.mutation_executed,
            "created_at": _now_iso(),
        }
        return out


def _validation_to_governance_result(
    v_result: ValidationResult,
) -> GovernanceResult:
    """Map a ValidationResult failure to a GovernanceResult.

    The integration runtime has a single ``governance_result``
    field on its result. When the validator (which is checked
    first) fails, we wrap the validator's verdict in a
    GovernanceResult so the result type is uniform. The
    ``rule_id`` is prefixed ``V`` to mark it as a validator
    failure (vs ``G`` for governance gate failures).
    """
    if v_result.is_valid:
        return GovernanceResult(
            approved=True, rule_id="", reason="",
        )
    return GovernanceResult(
        approved=False,
        rule_id="V" + v_result.rule,  # e.g. "VR1"
        reason="validator: " + v_result.reason,
    )


class EvolutionRuntime:
    """Flow-level runtime that wires the evolution pipeline.

    The runtime is **composable**: every collaborator is an
    optional constructor argument with a sensible default.
    Tests can inject a custom gate or audit store; production
    code can rely on the defaults.
    """

    def __init__(
        self,
        *,
        validator: Optional[EvolutionValidator] = None,
        governance_gate: Optional[EvolutionGovernanceGate] = None,
        audit_store: Optional[EvolutionAuditStore] = None,
    ) -> None:
        self.validator = validator or EvolutionValidator()
        self.governance_gate = governance_gate or EvolutionGovernanceGate()
        self.audit_store = audit_store or EvolutionAuditStore()

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    def execute(
        self,
        transaction: Optional[EvolutionTransaction],
        change_intent: Any = None,
        reviewer: Optional[str] = None,
    ) -> EvolutionExecutionResult:
        """Run the integration flow on a single transaction.

        Returns an ``EvolutionExecutionResult``. The flow:

            1. validate the transaction (EvolutionValidator),
            2. run the governance gate (EvolutionGovernanceGate),
            3. if any check fails: return the failure,
            4. if all checks pass: append an audit record and
               return success.

        ``mutation_executed`` is always False in V1. The runtime
        does not call any KO writer, version bumper, or engine
        mutator. The audit record's ``after`` field is ``None``
        to make the "no mutation" posture explicit.
        """
        if transaction is None:
            # Treat None as a hard validation failure.
            fake = ValidationResult(
                is_valid=False, reason="transaction is None", rule="R0",
            )
            return EvolutionExecutionResult(
                transaction_id="",
                success=False,
                governance_result=_validation_to_governance_result(fake),
                audit_created=False,
                mutation_executed=False,
            )

        # ---- Step 2: validate ----
        v_result: ValidationResult = self.validator.validate(transaction)
        if not v_result.is_valid:
            return EvolutionExecutionResult(
                transaction_id=transaction.transaction_id,
                success=False,
                governance_result=_validation_to_governance_result(
                    v_result,
                ),
                audit_created=False,
                mutation_executed=False,
            )

        # ---- Step 3: govern ----
        gov_result: GovernanceResult = self.governance_gate.govern(
            transaction, change_intent=change_intent,
        )
        if not gov_result.approved:
            return EvolutionExecutionResult(
                transaction_id=transaction.transaction_id,
                success=False,
                governance_result=gov_result,
                audit_created=False,
                mutation_executed=False,
            )

        # ---- Step 5: audit on pass ----
        actor = reviewer or transaction.reviewer
        self.audit_store.make_and_append(
            transaction_id=transaction.transaction_id,
            action="evolution_passed_governance",
            actor=actor,
            before=transaction.before_snapshot,
            after=None,  # explicit: no mutation in V1
            reason=(
                "governance approved; awaiting future mutation runtime"
            ),
        )

        return EvolutionExecutionResult(
            transaction_id=transaction.transaction_id,
            success=True,
            governance_result=gov_result,
            audit_created=True,
            mutation_executed=False,  # ALWAYS False in V1
        )

    # ------------------------------------------------------------------
    # Inspection helpers
    # ------------------------------------------------------------------

    def audit_records(self) -> list:
        """Return a snapshot of the audit store (read-only)."""
        return self.audit_store.list()

    def audit_count(self) -> int:
        return self.audit_store.count()


__all__ = [
    "EvolutionRuntime",
    "EvolutionExecutionResult",
]
