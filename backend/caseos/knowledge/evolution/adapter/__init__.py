"""Knowledge Object Evolution Adapter V1 (Sprint 23.0-B, ADR-020).

This package is the **bridge** between the Evolution Runtime
(Sprint 22.4.x) and the Knowledge Object Schema V1
(Sprint 23.0-A).

    EvolutionTransaction     (Sprint 22.4-A, .object)
            |
            |  before_snapshot: dict
            |  change_type: EvolutionChangeType
            |  requested_change: str
            v
    KnowledgeObjectAdapter  (this package)
            |
            |  resolves change_type -> KO V1 field
            |  deep-copies before_snapshot
            |  applies the requested change
            |  bumps version (next_version = before_version + 1)
            v
    AdapterResult           (new_snapshot: dict, mutation_executed=False)
            |
            v
    (caller decides whether to call KnowledgeMutationEngine)

Hard invariants (Sprint 23.0-B spec):

    * The adapter NEVER mutates the input request.
    * The adapter NEVER mutates the input before_snapshot.
    * The adapter NEVER touches VersionStore, AuditStore, or
      any Intelligence / Retrieval module.
    * The adapter returns ``mutation_executed=False`` in V1;
      the adapter only produces a *candidate* snapshot. The
      caller (a future Sprint or a test harness) is
      responsible for actually applying it.
    * The adapter's output is **always** compatible with
      ``KnowledgeObject.from_dict()`` (validated internally).
    * All dataclasses are frozen; collection fields are
      deep-copied on entry.

Architecture boundary (Sprint 23.0-B spec):

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
    AdapterRequest,
    AdapterResult,
    FieldMapping,
    AdapterError,
)
from .mapping import (
    CHANGE_TYPE_TO_KO_FIELD,
    V1_MAPPING_NOTE,
    resolve_target_field,
)
from .validator import (
    AdapterValidator,
    AdapterValidationResult,
)
from .engine import KnowledgeObjectAdapter
from .report import generate_adapter_report

__all__ = [
    # Objects
    "AdapterRequest",
    "AdapterResult",
    "FieldMapping",
    "AdapterError",
    # Mapping
    "CHANGE_TYPE_TO_KO_FIELD",
    "V1_MAPPING_NOTE",
    "resolve_target_field",
    # Validator
    "AdapterValidator",
    "AdapterValidationResult",
    # Engine
    "KnowledgeObjectAdapter",
    # Report
    "generate_adapter_report",
]
