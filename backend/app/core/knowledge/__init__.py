"""Knowledge retriever package for the CaseOS Decision Intelligence layer.

This package supplies the KnowledgeRetriever used by the
knowledge_retriever agent. It exposes:

  * KnowledgeSnippet      -- one retrieved knowledge unit
  * RelevantKnowledgeContext -- aggregate snapshot for one decision run
  * KnowledgeLoader       -- lazy loader over the on-disk knowledge library
  * KnowledgeRetriever    -- the retrieval logic (deterministic, local)

The package never edits or invents knowledge content; it only reads
files under knowledge/ and aggregates references.
"""

from app.core.knowledge.knowledge_context import (
    KnowledgeSnippet,
    RelevantKnowledgeContext,
)
from app.core.knowledge.knowledge_loader import KnowledgeLoader
from app.core.knowledge.retriever import KnowledgeRetriever

__all__ = [
    "KnowledgeLoader",
    "KnowledgeRetriever",
    "KnowledgeSnippet",
    "RelevantKnowledgeContext",
]
