"""Terminal Service (Sprint 26.0-A, Terminal MVP V1).

The single user-facing entry point that:

    TerminalRequest
          |
          v
        Validator
          |
          v
        QueryBuilder
          |
          v
        RetrievalPipeline
          |
          v
        TerminalResult

V1 does NOT generate design images, does NOT call any AI
runtime, does NOT mutate inputs. It only orchestrates the
existing retrieval stack against a fixed-shape request.

The service is **deterministic**: two ``execute`` calls with the
same request, knowledge objects and pipeline state produce the
same ``TerminalResult`` (modulo the auto-assigned
``query_id`` / ``request_id`` / ``created_at``).

Architecture boundary (Sprint 26.0-A spec section 7):

    This module imports from:
        * caseos.knowledge.retrieval.pipeline   (RetrievalPipeline)
        * caseos.knowledge.retrieval.object    (RetrievalQuery)
        * caseos.knowledge.object              (KnowledgeObject)
        * stdlib

    It does NOT import from:
        * caseos.intelligence.*
        * caseos.brain.*
        * caseos.knowledge.evolution.*
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * caseos.knowledge.intake
        * caseos.knowledge.corpus
        * any LLM / VLM / embedding SDK
"""
from __future__ import annotations

import copy
import dataclasses
from dataclasses import dataclass, field
from typing import Optional, Sequence

from caseos.knowledge.object import KnowledgeObject

from caseos.knowledge.retrieval.object import RetrievalQuery
from caseos.knowledge.retrieval.pipeline import (
    RetrievalPipeline,
    build_default_pipeline,
)

from .contract import DEFAULT_TERMINAL_CONTRACT, TerminalContract
from .object import (
    TerminalQuery,
    TerminalRequest,
    TerminalResult,
    TerminalValidationResult,
)
from .query_builder import TerminalQueryBuilder
from .validator import TerminalValidator


# ---------------------------------------------------------------------------
# Default factories
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class TerminalServiceError(RuntimeError):
    """Base error for TerminalService."""


# ---------------------------------------------------------------------------
# TerminalService
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TerminalService:
    """V1 orchestration entry point.

    Construction parameters
    -----------------------
    pipeline:
        Existing ``RetrievalPipeline`` instance. When None, the
        service builds a default HYBRID_AUTO pipeline via
        ``build_default_pipeline()``. The service never mutates
        the pipeline; calling ``execute`` is read-only on its
        side.
    contract:
        ``TerminalContract`` consumed by the validator and the
        query builder. When None, ``DEFAULT_TERMINAL_CONTRACT`` is
        used.

    The service is frozen so multiple threads can share one
    instance safely.
    """

    ENGINE_NAME: str = "TerminalService V1"

    pipeline: Optional[RetrievalPipeline] = None
    contract: TerminalContract = DEFAULT_TERMINAL_CONTRACT

    def __post_init__(self) -> None:
        if self.contract is None:
            object.__setattr__(self, "contract", DEFAULT_TERMINAL_CONTRACT)
        if not isinstance(self.contract, TerminalContract):
            raise TerminalServiceError(
                "contract must be a TerminalContract; got "
                + type(self.contract).__name__
            )
        if self.pipeline is not None and not isinstance(
            self.pipeline, RetrievalPipeline,
        ):
            raise TerminalServiceError(
                "pipeline must be a RetrievalPipeline or None; got "
                + type(self.pipeline).__name__
            )

    # ---- public ----------------------------------------------------

    def execute(
        self,
        request: TerminalRequest,
        knowledge_objects: Sequence[KnowledgeObject],
        *,
        limit: Optional[int] = None,
    ) -> TerminalResult:
        """Run the full chain.

        ``knowledge_objects`` is a snapshot of the retrieval
        corpus the caller wants searched. The service MUST NOT
        mutate it.

        ``limit`` overrides the contract default; when supplied,
        it must already satisfy validator T7.
        """
        validator = TerminalValidator(contract=self.contract)
        builder = TerminalQueryBuilder(contract=self.contract)

        # 1) Validate
        ck_validation: TerminalValidationResult = validator.validate(
            request, limit=limit,
        )
        if not ck_validation.valid:
            return TerminalResult(
                request_id=(
                    request.request_id
                    if isinstance(request, TerminalRequest) else ""
                ),
                success=False,
                failure_reason=ck_validation.reason,
                created_at=_now_iso(),
            )

        # 2) Build the query
        if limit is None:
            query: TerminalQuery = builder.build(request)
        else:
            query = builder.build_with_limit(request, limit)

        # 3) Construct RetrievalQuery from TerminalQuery
        retrieval_query = RetrievalQuery(
            query_text=query.query_text,
            filters=query.filters_dict(),
            limit=query.limit,
        )

        # 4) Execute the pipeline
        pipeline = self._get_pipeline()
        retrieval_result = pipeline.execute(
            retrieval_query, list(knowledge_objects),
        )

        # 5) Project into TerminalResult. NEVER mutate upstream.
        cases = tuple(retrieval_result.hits)
        return TerminalResult(
            request_id=request.request_id,
            query=query,
            retrieval_result=retrieval_result,
            total_hits=retrieval_result.total_hits,
            cases=cases,
            success=True,
            failure_reason="",
            created_at=_now_iso(),
        )

    # ---- private helpers ------------------------------------------

    def _get_pipeline(self) -> RetrievalPipeline:
        if self.pipeline is None:
            return build_default_pipeline()
        return self.pipeline


__all__ = [
    "TerminalServiceError",
    "TerminalService",
]
