"""Evolution Integration Verification V1 (Sprint 22.4-C, ADR-020).

This package is the **flow-level runtime** that wires together
the Sprint 22.4-A (Transaction + Validator + Audit) and Sprint
22.4-B (Policy + Governance Gate) modules into a single
executable pipeline.

The runtime answers one question:

    "Given a transaction, does the flow end in
    (a) governance-approved + audit-recorded, or
    (b) rejected at the validator or the gate?"

It does NOT answer:

    "Should the Knowledge Object be mutated?"
    "What does the new KO look like?"

Those are downstream concerns, gated on ADR-020 Rules 1-5 and
on a future Sprint 22.4.x mutation runtime. In V1, the
integration runtime **hard-stops** before any KO write-back.

Integration flow (Sprint 22.4-C spec):

    EvolutionTransaction
        |
        v
    EvolutionRuntime.execute(transaction, change_intent, reviewer)
        |
        +-- 1. receive transaction
        +-- 2. validate (EvolutionValidator)
        +-- 3. govern   (EvolutionGovernanceGate)
        +-- 4. if reject: stop, return result
        +-- 5. if pass:   create AuditRecord
        +-- 6. return EvolutionExecutionResult

Important boundary (Sprint 22.4-C spec Task 1):

    After execute() success, the runtime is allowed to:
        * create an AuditRecord

    After execute() success, the runtime is forbidden from:
        * changing the Knowledge Object,
        * increasing the KO version,
        * changing any Decision.

Architecture boundary (Sprint 22.4-C spec):

    This package does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * caseos.knowledge.objects
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * stdlib
"""
from .runtime import EvolutionRuntime, EvolutionExecutionResult
from .report import generate_report

__all__ = [
    "EvolutionRuntime",
    "EvolutionExecutionResult",
    "generate_report",
]
