"""Feedback Learning Loop Runtime Foundation V1 (Sprint 22.1, ADR-018).

The Feedback module is the FIRST concrete runtime for ADR-018.
It does NOT implement auto-learning. It implements:

    * FeedbackObject data structure (object.py)
    * Feedback lifecycle (event.py)
    * Append-only FeedbackStore (store.py)
    * FeedbackValidator (validator.py)
    * LearningProposal generator (proposal.py)
    * FeedbackManager orchestrator (manager.py)
    * Markdown report (report.py)

Architecture boundary (Sprint 22.1 spec section 9):

    The feedback module does NOT import from:
        * caseos.intelligence.decision
        * caseos.intelligence.recommendation
        * caseos.intelligence.trust
        * caseos.knowledge.retrieval

    The feedback module MAY import from:
        * caseos.knowledge.objects   (for target identity validation)
        * caseos.knowledge.governance (for trust-tier awareness)

The feedback module is a side-channel. It does NOT participate in
the main pipeline (Human -> Knowledge -> Retrieval -> Decision ->
Trust -> Recommendation -> Output). It is invoked by an operator
(or a future feedback tool) and writes only to the append-only
store; the corpus is read by the manager but never modified by
the feedback code path.

The "long-term memory evolution" loop is:

    Feedback
        |
        v
    Validation
        |
        v
    Proposal
        |
        v
    Human Review
        |
        v
    Knowledge Evolution  (future sprint; not in V1)
"""

from caseos.knowledge.feedback.object import (
    FeedbackObject,
    FeedbackSource,
    FeedbackType,
    SOURCE_PRIORITY,
    TYPES_REQUIRING_EXPERT_REVIEW,
    new_feedback,
)
from caseos.knowledge.feedback.event import (
    FeedbackEvent,
    FeedbackStatus,
    LIFECYCLE_ORDER,
    TERMINAL_STATES,
    DRAINED_STATES,
    is_forward,
    is_valid_transition,
    is_terminal,
    new_event,
)
from caseos.knowledge.feedback.store import FeedbackStore
from caseos.knowledge.feedback.validator import (
    FeedbackValidationResult,
    FeedbackValidator,
    ALLOWED_SOURCES,
    ALLOWED_FEEDBACK_TYPES,
)
from caseos.knowledge.feedback.proposal import (
    LearningProposal,
    generate_proposal,
)
from caseos.knowledge.feedback.manager import (
    FeedbackError,
    FeedbackManager,
)
from caseos.knowledge.feedback.report import (
    generate_report,
    generate_summary,
)

__all__ = [
    # Object
    "FeedbackObject",
    "FeedbackSource",
    "FeedbackType",
    "SOURCE_PRIORITY",
    "TYPES_REQUIRING_EXPERT_REVIEW",
    "new_feedback",
    # Lifecycle
    "FeedbackEvent",
    "FeedbackStatus",
    "LIFECYCLE_ORDER",
    "TERMINAL_STATES",
    "DRAINED_STATES",
    "is_forward",
    "is_valid_transition",
    "is_terminal",
    "new_event",
    # Store
    "FeedbackStore",
    # Validator
    "FeedbackValidationResult",
    "FeedbackValidator",
    "ALLOWED_SOURCES",
    "ALLOWED_FEEDBACK_TYPES",
    # Proposal
    "LearningProposal",
    "generate_proposal",
    # Manager
    "FeedbackError",
    "FeedbackManager",
    # Report
    "generate_report",
    "generate_summary",
]
