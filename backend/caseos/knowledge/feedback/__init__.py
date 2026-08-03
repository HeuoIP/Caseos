"""Feedback Learning Loop Runtime Foundation V1 (Sprint 22.1, ADR-018).

The Feedback module is the FIRST concrete runtime for ADR-018.
It does NOT implement auto-learning. It implements:

    * FeedbackObject data structure (object.py)
    * Feedback lifecycle (event.py)
    * Append-only FeedbackStore (store.py)
    * FeedbackValidator (validator.py)
    * LearningProposal generator (proposal.py)
    * Proposal lifecycle (proposal_lifecycle.py)
    * Append-only ProposalStore (proposal_store.py)
    * Proposal integration bridge (proposal_integration.py)
    * FeedbackManager orchestrator (manager.py)
    * Markdown report (report.py)

Architecture boundary (Sprint 22.1 spec section 9 / 22.3 spec):

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
    Evaluation
        |
        v
    Contradiction Analysis
        |
        v
    LearningProposal      (Sprint 22.3 integration)
        |
        v
    Human Review          (lifecycle: CREATED -> PENDING_REVIEW -> APPROVED/REJECTED)
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
    proposal_type_for_feedback_event,
    PROPOSAL_TYPE_BOUNDARY,
    PROPOSAL_TYPE_PRINCIPLE,
    PROPOSAL_TYPE_APPLICABILITY,
)
from caseos.knowledge.feedback.proposal_lifecycle import (
    ProposalStatus,
    LIFECYCLE_ORDER as PROPOSAL_LIFECYCLE_ORDER,
    TERMINAL_STATES as PROPOSAL_TERMINAL_STATES,
    is_valid_transition as is_valid_proposal_transition,
    is_terminal as is_proposal_terminal,
    allowed_next_states as allowed_proposal_next_states,
)
from caseos.knowledge.feedback.proposal_store import (
    ProposalEvent,
    ProposalStore,
)
from caseos.knowledge.feedback.proposal_integration import (
    propose_from_contradiction,
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
    # Proposal (data + generator)
    "LearningProposal",
    "generate_proposal",
    "proposal_type_for_feedback_event",
    "PROPOSAL_TYPE_BOUNDARY",
    "PROPOSAL_TYPE_PRINCIPLE",
    "PROPOSAL_TYPE_APPLICABILITY",
    # Proposal lifecycle
    "ProposalStatus",
    "PROPOSAL_LIFECYCLE_ORDER",
    "PROPOSAL_TERMINAL_STATES",
    "is_valid_proposal_transition",
    "is_proposal_terminal",
    "allowed_proposal_next_states",
    # Proposal store + integration
    "ProposalEvent",
    "ProposalStore",
    "propose_from_contradiction",
    # Manager
    "FeedbackError",
    "FeedbackManager",
    # Report
    "generate_report",
    "generate_summary",
]
