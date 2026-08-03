"""Feedback Interpretation Policy Foundation V1 (Sprint 22.3.2).

The interpretation layer sits *downstream* of the human review
queue and *upstream* of any future Knowledge Evolution step
(Sprint 22.4):

    Approved LearningProposal
        |
        v
    InterpretationPolicy
        |
        v
    ChangeIntent
        |
        v
    (Future Sprint 22.4) Knowledge Evolution

Architecture boundary (Sprint 22.3.2 spec Task 6):

    This package does NOT import from:
        * caseos.intelligence.decision
        * caseos.intelligence.trust
        * caseos.intelligence.recommendation
        * caseos.knowledge.retrieval
        * caseos.knowledge.governance
        * caseos.knowledge.intake
    This package MAY import from:
        * caseos.knowledge.feedback (parent package)
        * caseos.knowledge.objects
        * stdlib

The interpretation layer is a side-channel. It does NOT
participate in the brain pipeline. It does NOT mutate any
external state. The ChangeIntent is the operator-facing artifact
that a future Knowledge Evolution sprint will turn into an
actual KO update.
"""
from .object import ChangeIntent, VALID_CHANGE_TYPES, VALID_RISK_LEVELS
from .policy import InterpretationPolicy
from .validator import validate_change_intent, REQUIRED_STRING_FIELDS
from .report import generate_report

__all__ = [
    "ChangeIntent",
    "VALID_CHANGE_TYPES",
    "VALID_RISK_LEVELS",
    "InterpretationPolicy",
    "validate_change_intent",
    "REQUIRED_STRING_FIELDS",
    "generate_report",
]
