"""CaseOS Evidence Retrieval Intelligence (Sprint 20, ADR-019).

The retrieval layer turns the flat Knowledge Object corpus into
a ranked Evidence Package that the Decision Engine, Trust Engine,
and Recommendation Engine can consume selectively.

Architectural position in the pipeline:

    Human -> Knowledge -> Retrieval -> Decision -> Trust -> Recommendation

This package exports:

    * `EvidencePackage`     -- the 5-component output contract
    * `RetrievalEngine`     -- the scoring + ranking engine
    * `KnowledgeRetriever`  -- the Stage wrapper (name = "retrieval")
    * `RetrievalRule`       -- the rule base (parity with Decision/Trust)
    * `RULE_APPLICABILITY`  -- the default rule list
"""

from caseos.knowledge.retrieval.module import (
    EvidencePackage,
    KnowledgeRetriever,
    RetrievalEngine,
    RetrievalRule,
    RuleP1_Applicability,
    RuleP2_Diagnosis,
    RuleP3_Situation,
    RuleP4_Boundary,
    RULE_APPLICABILITY,
)

__all__ = [
    "EvidencePackage",
    "KnowledgeRetriever",
    "RetrievalEngine",
    "RetrievalRule",
    "RuleP1_Applicability",
    "RuleP2_Diagnosis",
    "RuleP3_Situation",
    "RuleP4_Boundary",
    "RULE_APPLICABILITY",
]