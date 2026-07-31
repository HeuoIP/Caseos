"""Append-only Feedback Store (Sprint 22.1, ADR-018 Section 5).

The Feedback Store is **append-only**. It records every
``FeedbackEvent`` that the manager produces. It does NOT support
update, delete, or overwrite of any past event.

Per ADR-018 §3.A and the Sprint 22.1 spec:

    * The Loop is append-only. Every feedback event is logged
      before it takes effect. A feedback event is never overwritten;
      corrections arrive as a *new* event (a Contradiction Signal),
      not by editing history.
    * This mirrors ADR-016 rule 6 ("Trust is monotonic in time,
      only with a written reason") and ADR-015 rule 6 (Feedback
      field is append-only).

Public API (Sprint 22.1 spec section 5):

    append(event)            mandatory
    list()                   all events, in insertion order
    list_by_target(identity) events whose snapshot.target_identity
                             matches the given identity
    latest_for(feedback_id)  the latest event for a feedback_id
    history_for(feedback_id) all events for a feedback_id
    count()                  total event count

Forbidden API (the spec explicitly rejects these):

    update(...)   History events are immutable.
    delete(...)   Removal is not a valid operation; a feedback
                  that should be "removed" is instead signalled as
                  a CONTRADICTION_SIGNAL feedback event.
    overwrite(...) Same as update.

The store does NOT import from retrieval / decision / trust /
recommendation. It is a pure data structure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from .event import FeedbackEvent


@dataclass
class FeedbackStore:
    """Append-only feedback event store.

    The class is a plain dataclass with a Python list of events.
    It deliberately does not expose update / delete / overwrite
    methods. The store becomes a permanent record of the
    feedback lifecycle.
    """

    _events: list[FeedbackEvent] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Mandatory API
    # ------------------------------------------------------------------

    def append(self, event: FeedbackEvent) -> None:
        """Append a single event. This is the only mutation method.

        The store does NOT enforce event identity uniqueness -- it
        permits multiple events with the same feedback_id over
        time (which is the lifecycle). The store just guarantees
        that past events are not modified.
        """
        if not isinstance(event, FeedbackEvent):
            raise TypeError(
                f"FeedbackStore.append expects FeedbackEvent, got "
                f"{type(event).__name__}"
            )
        self._events.append(event)

    def list(self) -> list[FeedbackEvent]:
        """Return a shallow copy of every event, in insertion order."""
        return list(self._events)

    def list_by_target(self, identity: str) -> list[FeedbackEvent]:
        """Return all events whose snapshot.target_identity matches.

        The lookup is O(n) by design -- the store is small (V1) and
        the operation is rare. An index is out of scope for V1.
        """
        if not identity:
            return []
        return [
            e for e in self._events
            if isinstance(e.snapshot, dict)
            and e.snapshot.get("target_identity") == identity
        ]

    def latest_for(self, feedback_id: str) -> Optional[FeedbackEvent]:
        """Return the latest event for ``feedback_id``, or None."""
        if not feedback_id:
            return None
        latest: Optional[FeedbackEvent] = None
        for e in self._events:
            if e.feedback_id == feedback_id:
                latest = e
        return latest

    def history_for(self, feedback_id: str) -> list[FeedbackEvent]:
        """Return every event for ``feedback_id`` in insertion order."""
        if not feedback_id:
            return []
        return [e for e in self._events if e.feedback_id == feedback_id]

    def count(self) -> int:
        """Total number of events in the store."""
        return len(self._events)

    def count_by_target(self, identity: str) -> int:
        """Convenience counter for one target."""
        return len(self.list_by_target(identity))

    # ------------------------------------------------------------------
    # Explicit forbidden helpers (they raise if called)
    # ------------------------------------------------------------------

    def update(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        """Forbidden. The store is append-only.

        Calling this method raises TypeError so any accidental
        caller is caught immediately.
        """
        raise TypeError(
            "FeedbackStore.update is forbidden: the store is "
            "append-only. Corrections arrive as new events."
        )

    def delete(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        """Forbidden. The store is append-only."""
        raise TypeError(
            "FeedbackStore.delete is forbidden: the store is "
            "append-only. Use a CONTRADICTION_SIGNAL event instead."
        )

    def overwrite(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        """Forbidden. The store is append-only."""
        raise TypeError(
            "FeedbackStore.overwrite is forbidden: the store is "
            "append-only. History is immutable."
        )

    def clear(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        """Forbidden. The store is append-only."""
        raise TypeError(
            "FeedbackStore.clear is forbidden: the store is "
            "append-only."
        )


__all__ = ["FeedbackStore"]
