"""Feedback Object (Sprint 22.1, ADR-018).

A `FeedbackObject` is the structured input to the Feedback Learning
Loop. It is **not** a Knowledge Object; it is a piece of evidence
about an existing Knowledge Object (or about a Decision / Trust
state) that the Loop will eventually translate into a Learning
Proposal.

Architecture (Sprint 22.1 spec section 3):

    FeedbackObject carries:
        id              unique identifier
        source          where this feedback came from (priority-ordered)
        feedback_type   what kind of feedback it is
        target_identity which KO / Decision / Trust is being qualified
        content         the human-readable feedback text
        created_at      ISO timestamp
        metadata        free-form source-specific metadata
        status          current lifecycle status (FeedbackStatus enum)

Source priority (ADR-018 Section 1, Sprint 22.1 spec):

    EXPERT
        |
        v
    OUTCOME
        |
        v
    REASON
        |
        v
    PREFERENCE

The priority order is the *trust order*. EXPERT is the lowest-volume
/ highest-signal source; PREFERENCE is the highest-volume / often
surface-only source. The Loop treats them in this order when
generating proposals, never reverses the order in V1.

Feedback types (Sprint 22.1 spec section 3):

    POSITIVE_CONFIRMATION
    NEGATIVE_CORRECTION
    PREFERENCE_SIGNAL
    UNEXPECTED_DISCOVERY
    CONTRADICTION_SIGNAL

The five types match ADR-018 Section 4 (the five feedback types).
``CONTRADICTION_SIGNAL`` is the only type that can veto an existing
Boundary field (per ADR-018 §4.5).

Architecture boundary (Sprint 22.1 spec section 9):

    The feedback module does NOT import from:
        * caseos.intelligence.decision
        * caseos.intelligence.recommendation
        * caseos.intelligence.trust
        * caseos.knowledge.retrieval
    The feedback module MAY import from:
        * caseos.knowledge.objects
        * caseos.knowledge.governance
"""
from __future__ import annotations

import copy
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class FeedbackSource(str, Enum):
    """The four feedback sources, priority-ordered.

    ADR-018 §1 declares the ordering:
        EXPERT > OUTCOME > REASON > PREFERENCE
    The ordering is preserved by the enum declaration order.
    """

    EXPERT = "EXPERT"
    OUTCOME = "OUTCOME"
    REASON = "REASON"
    PREFERENCE = "PREFERENCE"


# Numeric priority (higher = more authoritative). Used by the
# proposal generator when comparing feedback events; ADR-018 §1.
SOURCE_PRIORITY: dict[FeedbackSource, int] = {
    FeedbackSource.EXPERT: 4,
    FeedbackSource.OUTCOME: 3,
    FeedbackSource.REASON: 2,
    FeedbackSource.PREFERENCE: 1,
}


class FeedbackType(str, Enum):
    """The five feedback types (ADR-018 §4)."""

    POSITIVE_CONFIRMATION = "POSITIVE_CONFIRMATION"
    NEGATIVE_CORRECTION = "NEGATIVE_CORRECTION"
    PREFERENCE_SIGNAL = "PREFERENCE_SIGNAL"
    UNEXPECTED_DISCOVERY = "UNEXPECTED_DISCOVERY"
    CONTRADICTION_SIGNAL = "CONTRADICTION_SIGNAL"


# Types that always require expert review (ADR-018 §4.5 + §5 P4).
TYPES_REQUIRING_EXPERT_REVIEW: frozenset[FeedbackType] = frozenset({
    FeedbackType.CONTRADICTION_SIGNAL,
    FeedbackType.UNEXPECTED_DISCOVERY,
})


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class FeedbackObject:
    """A structured piece of feedback. Lifecycle lives in event.py.

    The dataclass is *append-only* at the runtime layer: once
    constructed, the field values are not edited by the manager.
    Lifecycle transitions are recorded as separate `FeedbackEvent`
    records (see event.py), not as in-place mutations of this
    object.
    """

    id: str
    # Both source and feedback_type are stored as strings. The
    # enum forms are accepted by ``new_feedback`` and converted
    # to their string values; the FeedbackObject does NOT enforce
    # enum membership. The validator (validator.py) is the gate.
    source: str
    feedback_type: str
    target_identity: str
    content: str
    created_at: str = field(default_factory=_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "RECEIVED"  # FeedbackStatus value; default at create time

    def to_dict(self) -> dict[str, Any]:
        """Serialise. The source and feedback_type are already
        stored as strings (the validator is the gate, not the
        constructor), so the asdict copy is JSON-safe as-is."""
        return asdict(self)

    def copy(self) -> "FeedbackObject":
        """Return a deep copy. The manager never mutates stored
        FeedbackObjects; transitions are recorded as new events."""
        return copy.deepcopy(self)


def new_feedback(
    source: FeedbackSource | str,
    feedback_type: FeedbackType | str,
    target_identity: str,
    content: str,
    metadata: Optional[dict[str, Any]] = None,
    feedback_id: Optional[str] = None,
) -> FeedbackObject:
    """Convenience constructor.

    Accepts both enum values and their string forms (so external
    callers do not need to import the enum classes). The validator
    enforces the enum membership when the manager calls
    ``validator.validate``.
    """
    if isinstance(source, FeedbackSource):
        src_str = source.value
    else:
        # The validator will reject invalid strings.
        src_str = str(source)
    if isinstance(feedback_type, FeedbackType):
        ftype_str = feedback_type.value
    else:
        ftype_str = str(feedback_type)
    return FeedbackObject(
        id=feedback_id or str(uuid.uuid4()),
        source=src_str,
        feedback_type=ftype_str,
        target_identity=target_identity,
        content=content,
        metadata=dict(metadata or {}),
    )


__all__ = [
    "FeedbackObject",
    "FeedbackSource",
    "FeedbackType",
    "SOURCE_PRIORITY",
    "TYPES_REQUIRING_EXPERT_REVIEW",
    "new_feedback",
]
