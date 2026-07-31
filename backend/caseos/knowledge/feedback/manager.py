"""Feedback Manager (Sprint 22.1, ADR-018 Section 2 + Sprint 22.1 spec section 8).

The Feedback Manager orchestrates the lifecycle:

    receive_feedback(...)  -> RECEIVED
        |
        v
    validate(feedback_id)  -> VALIDATING
        |
        +-- valid? -> VALIDATED
        |   not valid? -> REJECTED
        v
    generate_proposal(feedback_id) -> PROPOSAL_CREATED -> REVIEW_REQUIRED
        |
        v
    (Human review)
        |
        +- approve(feedback_id) -> APPROVED
        +- reject(feedback_id)  -> REJECTED

The manager is the **only** entry point that knows how to move a
feedback through the pipeline. It enforces:

    * forward-only lifecycle transitions (via
      ``event.is_valid_transition``)
    * the "no shortcut" rule (RECEIVED -> APPLIED is rejected)
    * append-only event storage (via FeedbackStore)
    * no auto-application (APPLIED is reserved for a future sprint)

Architecture boundary (Sprint 22.1 spec section 9):

    The manager does NOT import from:
        * caseos.intelligence.decision
        * caseos.intelligence.recommendation
        * caseos.intelligence.trust
        * caseos.knowledge.retrieval
    The manager MAY import from:
        * caseos.knowledge.objects (for target identity validation)
        * caseos.knowledge.governance (for trust-tier awareness)

The manager does NOT participate in the brain pipeline. It is
invoked by an operator (or a future feedback tool); it does not
modify the PipelineContext.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from .event import (
    FeedbackEvent,
    FeedbackStatus,
    is_valid_transition,
    new_event,
)
from .object import FeedbackObject, new_feedback
from .proposal import LearningProposal, generate_proposal
from .store import FeedbackStore
from .validator import FeedbackValidationResult, FeedbackValidator


class FeedbackError(ValueError):
    """Raised when a feedback operation violates the lifecycle.

    Examples:
        * Trying to skip a lifecycle state.
        * Trying to validate a feedback that does not exist.
        * Trying to generate a proposal for a non-VALIDATED feedback.
    """


@dataclass
class FeedbackManager:
    """Orchestrator for the feedback lifecycle.

    Stateless across instances -- create a new manager per
    operator session if you want isolation. The default
    constructor wires up the append-only store and the pure
    validator; callers can supply their own to customise.
    """

    store: FeedbackStore = field(default_factory=FeedbackStore)
    validator: FeedbackValidator = field(default_factory=FeedbackValidator)
    # Optional set of allowed target identities. When None, the
    # manager does NOT enforce target identity existence (the
    # validator defaults to "non-empty target").
    valid_targets: Optional[set[str]] = None
    # When True, the manager requires the target identity to be in
    # ``valid_targets`` during validation. Defaults to False for
    # calls without a corpus loaded; the corpus loader can flip it
    # on after populating ``valid_targets``.
    require_target_check: bool = False

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_corpus_dir(
        cls,
        corpus_dir: Optional[Any] = None,
        store: Optional[FeedbackStore] = None,
        validator: Optional[FeedbackValidator] = None,
    ) -> "FeedbackManager":
        """Build a manager whose valid_targets come from a corpus.

        The loader (``knowledge.objects.loader.load_corpus``) is
        imported lazily here so the boundary test does not pick up
        a hidden importer.
        """
        from caseos.knowledge.objects.loader import (
            DEFAULT_CORPUS_DIR,
            load_corpus,
        )
        if corpus_dir is None:
            corpus_dir = DEFAULT_CORPUS_DIR
        objects = load_corpus(corpus_dir)
        identities = {str(ko.get("identity", "")) for ko in objects if ko.get("identity")}
        return cls(
            store=store or FeedbackStore(),
            validator=validator or FeedbackValidator(),
            valid_targets=identities,
            require_target_check=True,
        )

    # ------------------------------------------------------------------
    # Read API
    # ------------------------------------------------------------------

    def get(self, feedback_id: str) -> Optional[FeedbackObject]:
        """Return the current logical state of a feedback, or None.

        The logical state is reconstructed from the latest event's
        snapshot. The original FeedbackObject was never mutated.
        """
        latest = self.store.latest_for(feedback_id)
        if latest is None:
            return None
        return _reconstruct_feedback_object(latest)

    def list_by_target(self, identity: str) -> list[FeedbackObject]:
        """Return every feedback event whose target_identity matches."""
        events = self.store.list_by_target(identity)
        # Deduplicate: keep one current FeedbackObject per feedback_id.
        seen: set[str] = set()
        out: list[FeedbackObject] = []
        for ev in events:
            if ev.feedback_id in seen:
                continue
            seen.add(ev.feedback_id)
            fb = _reconstruct_feedback_object(ev)
            if fb is not None:
                out.append(fb)
        return out

    def list_by_status(self, status: FeedbackStatus) -> list[FeedbackObject]:
        """Return every feedback whose current status matches."""
        out: list[FeedbackObject] = []
        seen: set[str] = set()
        for ev in reversed(self.store.list()):
            if ev.feedback_id in seen:
                continue
            seen.add(ev.feedback_id)
            if ev.to_status == status.value:
                fb = _reconstruct_feedback_object(ev)
                if fb is not None:
                    out.append(fb)
        return out

    def history(self, feedback_id: str) -> list[FeedbackEvent]:
        """Return the full lifecycle of a feedback, in insertion order."""
        return self.store.history_for(feedback_id)

    # ------------------------------------------------------------------
    # Write API
    # ------------------------------------------------------------------

    def receive_feedback(
        self,
        source: Any,
        feedback_type: Any,
        target_identity: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
        feedback_id: Optional[str] = None,
    ) -> FeedbackObject:
        """Create a new FeedbackObject in the RECEIVED state.

        The first event appended to the store is the RECEIVED
        event. The manager does NOT validate at this point; that
        happens in ``validate(...)``.
        """
        fb = new_feedback(
            source=source,
            feedback_type=feedback_type,
            target_identity=target_identity,
            content=content,
            metadata=metadata,
            feedback_id=feedback_id,
        )
        event = new_event(
            feedback_id=fb.id,
            from_status=None,
            to_status=FeedbackStatus.RECEIVED,
            snapshot=fb.to_dict(),
            note="received",
        )
        self.store.append(event)
        return fb

    def validate(self, feedback_id: str) -> FeedbackValidationResult:
        """Move the feedback to VALIDATING, then VALIDATED or REJECTED.

        Forbidden transitions:

          * VALIDATING -> APPLIED (the spec explicitly forbids
            RECEIVED -> APPLIED; the same forward-only rule
            applies at every transition).
          * VALIDATING -> VALIDATED directly skips the validation
            step. The manager never does this -- it always runs
            the validator first.
        """
        current = self.get(feedback_id)
        if current is None:
            raise FeedbackError(f"feedback not found: {feedback_id!r}")
        if current.status not in (
            FeedbackStatus.RECEIVED.value,
            FeedbackStatus.VALIDATING.value,
        ):
            raise FeedbackError(
                f"feedback {feedback_id!r} is in status "
                f"{current.status!r}; validation only allowed from "
                "RECEIVED."
            )

        # VALIDATING event
        _assert_and_append(
            self.store,
            feedback_id=feedback_id,
            from_status=FeedbackStatus(current.status),
            to_status=FeedbackStatus.VALIDATING,
            snapshot=current.to_dict(),
            note="validation started",
        )

        # Run the validator
        result = self.validator.validate(
            current,
            valid_targets=self.valid_targets,
            require_target_check=self.require_target_check,
        )

        if result.valid:
            _assert_and_append(
                self.store,
                feedback_id=feedback_id,
                from_status=FeedbackStatus.VALIDATING,
                to_status=FeedbackStatus.VALIDATED,
                snapshot=_attach_validation_to_snapshot(current.to_dict(), result),
                note="validation passed",
            )
        else:
            _assert_and_append(
                self.store,
                feedback_id=feedback_id,
                from_status=FeedbackStatus.VALIDATING,
                to_status=FeedbackStatus.REJECTED,
                snapshot=_attach_validation_to_snapshot(current.to_dict(), result),
                note=f"validation rejected: {len(result.errors)} error(s)",
            )

        return result

    def generate_proposal(
        self,
        feedback_id: str,
        current_state: Optional[dict[str, Any]] = None,
    ) -> LearningProposal:
        """Generate a LearningProposal for a validated feedback.

        The feedback MUST be in VALIDATED. PROPOSAL_CREATED is
        appended, then REVIEW_REQUIRED (which is the human gate).

        If the feedback_type is CONTRADICTION_SIGNAL or
        UNEXPECTED_DISCOVERY, the proposal is built with
        ``requires_expert_review=True`` (the validator already
        flagged this in the validation result).

        The ``current_state`` parameter is a snapshot of the
        target KO's ADR-015 fields. The manager does NOT load the
        corpus; the caller is responsible for the snapshot. The
        proposal takes the snapshot by value, so the corpus is
        never modified.
        """
        current = self.get(feedback_id)
        if current is None:
            raise FeedbackError(f"feedback not found: {feedback_id!r}")
        if current.status != FeedbackStatus.VALIDATED.value:
            raise FeedbackError(
                f"feedback {feedback_id!r} is in status "
                f"{current.status!r}; proposal generation only "
                "allowed from VALIDATED."
            )

        # Build the historical feed of feedback events for the same
        # target. The proposal might want to combine multiple events.
        target_history = self.store.list_by_target(current.target_identity)

        # Insert the PROPOSAL_CREATED event.
        _assert_and_append(
            self.store,
            feedback_id=feedback_id,
            from_status=FeedbackStatus.VALIDATED,
            to_status=FeedbackStatus.PROPOSAL_CREATED,
            snapshot=current.to_dict(),
            note="learning proposal created",
        )

        # Build the proposal.
        proposal = generate_proposal(
            target_identity=current.target_identity,
            current_state=current_state or {},
            feedback_events=target_history,
        )

        # Insert the REVIEW_REQUIRED event.
        _assert_and_append(
            self.store,
            feedback_id=feedback_id,
            from_status=FeedbackStatus.PROPOSAL_CREATED,
            to_status=FeedbackStatus.REVIEW_REQUIRED,
            snapshot={
                **current.to_dict(),
                "proposal_id": proposal.proposal_id,
                "proposal_risk": proposal.risk,
                "proposal_requires_expert_review":
                    proposal.requires_expert_review,
            },
            note="awaiting human review",
        )

        return proposal

    def mark_approved(
        self,
        feedback_id: str,
        reviewer: str = "",
        note: str = "",
    ) -> FeedbackEvent:
        """Approve a feedback in REVIEW_REQUIRED.

        This is the **human review gate**. The manager itself does
        not decide -- it only records the human action. The
        reviewer identity is required by the spec (Sprint 22.1
        section 11) for accountability.
        """
        current = self.get(feedback_id)
        if current is None:
            raise FeedbackError(f"feedback not found: {feedback_id!r}")
        if current.status != FeedbackStatus.REVIEW_REQUIRED.value:
            raise FeedbackError(
                f"feedback {feedback_id!r} is in status "
                f"{current.status!r}; approval only allowed from "
                "REVIEW_REQUIRED."
            )
        return _assert_and_append(
            self.store,
            feedback_id=feedback_id,
            from_status=FeedbackStatus.REVIEW_REQUIRED,
            to_status=FeedbackStatus.APPROVED,
            snapshot=current.to_dict(),
            note=f"approved by {reviewer or '<unspecified>'}: {note}",
        )

    def mark_rejected(
        self,
        feedback_id: str,
        reviewer: str = "",
        note: str = "",
    ) -> FeedbackEvent:
        """Reject a feedback in REVIEW_REQUIRED.

        This is the **human review gate** (rejection path). The
        manager itself does not decide -- it only records the
        human action.
        """
        current = self.get(feedback_id)
        if current is None:
            raise FeedbackError(f"feedback not found: {feedback_id!r}")
        if current.status != FeedbackStatus.REVIEW_REQUIRED.value:
            raise FeedbackError(
                f"feedback {feedback_id!r} is in status "
                f"{current.status!r}; rejection only allowed from "
                "REVIEW_REQUIRED."
            )
        return _assert_and_append(
            self.store,
            feedback_id=feedback_id,
            from_status=FeedbackStatus.REVIEW_REQUIRED,
            to_status=FeedbackStatus.REJECTED,
            snapshot=current.to_dict(),
            note=f"rejected by {reviewer or '<unspecified>'}: {note}",
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _attach_validation_to_snapshot(
    snapshot: dict[str, Any],
    result: FeedbackValidationResult,
) -> dict[str, Any]:
    """Decorative attachment. The snapshot is mutated (a copy is
    taken first because the manager treats snapshots as immutable
    from the manager's perspective)."""
    out = dict(snapshot)
    out["validation"] = result.to_dict()
    return out


def _reconstruct_feedback_object(event: FeedbackEvent) -> Optional[FeedbackObject]:
    """Rehydrate a FeedbackObject from an event's snapshot.

    The snapshot is a JSON-serialised dict. Source and
    feedback_type are stored as strings; if the strings are
    valid enum values, the FeedbackObject preserves them; if
    not, the raw strings are preserved (the validator already
    rejected them, but the manager still tracks the feedback).
    """
    snap = event.snapshot or {}
    src_str = str(snap.get("source", "") or "")
    ftype_str = str(snap.get("feedback_type", "") or "")
    return FeedbackObject(
        id=event.feedback_id,
        source=src_str,
        feedback_type=ftype_str,
        target_identity=snap.get("target_identity", ""),
        content=snap.get("content", ""),
        created_at=snap.get("created_at", event.timestamp),
        metadata=dict(snap.get("metadata") or {}),
        status=event.to_status,
    )


def _assert_and_append(
    store: FeedbackStore,
    *,
    feedback_id: str,
    from_status: FeedbackStatus,
    to_status: FeedbackStatus,
    snapshot: dict[str, Any],
    note: str,
) -> FeedbackEvent:
    """Append a new event after enforcing the forward-only rule.

    ``is_valid_transition`` rejects:

      * Backward transitions.
      * Same-state transitions.
      * Skip transitions (e.g. RECEIVED -> APPLIED).

    The manager wraps this in a try/except so that any caller
    error is raised as a ``FeedbackError``.
    """
    if not is_valid_transition(from_status, to_status):
        raise FeedbackError(
            f"forbidden transition: {from_status.value} -> "
            f"{to_status.value}"
        )
    event = new_event(
        feedback_id=feedback_id,
        from_status=from_status,
        to_status=to_status,
        snapshot=dict(snapshot),
        note=note,
    )
    store.append(event)
    return event


__all__ = [
    "FeedbackError",
    "FeedbackManager",
]
