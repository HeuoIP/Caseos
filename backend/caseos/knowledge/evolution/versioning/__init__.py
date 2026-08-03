"""Knowledge Versioning Foundation V1 (Sprint 22.4-D, ADR-020).

This package implements **ADR-020 Rule 2 (Version Required)**
at the foundation level: a container for versioned Knowledge
Object snapshots, plus a deterministic differ.

The package is the **future version record container** that
a future Sprint 22.4.x mutation runtime will populate. In V1:

    * No EvolutionTransaction -> KO mutation is wired.
    * No `KnowledgeObject.version += 1` happens anywhere.
    * No corpus data is touched.
    * No intelligence engine is touched.

The runtime semantics are:

    KnowledgeDiff     (compare snapshots)
        |
        v
    KnowledgeVersion  (frozen record)
        |
        v
    VersionStore      (append-only container)

The differ is deterministic. The store is append-only. The
version record is frozen. A future Sprint 22.4.x can consume
these three primitives to wire the actual KO write-back,
gated on ADR-020 Rules 1 and 5 (Transaction + No Intelligence
Rewrite) and on a concrete implementation.

Architecture boundary (Sprint 22.4-D spec Task 4):

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
from .object import KnowledgeVersion
from .store import VersionStore, VersionStoreError
from .diff import KnowledgeDiff, KnowledgeDiffer
from .report import generate_report

__all__ = [
    "KnowledgeVersion",
    "VersionStore",
    "VersionStoreError",
    "KnowledgeDiff",
    "KnowledgeDiffer",
    "generate_report",
]
