"""Evolution Runtime V2 -- Full Simulation (Sprint 22.4-F, ADR-020).

This package implements the **full simulation** of the
ADR-020 Evolution Pipeline:

    EvolutionTransaction
        |
        v
    EvolutionValidator
        |
        v
    EvolutionGovernanceGate
        |
        v
    KnowledgeVersion        (versioned snapshot)
        |
        v
    EvolutionAuditRecord V2 (per-evolution audit)
        |
        v
    EvolutionExecutionResult

The simulation is **read-and-record**, never **write**:

    * No Knowledge Object is mutated.
    * No corpus data is touched.
    * No retrieval, decision, trust, or recommendation
      engine is called.
    * ``mutation_executed`` is always False.
    * The "after_snapshot" on the audit record is None
      because there is no real "after" in V1.

A future Sprint 22.4.x mutation runtime will consume the
``KnowledgeVersion`` and ``EvolutionAuditRecord`` produced
here under ADR-020 Rules 1-5 and a new mutation ADR. In
V1, the runtime is passive: it simulates the chain end
to end and records the audit log.

Architecture boundary (Sprint 22.4-F spec):

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
from .executor import EvolutionExecutor, EvolutionExecutionResult
from .report import generate_report

__all__ = [
    "EvolutionExecutor",
    "EvolutionExecutionResult",
    "generate_report",
]
