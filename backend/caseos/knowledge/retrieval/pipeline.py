"""Knowledge Retrieval Pipeline Facade V1 (Sprint 24.3-A).

This module ships the **single entry point** that wires
together the retrieval stack delivered by Sprints 24.0
through 24.2. The facade is intentionally small:

    Pipeline
      |
      +-- one or more sub-engines (Keyword / Structured /
      |   Semantic, all built from the V1 contract layer)
      |
      +-- optional HitFusion (Hybrid layer from 24.0-D)
      |
      +-- optional Ranking post-pass (24.0-C)
      |
      v
    RetrievalResult

Strategies (V1):

    KEYWORD_ONLY      -- one sub-engine: KeywordRetrievalEngine
    STRUCTURED_ONLY   -- one sub-engine: StructuredRetrievalEngine
    SEMANTIC_ONLY     -- one sub-engine: SemanticRetrievalEngine
                          (requires ``semantic_index``)
    HYBRID_AUTO       -- two sub-engines: keyword + structured
                          (default strategy; no semantic needed)
    HYBRID_FULL       -- three sub-engines: keyword + structured
                          + semantic (requires ``semantic_index``)

Architecture boundary (Sprint 24.3-A spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
        * caseos.brain.*
    This module MAY import from:
        * caseos.knowledge.object
        * caseos.knowledge.attribute
        * caseos.knowledge.domain
        * caseos.knowledge.binding
        * caseos.knowledge.taxonomy
        * caseos.knowledge.graph
        * caseos.knowledge.retrieval (sibling modules)
        * stdlib
"""
from __future__ import annotations

import time
from typing import (
    Any,
    Iterable,
    List,
    Literal,
    Mapping,
    Optional,
    Sequence,
)

from .engine import KeywordRetrievalEngine
from .hybrid import (
    HitFusionStrategy,
    HybridRetrievalEngine,
    LambdaSubEngine,
    WeightedScoreFusion,
)
from .object import (
    RetrievalQuery,
    RetrievalResult,
)
from .ranking import RankingEngine
from .semantic import SemanticIndex, SemanticRetrievalEngine
from .structured import StructuredRetrievalEngine


# ---------------------------------------------------------------------------
# Strategy constants
# ---------------------------------------------------------------------------


STRATEGY_KEYWORD_ONLY: str = "KEYWORD_ONLY"
STRATEGY_STRUCTURED_ONLY: str = "STRUCTURED_ONLY"
STRATEGY_SEMANTIC_ONLY: str = "SEMANTIC_ONLY"
STRATEGY_HYBRID_AUTO: str = "HYBRID_AUTO"
STRATEGY_HYBRID_FULL: str = "HYBRID_FULL"

STRATEGY_ALLOW_LIST: frozenset = frozenset(
    {
        STRATEGY_KEYWORD_ONLY,
        STRATEGY_STRUCTURED_ONLY,
        STRATEGY_SEMANTIC_ONLY,
        STRATEGY_HYBRID_AUTO,
        STRATEGY_HYBRID_FULL,
    }
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class RetrievalPipelineError(ValueError):
    """Base error for the pipeline facade."""


# ---------------------------------------------------------------------------
# RetrievalPipeline
# ---------------------------------------------------------------------------


class RetrievalPipeline:
    """The single retrieval entry point.

    The pipeline composes the V1 retrieval stack into a
    deterministic, read-only consumer of Knowledge Objects.

    Construction parameters
    -----------------------
    strategy:
        One of ``STRATEGY_*``. Defaults to
        ``STRATEGY_HYBRID_AUTO`` (keyword + structured).
    post_ranker:
        Optional ``RankingEngine`` instance. When set,
        the pipeline applies the ranker after fusing.
    fusion:
        Optional ``HitFusionStrategy``. When ``None``,
        ``WeightedScoreFusion`` is used for hybrid
        strategies; single-engine strategies ignore it.
    engine_weights:
        Optional ``{"keyword": float, "structured": float,
        "semantic": float}`` mapping. Missing keys fall
        back to the fusion strategy's default weight.
    semantic_index:
        Required only for ``SEMANTIC_ONLY`` and
        ``HYBRID_FULL``. A plain ``SemanticIndex`` from
        Sprint 24.1-A (or its bridge from
        ``build_semantic_index`` in Sprint 24.1-B).
    attribute_registry / binding_registry:
        Forwarded to the structured engine when it is
        wired in. Both are optional; absent registries
        are treated as empty by the engine layer.
    """

    ENGINE_NAME: str = "RetrievalPipeline V1"

    def __init__(
        self,
        strategy: str = STRATEGY_HYBRID_AUTO,
        *,
        post_ranker: Optional[RankingEngine] = None,
        fusion: Optional[HitFusionStrategy] = None,
        engine_weights: Optional[Mapping[str, float]] = None,
        semantic_index: Optional[SemanticIndex] = None,
        attribute_registry: Optional[Iterable[Any]] = None,
        binding_registry: Optional[Iterable[Any]] = None,
        binding_lookup: Optional[Mapping[str, Sequence[str]]] = None,
    ) -> None:
        if not isinstance(strategy, str) or strategy not in STRATEGY_ALLOW_LIST:
            raise RetrievalPipelineError(
                "strategy must be one of "
                + ", ".join(sorted(STRATEGY_ALLOW_LIST))
                + "; got " + repr(strategy)
            )
        self.strategy: str = strategy

        # Optional post-ranker.
        if post_ranker is not None and not isinstance(
            post_ranker, RankingEngine
        ):
            raise RetrievalPipelineError(
                "post_ranker must be a RankingEngine or None; got "
                + type(post_ranker).__name__
            )
        self.post_ranker: Optional[RankingEngine] = post_ranker

        # Fusion strategy (hybrid only).
        if fusion is not None and not isinstance(fusion, HitFusionStrategy):
            raise RetrievalPipelineError(
                "fusion must be a HitFusionStrategy or None; got "
                + type(fusion).__name__
            )
        self.fusion: HitFusionStrategy = (
            fusion if fusion is not None else WeightedScoreFusion()
        )

        # Engine weights.
        weights: dict = {}
        if engine_weights is not None:
            for k, v in engine_weights.items():
                if isinstance(k, str) and k:
                    try:
                        weights[k] = float(v)
                    except (TypeError, ValueError):
                        continue
        self.engine_weights: dict = weights

        # Semantic index (lazy-validated per-strategy).
        self.semantic_index: Optional[SemanticIndex] = semantic_index

        # Registries for downstream engines.
        self.attribute_registry: Optional[Iterable[Any]] = attribute_registry
        self.binding_registry: Optional[Iterable[Any]] = binding_registry
        self.binding_lookup: Optional[Mapping[str, Sequence[str]]] = (
            binding_lookup
        )

        # Build the underlying hybrid (or single-engine
        # adapter) once at construction time so
        # ``execute`` is a fast dispatch.
        self._engine, self._uses_hybrid = self._build_engine()

    # ---- public ----------------------------------------------------

    def execute(
        self,
        query: RetrievalQuery,
        knowledge_objects: Sequence[Any],
        **engine_kwargs: Any,
    ) -> RetrievalResult:
        """Run the pipeline.

        The pipeline never mutates the input KOs or the
        query; downstream engines are guaranteed read-only.
        Returned ``RetrievalResult`` is a fresh frozen
        envelope.
        """
        started = time.perf_counter()

        # Strategy-aware kwarg forwarding. For single-engine
        # strategies we pass the registries directly to the
        # engine; for hybrid strategies we let the hybrid
        # engine forward them.
        if self._uses_hybrid:
            try:
                result = self._engine.execute(
                    query, knowledge_objects, **engine_kwargs
                )
            except TypeError:
                # Hybrid engine does not accept the kwargs;
                # retry without them.
                result = self._engine.execute(query, knowledge_objects)
        else:
            # Single-engine dispatch: forward registry
            # kwargs so the structured / semantic engines
            # get their data.
            kwargs = self._single_engine_kwargs(engine_kwargs)
            if hasattr(self._engine, "execute"):
                sig = self._engine.execute
                try:
                    result = sig(query, knowledge_objects, **kwargs)
                except TypeError:
                    result = sig(query, knowledge_objects)
            else:
                # Duck-typed callable.
                result = self._engine(query, knowledge_objects)

        # Optional post-rank pass.
        if self.post_ranker is not None and result.success:
            result = self.post_ranker.execute(result)

        # Stamp the execution_time_ms with the pipeline's
        # wall-clock (downstream engine already records
        # its own time; we add a small delta to keep the
        # call transparent).
        # -- We do NOT modify the result; downstream
        # -- execution_time_ms is preserved as-is.
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if elapsed_ms > 0.0:
            # Tag via a *new* result so the original stays
            # frozen. We only update execution_time_ms when
            # the caller has not set it (== 0.0).
            if getattr(result, "execution_time_ms", 0.0) == 0.0:
                from dataclasses import replace
                result = replace(result, execution_time_ms=elapsed_ms)
        return result

    # ---- introspection ---------------------------------------------

    @property
    def engine_count(self) -> int:
        if self._uses_hybrid:
            return len(self._engine.sub_engines)
        return 1

    @property
    def sub_engine_names(self) -> List[str]:
        if self._uses_hybrid:
            return [s.name for s in self._engine.sub_engines]
        return [self.strategy.lower()]

    # ---- private helpers -------------------------------------------

    def _single_engine_kwargs(
        self, extra: Mapping[str, Any]
    ) -> dict:
        """Build the kwargs for a single-engine call.

        For STRUCTURED_ONLY the attribute / binding
        registries are forwarded. For SEMANTIC_ONLY the
        semantic_index is forwarded. For KEYWORD_ONLY no
        registries are forwarded (the keyword engine does
        not consult them).
        """
        kwargs: dict = dict(extra)
        if self.strategy == STRATEGY_STRUCTURED_ONLY:
            if self.attribute_registry is not None:
                kwargs.setdefault(
                    "attribute_registry", self.attribute_registry,
                )
            if self.binding_registry is not None:
                kwargs.setdefault(
                    "binding_registry", self.binding_registry,
                )
            if self.binding_lookup is not None:
                kwargs.setdefault(
                    "binding_lookup", self.binding_lookup,
                )
        return kwargs

    def _build_engine(self) -> tuple:
        """Construct the underlying engine (single or hybrid).

        Returns ``(engine, uses_hybrid)``.
        """
        if self.strategy == STRATEGY_KEYWORD_ONLY:
            return KeywordRetrievalEngine(), False

        if self.strategy == STRATEGY_STRUCTURED_ONLY:
            return StructuredRetrievalEngine(), False

        if self.strategy == STRATEGY_SEMANTIC_ONLY:
            if self.semantic_index is None:
                raise RetrievalPipelineError(
                    "SEMANTIC_ONLY requires semantic_index; got None"
                )
            return SemanticRetrievalEngine(self.semantic_index), False

        # ---- hybrid strategies -----------------------------------
        subs: List[LambdaSubEngine] = []
        subs.append(
            LambdaSubEngine(
                name="keyword",
                runner=KeywordRetrievalEngine().execute,
            )
        )
        subs.append(
            LambdaSubEngine(
                name="structured",
                runner=StructuredRetrievalEngine().execute,
            )
        )
        if self.strategy == STRATEGY_HYBRID_FULL:
            if self.semantic_index is None:
                raise RetrievalPipelineError(
                    "HYBRID_FULL requires semantic_index; got None"
                )
            sem_engine = SemanticRetrievalEngine(self.semantic_index)
            subs.append(
                LambdaSubEngine(
                    name="semantic",
                    runner=sem_engine.execute,
                )
            )

        # For hybrid strategies we want the structured
        # engine to receive its registries. The hybrid
        # engine forwards the same kwargs to every
        # sub-engine; the keyword engine ignores unknown
        # kwargs (or rejects them gracefully).
        # We do not need to wire attribute_registry at
        # construction time -- the pipeline forwards it
        # at execute() time.
        hybrid = HybridRetrievalEngine(
            sub_engines=subs,
            fusion=self.fusion,
            engine_weights=self.engine_weights,
            post_ranker=self.post_ranker,
        )
        return hybrid, True


# ---------------------------------------------------------------------------
# Convenience builder
# ---------------------------------------------------------------------------


def build_default_pipeline(
    *,
    semantic_index: Optional[SemanticIndex] = None,
    post_ranker: Optional[RankingEngine] = None,
    attribute_registry: Optional[Iterable[Any]] = None,
    binding_lookup: Optional[Mapping[str, Sequence[str]]] = None,
) -> RetrievalPipeline:
    """Build a sensible default ``RetrievalPipeline``.

    V1 default strategy: ``HYBRID_AUTO`` (keyword + structured).
    When ``semantic_index`` is supplied, the caller may
    further opt into ``HYBRID_FULL`` by constructing a
    pipeline explicitly with that strategy.
    """
    return RetrievalPipeline(
        strategy=STRATEGY_HYBRID_AUTO,
        post_ranker=post_ranker,
        semantic_index=semantic_index,
        attribute_registry=attribute_registry,
        binding_lookup=binding_lookup,
    )


__all__ = [
    "RetrievalPipeline",
    "RetrievalPipelineError",
    "STRATEGY_KEYWORD_ONLY",
    "STRATEGY_STRUCTURED_ONLY",
    "STRATEGY_SEMANTIC_ONLY",
    "STRATEGY_HYBRID_AUTO",
    "STRATEGY_HYBRID_FULL",
    "STRATEGY_ALLOW_LIST",
    "build_default_pipeline",
]
