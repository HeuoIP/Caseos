"""Knowledge Object Evolution Writer V1 (Sprint 23.0-C, ADR-020).

This package is the **persistence layer** between the
Evolution Adapter (Sprint 23.0-B) and the append-only
stores that exist today:

    AdapterResult (new_snapshot)
        |
        v
    KnowledgeObjectWriter (this package)
        |
        +---> VersionStore.append(KnowledgeVersion)
        |
        +---> AuditStore.append(EvolutionAuditRecord)
        |
        v
    WriteResult (frozen, audit-friendly)

Hard invariants (Sprint 23.0-C spec):

    * The writer NEVER mutates an existing KnowledgeVersion.
    * The writer NEVER overwrites a store. It only appends.
    * The writer NEVER touches caseos.intelligence.* or
      caseos.knowledge.retrieval.
    * The writer NEVER bypasses VersionStore / AuditStore.
    * The writer's WriteRequest is frozen; collection
      fields are deep-copied in __post_init__.
    * On success, ``mutation_executed=True`` is the first
      layer in the Evolution pipeline that actually
      appends. Prior layers (Adapter, Interpretation,
      Proposal, Review) are candidate-only.

Architecture boundary (Sprint 23.0-C spec):

    This package does NOT import from:
        * caseos.intelligence.decision
        * caseos.intelligence.trust
        * caseos.intelligence.recommendation
        * caseos.knowledge.retrieval
    This package MAY import from:
        * caseos.knowledge.evolution (sibling packages)
        * caseos.knowledge.evolution.contracts
        * caseos.knowledge.object (the new KO V1 schema)
        * stdlib
"""
from .object import (
    WriteRequest,
    WriteResult,
    WriteError,
)
from .validator import (
    WriterValidator,
    WriterValidationResult,
)
from .engine import KnowledgeObjectWriter
from .report import generate_writer_report

__all__ = [
    # Objects
    "WriteRequest",
    "WriteResult",
    "WriteError",
    # Validator
    "WriterValidator",
    "WriterValidationResult",
    # Engine
    "KnowledgeObjectWriter",
    # Report
    "generate_writer_report",
]
