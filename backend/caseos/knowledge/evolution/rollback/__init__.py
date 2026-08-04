"""Evolution Rollback Module V1 (Sprint 22.4-G, ADR-020 Rule 4).

This package implements **ADR-020 Rule 4 (Rollback Required)**
at the foundation level: a deterministic request, a five-rule
validator, a frozen plan, and a Markdown report. The package
is the **rollback foundation** that a future Sprint 22.4.x
mutation runtime will consume.

In V1:

    * No Knowledge Object is restored.
    * No corpus data is touched.
    * No intelligence / retrieval / decision / trust /
      recommendation engine is called.
    * The plan is a description, not an executor.
    * No `restore()`, `rollback()`, `apply()`, `execute()`,
      or `mutate()` method exists on any class.

The runtime semantics are:

    EvolutionAuditRecord (Sprint 22.4-E)
        |
        v
    RollbackRequest        (this package)
        |
        v
    RollbackValidator      (this package, R1-R5)
        |
        v
    RollbackPlan           (this package, frozen)
        |
        X  <-- no execution in V1

A future Sprint 22.4.x rollback runtime will consume the
``RollbackPlan`` and apply it. The V1 plan is intentionally
a static description so the contract is locked before the
runtime is built.

Architecture boundary (Sprint 22.4-G spec Task 6):

    This package does NOT import from:
        * caseos.intelligence.decision
        * caseos.intelligence.trust
        * caseos.intelligence.recommendation
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.evolution (sibling modules)
        * caseos.knowledge.objects
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * stdlib
"""
from .object import (
    RollbackRequest,
    RollbackPlan,
    RollbackValidationResult,
)
from .request import build_request_from_audit
from .validator import RollbackValidator
from .plan import RollbackPlanner
from .report import generate_report

__all__ = [
    # Object
    "RollbackRequest",
    "RollbackPlan",
    "RollbackValidationResult",
    # Request builder
    "build_request_from_audit",
    # Validator
    "RollbackValidator",
    # Planner
    "RollbackPlanner",
    # Report
    "generate_report",
]
