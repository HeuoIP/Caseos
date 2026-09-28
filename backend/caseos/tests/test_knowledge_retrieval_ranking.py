"""Tests for Knowledge Retrieval Ranking Engine V1 (Sprint 24.0-C).

Coverage:

    * Strategy primitives (Recency / Coverage / Priority /
      Stable / Diversity)
    * CompositeRanking weight blending
    * RankingEngine:
        - identity re-rank
        - composite re-rank
        - enforce_diversity
        - limit cut
        - tie-breakers (deterministic order)
        - input RetrievalResult is NOT mutated
        - input KOs are NOT mutated
    * AST architecture boundary
        The ranking engine does NOT import from:
            * caseos.intelligence.*
            * caseos.knowledge.evolution
            * caseos.knowledge.governance
            * caseos.knowledge.intake
            * caseos.knowledge.feedback
            * caseos.brain.*

Architecture boundary (Sprint 24.0-C spec):

    These tests do NOT import from forbidden modules.
    These tests MAY import from:
        * caseos.knowledge.object
        * caseos.knowledge.attribute
        * caseos.knowledge.retrieval
        * stdlib
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from caseos.knowledge.retrieval.object import (  # noqa: E402
    RetrievalHit,
    RetrievalResult,
)
from caseos.knowledge.retrieval.ranking import (  # noqa: E402
    DEFAULT_COVERAGE_WEIGHT,
    DEFAULT_PRIORITY_WEIGHT,
    DEFAULT_RECENCY_WEIGHT,
    DEFAULT_STABLE_WEIGHT,
    CompositeRanking,
    CoverageRanking,
    DiversityRanking,
    PriorityRanking,
    RankingEngine,
    RankingStrategy,
    RecencyRanking,
    StableRanking,
    _as_float,
    _coverage_factor,
    _select_one_per_knowledge_id,
    _version_factor,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _hit(
    knowledge_id: str,
    *,
    version: int = 1,
    score: float = 0.5,
    matched_fields=None,
    created_at: str = "2026-01-01T00:00:00Z",
) -> RetrievalHit:
    return RetrievalHit(
        knowledge_id=knowledge_id,
        knowledge_version=version,
        match_score=score,
        matched_fields=list(matched_fields or []),
        matched_snippets={},
        knowledge_object_snapshot={"created_at": created_at},
    )


def _result_with(hits) -> RetrievalResult:
    return RetrievalResult(
        query_id="q_test",
        success=True,
        total_hits=len(hits),
        hits=tuple(hits),
        execution_time_ms=0.0,
    )


# ---------------------------------------------------------------------------
# 1. Helper / strategy tests
# ---------------------------------------------------------------------------


class TestFloatCoercion:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (0.5, 0.5),
            (0.0, 0.0),
            (1.0, 1.0),
            (1.5, 1.0),
            (-0.1, 0.0),
            ("0.7", 0.7),
            (1, 1.0),
            (None, 0.0),
            ("abc", 0.0),
            (float("nan"), 0.0),
        ],
    )
    def test_as_float(self, value, expected) -> None:
        assert _as_float(value) == expected


class TestCoverageFactor:
    def test_empty(self) -> None:
        assert _coverage_factor(_hit("ko_a", matched_fields=[])) == 0.0

    def test_clamped_at_cap(self) -> None:
        # 16 fields -> clamped to 1.0
        fields = [f"f{i}" for i in range(16)]
        assert _coverage_factor(_hit("ko_a", matched_fields=fields)) == 1.0

    def test_partial(self) -> None:
        assert _coverage_factor(_hit("ko_a", matched_fields=["a", "b"])) > 0.0
        assert _coverage_factor(_hit("ko_a", matched_fields=["a", "b"])) < 1.0


class TestVersionFactor:
    def test_zero(self) -> None:
        assert _version_factor(_hit("ko_a", version=0)) == 0.0

    def test_one(self) -> None:
        assert _version_factor(_hit("ko_a", version=1)) > 0.0

    def test_clamped_at_cap(self) -> None:
        assert _version_factor(_hit("ko_a", version=999)) == 1.0

    def test_monotonic(self) -> None:
        a = _version_factor(_hit("ko_a", version=2))
        b = _version_factor(_hit("ko_a", version=4))
        assert a < b


# ---------------------------------------------------------------------------
# 2. Strategy tests
# ---------------------------------------------------------------------------


class TestRecencyRanking:
    def test_empty_snapshot_returns_zero(self) -> None:
        h = RetrievalHit(knowledge_id="ko_a")
        assert RecencyRanking().boost(h) == 0.0

    def test_newer_timestamp_higher(self) -> None:
        old = _hit("ko_a", created_at="2024-01-01T00:00:00Z")
        new = _hit("ko_a", created_at="2026-09-28T00:00:00Z")
        r = RecencyRanking()
        assert r.boost(new) > r.boost(old)

    def test_pre_1970_returns_zero(self) -> None:
        ancient = _hit("ko_a", created_at="1900-01-01T00:00:00Z")
        assert RecencyRanking().boost(ancient) == 0.0


class TestCoverageRanking:
    def test_more_fields_higher(self) -> None:
        small = _hit("ko_a", matched_fields=["title"])
        big = _hit("ko_a", matched_fields=["title", "theme", "style"])
        assert CoverageRanking().boost(big) > CoverageRanking().boost(small)


class TestStableRanking:
    def test_higher_version_higher_boost(self) -> None:
        a = StableRanking().boost(_hit("ko_a", version=1))
        b = StableRanking().boost(_hit("ko_a", version=3))
        assert b > a


class TestPriorityRanking:
    def test_unknown_ko_id_is_zero(self) -> None:
        h = _hit("ko_unknown")
        assert PriorityRanking({"ko_x": 1.0}).boost(h) == 0.0

    def test_known_ko_id_with_value(self) -> None:
        h = _hit("ko_x")
        assert PriorityRanking({"ko_x": 0.8}).boost(h) == 0.8

    def test_clip_value(self) -> None:
        h = _hit("ko_x")
        assert PriorityRanking({"ko_x": 99}).boost(h) == 1.0
        assert PriorityRanking({"ko_x": -1}).boost(h) == 0.0

    def test_none_lookup(self) -> None:
        h = _hit("ko_x")
        assert PriorityRanking(None).boost(h) == 0.0

    def test_ignores_bad_values(self) -> None:
        h = _hit("ko_x")
        # 'abc' is unparseable -> coerced to 0.0
        assert PriorityRanking({"ko_x": "abc"}).boost(h) == 0.0


# ---------------------------------------------------------------------------
# 3. Diversity selection
# ---------------------------------------------------------------------------


class TestDiversitySelection:
    def test_keeps_highest_score(self) -> None:
        a1 = _hit("ko_x", version=1, score=0.4)
        a2 = _hit("ko_x", version=2, score=0.7)
        b = _hit("ko_y", version=1, score=0.5)
        kept = _select_one_per_knowledge_id([a1, a2, b])
        kept_ids = [h.knowledge_id for h in kept]
        assert sorted(kept_ids) == ["ko_x", "ko_y"]
        picked_x = next(h for h in kept if h.knowledge_id == "ko_x")
        assert picked_x.knowledge_version == 2
        assert picked_x.match_score == 0.7

    def test_tie_break_by_version_then_hit_id(self) -> None:
        a1 = _hit("ko_x", version=2, score=0.5)
        a2 = _hit("ko_x", version=1, score=0.5)
        kept = _select_one_per_knowledge_id([a1, a2])
        assert len(kept) == 1
        # Same score; higher version wins.
        assert kept[0].knowledge_version == 2

    def test_empty_input(self) -> None:
        assert _select_one_per_knowledge_id([]) == []


# ---------------------------------------------------------------------------
# 4. Composite ranking
# ---------------------------------------------------------------------------


class TestCompositeRanking:
    def test_zero_weights_contribute_nothing(self) -> None:
        h = _hit("ko_a", version=1, score=0.5)
        c = CompositeRanking(
            recency_weight=0.0,
            coverage_weight=0.0,
            priority_weight=0.0,
            stable_weight=0.0,
        )
        assert c.boost(h) == 0.0

    def test_max_priority_with_zero_weights_yields_zero_boost(self) -> None:
        h = _hit("ko_a", version=1, score=0.5)
        c = CompositeRanking(
            recency_weight=0.0,
            coverage_weight=0.0,
            priority_weight=0.0,
            stable_weight=0.0,
            priority_lookup={"ko_a": 1.0},
        )
        assert c.boost(h) == 0.0

    def test_full_weights_at_max_signals(self) -> None:
        h = _hit(
            "ko_a",
            version=999,    # stable = 1.0
            score=0.5,
            matched_fields=[f"f{i}" for i in range(99)],   # coverage = 1.0
            created_at="9999-12-31T23:59:59Z",             # recency = 1.0
        )
        c = CompositeRanking(
            recency_weight=1.0,
            coverage_weight=1.0,
            priority_weight=1.0,
            stable_weight=1.0,
            priority_lookup={"ko_a": 1.0},
        )
        # 4*1.0 = 4.0 -> clipped to 1.0 at boost() boundary.
        assert c.boost(h) == 1.0

    def test_negative_weight_clipped(self) -> None:
        h = _hit("ko_a", version=1, score=0.5)
        c = CompositeRanking(stable_weight=-10.0)
        # Negative weight × 1.0 boost = -10.0 -> clipped to 0.
        assert c.boost(h) == 0.0

    def test_partial_weights_blend(self) -> None:
        h = _hit(
            "ko_a",
            version=4,
            score=0.5,
            matched_fields=["a", "b", "c", "d"],
            created_at="2026-09-28T00:00:00Z",
        )
        c = CompositeRanking(
            recency_weight=0.1,
            coverage_weight=0.2,
            priority_weight=0.3,
            stable_weight=0.0,
            priority_lookup={"ko_a": 0.5},
        )
        boost = c.boost(h)
        # Some signal > 0 but < 1.0.
        assert boost > 0.0
        assert boost <= 1.0

    def test_default_weights(self) -> None:
        assert DEFAULT_RECENCY_WEIGHT == 0.10
        assert DEFAULT_COVERAGE_WEIGHT == 0.10
        assert DEFAULT_PRIORITY_WEIGHT == 0.15
        assert DEFAULT_STABLE_WEIGHT == 0.05


# ---------------------------------------------------------------------------
# 5. RankingEngine tests
# ---------------------------------------------------------------------------


class TestRankingEngine:
    def test_engine_name(self) -> None:
        assert RankingEngine.ENGINE_NAME == "RankingEngine V1"

    def test_engine_is_strategy_agnostic(self) -> None:
        # RankingEngine is not a RankingStrategy itself;
        # it composes one.
        assert not issubclass(RankingEngine, RankingStrategy)

    def test_identity_sort_when_no_composite(self) -> None:
        h1 = _hit("ko_a", score=0.5)
        h2 = _hit("ko_b", score=0.3)
        out = RankingEngine().execute(
            _result_with([h1, h2]), composite=None
        )
        assert [h.knowledge_id for h in out.hits] == ["ko_a", "ko_b"]
        # Identity: scores unchanged.
        assert out.hits[0].match_score == 0.5
        assert out.hits[1].match_score == 0.3

    def test_composite_re_orders_by_score(self) -> None:
        h1 = _hit("ko_a", score=0.2)
        h2 = _hit("ko_b", score=0.9)
        out = RankingEngine().execute(
            _result_with([h1, h2]),
            composite=CompositeRanking(
                recency_weight=0.0,
                coverage_weight=0.0,
                priority_weight=0.0,
                stable_weight=0.0,
            ),
        )
        # No boost should keep their order based on score
        # desc.
        assert [h.knowledge_id for h in out.hits] == ["ko_b", "ko_a"]

    def test_priority_lookup_overrides_score(self) -> None:
        # ko_a has higher raw score but lower priority.
        h1 = _hit("ko_a", score=0.9)
        h2 = _hit("ko_b", score=0.5)
        out = RankingEngine().execute(
            _result_with([h1, h2]),
            composite=CompositeRanking(
                recency_weight=0.0,
                coverage_weight=0.0,
                priority_weight=1.0,
                stable_weight=0.0,
                priority_lookup={"ko_b": 1.0, "ko_a": 0.0},
            ),
        )
        # ko_b: 0.5 + 1.0*1.0 = 1.5 -> clipped to 1.0
        # ko_a: 0.9 + 1.0*0.0 = 0.9
        # ko_b is now first.
        assert out.hits[0].knowledge_id == "ko_b"
        assert out.hits[0].match_score == 1.0
        assert out.hits[1].knowledge_id == "ko_a"

    def test_enforce_diversity_caps_one_per_ko(self) -> None:
        h_old = _hit("ko_x", version=1, score=0.4)
        h_new = _hit("ko_x", version=3, score=0.6)
        h_y = _hit("ko_y", version=1, score=0.5)
        out = RankingEngine().execute(
            _result_with([h_old, h_new, h_y]),
            composite=None,
            enforce_diversity=True,
        )
        # ko_y + ko_x[v=3] only.
        ids = [(h.knowledge_id, h.knowledge_version) for h in out.hits]
        assert ("ko_y", 1) in ids
        assert ("ko_x", 3) in ids
        assert ("ko_x", 1) not in ids
        assert out.total_hits == 2

    def test_limit_cuts_output(self) -> None:
        hits = [_hit(f"ko_{i}", score=0.5) for i in range(10)]
        out = RankingEngine().execute(
            _result_with(hits), composite=None, limit=3
        )
        assert out.total_hits == 3

    def test_limit_zero_returns_empty(self) -> None:
        hits = [_hit(f"ko_{i}", score=0.5) for i in range(3)]
        out = RankingEngine().execute(
            _result_with(hits), composite=None, limit=0
        )
        assert out.total_hits == 0
        assert out.hits == ()

    def test_negative_limit_becomes_zero(self) -> None:
        hits = [_hit(f"ko_{i}", score=0.5) for i in range(3)]
        out = RankingEngine().execute(
            _result_with(hits), composite=None, limit=-5
        )
        assert out.total_hits == 0

    def test_tie_breaker_by_version_desc(self) -> None:
        # Two hits with the same score -> higher version
        # wins (tie-breaker).
        a = _hit("ko_x", version=1, score=0.5)
        b = _hit("ko_x", version=5, score=0.5)
        out = RankingEngine().execute(
            _result_with([a, b]), composite=None
        )
        assert out.hits[0].knowledge_version == 5

    def test_tie_breaker_by_knowledge_id_lexicographic(self) -> None:
        # Two distinct KOs, same score, same version 1 ->
        # lexicographic KO id wins.
        a = _hit("ko_z", version=1, score=0.5)
        b = _hit("ko_a", version=1, score=0.5)
        out = RankingEngine().execute(
            _result_with([a, b]), composite=None
        )
        assert out.hits[0].knowledge_id == "ko_a"

    def test_diversity_tie_breaker_uses_hit_id(self) -> None:
        # Two identical hits except for hit_id; both keep
        # their own when overlap is impossible.
        hits = [
            _hit("ko_x", score=0.5),
            _hit("ko_y", score=0.5),
        ]
        out = RankingEngine().execute(
            _result_with(hits), composite=None, enforce_diversity=True
        )
        assert out.total_hits == 2

    def test_input_result_is_not_mutated(self) -> None:
        h1 = _hit("ko_a", score=0.3)
        h2 = _hit("ko_b", score=0.7)
        before_ids = [h1.hit_id, h2.hit_id]
        before_scores = [h1.match_score, h2.match_score]
        r = _result_with([h1, h2])
        result_id_before = id(r)
        out = RankingEngine().execute(
            r,
            composite=CompositeRanking(priority_weight=1.0,
                                      priority_lookup={"ko_b": 1.0}),
            enforce_diversity=True,
        )
        assert id(r) == result_id_before
        # The *frozen* dataclass objects inside r are the
        # same; their scores are immutable.
        assert [h.hit_id for h in r.hits] == before_ids
        assert [h.match_score for h in r.hits] == before_scores
        # Output is a different object (new RetrievalResult).
        assert out is not r
        # But the output is *also* frozen.
        assert out.total_hits in (1, 2)

    def test_hits_in_output_are_new_objects_when_score_changed(
        self,
    ) -> None:
        h1 = _hit("ko_a", score=0.3)
        h2 = _hit("ko_b", score=0.7)
        out = RankingEngine().execute(
            _result_with([h1, h2]),
            composite=CompositeRanking(priority_weight=1.0,
                                      priority_lookup={"ko_b": 1.0}),
        )
        # ko_b's score was bumped to 1.0; the output hit
        # is a freshly-built RetrievalHit with the new score.
        b_out = next(h for h in out.hits if h.knowledge_id == "ko_b")
        assert b_out.match_score == 1.0
        # Original h2 *unchanged*.
        assert h2.match_score == 0.7

    def test_composite_via_individual_strategy(self) -> None:
        # Caller may use a bare RankingStrategy (not the
        # composite wrapper) -- boost() must still be
        # called per hit.
        class AlwaysOne(RankingStrategy):
            def boost(self, hit):
                return 1.0

        h1 = _hit("ko_a", score=0.4)
        out = RankingEngine().execute(
            _result_with([h1]), composite=AlwaysOne()
        )
        # 0.4 + 1.0 -> 1.0 after clip
        assert out.hits[0].match_score == 1.0

    def test_limit_default_is_input_size(self) -> None:
        hits = [_hit(f"ko_{i}", score=0.5) for i in range(5)]
        out = RankingEngine().execute(
            _result_with(hits), composite=None
        )
        assert out.total_hits == 5

    def test_execution_time_ms_recorded(self) -> None:
        hits = [_hit("ko_a", score=0.5)]
        out = RankingEngine().execute(_result_with(hits))
        assert out.execution_time_ms >= 0.0

    def test_total_hits_matches_len(self) -> None:
        hits = [_hit(f"ko_{i}", score=0.5) for i in range(3)]
        out = RankingEngine().execute(
            _result_with(hits), composite=None, limit=2
        )
        assert out.total_hits == 2
        assert out.total_hits == len(out.hits)

    def test_query_id_preserved(self) -> None:
        hits = [_hit("ko_a", score=0.5)]
        r = RetrievalResult(
            query_id="q_unique_42", success=True, total_hits=1, hits=tuple(hits)
        )
        out = RankingEngine().execute(r)
        assert out.query_id == "q_unique_42"

    def test_success_flag_preserved(self) -> None:
        h = _hit("ko_a", score=0.5)
        r = RetrievalResult(query_id="q", success=False, total_hits=1, hits=(h,))
        out = RankingEngine().execute(r)
        assert out.success is False


# ---------------------------------------------------------------------------
# 6. End-to-end with the keyword engine
# ---------------------------------------------------------------------------


class TestRankerEndToEnd:
    """Smoke test: feed the keyword engine into the ranking engine."""

    def test_ranker_can_consume_keyword_engine_output(self) -> None:
        from caseos.knowledge.object.object import KnowledgeObject
        from caseos.knowledge.retrieval.engine import KeywordRetrievalEngine
        from caseos.knowledge.retrieval.object import RetrievalQuery

        kos = [
            KnowledgeObject(
                knowledge_id=f"ko_{i}",
                version=1,
                title=f"forest kindergarten {i}",
                description="forest outdoor design",
                category="kindergarten",
                project_type="kindergarten",
                site_type="outdoor",
                location_type="urban",
                space_size="medium",
                theme="forest",
                style="natural",
                color_system="green",
                interaction_type="exploration",
                function_tags=["forest"],
                created_at=("2024-01-01T00:00:00Z" if i % 2 == 0 else "2026-09-28T00:00:00Z"),
                updated_at="2026-01-01T00:00:00Z",
            )
            for i in range(5)
        ]
        kr = KeywordRetrievalEngine()
        raw = kr.execute(
            RetrievalQuery(
                query_text="forest kindergarten",
                sort_by="knowledge_id",
                sort_order="asc",
                limit=5,
            ),
            kos,
        )
        # Re-rank with default composite.
        rr = RankingEngine().execute(raw, composite=CompositeRanking())
        assert rr.success is True
        assert rr.total_hits == 5


# ---------------------------------------------------------------------------
# 7. AST architecture boundary
# ---------------------------------------------------------------------------


class TestRankingArchitectureBoundary:
    FORBIDDEN_SUBSTRINGS = (
        "caseos.intelligence",
        "caseos.knowledge.evolution",
        "caseos.knowledge.governance",
        "caseos.knowledge.intake",
        "caseos.knowledge.feedback",
        "caseos.brain",
    )

    def _collect_imports(self, source: str) -> list[str]:
        if source and source[0] == "\ufeff":
            source = source[1:]
        tree = ast.parse(source)
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    if module:
                        imports.append(module + "." + alias.name)
        return imports

    def test_ranking_engine_has_no_forbidden_imports(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "retrieval"
            / "ranking.py"
        )
        source = path.read_text(encoding="utf-8-sig")
        imports = self._collect_imports(source)
        offenders = [
            imp for imp in imports
            if any(f in imp for f in self.FORBIDDEN_SUBSTRINGS)
        ]
        assert offenders == [], (
            "Forbidden architecture boundary import: " + repr(offenders)
        )
