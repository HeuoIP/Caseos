"""Feedback Evolution Runtime V1 (Sprint 22.5-A, ADR-018/020).

The runtime is the **real integration entry point** that wires
the Feedback Layer to the Knowledge Evolution Layer:

    FeedbackEvent
        |
        v
    Feedback Evaluation               (FeedbackEvaluator)
        |
        v
    Contradiction Analysis            (ContradictionAnalyzer)
        |
        v
    Learning Proposal                 (propose_from_contradiction)
        |
        v
    Human Review Gate                 (status == APPROVED?)
        |
        +-- not approved --> stop, WAITING_HUMAN_REVIEW / REJECTED
        |
        v
    Interpretation                    (InterpretationPolicy)
        |
        v
    ChangeIntent
        |
        v
    EvolutionTransaction              (built here)
        |
        v
    EvolutionExecutor                 (validate, govern,
        |                                version, audit)
        v
    FeedbackEvolutionResult

Hard invariants:

    * The runtime NEVER re-implements existing component logic.
      It only orchestrates.
    * The runtime NEVER modifies Decision / Trust / Recommendation.
    * The runtime NEVER calls retrieval.
    * The runtime NEVER applies LearningProposal status mutation.
      The proposal must already carry the correct ``status`` field
      (typically set by ``ReviewManager.approve`` upstream).
    * In V1, ``mutation_executed`` is always False: the runtime
      reaches the simulation layer (EvolutionExecutor) but does
      not run a KO writer.

Architecture boundary (Sprint 22.5-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.feedback
        * caseos.knowledge.feedback.evolution_runtime (sibling)
        * caseos.knowledge.evolution
        * caseos.knowledge.evolution.contracts
        * stdlib
"""
from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from caseos.knowledge.evolution.audit_v2 import AuditStore
from caseos.knowledge.evolution.object import EvolutionTransaction
from caseos.knowledge.evolution.runtime_v2.executor import (
    EvolutionExecutor,
)
from caseos.knowledge.evolution.versioning import VersionStore

from caseos.knowledge.feedback import (
    LearningProposal,
    ProposalStatus,
    propose_from_contradiction,
)
from caseos.knowledge.feedback.evaluation import FeedbackEvaluator
from caseos.knowledge.feedback.evaluation.analyzer import (
    ContradictionAnalyzer,
)
from caseos.knowledge.feedback.interpretation import (
    InterpretationPolicy,
)

from .object import (
    EVOLUTION_STATUS_APPROVED_AND_EXECUTED,
    EVOLUTION_STATUS_APPROVED_BUT_BLOCKED,
    EVOLUTION_STATUS_REJECTED,
    EVOLUTION_STATUS_WAITING_HUMAN_REVIEW,
    FeedbackEvolutionResult,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_proposal_status(value: Any) -> str:
    """Coerce ``value`` to a ``ProposalStatus`` string.

    Accepts a ``ProposalStatus`` enum member, the bare
    string ``"APPROVED"`` / ``"REJECTED"`` / etc., or any
    object with a ``.value`` attribute. The returned string
    is the canonical lifecycle value (uppercase).
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    raw = getattr(value, "value", None)
    if isinstance(raw, str):
        return raw
    return str(value)


def _build_transaction(
    *,
    change_intent: Any,
    proposal: LearningProposal,
    target_version: int,
    reviewer: str = "",
) -> EvolutionTransaction:
    """Construct an ``EvolutionTransaction`` from intent + proposal.

    The runtime uses a fresh transaction id (UUID4). ``status``
    starts at ``CREATED`` (the standard initial lifecycle
    state); ``target_version`` is computed upstream.
    """
    tx_id = "tx-" + str(uuid.uuid4())
    intent_id = getattr(change_intent, "intent_id", "") or ""
    target_identity = (
        getattr(change_intent, "target_identity", "")
        or getattr(proposal, "target_identity", "")
    )
    change_type = getattr(change_intent, "change_type", "")
    requested_change = (
        getattr(proposal, "suggested_change", "")
        or getattr(proposal, "reason", "")
    )
    before_snapshot = copy.deepcopy(
        getattr(proposal, "current_state", {}) or {}
    )
    return EvolutionTransaction(
        transaction_id=tx_id,
        proposal_id=str(getattr(proposal, "proposal_id", "") or ""),
        change_intent_id=str(intent_id),
        target_identity=str(target_identity),
        target_version=int(target_version),
        change_type=change_type,
        before_snapshot=before_snapshot,
        requested_change=str(requested_change),
        reviewer=(
            str(reviewer or "")
            or str(getattr(proposal, "reviewer", "") or "")
        ),
        status="CREATED",
        created_at=_now(),
    )


def execute_feedback_evolution(
    *,
    feedback_event: Any,
    knowledge_object: Any,
    runtime: "FeedbackEvolutionRuntime",
    proposal_override: Optional[LearningProposal] = None,
    target_version: int = 2,
    reviewer: str = "",
) -> FeedbackEvolutionResult:
    """Module-level entry point for the runtime flow.

    This is the function called by ``FeedbackEvolutionRuntime.execute``
    (it shares the same body). Kept at module scope so callers can
    import it directly without instantiating a runtime class.

    Args:
        feedback_event: a FeedbackEvent-shaped object (or dict).
        knowledge_object: a dict-shaped Knowledge Object snapshot.
        runtime: the configured runtime instance whose collaborators
            perform evaluation / contradiction / interpretation /
            evolution.
        proposal_override: optional pre-built LearningProposal. When
            provided, the runtime skips the auto-proposal step and
            uses this proposal directly. Tests use this to set
            status (APPROVED / REJECTED / PENDING_REVIEW).
        target_version: the version the runtime targets. Defaults
            to 2 to keep the V1 deterministic.
        reviewer: optional human reviewer id; flows onto the
            EvolutionTransaction so the EvolutionValidator R2
            check passes.

    Returns:
        ``FeedbackEvolutionResult``.
    """
    return runtime.execute_feedback_evolution(
        feedback_event=feedback_event,
        knowledge_object=knowledge_object,
        proposal_override=proposal_override,
        target_version=target_version,
        reviewer=reviewer,
    )


class FeedbackEvolutionRuntime:
    """Stateless orchestrator. The runtime holds only references
    to the injected collaborators and the shared stores.

    The runtime does NOT store any per-call state. ``execute_...``
    is a pure function of (feedback_event, knowledge_object,
    proposal_override, target_version) given the same store
    contents.
    """

    def __init__(
        self,
        *,
        feedback_evaluator: FeedbackEvaluator,
        contradiction_analyzer: ContradictionAnalyzer,
        interpretation_policy: InterpretationPolicy,
        evolution_executor: EvolutionExecutor,
        version_store: VersionStore,
        audit_store: AuditStore,
    ) -> None:
        self.feedback_evaluator = feedback_evaluator
        self.contradiction_analyzer = contradiction_analyzer
        self.interpretation_policy = interpretation_policy
        self.evolution_executor = evolution_executor
        self.version_store = version_store
        self.audit_store = audit_store

    # ------------------------------------------------------------------
    # Public entry
    # ------------------------------------------------------------------

    def execute_feedback_evolution(
        self,
        *,
        feedback_event: Any,
        knowledge_object: Any,
        proposal_override: Optional[LearningProposal] = None,
        target_version: int = 2,
        reviewer: str = "",
    ) -> FeedbackEvolutionResult:
        """Run the full feedback -> evolution pipeline once.

        See module-level ``execute_feedback_evolution`` for
        argument semantics.
        """
        feedback_id = self._extract_feedback_id(feedback_event)

        # Step 1 -- Feedback Evaluation.
        evaluation = self.feedback_evaluator.evaluate(feedback_event)

        # Step 2 -- Contradiction Analysis.
        contradiction = self.contradiction_analyzer.analyze(
            feedback_event, knowledge_object,
        )

        # Step 3 -- Learning Proposal.
        proposal = proposal_override or propose_from_contradiction(
            contradiction,
            feedback_event=feedback_event,
        )

        proposal_id = str(getattr(proposal, "proposal_id", "") or "")

        # Step 4 -- Human Review Gate.
        status_value = _coerce_proposal_status(
            getattr(proposal, "status", "")
        )
        if status_value == ProposalStatus.REJECTED.value:
            return FeedbackEvolutionResult(
                feedback_id=feedback_id,
                proposal_id=proposal_id,
                change_intent=None,
                transaction_id="",
                evolution_status=EVOLUTION_STATUS_REJECTED,
                mutation_executed=False,
                version_number=0,
                audit_id=None,
            )
        if status_value != ProposalStatus.APPROVED.value:
            # CREATED, PENDING_REVIEW, or anything else:
            # stop at the human gate.
            return FeedbackEvolutionResult(
                feedback_id=feedback_id,
                proposal_id=proposal_id,
                change_intent=None,
                transaction_id="",
                evolution_status=EVOLUTION_STATUS_WAITING_HUMAN_REVIEW,
                mutation_executed=False,
                version_number=0,
                audit_id=None,
            )

        # Step 5 -- Interpretation.
        change_intent = self.interpretation_policy.interpret(
            proposal, knowledge_object,
        )
        if change_intent is None:
            # Proposal approved, but interpretation refused.
            # Treat as "blocked at interpretation"; no transaction.
            return FeedbackEvolutionResult(
                feedback_id=feedback_id,
                proposal_id=proposal_id,
                change_intent=None,
                transaction_id="",
                evolution_status=EVOLUTION_STATUS_APPROVED_BUT_BLOCKED,
                mutation_executed=False,
                version_number=0,
                audit_id=None,
            )

        # Step 6 -- Evolution Transaction.
        transaction = _build_transaction(
            change_intent=change_intent,
            proposal=proposal,
            target_version=target_version,
            reviewer=reviewer,
        )

        # Step 7 -- Evolution Executor (validate + govern +
        # version + audit). On success the executor appends to
        # the shared stores.
        exec_result = self.evolution_executor.execute(
            transaction, change_intent=change_intent,
        )

        # Step 8 -- Aggregate result.
        version_number = 0
        audit_id: Optional[str] = None
        if exec_result.version_created:
            latest = self.version_store.get(transaction.target_identity)
            if latest is not None:
                version_number = int(getattr(latest, "version_number", 0))
        if exec_result.audit_created:
            history = self.audit_store.history(
                transaction.target_identity,
            )
            if history:
                audit_id = str(
                    getattr(history[-1], "audit_id", "") or ""
                ) or None

        evolution_status = (
            EVOLUTION_STATUS_APPROVED_AND_EXECUTED
            if (
                exec_result.governance_passed
                and exec_result.version_created
                and exec_result.audit_created
            )
            else EVOLUTION_STATUS_APPROVED_BUT_BLOCKED
        )

        return FeedbackEvolutionResult(
            feedback_id=feedback_id,
            proposal_id=proposal_id,
            change_intent=change_intent,
            transaction_id=transaction.transaction_id,
            evolution_status=evolution_status,
            mutation_executed=exec_result.mutation_executed,
            version_number=version_number,
            audit_id=audit_id,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_feedback_id(feedback_event: Any) -> str:
        """Return the feedback id from the event, tolerating dicts
        and object inputs.
        """
        if feedback_event is None:
            return ""
        if isinstance(feedback_event, dict):
            return str(
                feedback_event.get("feedback_id", "")
                or feedback_event.get("id", "")
                or ""
            )
        return str(
            getattr(feedback_event, "feedback_id", "")
            or getattr(feedback_event, "id", "")
            or ""
        )


__all__ = [
    "FeedbackEvolutionRuntime",
    "execute_feedback_evolution",
]
