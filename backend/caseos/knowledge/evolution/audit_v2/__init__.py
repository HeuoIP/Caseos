"""Evolution Audit Log Schema V1 (Sprint 22.4-E, ADR-020 Rule 3).

This package implements **ADR-020 Rule 3 (Audit Required)**
at the foundation level: a 13-field immutable audit record
plus an append-only store.

The package is the **schema foundation** that a future
Sprint 22.4.x mutation runtime will write to. In V1:

    * No EvolutionTransaction -> KO mutation is wired.
    * No `restore()`, `rollback()`, or `apply()` method exists.
    * The rollback_reference field is stored but never used.
    * No corpus, retrieval, or intelligence engine is touched.

The runtime semantics are:

    EvolutionAuditRecord  (frozen, 13 fields)
        |
        v
    AuditStore            (append-only container)

This package is **additive** to Sprint 22.4-A's
``evolution/audit.py``. The 22.4-A audit is the
lifecycle-event log used by ``EvolutionRuntime``; this
package is the per-evolution audit record required by
ADR-020 Rule 3.

Architecture boundary (Sprint 22.4-E spec Task 3):

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
from .object import EvolutionAuditRecord
from .store import AuditStore, AuditStoreError
from .report import generate_report

__all__ = [
    "EvolutionAuditRecord",
    "AuditStore",
    "AuditStoreError",
    "generate_report",
]
