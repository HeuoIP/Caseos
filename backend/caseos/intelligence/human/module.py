"""Human Understanding Module -- Sprint 21 runtime (ADR-013).

The `HumanModule` is the pipeline stage that produces a
`HumanContext` from the project input. It is the first
non-trivial replacement of the Sprint 19.1 placeholder.

Pipeline position (Sprint 21 spec section 5):

    Human Understanding
        |
        v
    Knowledge
        |
        v
    Retrieval   (Sprint 20 / ADR-019)
        |
        v
    Decision
        |
        v
    Trust
        |
        v
    Recommendation
        |
        v
    Output

The stage writes `ctx.human_context` (a `HumanContext`-shaped
dict) and adds a small validation summary to `ctx.metadata`
so downstream rules and the Markdown renderer can see:

    * which fields were filled
    * which fields are unknown
    * whether the context is valid (required fields present)

Architecture boundary (Sprint 21 spec section "Key Principle"):

    * HumanModule MUST NOT call any LLM, NLP, vision, DB, or
      retrieval engine. It only converts structured input.
    * HumanModule MUST NOT modify the Decision Object. The
      Decision Engine is the authority.
    * HumanModule MUST NOT import from:
        - caseos.knowledge.retrieval
        - caseos.intelligence.decision
        - caseos.intelligence.trust
        - caseos.intelligence.recommendation
        - caseos.knowledge.governance
        - caseos.knowledge.intake
"""
from __future__ import annotations

from typing import Any

from caseos.brain.runtime import Stage
from caseos.brain.runtime.context import PipelineContext

from .extractor import extract_human_context
from .object import HumanContext, UNKNOWN
from .validator import validate_human_context


class HumanModule(Stage):
    """Pipeline stage: `human_understanding`.

    Reads `ctx.project` (frozen `ProjectContext`), writes
    `ctx.human_context` (dict), and records a validation
    summary in `ctx.metadata["human_validation"]`.
    """

    name = "human_understanding"

    def run(self, ctx: PipelineContext) -> PipelineContext:
        result = extract_human_context(ctx.project)
        validation = validate_human_context(result.human_context)

        # Persist as a dict so downstream stages (decision, retrieval,
        # recommendation) can keep treating `ctx.human_context` as a
        # mapping -- no API change required.
        ctx.human_context = result.human_context.to_dict()
        ctx.metadata["human_validation"] = validation.to_dict()
        ctx.metadata["human_mapped_fields"] = list(result.mapped_fields)
        ctx.metadata["human_skipped_fields"] = list(result.skipped_fields)
        ctx.metadata["human_schema_version"] = result.human_context.schema_version
        return ctx


__all__ = [
    "HumanContext",
    "HumanModule",
    "UNKNOWN",
    "extract_human_context",
    "validate_human_context",
]
