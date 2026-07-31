"""Knowledge Retrieval Module (placeholder)."""
from __future__ import annotations
from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext
from caseos.knowledge.objects.loader import load_objects_from_dir, DEFAULT_SAMPLES_DIR


class KnowledgeModule(Stage):
    name = "knowledge"

    def __init__(self, samples_dir=None) -> None:
        from pathlib import Path
        self.samples_dir = Path(samples_dir) if samples_dir else DEFAULT_SAMPLES_DIR

    def run(self, ctx: PipelineContext) -> PipelineContext:
        objects = load_objects_from_dir(self.samples_dir)
        ctx.knowledge_patterns = objects
        ctx.metadata["knowledge_loaded_count"] = len(objects)
        return ctx


__all__ = ["KnowledgeModule"]