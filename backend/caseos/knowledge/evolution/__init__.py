"""Knowledge Evolution Transaction Foundation V1 (Sprint 22.4-A, ADR-020).

This package provides the **safe entry point** for the future
Knowledge Evolution runtime. It does NOT mutate the Knowledge
Object. It does NOT modify the corpus. It does NOT trigger any
learning.

The evolution layer sits between the Interpretation Policy and
the not-yet-implemented Knowledge Object write-back:

    ChangeIntent
        |
        v
    EvolutionTransaction   (this package, V1)
        |
        v
    Governance Validation  (this package, V1)
        |
        v
    Audit Record           (this package, V1)
        |
        X   <-- Knowledge Object Mutation: NOT IMPLEMENTED in V1

Architecture boundary (Sprint 22.4-A spec):

    This package does NOT import from:
        * caseos.intelligence.decision
        * caseos.intelligence.trust
        * caseos.intelligence.recommendation
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.objects
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * stdlib

The evolution layer is a **side-channel** of the Feedback
Learning Loop. It is not inserted into the main pipeline:

    Human -> Knowledge -> Retrieval -> Decision -> Trust
           -> Recommendation -> Output

The evolution runtime is gated on:

    * an approved `ChangeIntent` from Sprint 22.3.2,
    * the Five Mandatory Rules of ADR-020,
    * the four Hard Rules of ADR-018 (Sections 14-17).

V1 hard-stops at the Audit Record. The "APPLIED" status is
declared in the lifecycle enum but **transitions to APPLIED
are forbidden** in V1. The mutation of the Knowledge Object
is a future Sprint 22.4.x concern, gated on a new ADR and on
a concrete implementation that respects ADR-020 Rules 1-5.
"""
from .object import (
    EvolutionTransaction,
    EvolutionStatus,
)
from .transaction import (
    ALLOWED_TRANSITIONS,
    is_valid_transition,
)
from .validator import (
    EvolutionValidator,
    ValidationResult,
)
from .audit import (
    EvolutionAuditRecord,
    EvolutionAuditStore,
    EvolutionAuditError,
)
from .policy import (
    ALLOWED_CHANGE_TYPES,
    FORBIDDEN_CHANGE_TYPES,
    G2_FORBIDDEN_CHANGE_TYPES,
    G3_FORBIDDEN_CHANGE_TYPES,
    G4_FORBIDDEN_CHANGE_TYPES,
    EvolutionChangePolicy,
)
from .governance import (
    GovernanceResult,
    EvolutionGovernanceGate,
)
from .report import generate_report

__all__ = [
    # Object
    "EvolutionTransaction",
    "EvolutionStatus",
    # Lifecycle
    "ALLOWED_TRANSITIONS",
    "is_valid_transition",
    # Validator
    "EvolutionValidator",
    "ValidationResult",
    # Audit
    "EvolutionAuditRecord",
    "EvolutionAuditStore",
    "EvolutionAuditError",
    # Policy (Sprint 22.4-B)
    "ALLOWED_CHANGE_TYPES",
    "FORBIDDEN_CHANGE_TYPES",
    "G2_FORBIDDEN_CHANGE_TYPES",
    "G3_FORBIDDEN_CHANGE_TYPES",
    "G4_FORBIDDEN_CHANGE_TYPES",
    "EvolutionChangePolicy",
    # Governance (Sprint 22.4-B)
    "GovernanceResult",
    "EvolutionGovernanceGate",
    # Report
    "generate_report",
]
