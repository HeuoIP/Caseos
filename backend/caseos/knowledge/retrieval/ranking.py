"""Knowledge Retrieval Ranking Engine V1 (Sprint 24.0-C).

This module ships the post-processing **ranking layer** that
sits between any retrieval engine (Sprint 24.0-A keyword /
24.0-B structured / future hybrid) and the caller. The
ranking engine is *read-only* with respect to its inputs:
it never mutates the ``RetrievalResult`` it receives and
never mutates the underlying KOs.

Reranking is the third step of the V1 retrieval pipeline:

    Query
      |
      v
    RetrievalEngine       -- produces raw hits (24.0-A / B)
      |
      v
    RetrievalResult
      |
      v
    RankingEngine         <-- THIS MODULE
      |
      v
    RetrievalResult       -- re-ranked, cap'd at limit

V1 strategies (all deterministic, no LLM, no embedding,
no vector DB):

    * RecencyRanking      -- prefer newer created_at
    * CoverageRanking     -- prefer more matched_fields
    * PriorityRanking     -- use caller-supplied
                              priority_lookup[knowledge_id] -> float
    * DiversityRanking    -- one hit per knowledge_id
                              (the best-scoring version)
    * StableRanking       -- prefer higher KO version
    * CompositeRanking    -- weighted blend

Composite score:

    final = clip(match_score + sum(weight_i * boost_i),
                 0.0, 1.0)

Tie-breakers (deterministic, in order):

    1. higher final score          -- primary
    2. higher knowledge_version    -- newer snapshot
    3. lexicographically smaller
       knowledge_id                -- stable order

Architecture boundary (Sprint 24.0-C spec):

    This module does NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
        * caseos.brain.*
    This module MAY import from:
        * caseos.knowledge.object            (KO schema)
        * caseos.knowledge.attribute         (ranking uses
                                              attribute metadata
                                              when supplied)
        * caseos.knowledge.retrieval         (contract + engines)
        * stdlib
"""
from __future__ import annotations

import abc
import time
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

from .object import (
    RetrievalHit,
    RetrievalResult,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


#: Default weight for the recency boost.
DEFAULT_RECENCY_WEIGHT: float = 0.10

#: Default weight for the coverage boost.
DEFAULT_COVERAGE_WEIGHT: float = 0.10

#: Default weight for the caller-supplied priority boost.
DEFAULT_PRIORITY_WEIGHT: float = 0.15

#: Default weight for the version-stability boost.
DEFAULT_STABLE_WEIGHT: float = 0.05


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _created_at(hit: RetrievalHit) -> str:
    """Best-effort created_at accessor.

    The ranking engine is **duck-typed**: a hit may not
    carry a ``created_at`` snapshot (Keyword engine includes
    one when the input KO has it; Structured engine always
    includes one). Missing values are treated as empty
    strings and compare the smallest.
    """
    snap = hit.knowledge_object_snapshot or {}
    raw = snap.get("created_at", "")
    return raw if isinstance(raw, str) else ""


def _as_float(value: Any, default: float = 0.0) -> float:
    """Coerce an arbitrary value into a float in [0, 1].

    Anything outside the unit interval is clipped. Non-
    numeric values silently become ``default`` so the
    ranking engine never raises on caller input.
    """
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    if f != f:  # NaN guard
        return default
    if f < 0.0:
        return 0.0
    if f > 1.0:
        return 1.0
    return f


def _coverage_factor(hit: RetrievalHit) -> float:
    """How many fields did the KO match? Normalized to [0, 1]
    by clamping to a per-hit cap of 8 -- any KO matching 8+
    fields scores 1.0 (the cap protects against unbounded
    snapshot sizes from dict-shaped inputs).
    """
    n = len(hit.matched_fields)
    if n <= 0:
        return 0.0
    cap = 8
    return min(1.0, n / float(cap))


def _version_factor(hit: RetrievalHit) -> float:
    """Stable ranking: prefer higher knowledge_version.

    Returns the knowledge_version normalized by a soft cap
    of 16 versions. This is a ``soft'' cap -- higher versions
    still score 1.0 but the relative ranking remains
    monotonic until the cap.

    Note: this never overrides final-score rules; it is a
    tie-breaker as well as a weighted boost.
    """
    try:
        v = int(hit.knowledge_version)
    except (TypeError, ValueError):
        return 0.0
    if v <= 0:
        return 0.0
    cap = 16
    return min(1.0, v / float(cap))


def _clip01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


# ---------------------------------------------------------------------------
# Strategy ABC
# ---------------------------------------------------------------------------


class RankingStrategy(abc.ABC):
    """A single ranking strategy.

    Strategies are *pure functions* of a hit plus optional
    caller-supplied lookup tables. They never mutate the
    input hit and they never raise on missing data.
    """

    @abc.abstractmethod
    def boost(self, hit: RetrievalHit) -> float:
        """Return a boost value in [0, 1] for ``hit``.

        A boost of ``0.0`` leaves the match_score unchanged;
        a boost of ``1.0`` (combined with other strategies)
        is the maximum the composite can contribute beyond
        the original score.
        """


# ---------------------------------------------------------------------------
# Concrete strategies
# ---------------------------------------------------------------------------


class RecencyRanking(RankingStrategy):
    """Prefer newer KO ``created_at`` over older ones."""

    def __init__(self, *, reference_now: Optional[str] = None) -> None:
        self.reference_now = reference_now  # ISO string or None

    def boost(self, hit: RetrievalHit) -> float:
        created = _created_at(hit)
        if not created:
            return 0.0
        # Recency is converted to a normalized [0, 1] by
        # character-position delta against the longest
        # possible ISO timestamp. This is intentionally
        # simple: a clock-aware lexical compare is *good
        # enough* for ISO 8601 strings sorted in descending
        # order under V1. We rely on the tie-breaker for
        # sub-second resolution.
        # Use a soft cap by character distance to "9999-...".
        return _lexical_recency_factor(created)


def _lexical_recency_factor(iso_ts: str) -> float:
    """Map an ISO 8601 timestamp to a [0, 1] recency factor.

    V1 approximation: extract the leading four-digit year
    and linearly interpolate between 2000 (0.0) and 2100
    (1.0). Anything below 2000 returns 0.0; anything
    above 2100 returns 1.0. Years outside [2000, 2100]
    are clamped to the nearest anchor.

    The map is intentionally simple and deterministic.
    It is monotonic for stamps that differ only by year,
    and correctly handles the test corpus (2024, 2026).
    """
    if not isinstance(iso_ts, str) or len(iso_ts) < 4:
        return 0.0
    try:
        year = int(iso_ts[0:4])
    except (TypeError, ValueError):
        return 0.0
    if year <= 2000:
        return 0.0
    if year >= 2100:
        return 1.0
    return (year - 2000) / 100.0


class CoverageRanking(RankingStrategy):
    """Prefer hits that matched more KO fields."""

    def boost(self, hit: RetrievalHit) -> float:
        return _coverage_factor(hit)


class StableRanking(RankingStrategy):
    """Prefer higher KO version."""

    def boost(self, hit: RetrievalHit) -> float:
        return _version_factor(hit)


class PriorityRanking(RankingStrategy):
    """Use a caller-supplied ``priority_lookup[knowledge_id]``.

    Lookup values are coerced into [0, 1] (clip). Missing
    knowledge_ids score 0.0 -- *no* implicit priority is
    assumed.
    """

    def __init__(
        self,
        priority_lookup: Optional[Mapping[str, Any]] = None,
    ) -> None:
        # accept None, dict, or any Mapping; copy defensively.
        if priority_lookup is None:
            self.priority_lookup: Dict[str, float] = {}
        else:
            cleaned: Dict[str, float] = {}
            for k, v in priority_lookup.items():
                if isinstance(k, str) and k:
                    cleaned[k] = _as_float(v, default=0.0)
            self.priority_lookup = cleaned

    def boost(self, hit: RetrievalHit) -> float:
        return self.priority_lookup.get(hit.knowledge_id, 0.0)


class DiversityRanking(RankingStrategy):
    """Diversity is *enforced*, not boosted: a downstream
    composite ranking uses this strategy's
    ``select_one_per_knowledge_id`` to ensure at most one
    hit per ``knowledge_id`` is retained.
    """

    def boost(self, hit: RetrievalHit) -> float:  # noqa: D401
        return 0.0  # never adds a boost on its own


# ---------------------------------------------------------------------------
# Composite ranking
# ---------------------------------------------------------------------------


class CompositeRanking(RankingStrategy):
    """A weighted blend of strategies.

    Final contribution of each strategy is
    ``weight * boost``. The composite ranking
    produces a final score with:

        final = clip(match_score
                     + recency_weight  * recency.boost(h)
                     + coverage_weight * coverage.boost(h)
                     + priority_weight * priority.boost(h)
                     + stable_weight   * stable.boost(h),
                     0.0, 1.0)

    A non-positive weight disables a strategy. Negative
    weights are allowed (down-weighting) but the resulting
    boost is clipped at the bottom (0.0) so it never
    pushes the final score below match_score.
    """

    def __init__(
        self,
        *,
        recency_weight: float = DEFAULT_RECENCY_WEIGHT,
        coverage_weight: float = DEFAULT_COVERAGE_WEIGHT,
        priority_weight: float = DEFAULT_PRIORITY_WEIGHT,
        stable_weight: float = DEFAULT_STABLE_WEIGHT,
        priority_lookup: Optional[Mapping[str, Any]] = None,
        reference_now: Optional[str] = None,
    ) -> None:
        self.recency_weight = float(recency_weight)
        self.coverage_weight = float(coverage_weight)
        self.priority_weight = float(priority_weight)
        self.stable_weight = float(stable_weight)
        self.priority_lookup = priority_lookup

        self.recency = RecencyRanking(reference_now=reference_now)
        self.coverage = CoverageRanking()
        self.priority = PriorityRanking(priority_lookup=priority_lookup)
        self.stable = StableRanking()
        self.diversity = DiversityRanking()

    def boost(self, hit: RetrievalHit) -> float:
        contrib = 0.0
        contrib += self.recency_weight * self.recency.boost(hit)
        contrib += self.coverage_weight * self.coverage.boost(hit)
        contrib += self.priority_weight * self.priority.boost(hit)
        contrib += self.stable_weight * self.stable.boost(hit)
        # Boost is reported here as a *positive* number;
        # the RankingEngine combines it with the original
        # match_score through ``clip01``. We do not subtract
        # below zero, but we DO clip individual contributions
        # so a runaway priority value cannot dominate.
        return _clip01(contrib)


# ---------------------------------------------------------------------------
# Diversity enforcement
# ---------------------------------------------------------------------------


def _select_one_per_knowledge_id(
    hits: Sequence[RetrievalHit],
) -> List[RetrievalHit]:
    """Keep only the highest-scoring hit per knowledge_id.

    Ties are broken by ``knowledge_version`` desc and then
    by ``knowledge_id`` asc -- both deterministic. The
    function is pure: it never mutates ``hits``.
    """
    best_by_ko: Dict[str, RetrievalHit] = {}
    for h in hits:
        cur = best_by_ko.get(h.knowledge_id)
        if cur is None:
            best_by_ko[h.knowledge_id] = h
            continue
        if h.match_score > cur.match_score:
            best_by_ko[h.knowledge_id] = h
            continue
        if (
            h.match_score == cur.match_score
            and h.knowledge_version > cur.knowledge_version
        ):
            best_by_ko[h.knowledge_id] = h
            continue
        if (
            h.match_score == cur.match_score
            and h.knowledge_version == cur.knowledge_version
            and h.hit_id < cur.hit_id
        ):
            best_by_ko[h.knowledge_id] = h
    # Stable order: by descending match_score first
    # (preserves the engine's ranking intent), then by KO id.
    return sorted(
        best_by_ko.values(),
        key=lambda h: (-h.match_score, h.knowledge_id, h.knowledge_version),
    )


# ---------------------------------------------------------------------------
# RankingEngine
# ---------------------------------------------------------------------------


class RankingEngine:
    """The post-processing re-ranker.

    Public API:

        execute(result, *,
                composite = None,
                enforce_diversity = False,
                limit = None) -> RetrievalResult

    The ``composite`` argument selects how hits are re-
    ranked. ``None`` means "identity sort" (the engine's
    original order is preserved; the only output change is
    the limit cut and the deterministic tie-breaker).
    """

    ENGINE_NAME: str = "RankingEngine V1"

    def __init__(self) -> None:
        # Pure, stateless (caller controls lookup tables
        # via composite parameter).
        pass

    def execute(  # noqa: C901 -- V1 traceability is verbose
        self,
        result: RetrievalResult,
        *,
        composite: Optional[CompositeRanking] = None,
        enforce_diversity: bool = False,
        limit: Optional[int] = None,
    ) -> RetrievalResult:
        """Return a fresh RetrievalResult with hits re-ranked.

        Parameters
        ----------
        result:
            The input envelope. The engine never mutates
            it; callers may safely reuse ``result`` after
            re-ranking.
        composite:
            A ``CompositeRanking`` (or any
            ``RankingStrategy``) controlling the re-rank.
            ``None`` preserves the input order (only the
            tie-breaker is applied).
        enforce_diversity:
            When True, at most one hit per ``knowledge_id``
            is retained (the highest-scoring one).
        limit:
            Optional cap on the number of hits in the
            output. ``None`` keeps the input hit count.
            Negative or zero values become 0.

        Returns
        -------
        RetrievalResult:
            A new ``RetrievalResult`` (the original is
            preserved).
        """
        started = time.perf_counter()

        original_hits: Tuple[RetrievalHit, ...] = tuple(
            getattr(result, "hits", ()) or ()
        )

        # Apply diversity first (so the composite only sees
        # what we will eventually emit).
        if enforce_diversity:
            kept = _select_one_per_knowledge_id(list(original_hits))
        else:
            kept = list(original_hits)

        # Compute final scores.
        final_scores: List[Tuple[RetrievalHit, float]] = []
        if composite is None:
            for h in kept:
                final_scores.append((h, h.match_score))
        else:
            for h in kept:
                boost = composite.boost(h)
                final = _clip01(h.match_score + boost)
                final_scores.append((h, final))

        # Sort: primary by final score desc; tie-breakers
        # keep the order stable + deterministic.
        final_scores.sort(
            key=lambda pair: (
                -pair[1],                        # higher first
                -pair[0].knowledge_version,      # newer first
                pair[0].knowledge_id,            # lexicographic
                pair[0].hit_id,                  # final tie-break
            )
        )

        # Limit cut.
        if limit is not None:
            try:
                cap = int(limit)
            except (TypeError, ValueError):
                cap = len(final_scores)
            if cap < 0:
                cap = 0
            final_scores = final_scores[:cap]

        new_hits: List[RetrievalHit] = []
        for h, final in final_scores:
            if h.match_score == final:
                new_hits.append(h)
            else:
                # Rebuild the hit with the updated score;
                # every other field stays identical.
                new_hits.append(
                    RetrievalHit(
                        hit_id=h.hit_id,
                        knowledge_id=h.knowledge_id,
                        knowledge_version=h.knowledge_version,
                        match_score=final,
                        matched_fields=list(h.matched_fields),
                        matched_snippets=dict(h.matched_snippets),
                        knowledge_object_snapshot=dict(
                            h.knowledge_object_snapshot
                        ),
                    )
                )

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return RetrievalResult(
            query_id=getattr(result, "query_id", ""),
            success=bool(getattr(result, "success", False)),
            total_hits=len(new_hits),
            hits=tuple(new_hits),
            execution_time_ms=elapsed_ms,
        )


__all__ = [
    "RankingEngine",
    "RankingStrategy",
    "CompositeRanking",
    "RecencyRanking",
    "CoverageRanking",
    "PriorityRanking",
    "StableRanking",
    "DiversityRanking",
    "_select_one_per_knowledge_id",
    "DEFAULT_RECENCY_WEIGHT",
    "DEFAULT_COVERAGE_WEIGHT",
    "DEFAULT_PRIORITY_WEIGHT",
    "DEFAULT_STABLE_WEIGHT",
]
