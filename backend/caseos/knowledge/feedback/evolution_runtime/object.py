"""Feedback Evolution Runtime Result V1 (Sprint 22.5-A, ADR-018/020).

The ``FeedbackEvolutionResult`` is the **single contract** that
the runtime returns after running one feedback event through the
full pipeline. It carries:

    * the source feedback id and proposal id,
    * the resolved ChangeIntent (when the human gate opened),
    * the EvolutionTransaction id (when the gate opened),
    * an evolution_status string describing the gate verdict,
    * a mutation_executed boolean (always False in V1; the
      runtime is a real integration runtime but the underlying
      mutation step is a simulation until the writer ships),
    * the resulting KnowledgeVersion number (0 when no version
      was created),
    * the audit record id (None when no audit was created),
    * an ISO timestamp.

The dataclass is **frozen**. ``to_dict`` is JSON-safe.

Evolution status values (V1):

    WAITING_HUMAN_REVIEW   -- proposal status is CREATED or
                              PENDING_REVIEW. No transaction,
                              no version, no audit. The runtime
                              stopped at the human gate.
    REJECTED               -- proposal status is REJECTED.
                              No transaction, no version, no
                              audit. The human explicitly
                              rejected the proposal.
    APPROVED_AND_EXECUTED  -- proposal status was APPROVED. A
                              transaction was built, governance
                              passed, a version was appended,
                              an audit was appended.
    APPROVED_BUT_BLOCKED   -- proposal status was APPROVED but
                              governance or validation failed.
                              Transaction was built but never
                              executed. No version, no audit.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


# Evolution status enum-like string set. The runtime does not
# declare a new Python Enum for this -- the set is small,
# stable, and the value flows through Markdown reports and
# logs rather than policy code.
EVOLUTION_STATUS_WAITING_HUMAN_REVIEW = "WAITING_HUMAN_REVIEW"
EVOLUTION_STATUS_REJECTED = "REJECTED"
EVOLUTION_STATUS_APPROVED_AND_EXECUTED = "APPROVED_AND_EXECUTED"
EVOLUTION_STATUS_APPROVED_BUT_BLOCKED = "APPROVED_BUT_BLOCKED"

EVOLUTION_STATUSES = frozenset({
    EVOLUTION_STATUS_WAITING_HUMAN_REVIEW,
    EVOLUTION_STATUS_REJECTED,
    EVOLUTION_STATUS_APPROVED_AND_EXECUTED,
    EVOLUTION_STATUS_APPROVED_BUT_BLOCKED,
})


@dataclass(frozen=True)
class FeedbackEvolutionResult:
    """The runtime's single output contract.

    Required fields (Sprint 22.5-A spec Task 5):

        feedback_id          the source FeedbackEvent / FeedbackObject id
        proposal_id          the resolved LearningProposal id (str);
                             empty string when the proposal was not
                             built (e.g. feedback did not reach the
                             proposal stage)
        change_intent        the resolved ChangeIntent (when the
                             human gate opened); None otherwise
        transaction_id       the EvolutionTransaction id (when one
                             was built); empty string otherwise
        evolution_status     one of EVOLUTION_STATUSES
        mutation_executed    boolean marker (False in V1; the
                             runtime does not perform KO writer
                             mutations; only the simulation layer
                             is reached)
        version_number       the new KnowledgeVersion number when
                             a version was appended; 0 otherwise
        audit_id             the EvolutionAuditRecord id when an
                             audit was appended; None otherwise
        created_at           ISO timestamp (datetime)
    """

    feedback_id: str
    proposal_id: str
    change_intent: Optional[Any]
    transaction_id: str
    evolution_status: str
    mutation_executed: bool
    version_number: int
    audit_id: Optional[str]
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict:
        """Return a JSON-safe representation.

        The optional ``change_intent`` is rendered through its
        own ``to_dict`` when available; otherwise as ``None``.
        """
        out = {
            "feedback_id": self.feedback_id,
            "proposal_id": self.proposal_id,
            "transaction_id": self.transaction_id,
            "evolution_status": self.evolution_status,
            "mutation_executed": self.mutation_executed,
            "version_number": self.version_number,
            "audit_id": self.audit_id,
            "created_at": (
                self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                if isinstance(self.created_at, datetime)
                else self.created_at
            ),
        }
        if self.change_intent is not None and hasattr(
            self.change_intent, "to_dict"
        ):
            out["change_intent"] = self.change_intent.to_dict()
        else:
            out["change_intent"] = self.change_intent
        return out


__all__ = [
    "FeedbackEvolutionResult",
    "EVOLUTION_STATUS_WAITING_HUMAN_REVIEW",
    "EVOLUTION_STATUS_REJECTED",
    "EVOLUTION_STATUS_APPROVED_AND_EXECUTED",
    "EVOLUTION_STATUS_APPROVED_BUT_BLOCKED",
    "EVOLUTION_STATUSES",
]
