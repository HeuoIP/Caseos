"""Tests for Knowledge Retrieval Hybrid Engine V1 (Sprint 24.0-D).

Coverage:

    * HybridSubEngine + LambdaSubEngine adapter
    * WeightedScoreFusion / RRF / MaxScoreFusion / UnionFusion
    * HybridRetrievalEngine:
        - single sub-engine short-circuit
        - multi-engine fusion
        - failure isolation (a sub-engine that raises
          does not poison the others)
        - post-ranking pass (24.0-C integration)
        - limit cut
        - input KOs and input sub-results are NOT mutated
        - deterministic tie-breakers
    * Convenience builder
        ``build_keyword_structured_hybrid``
    * AST architecture boundary
        The hybrid engine does NOT import from:
            * caseos.intelligence.*
            * caseos.knowledge.evolution
            * caseos.knowledge.governance
            * caseos.knowledge.intake
            * caseos.knowledge.feedback
            * caseos.brain.*

Architecture boundary (Sprint 24.0-D spec):

    These tests do NOT import forbidden modules.
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

from caseos.knowledge.object.object import KnowledgeObject  # noqa: E402

from caseos.knowledge.retrieval.engine import KeywordRetrievalEngine  # noqa: E402
from caseos.knowledge.retrieval.hybrid import (  # noqa: E402
    DEFAULT_MISSING_WEIGHT,
    DEFAULT_RRF_K,
    HitFusionStrategy,
    HybridRetrievalEngine,
    HybridSubEngine,
    LambdaSubEngine,
    MaxScoreFusion,
    ReciprocalRankFusion,
    UnionFusion,
    WeightedScoreFusion,
    _hit_key,
    build_keyword_structured_hybrid,
)
from caseos.knowledge.retrieval.object import (  # noqa: E402
    RetrievalHit,
    RetrievalQuery,
    RetrievalResult,
)
from caseos.knowledge.retrieval.ranking import RankingEngine  # noqa: E402
from caseos.knowledge.retrieval.structured import (  # noqa: E402
    StructuredRetrievalEngine,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ko(
    knowledge_id: str,
    *,
    title: str = "",
    theme: str = "",
    style: str = "",
    category: str = "kindergarten",
    project_type: str = "kindergarten",
    site_type: str = "outdoor",
    location_type: str = "urban",
    space_size: str = "medium",
    color_system: str = "green",
    interaction_type: str = "exploration",
    function_tags=None,
    version: int = 1,
    created_at: str = "2026-01-01T00:00:00Z",
    updated_at: str = "2026-01-01T00:00:00Z",
    source: str = "human",
    description: str = "",
    image_refs=None,
    document_refs=None,
) -> KnowledgeObject:
    return KnowledgeObject(
        knowledge_id=knowledge_id,
        version=version,
        title=title or knowledge_id,
        description=description,
        category=category,
        project_type=project_type,
        site_type=site_type,
        location_type=location_type,
        space_size=space_size,
        theme=theme,
        style=style,
        color_system=color_system,
        interaction_type=interaction_type,
        function_tags=list(function_tags or []),
        image_refs=list(image_refs or []),
        document_refs=list(document_refs or []),
        created_at=created_at,
        updated_at=updated_at,
        source=source,
    )


@pytest.fixture
def three_kos():
    return [
        _ko("ko_forest_v1", title="Forest Kindergarten",
            theme="forest", style="natural", description="forest outdoor"),
        _ko("ko_ocean_v1", title="Ocean Kindergarten",
            theme="ocean", style="modern", description="ocean indoor"),
        _ko("ko_park_v1", title="City Park",
            theme="park", style="rustic", description="city park"),
    ]


@pytest.fixture
def attribute_registry():
    return [
        {"attribute_id": "theme", "name": "theme"},
        {"attribute_id": "style", "name": "style"},
    ]


def _hit(knowledge_id: str, *, version: int = 1, score: float = 0.5) -> RetrievalHit:
    return RetrievalHit(
        knowledge_id=knowledge_id,
        knowledge_version=version,
        match_score=score,
    )


def _result_with(hits, *, success: bool = True) -> RetrievalResult:
    return RetrievalResult(
        query_id="q_test",
        success=success,
        total_hits=len(hits),
        hits=tuple(hits),
    )


# ---------------------------------------------------------------------------
# 1. LambdaSubEngine + HybridSubEngine
# ---------------------------------------------------------------------------


class TestLambdaSubEngine:
    def test_name_must_be_non_empty(self) -> None:
        with pytest.raises(ValueError):
            LambdaSubEngine("", lambda q, k, **kw: None)
        with pytest.raises(ValueError):
            LambdaSubEngine("   ", lambda q, k, **kw: None)

    def test_retrieve_calls_runner(self) -> None:
        called = {}

        def runner(query, kos, **kw):
            called["query"] = query
            called["kos"] = kos
            called["kw"] = kw
            return _result_with([_hit("ko_a")])

        sub = LambdaSubEngine("alpha", runner)
        result = sub.retrieve(
            RetrievalQuery(query_text="x"),
            [1, 2, 3],
            extra="hi",
        )
        assert called["query"].query_text == "x"
        assert called["kos"] == [1, 2, 3]
        assert called["kw"] == {"extra": "hi"}
        assert result.total_hits == 1

    def test_subclass_can_be_built_directly(self) -> None:
        class MySub(HybridSubEngine):
            name = "my-sub"

            def retrieve(self, query, kos, **kw):
                return _result_with([_hit("ko_a")])

        s = MySub()
        assert s.name == "my-sub"
        assert s.retrieve(RetrievalQuery(query_text="x"), []).total_hits == 1


# ---------------------------------------------------------------------------
# 2. Fusion strategies
# ---------------------------------------------------------------------------


class TestWeightedScoreFusion:
    def test_sum_of_weighted_scores(self) -> None:
        r1 = _result_with(
            [_hit("ko_a", score=0.4), _hit("ko_b", score=0.3)]
        )
        r2 = _result_with(
            [_hit("ko_a", score=0.2), _hit("ko_c", score=0.5)]
        )
        f = WeightedScoreFusion()
        fused = f.fuse(
            [("keyword", r1), ("structured", r2)],
            {"keyword": 1.0, "structured": 0.5},
        )
        by_id = {h.knowledge_id: s for h, s in fused}
        # ko_a: 1.0*0.4 + 0.5*0.2 = 0.5
        assert by_id["ko_a"] == pytest.approx(0.5, abs=1e-6)
        # ko_b: only keyword -> 1.0*0.3 = 0.3
        assert by_id["ko_b"] == pytest.approx(0.3, abs=1e-6)
        # ko_c: only structured -> 0.5*0.5 = 0.25
        assert by_id["ko_c"] == pytest.approx(0.25, abs=1e-6)

    def test_clipped_to_unit_interval(self) -> None:
        r1 = _result_with([_hit("ko_a", score=1.0)])
        r2 = _result_with([_hit("ko_a", score=1.0)])
        f = WeightedScoreFusion()
        fused = f.fuse(
            [("e1", r1), ("e2", r2)],
            {"e1": 1.0, "e2": 1.0},
        )
        # 1.0 + 1.0 = 2.0 -> clipped to 1.0
        assert fused[0][1] == 1.0

    def test_missing_engine_uses_default_weight(self) -> None:
        r1 = _result_with([_hit("ko_a", score=0.4)])
        f = WeightedScoreFusion(missing_weight=0.7)
        fused = f.fuse([("unknown", r1)], engine_weights={})
        assert fused[0][1] == pytest.approx(0.28, abs=1e-6)

    def test_no_clip_mode_preserves_sum(self) -> None:
        r1 = _result_with([_hit("ko_a", score=0.8)])
        r2 = _result_with([_hit("ko_a", score=0.8)])
        f = WeightedScoreFusion(clip=False)
        fused = f.fuse([("e1", r1), ("e2", r2)], {"e1": 1.0, "e2": 1.0})
        assert fused[0][1] == pytest.approx(1.6, abs=1e-6)


class TestReciprocalRankFusion:
    def test_rrf_sum(self) -> None:
        r1 = _result_with(
            [_hit("ko_a", score=0.9), _hit("ko_b", score=0.3)]
        )
        r2 = _result_with(
            [_hit("ko_a", score=0.5), _hit("ko_c", score=0.7)]
        )
        f = ReciprocalRankFusion(k=DEFAULT_RRF_K)
        fused = f.fuse(
            [("keyword", r1), ("structured", r2)],
            {"keyword": 1.0, "structured": 1.0},
        )
        by_id = {h.knowledge_id: s for h, s in fused}
        # ko_a ranks 1 in r1 (highest score=0.9) and
        # rank 2 in r2 (ko_c is rank 1 with score=0.7,
        # ko_a is rank 2 with score=0.5).
        expected_a = 1.0 / 61.0 + 1.0 / 62.0
        assert by_id["ko_a"] == pytest.approx(expected_a, abs=1e-6)

    def test_rrf_k_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            ReciprocalRankFusion(k=0)

    def test_rrf_handles_empty(self) -> None:
        f = ReciprocalRankFusion()
        out = f.fuse([], {})
        assert out == []


class TestMaxScoreFusion:
    def test_max_score(self) -> None:
        r1 = _result_with([_hit("ko_a", score=0.4)])
        r2 = _result_with([_hit("ko_a", score=0.9)])
        r3 = _result_with([_hit("ko_a", score=0.3)])
        f = MaxScoreFusion()
        fused = f.fuse(
            [("e1", r1), ("e2", r2), ("e3", r3)],
            {},
        )
        assert len(fused) == 1
        assert fused[0][1] == 0.9

    def test_max_score_dedup_across_engines(self) -> None:
        r1 = _result_with([_hit("ko_a", score=0.5), _hit("ko_b", score=0.7)])
        r2 = _result_with([_hit("ko_b", score=0.4), _hit("ko_c", score=0.6)])
        f = MaxScoreFusion()
        fused = f.fuse([("e1", r1), ("e2", r2)], {})
        ids = {h.knowledge_id for h, _ in fused}
        assert ids == {"ko_a", "ko_b", "ko_c"}


class TestUnionFusion:
    def test_union_preserves_first_score(self) -> None:
        r1 = _result_with([_hit("ko_a", score=0.7)])
        r2 = _result_with([_hit("ko_a", score=0.5), _hit("ko_b", score=0.4)])
        f = UnionFusion()
        fused = f.fuse([("e1", r1), ("e2", r2)], {})
        by_id = {h.knowledge_id: s for h, s in fused}
        assert by_id["ko_a"] == 0.7  # first engine wins
        assert by_id["ko_b"] == 0.4


# ---------------------------------------------------------------------------
# 3. HybridRetrievalEngine
# ---------------------------------------------------------------------------


class TestHybridRetrievalEngine:
    def test_engine_name(self) -> None:
        e = HybridRetrievalEngine(
            sub_engines=[LambdaSubEngine("a", lambda q, k, **kw: _result_with([]))]
        )
        assert e.ENGINE_NAME == "HybridRetrievalEngine V1"

    def test_requires_at_least_one_sub_engine(self) -> None:
        with pytest.raises(ValueError):
            HybridRetrievalEngine(sub_engines=[])

    def test_duplicate_sub_engine_name_rejected(self) -> None:
        with pytest.raises(ValueError):
            HybridRetrievalEngine(
                sub_engines=[
                    LambdaSubEngine("dup", lambda q, k, **kw: _result_with([])),
                    LambdaSubEngine("dup", lambda q, k, **kw: _result_with([])),
                ],
            )

    def test_empty_sub_engine_name_rejected(self) -> None:
        with pytest.raises(ValueError):
            LambdaSubEngine("", lambda q, k, **kw: _result_with([]))

    def test_non_hybrid_sub_engine_rejected(self) -> None:
        with pytest.raises(TypeError):
            HybridRetrievalEngine(sub_engines=["not-a-sub-engine"])  # type: ignore[list-item]

    def test_single_sub_engine_short_circuit(
        self, three_kos, attribute_registry
    ) -> None:
        engine = StructuredRetrievalEngine()
        hybrid = HybridRetrievalEngine(
            sub_engines=[
                LambdaSubEngine("structured", engine.execute),
            ],
            fusion=WeightedScoreFusion(),
        )
        q = RetrievalQuery(
            filters={"category": "kindergarten"},
            required_attributes=["theme"],
        )
        r = hybrid.execute(
            q, three_kos, attribute_registry=attribute_registry
        )
        assert r.success is True
        assert r.total_hits == 3

    def test_multi_engine_fusion_basic(
        self, three_kos, attribute_registry
    ) -> None:
        hybrid = build_keyword_structured_hybrid(
            keyword_engine=KeywordRetrievalEngine(),
            structured_engine=StructuredRetrievalEngine(),
            engine_weights={"keyword": 1.0, "structured": 0.5},
            fusion=WeightedScoreFusion(),
        )
        q = RetrievalQuery(
            query_text="forest",
            filters={"category": "kindergarten"},
        )
        r = hybrid.execute(
            q, three_kos, attribute_registry=attribute_registry
        )
        assert r.success is True
        # At least one hit. Highest score should be the
        # forest KO which both engines hit.
        assert r.total_hits >= 1
        assert r.hits[0].knowledge_id == "ko_forest_v1"

    def test_sub_engine_failure_isolation(self, three_kos) -> None:
        def bad_engine(query, kos, **kw):
            raise RuntimeError("simulated sub-engine failure")

        hybrid = HybridRetrievalEngine(
            sub_engines=[
                LambdaSubEngine("good", KeywordRetrievalEngine().execute),
                LambdaSubEngine("bad", bad_engine),
            ],
            fusion=WeightedScoreFusion(),
        )
        q = RetrievalQuery(query_text="forest")
        r = hybrid.execute(q, three_kos)
        # The good engine contributed; bad one was skipped.
        assert r.success is True
        assert r.total_hits >= 1

    def test_all_sub_engines_fail_returns_zero_hits(self) -> None:
        def bad_engine(query, kos, **kw):
            raise RuntimeError("always fails")

        hybrid = HybridRetrievalEngine(
            sub_engines=[
                LambdaSubEngine("a", bad_engine),
                LambdaSubEngine("b", bad_engine),
            ],
            fusion=WeightedScoreFusion(),
        )
        r = hybrid.execute(
            RetrievalQuery(query_text="x"), [1, 2, 3]
        )
        assert r.success is False
        assert r.total_hits == 0

    def test_input_kos_not_mutated(self, three_kos) -> None:
        before = [
            (k.knowledge_id, k.title, k.theme) for k in three_kos
        ]
        hybrid = build_keyword_structured_hybrid(
            KeywordRetrievalEngine(),
            StructuredRetrievalEngine(),
        )
        hybrid.execute(
            RetrievalQuery(query_text="forest"), three_kos
        )
        after = [
            (k.knowledge_id, k.title, k.theme) for k in three_kos
        ]
        assert before == after

    def test_input_sub_results_not_mutated(
        self, three_kos, attribute_registry
    ) -> None:
        # Build sub-results once, capture a snapshot of the
        # hit list, then ensure the hybrid engine doesn't
        # mutate that list when it consumes the underlying
        # engines.
        engine1 = KeywordRetrievalEngine()
        engine2 = StructuredRetrievalEngine()
        q = RetrievalQuery(
            query_text="forest",
            filters={"category": "kindergarten"},
            required_attributes=["theme"],
        )
        r1 = engine1.execute(q, three_kos)
        r2 = engine2.execute(
            q, three_kos, attribute_registry=attribute_registry
        )
        # Snapshot the hits (frozen dataclasses are hashable;
        # but our snapshot uses the match_score field which
        # is what the hybrid *may* rebuild).
        snapshot1 = [(h.knowledge_id, h.match_score) for h in r1.hits]
        snapshot2 = [(h.knowledge_id, h.match_score) for h in r2.hits]

        hybrid = build_keyword_structured_hybrid(
            engine1, engine2, fusion=WeightedScoreFusion()
        )
        hybrid.execute(q, three_kos, attribute_registry=attribute_registry)

        # The original sub-results are unchanged.
        assert [(h.knowledge_id, h.match_score) for h in r1.hits] == snapshot1
        assert [(h.knowledge_id, h.match_score) for h in r2.hits] == snapshot2

    def test_limit_cuts_output(self, three_kos) -> None:
        hybrid = build_keyword_structured_hybrid(
            KeywordRetrievalEngine(),
            StructuredRetrievalEngine(),
            fusion=WeightedScoreFusion(),
        )
        q = RetrievalQuery(
            query_text="o", limit=1, sort_by="score", sort_order="desc"
        )
        r = hybrid.execute(q, three_kos)
        assert r.total_hits == 1

    def test_query_id_preserved(self, three_kos) -> None:
        hybrid = build_keyword_structured_hybrid(
            KeywordRetrievalEngine(),
            StructuredRetrievalEngine(),
        )
        q = RetrievalQuery(
            query_id="q_specific_42",
            query_text="forest",
        )
        r = hybrid.execute(q, three_kos)
        assert r.query_id == "q_specific_42"

    def test_tie_breaker_by_version_desc(self) -> None:
        # Two KOs identical except version -> higher
        # version wins the tie.
        r1 = _result_with(
            [
                _hit("ko_a", version=1, score=0.5),
                _hit("ko_a", version=3, score=0.5),
            ]
        )
        hybrid = HybridRetrievalEngine(
            sub_engines=[LambdaSubEngine("e", lambda q, k, **kw: r1)],
            fusion=UnionFusion(),
        )
        q = RetrievalQuery(query_text="x")
        r = hybrid.execute(q, [])
        assert r.hits[0].knowledge_version == 3

    def test_tie_breaker_by_knowledge_id_lexicographic(self) -> None:
        r1 = _result_with(
            [_hit("ko_z", score=0.5), _hit("ko_a", score=0.5)]
        )
        hybrid = HybridRetrievalEngine(
            sub_engines=[LambdaSubEngine("e", lambda q, k, **kw: r1)],
            fusion=UnionFusion(),
        )
        q = RetrievalQuery(query_text="x")
        r = hybrid.execute(q, [])
        assert r.hits[0].knowledge_id == "ko_a"

    def test_post_ranking_pass(
        self, three_kos, attribute_registry
    ) -> None:
        ranker = RankingEngine()
        hybrid = build_keyword_structured_hybrid(
            KeywordRetrievalEngine(),
            StructuredRetrievalEngine(),
            engine_weights={"keyword": 1.0, "structured": 1.0},
            fusion=WeightedScoreFusion(),
            post_ranker=ranker,
        )
        q = RetrievalQuery(
            query_text="o", filters={"category": "kindergarten"}
        )
        r = hybrid.execute(
            q, three_kos, attribute_registry=attribute_registry
        )
        # The result must be a valid RetrievalResult and
        # contain hits.
        assert r.success is True
        assert r.total_hits >= 1

    def test_total_hits_matches_len(self, three_kos) -> None:
        hybrid = build_keyword_structured_hybrid(
            KeywordRetrievalEngine(),
            StructuredRetrievalEngine(),
        )
        r = hybrid.execute(
            RetrievalQuery(query_text="o"), three_kos
        )
        assert r.total_hits == len(r.hits)

    def test_rrf_fusion_used_by_hybrid(self, three_kos) -> None:
        hybrid = build_keyword_structured_hybrid(
            KeywordRetrievalEngine(),
            StructuredRetrievalEngine(),
            engine_weights={"keyword": 1.0, "structured": 1.0},
            fusion=ReciprocalRankFusion(),
        )
        q = RetrievalQuery(query_text="forest")
        r = hybrid.execute(q, three_kos)
        assert r.success is True
        # RRF scores are small fractions in [0, 1].
        if r.hits:
            assert r.hits[0].match_score < 1.0

    def test_max_score_fusion_used_by_hybrid(self, three_kos) -> None:
        hybrid = build_keyword_structured_hybrid(
            KeywordRetrievalEngine(),
            StructuredRetrievalEngine(),
            fusion=MaxScoreFusion(),
        )
        q = RetrievalQuery(query_text="forest")
        r = hybrid.execute(q, three_kos)
        # Max of two engines cannot exceed 1.0
        for h in r.hits:
            assert h.match_score <= 1.0


# ---------------------------------------------------------------------------
# 4. Convenience builder
# ---------------------------------------------------------------------------


class TestBuildKeywordStructuredHybrid:
    def test_returns_hybrid_engine(self) -> None:
        e = build_keyword_structured_hybrid(
            KeywordRetrievalEngine(),
            StructuredRetrievalEngine(),
        )
        assert isinstance(e, HybridRetrievalEngine)
        assert len(e.sub_engines) == 2
        names = {s.name for s in e.sub_engines}
        assert names == {"keyword", "structured"}

    def test_default_fusion_is_weighted(self) -> None:
        e = build_keyword_structured_hybrid(
            KeywordRetrievalEngine(),
            StructuredRetrievalEngine(),
        )
        assert isinstance(e.fusion, WeightedScoreFusion)

    def test_engine_weights_propagated(self) -> None:
        weights = {"keyword": 0.3, "structured": 0.7}
        e = build_keyword_structured_hybrid(
            KeywordRetrievalEngine(),
            StructuredRetrievalEngine(),
            engine_weights=weights,
        )
        assert e.engine_weights == weights


# ---------------------------------------------------------------------------
# 5. Hit key helper
# ---------------------------------------------------------------------------


class TestHitKey:
    def test_distinct_versions_same_id(self) -> None:
        a = _hit("ko_x", version=1)
        b = _hit("ko_x", version=2)
        assert _hit_key(a) != _hit_key(b)

    def test_same_key_for_same_hit(self) -> None:
        a = _hit("ko_x", version=3)
        b = _hit("ko_x", version=3)
        assert _hit_key(a) == _hit_key(b)

    def test_distinct_kos(self) -> None:
        a = _hit("ko_x", version=1)
        b = _hit("ko_y", version=1)
        assert _hit_key(a) != _hit_key(b)


# ---------------------------------------------------------------------------
# 6. AST architecture boundary
# ---------------------------------------------------------------------------


class TestHybridArchitectureBoundary:
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

    def test_hybrid_engine_has_no_forbidden_imports(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "retrieval"
            / "hybrid.py"
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
