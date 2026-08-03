"""Append-only Proposal Store (Sprint 22.3, ADR-018 Section 5).

Mirrors the design of ``FeedbackStore`` (Sprint 22.1). The store
records every ``LearningProposal`` event -- creation, lifecycle
transition, reviewer comment. It does NOT support update, delete,
or overwrite of any past event.

Architecture boundary (Sprint 22.3 spec):

    This module does NOT import from:
        * caseos.intelligence.decision
        * caseos.intelligence.trust
        * caseos.intelligence.recommendation
        * caseos.knowledge.retrieval
    This module MAY import from:
        * caseos.knowledge.feedback (parent package)
        * caseos.knowledge.governance (read-only, future)

Per ADR-018 Section 10 rule 4 ("the Loop is append-only"):

    Every feedback event is logged before it takes effect. A
    feedback event is never overwritten; corrections arrive as a
    *new* event, not by editing history.

The proposal store is the implementation of that rule for the
proposal layer.

Public API:

    append(proposal_event)        mandatory
    list()                        all events, in insertion order
    list_by_target(identity)      events whose target_identity matches
    latest_for(feedback_id)       the latest event for a feedback_id
    history_for(feedback_id)      all events for a feedback_id
    count()                       total event count

Forbidden API:

    update / delete / overwrite    (Sprint 22.3 spec Task 5)

The events recorded here are *proposal lifecycle events*, NOT
``FeedbackEvent`` instances. They carry:

    proposal_id      the LearningProposal id
    feedback_id      the source feedback id
    target_identity  the KO identity
    from_status      previous status (None on CREATED)
    to_status        new status (a ProposalStatus value)
    timestamp        ISO-8601 UTC
    note             optional reviewer comment
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional


@dataclass(frozen=True)
class ProposalEvent:
    """One lifecycle event for a single LearningProposal.

    The event is the append-only record. It does NOT carry the
    full LearningProposal -- only the metadata needed to rebuild
    the lifecycle trace.
    """

    proposal_id: str
    feedback_id: str
    target_identity: str
    from_status: Optional[str]
    to_status: str
    timestamp: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


@dataclass
class ProposalStore:
    """Append-only proposal event store.

    The store deliberately exposes only append + read methods.
    Update / delete / overwrite would violate ADR-018 Section 10
    rule 4 ("the Loop is append-only").
    """

    _events: list[ProposalEvent] = field(default_factory=list)

    def append(self, event: ProposalEvent) -> None:
        if not isinstance(event, ProposalEvent):
            raise TypeError(
                "ProposalStore.append expects ProposalEvent, got "
                + type(event).__name__
            )
        self._events.append(event)

    def list(self) -> list[ProposalEvent]:
        return list(self._events)

    def list_by_target(self, identity: str) -> list[ProposalEvent]:
        if not identity:
            return []
        return [
            e for e in self._events
            if e.target_identity == identity
        ]

    def latest_for(self, proposal_id: str) -> Optional[ProposalEvent]:
        if not proposal_id:
            return None
        latest: Optional[ProposalEvent] = None
        for e in self._events:
            if e.proposal_id == proposal_id:
                latest = e
        return latest

    def history_for(self, proposal_id: str) -> list[ProposalEvent]:
        if not proposal_id:
            return []
        return [e for e in self._events if e.proposal_id == proposal_id]

    def count(self) -> int:
        return len(self._events)


__all__ = [
    "ProposalEvent",
    "ProposalStore",
]
