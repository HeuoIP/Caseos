"""Knowledge Retrieval Module (corpus-backed since Sprint 20.5).

Sprint 19.1: loaded 3 sample KOs from a single directory.
Sprint 20.5: loads the full 5-subdirectory corpus (per ADR-015).

The retrieval decision logic in Sprint 20 is unchanged. The
Knowledge Module is the loader; retrieval happens in the
Retrieval stage.
"""
from __future__ import annotations

from pathlib import Path

from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext
from caseos.knowledge.objects.loader import (
    DEFAULT_CORPUS_DIR,
    load_corpus,
    load_objects_from_dir,
)


class KnowledgeModule(Stage):
    name = "knowledge"

    def __init__(self, corpus_dir=None, samples_dir=None) -> None:
        # Backward-compat: `samples_dir` is the Sprint 19.1
        # parameter name. New code passes `corpus_dir`. The
        # default is the new 5-subdir corpus.
        if corpus_dir is not None:
            self._dir = Path(corpus_dir)
        elif samples_dir is not None:
            self._dir = Path(samples_dir)
        else:
            self._dir = DEFAULT_CORPUS_DIR

    def run(self, ctx: PipelineContext) -> PipelineContext:
        # If the configured directory has subdirectories, treat it
        # as a corpus and walk recursively. Otherwise fall back
        # to the legacy single-directory loader (for tests that
        # use tmp dirs).
        dir_path = self._dir
        if any(p.is_dir() for p in dir_path.iterdir()) if dir_path.exists() else False:
            objects = load_corpus(dir_path)
        else:
            objects = load_objects_from_dir(dir_path)
        ctx.knowledge_patterns = objects
        ctx.metadata["knowledge_loaded_count"] = len(objects)
        ctx.metadata["knowledge_source"] = str(dir_path)
        return ctx


__all__ = ["KnowledgeModule"]