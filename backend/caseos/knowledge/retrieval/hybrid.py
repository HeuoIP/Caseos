"""Knowledge Retrieval Hybrid Engine V1 (Sprint 24.0-D).

This module ships the **multi-engine fusion layer** that
sits above the keyword and structured engines. A hybrid
run looks like:

    Query
      |
      v
    HybridRetrievalEngine
      |
      +-- sub-engine #1 (e.g. KeywordRetrievalEngine)
      |
      +-- sub-engine #2 (e.g. StructuredRetrievalEngine)
      |
      v
    HitFusionStrategy
      |
      v
    (optional RankingEngine post-pass)
      |
      v
    RetrievalResult

V1 ships four fusion strategies:

    WeightedScoreFusion       -- sum of weighted scores
    ReciprocalRankFusion      -- 1/(k + rank) classic IR
    MaxScoreFusion            -- max across engines
    UnionFusion               -- dedup, scores preserved

All strategies are deterministic, never mutate inputs,
never touch KOs, and never import intelligence / evolution
/ governance / intake / feedback / brain modules.

Architecture boundary (Sprint 24.0-D spec):

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
        * caseos.knowledge.retrieval
        * stdlib
"""
from __future__ import annotations

import abc
import time
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

from .object import (
    DEFAULT_SORT_BY,
    DEFAULT_SORT_ORDER,
    RetrievalHit,
    RetrievalQuery,
    RetrievalResult,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


#: Default RRF constant. ``k=60`` is the value used in
#: the original Cormack / Clarke / Buettcher paper and
#: is the conventional default in modern search stacks.
DEFAULT_RRF_K: int = 60

#: Default weight for WeightedScoreFusion when a caller
#: supplies a weights mapping that omits some engines.
DEFAULT_MISSING_WEIGHT: float = 1.0


# ---------------------------------------------------------------------------
# Sub-engine ABC
# ---------------------------------------------------------------------------


class HybridSubEngine(abc.ABC):
    """Adapter for a retrieval engine that can be plugged
    into the hybrid layer.

    The contract is intentionally minimal:

        * ``name``     -- a stable, non-empty string label
        * ``retrieve`` -- a callable that returns a
                          ``RetrievalResult`` for a given
                          ``RetrievalQuery`` and corpus

    Both ``KeywordRetrievalEngine`` (Sprint 24.0-A) and
    ``StructuredRetrievalEngine`` (Sprint 24.0-B) can be
    wrapped via ``LambdaSubEngine``; future retrieval
    engines plug in identically.

    Sub-engines MUST be **read-only** with respect to the
    query / corpus / KO objects they consume. The hybrid
    layer assumes this and never copies the corpus.
    """

    name: str

    @abc.abstractmethod
    def retrieve(
        self,
        query: RetrievalQuery,
        knowledge_objects: Sequence[Any],
        **kwargs: Any,
    ) -> RetrievalResult:
        """Run this sub-engine and return its RetrievalResult."""
        ...


class LambdaSubEngine(HybridSubEngine):
    """Wrap a plain ``callable`` as a ``HybridSubEngine``.

    This avoids forcing every existing engine to subclass
    ``HybridSubEngine``. The Sprint 24.0-A keyword engine
    and the Sprint 24.0-B structured engine each expose an
    ``execute(query, kos, ...) -> RetrievalResult`` method
    -- this adapter funnels that interface through.
    """

    def __init__(
        self,
        name: str,
        runner: Callable[..., RetrievalResult],
    ) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("LambdaSubEngine.name must be a non-empty string")
        self.name = name
        self._runner = runner

    def retrieve(
        self,
        query: RetrievalQuery,
        knowledge_objects: Sequence[Any],
        **kwargs: Any,
    ) -> RetrievalResult:
        return self._runner(query, knowledge_objects, **kwargs)


# ---------------------------------------------------------------------------
# HitFusionStrategy ABC
# ---------------------------------------------------------------------------


class HitFusionStrategy(abc.ABC):
    """Combine the per-engine hits into a single scored list.

    The strategy receives one ``RetrievalResult`` per sub-
    engine (in declaration order) plus the configured
    ``engine_weights``. It returns a *list of scored hits*
    (the hybrid engine will sort + limit them).

    A "scored hit" is a tuple ``(RetrievalHit, float)``
    where the float is the fused score. The hit's own
    ``match_score`` is NOT mutated by the strategy; the
    hybrid engine decides whether to rebuild the hit.
    """

    @abc.abstractmethod
    def fuse(
        self,
        per_engine_results: Sequence[Tuple[str, RetrievalResult]],
        engine_weights: Mapping[str, float],
    ) -> List[Tuple[RetrievalHit, float]]:
        ...


# ---------------------------------------------------------------------------
# Concrete fusion strategies
# ---------------------------------------------------------------------------


def _hit_key(h: RetrievalHit) -> Tuple[str, int]:
    """Identity for the ``(knowledge_id, version)`` pair."""
    return (h.knowledge_id, int(h.knowledge_version))


class WeightedScoreFusion(HitFusionStrategy):
    """``final = sum(weight_i * engine_i.score)`` per hit.

    Missing engines contribute 0.0. Each hit's score is
    summed across every engine that produced it. The
    output score is clipped to [0, 1] for parity with the
    retrieval contract's unit-interval invariant.
    """

    def __init__(
        self,
        *,
        missing_weight: float = DEFAULT_MISSING_WEIGHT,
        clip: bool = True,
    ) -> None:
        self.missing_weight = float(missing_weight)
        self.clip = bool(clip)

    def fuse(
        self,
        per_engine_results: Sequence[Tuple[str, RetrievalResult]],
        engine_weights: Mapping[str, float],
    ) -> List[Tuple[RetrievalHit, float]]:
        accumulator: Dict[Tuple[str, int], Tuple[RetrievalHit, float]] = {}
        for engine_name, result in per_engine_results:
            weight = float(
                engine_weights.get(engine_name, self.missing_weight)
            )
            for h in result.hits:
                key = _hit_key(h)
                cur_hit, cur_score = accumulator.get(
                    key, (h, 0.0)
                )
                new_score = cur_score + weight * float(h.match_score)
                accumulator[key] = (cur_hit, new_score)
        out: List[Tuple[RetrievalHit, float]] = []
        for hit, score in accumulator.values():
            if self.clip:
                score = max(0.0, min(1.0, score))
            out.append((hit, score))
        return out


class ReciprocalRankFusion(HitFusionStrategy):
    """Classic RRF: ``final = sum(1 / (k + rank_i))`` per hit.

    Rank ``1`` is the top of a sub-engine's hit list; ties
    are broken deterministically by ``(knowledge_id,
    knowledge_version)`` so the rank assignment is stable.
    """

    def __init__(self, *, k: int = DEFAULT_RRF_K) -> None:
        self.k = int(k)
        if self.k < 1:
            raise ValueError("RRF k must be >= 1")

    def fuse(
        self,
        per_engine_results: Sequence[Tuple[str, RetrievalResult]],
        engine_weights: Mapping[str, float],
    ) -> List[Tuple[RetrievalHit, float]]:
        accumulator: Dict[Tuple[str, int], Tuple[RetrievalHit, float, int]] = {}
        for engine_name, result in per_engine_results:
            # Build a deterministic rank order over this
            # sub-engine's hits: by descending match_score,
            # then by descending knowledge_version, then by
            # lexicographic knowledge_id, finally hit_id.
            ordered = sorted(
                result.hits,
                key=lambda h: (
                    -float(h.match_score),
                    -int(h.knowledge_version),
                    h.knowledge_id,
                    h.hit_id,
                ),
            )
            weight = float(engine_weights.get(engine_name, 1.0))
            for rank, h in enumerate(ordered, start=1):
                key = _hit_key(h)
                cur_hit, cur_score, cur_seen = accumulator.get(
                    key, (h, 0.0, 0)
                )
                contribution = weight * (1.0 / float(self.k + rank))
                accumulator[key] = (
                    cur_hit,
                    cur_score + contribution,
                    cur_seen + 1,
                )
        out: List[Tuple[RetrievalHit, float]] = []
        for hit, score, _seen in accumulator.values():
            out.append((hit, float(score)))
        return out


class MaxScoreFusion(HitFusionStrategy):
    """``final = max(engine_i.score)`` per hit.

    Each hit's fused score is the highest match_score any
    sub-engine gave it. Other engines' scores are ignored.
    Useful when callers want a "best-of" surface that is
    robust to one engine being noisy.
    """

    def fuse(
        self,
        per_engine_results: Sequence[Tuple[str, RetrievalResult]],
        engine_weights: Mapping[str, float],
    ) -> List[Tuple[RetrievalHit, float]]:
        accumulator: Dict[Tuple[str, int], Tuple[RetrievalHit, float]] = {}
        for _engine_name, result in per_engine_results:
            for h in result.hits:
                key = _hit_key(h)
                cur_hit, cur_score = accumulator.get(key, (h, 0.0))
                if float(h.match_score) > cur_score:
                    accumulator[key] = (h, float(h.match_score))
        return list(accumulator.values())


class UnionFusion(HitFusionStrategy):
    """Dedup by ``(knowledge_id, version)`` and keep the
    FIRST engine's score for that hit (engine order is
    the declaration order in ``per_engine_results``).
    """

    def fuse(
        self,
        per_engine_results: Sequence[Tuple[str, RetrievalResult]],
        engine_weights: Mapping[str, float],
    ) -> List[Tuple[RetrievalHit, float]]:
        out: List[Tuple[RetrievalHit, float]] = []
        seen: set = set()
        for _engine_name, result in per_engine_results:
            for h in result.hits:
                key = _hit_key(h)
                if key in seen:
                    continue
                seen.add(key)
                out.append((h, float(h.match_score)))
        return out


# ---------------------------------------------------------------------------
# Helper: rebuild a hit with a new score
# ---------------------------------------------------------------------------


def _rebuild_hit_with_score(
    h: RetrievalHit, new_score: float
) -> RetrievalHit:
    """Return a new RetrievalHit with ``match_score`` replaced."""
    return RetrievalHit(
        hit_id=h.hit_id,
        knowledge_id=h.knowledge_id,
        knowledge_version=h.knowledge_version,
        match_score=float(new_score),
        matched_fields=list(h.matched_fields),
        matched_snippets=dict(h.matched_snippets),
        knowledge_object_snapshot=dict(
            h.knowledge_object_snapshot
        ),
    )


# ---------------------------------------------------------------------------
# HybridRetrievalEngine
# ---------------------------------------------------------------------------


class HybridRetrievalEngine:
    """Run several sub-engines in parallel and fuse the
    results into a single ``RetrievalResult``.

    The engine is **stateless** and **deterministic**:

        * The order of ``sub_engines`` is preserved when
          scoring (UnionFusion, RRF rank tie-break).
        * KOs are never mutated.
        * Sub-engines are called exactly once per query.

    Sub-engines are wrapped via ``LambdaSubEngine`` when
    raw callables are passed. ``KeywordRetrievalEngine``
    and ``StructuredRetrievalEngine`` expose the right
    ``execute(query, kos, ...)`` signature so they plug
    in directly.
    """

    ENGINE_NAME: str = "HybridRetrievalEngine V1"

    def __init__(
        self,
        sub_engines: Sequence[HybridSubEngine],
        fusion: Optional[HitFusionStrategy] = None,
        *,
        engine_weights: Optional[Mapping[str, float]] = None,
        post_ranker: Optional[Any] = None,
    ) -> None:
        if not sub_engines:
            raise ValueError(
                "HybridRetrievalEngine requires at least one sub-engine"
            )
        seen_names: set = set()
        for s in sub_engines:
            if not isinstance(s, HybridSubEngine):
                raise TypeError(
                    "sub_engines entries must be HybridSubEngine "
                    "instances; got " + type(s).__name__
                )
            if not isinstance(s.name, str) or not s.name.strip():
                raise ValueError(
                    "Each sub-engine must have a non-empty name"
                )
            if s.name in seen_names:
                raise ValueError(
                    "Duplicate sub-engine name: " + repr(s.name)
                )
            seen_names.add(s.name)
        self.sub_engines: List[HybridSubEngine] = list(sub_engines)
        self.fusion: HitFusionStrategy = (
            fusion if fusion is not None else WeightedScoreFusion()
        )
        weights: Dict[str, float] = {}
        if engine_weights is not None:
            for k, v in engine_weights.items():
                if isinstance(k, str) and k:
                    weights[k] = float(v)
        self.engine_weights: Dict[str, float] = weights
        self.post_ranker = post_ranker  # duck-typed RankingEngine

    # ---- public ----------------------------------------------------

    def execute(
        self,
        query: RetrievalQuery,
        knowledge_objects: Sequence[Any],
        **sub_engine_kwargs: Any,
    ) -> RetrievalResult:
        """Run every sub-engine, fuse, optional rank, cut to limit.

        Parameters
        ----------
        query:
            The contract-layer query. The same query is
            passed to every sub-engine.
        knowledge_objects:
            The corpus. Sub-engines may read it; they
            MUST NOT mutate it.
        sub_engine_kwargs:
            Optional keyword arguments forwarded to every
            sub-engine's ``retrieve`` call. Useful for
            passing ``attribute_registry`` etc.

        Returns
        -------
        RetrievalResult:
            A frozen envelope whose ``hits`` are the fused
            + sorted + capped result list. ``success`` is
            True iff at least one sub-engine ran cleanly.
        """
        started = time.perf_counter()

        per_engine: List[Tuple[str, RetrievalResult]] = []
        any_success: bool = False
        for sub in self.sub_engines:
            try:
                result = sub.retrieve(
                    query, knowledge_objects, **sub_engine_kwargs
                )
            except Exception:
                # Sub-engines MUST NOT raise, but if one
                # does we degrade gracefully: skip it.
                continue
            per_engine.append((sub.name, result))
            if getattr(result, "success", False):
                any_success = True

        if not per_engine:
            # All sub-engines failed -> return a 0-hit
            # failure result without fusing anything.
            elapsed = (time.perf_counter() - started) * 1000.0
            return RetrievalResult(
                query_id=getattr(query, "query_id", ""),
                success=False,
                total_hits=0,
                hits=(),
                execution_time_ms=elapsed,
            )

        fused = self.fusion.fuse(per_engine, self.engine_weights)

        # Apply caller-controlled ranking post-pass.
        if self.post_ranker is not None:
            fused = self._apply_post_ranker(fused, query)

        # Sort: by fused score desc; tie-breakers match
        # the ranking engine for cross-engine consistency.
        fused.sort(
            key=lambda pair: (
                -float(pair[1]),
                -int(pair[0].knowledge_version),
                pair[0].knowledge_id,
                pair[0].hit_id,
            )
        )

        # Cut to limit.
        limit: int = int(getattr(query, "limit", 20) or 20)
        if limit < 1:
            limit = 1
        fused = fused[:limit]

        # Rebuild hits with their fused scores.
        rebuilt: List[RetrievalHit] = []
        for hit, score in fused:
            if float(score) == float(hit.match_score):
                rebuilt.append(hit)
            else:
                rebuilt.append(_rebuild_hit_with_score(hit, score))

        elapsed = (time.perf_counter() - started) * 1000.0
        return RetrievalResult(
            query_id=getattr(query, "query_id", ""),
            success=any_success,
            total_hits=len(rebuilt),
            hits=tuple(rebuilt),
            execution_time_ms=elapsed,
        )

    # ---- private helpers ------------------------------------------

    def _apply_post_ranker(
        self,
        fused: List[Tuple[RetrievalHit, float]],
        query: RetrievalQuery,
    ) -> List[Tuple[RetrievalHit, float]]:
        """Apply a duck-typed ranking engine.

        The post_ranker exposes ``execute(result, ...) -> RetrievalResult``.
        We pass a synthetic result with the fused hits, then
        pull the resulting scored list back into a
        ``List[Tuple[RetrievalHit, float]]``.
        """
        synthetic = RetrievalResult(
            query_id=getattr(query, "query_id", ""),
            success=True,
            total_hits=len(fused),
            hits=tuple(h for h, _ in fused),
        )
        reranked = self.post_ranker.execute(synthetic)
        reranked_hits = list(getattr(reranked, "hits", ()) or ())
        # Re-zip by (knowledge_id, version). The post-
        # ranker may have reordered; we trust its order.
        original_scores: Dict[Tuple[str, int], float] = {
            _hit_key(h): s for h, s in fused
        }
        out: List[Tuple[RetrievalHit, float]] = []
        for h in reranked_hits:
            new_score = float(h.match_score)
            original = original_scores.get(_hit_key(h), new_score)
            # The post-ranker may have updated the score
            # itself; we honor its value over the original
            # fused score.
            out.append((h, new_score if new_score != original else new_score))
        return out


# ---------------------------------------------------------------------------
# Convenience: build a hybrid engine from existing V1 engines
# ---------------------------------------------------------------------------


def build_keyword_structured_hybrid(
    keyword_engine: Any,
    structured_engine: Any,
    *,
    fusion: Optional[HitFusionStrategy] = None,
    engine_weights: Optional[Mapping[str, float]] = None,
    post_ranker: Optional[Any] = None,
) -> HybridRetrievalEngine:
    """Build a hybrid engine that wires the Sprint 24.0-A
    keyword engine and the Sprint 24.0-B structured engine
    through a configurable fusion strategy.

    Parameters
    ----------
    keyword_engine, structured_engine:
        Existing engine instances with
        ``execute(query, kos, ...) -> RetrievalResult``.
    fusion:
        Optional ``HitFusionStrategy``. ``None`` defaults
        to ``WeightedScoreFusion()``.
    engine_weights:
        Optional ``{"keyword": float, "structured": float}``
        mapping. Missing keys fall back to the fusion
        strategy's default.
    post_ranker:
        Optional ranking engine (``RankingEngine`` from
        Sprint 24.0-C) for a re-rank post-pass.
    """
    subs: List[HybridSubEngine] = [
        LambdaSubEngine(
            name="keyword",
            runner=keyword_engine.execute,
        ),
        LambdaSubEngine(
            name="structured",
            runner=structured_engine.execute,
        ),
    ]
    return HybridRetrievalEngine(
        sub_engines=subs,
        fusion=fusion,
        engine_weights=engine_weights,
        post_ranker=post_ranker,
    )


__all__ = [
    "HybridRetrievalEngine",
    "HybridSubEngine",
    "LambdaSubEngine",
    "HitFusionStrategy",
    "WeightedScoreFusion",
    "ReciprocalRankFusion",
    "MaxScoreFusion",
    "UnionFusion",
    "build_keyword_structured_hybrid",
    "DEFAULT_RRF_K",
    "DEFAULT_MISSING_WEIGHT",
]
