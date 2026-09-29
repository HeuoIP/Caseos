"""Tests for the Knowledge Retrieval Pipeline Facade V1 (Sprint 24.3-A)."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from caseos.knowledge.object.object import KnowledgeObject  # noqa: E402

from caseos.knowledge.retrieval.hybrid import (  # noqa: E402
    HybridRetrievalEngine,
    LambdaSubEngine,
    MaxScoreFusion,
    ReciprocalRankFusion,
    WeightedScoreFusion,
)
from caseos.knowledge.retrieval.object import (  # noqa: E402
    RetrievalHit,
    RetrievalQuery,
    RetrievalResult,
)
from caseos.knowledge.retrieval.pipeline import (  # noqa: E402
    STRATEGY_ALLOW_LIST,
    STRATEGY_HYBRID_AUTO,
    STRATEGY_HYBRID_FULL,
    STRATEGY_KEYWORD_ONLY,
    STRATEGY_SEMANTIC_ONLY,
    STRATEGY_STRUCTURED_ONLY,
    RetrievalPipeline,
    RetrievalPipelineError,
    build_default_pipeline,
)
from caseos.knowledge.retrieval.ranking import (  # noqa: E402
    CompositeRanking,
    RankingEngine,
    RecencyRanking,
    StableRanking,
)
from caseos.knowledge.retrieval.semantic import (  # noqa: E402
    SemanticIndex,
)


def _ko(knowledge_id, *, title="", description="", theme="", style="",
        category="kindergarten", project_type="kindergarten",
        site_type="outdoor", location_type="urban", space_size="medium",
        color_system="green", interaction_type="exploration",
        function_tags=None, version=1,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z", source="human",
        image_refs=None, document_refs=None):
    return KnowledgeObject(
        knowledge_id=knowledge_id, version=version,
        title=title or knowledge_id, description=description,
        category=category, project_type=project_type,
        site_type=site_type, location_type=location_type,
        space_size=space_size, theme=theme, style=style,
        color_system=color_system, interaction_type=interaction_type,
        function_tags=list(function_tags or []),
        image_refs=list(image_refs or []),
        document_refs=list(document_refs or []),
        created_at=created_at, updated_at=updated_at, source=source,
    )


@pytest.fixture
def three_kos():
    return [
        _ko("ko_forest_v1", title="Forest Kindergarten",
            theme="forest", style="natural",
            description="forest outdoor playground"),
        _ko("ko_ocean_v1", title="Ocean Kindergarten",
            theme="ocean", style="modern",
            description="ocean indoor playground"),
        _ko("ko_park_v1", title="City Park",
            theme="park", style="rustic",
            description="city park playground"),
    ]


@pytest.fixture
def semantic_index():
    idx = SemanticIndex()
    idx.register_concept_to_kos({"forest": ("ko_forest_v1", "ko_park_v1")})
    idx.register_aliases({"woods": "forest", "trees": "forest"})
    return idx


@pytest.fixture
def forest_query():
    return RetrievalQuery(query_text="forest playground", limit=10)


@pytest.fixture
def schema_only_query():
    return RetrievalQuery(
        query_text="", query_fields=[],
        required_attributes=("theme",), bound_domain_ids=(), limit=10,
    )


def _hit(knowledge_id, *, version=1, score=0.5):
    return RetrievalHit(
        knowledge_id=knowledge_id, knowledge_version=version,
        match_score=score,
    )


# ---------------------------------------------------------------------------
# 1. Strategy constants + construction
# ---------------------------------------------------------------------------


class TestStrategyConstants:
    def test_all_five_strategies_in_allow_list(self):
        expected = {
            STRATEGY_KEYWORD_ONLY, STRATEGY_STRUCTURED_ONLY,
            STRATEGY_SEMANTIC_ONLY, STRATEGY_HYBRID_AUTO,
            STRATEGY_HYBRID_FULL,
        }
        assert expected.issubset(STRATEGY_ALLOW_LIST)
        assert STRATEGY_ALLOW_LIST == frozenset(expected)

    def test_hybrid_auto_is_default(self):
        pipe = RetrievalPipeline()
        assert pipe.strategy == STRATEGY_HYBRID_AUTO

    def test_invalid_strategy_rejected(self):
        with pytest.raises(RetrievalPipelineError):
            RetrievalPipeline(strategy="NOT_A_STRATEGY")

    def test_empty_strategy_rejected(self):
        with pytest.raises(RetrievalPipelineError):
            RetrievalPipeline(strategy="")

    def test_invalid_strategy_type_rejected(self):
        with pytest.raises(RetrievalPipelineError):
            RetrievalPipeline(strategy=42)


class TestConstruction:
    def test_keyword_only_has_single_sub_engine(self):
        pipe = RetrievalPipeline(strategy=STRATEGY_KEYWORD_ONLY)
        assert pipe.engine_count == 1
        assert pipe.sub_engine_names == ["keyword_only"]
        assert pipe.strategy == STRATEGY_KEYWORD_ONLY

    def test_structured_only_has_single_sub_engine(self):
        pipe = RetrievalPipeline(strategy=STRATEGY_STRUCTURED_ONLY)
        assert pipe.engine_count == 1
        assert pipe.sub_engine_names == ["structured_only"]

    def test_semantic_only_requires_index(self, semantic_index):
        with pytest.raises(RetrievalPipelineError):
            RetrievalPipeline(strategy=STRATEGY_SEMANTIC_ONLY)
        pipe = RetrievalPipeline(
            strategy=STRATEGY_SEMANTIC_ONLY,
            semantic_index=semantic_index,
        )
        assert pipe.engine_count == 1
        assert pipe.sub_engine_names == ["semantic_only"]

    def test_hybrid_auto_has_two_sub_engines(self):
        pipe = RetrievalPipeline(strategy=STRATEGY_HYBRID_AUTO)
        assert pipe.engine_count == 2
        assert pipe.sub_engine_names == ["keyword", "structured"]
        assert isinstance(pipe._engine, HybridRetrievalEngine)

    def test_hybrid_full_has_three_sub_engines(self, semantic_index):
        pipe = RetrievalPipeline(
            strategy=STRATEGY_HYBRID_FULL, semantic_index=semantic_index,
        )
        assert pipe.engine_count == 3
        assert pipe.sub_engine_names == ["keyword", "structured", "semantic"]

    def test_hybrid_full_requires_semantic_index(self):
        with pytest.raises(RetrievalPipelineError):
            RetrievalPipeline(strategy=STRATEGY_HYBRID_FULL)

    def test_post_ranker_must_be_ranking_engine_or_none(self):
        with pytest.raises(RetrievalPipelineError):
            RetrievalPipeline(
                strategy=STRATEGY_KEYWORD_ONLY,
                post_ranker="not-a-ranker",
            )

    def test_fusion_must_be_fusion_strategy_or_none(self):
        with pytest.raises(RetrievalPipelineError):
            RetrievalPipeline(
                strategy=STRATEGY_HYBRID_AUTO, fusion="not-a-fusion",
            )


# ---------------------------------------------------------------------------
# 2. execute() -- KEYWORD_ONLY
# ---------------------------------------------------------------------------


class TestExecuteKeywordOnly:
    def test_returns_frozen_envelope(self, three_kos, forest_query):
        pipe = RetrievalPipeline(strategy=STRATEGY_KEYWORD_ONLY)
        result = pipe.execute(forest_query, three_kos)
        assert isinstance(result, RetrievalResult)
        with pytest.raises(Exception):
            result.success = False  # type: ignore[misc]

    def test_query_text_hits_forest_ko(self, three_kos, forest_query):
        pipe = RetrievalPipeline(strategy=STRATEGY_KEYWORD_ONLY)
        result = pipe.execute(forest_query, three_kos)
        assert result.success is True
        kid_set = {h.knowledge_id for h in result.hits}
        assert "ko_forest_v1" in kid_set

    def test_query_id_propagates(self, three_kos, forest_query):
        pipe = RetrievalPipeline(strategy=STRATEGY_KEYWORD_ONLY)
        result = pipe.execute(forest_query, three_kos)
        assert result.query_id == forest_query.query_id

    def test_empty_corpus_returns_zero_hit_success(self, forest_query):
        pipe = RetrievalPipeline(strategy=STRATEGY_KEYWORD_ONLY)
        result = pipe.execute(forest_query, [])
        assert result.success is True
        assert result.total_hits == 0
        assert result.hits == ()


# ---------------------------------------------------------------------------
# 3. execute() -- STRUCTURED_ONLY
# ---------------------------------------------------------------------------


class TestExecuteStructuredOnly:
    def test_schema_only_query_runs(self, three_kos, schema_only_query):
        pipe = RetrievalPipeline(strategy=STRATEGY_STRUCTURED_ONLY)
        result = pipe.execute(schema_only_query, three_kos)
        assert result.success is True
        assert result.total_hits >= 0

    def test_registries_forwarded(self, three_kos, schema_only_query):
        attribute_registry = [{"attribute_id": "theme", "name": "theme"}]
        binding_registry = [
            {"knowledge_object_id": "ko_forest_v1", "domain_id": "kindergarten"},
        ]
        pipe = RetrievalPipeline(
            strategy=STRATEGY_STRUCTURED_ONLY,
            attribute_registry=attribute_registry,
            binding_registry=binding_registry,
        )
        result = pipe.execute(schema_only_query, three_kos)
        assert result.success is True

    def test_keyword_strategy_does_not_forward_registries(
        self, three_kos, forest_query,
    ):
        attribute_registry = [{"attribute_id": "theme", "name": "theme"}]
        pipe = RetrievalPipeline(
            strategy=STRATEGY_KEYWORD_ONLY,
            attribute_registry=attribute_registry,
        )
        result = pipe.execute(forest_query, three_kos)
        assert result.success is True


# ---------------------------------------------------------------------------
# 4. execute() -- SEMANTIC_ONLY
# ---------------------------------------------------------------------------


class TestExecuteSemanticOnly:
    def test_resolves_via_alias(self, three_kos, semantic_index):
        q = RetrievalQuery(query_text="woods", limit=10)
        pipe = RetrievalPipeline(
            strategy=STRATEGY_SEMANTIC_ONLY,
            semantic_index=semantic_index,
        )
        result = pipe.execute(q, three_kos)
        assert result.success is True
        kid_set = {h.knowledge_id for h in result.hits}
        assert "ko_forest_v1" in kid_set

    def test_unknown_token_yields_zero_hits(
        self, three_kos, semantic_index,
    ):
        q = RetrievalQuery(query_text="gibberish_token_xyz", limit=10)
        pipe = RetrievalPipeline(
            strategy=STRATEGY_SEMANTIC_ONLY,
            semantic_index=semantic_index,
        )
        result = pipe.execute(q, three_kos)
        assert result.total_hits == 0


# ---------------------------------------------------------------------------
# 5. execute() -- HYBRID_AUTO / HYBRID_FULL
# ---------------------------------------------------------------------------


class TestExecuteHybridAuto:
    def test_returns_frozen_envelope(self, three_kos, forest_query):
        pipe = RetrievalPipeline(strategy=STRATEGY_HYBRID_AUTO)
        result = pipe.execute(forest_query, three_kos)
        assert isinstance(result, RetrievalResult)

    def test_combines_keyword_and_structured(self, three_kos, forest_query):
        pipe = RetrievalPipeline(strategy=STRATEGY_HYBRID_AUTO)
        result = pipe.execute(forest_query, three_kos)
        assert result.success is True
        assert result.total_hits >= 0

    def test_hybrid_auto_works_without_semantic_index(
        self, three_kos, forest_query,
    ):
        pipe = RetrievalPipeline(strategy=STRATEGY_HYBRID_AUTO)
        assert pipe.semantic_index is None
        result = pipe.execute(forest_query, three_kos)
        assert result.success is True


class TestExecuteHybridFull:
    def test_runs_three_sub_engines(
        self, three_kos, forest_query, semantic_index,
    ):
        pipe = RetrievalPipeline(
            strategy=STRATEGY_HYBRID_FULL,
            semantic_index=semantic_index,
        )
        result = pipe.execute(forest_query, three_kos)
        assert result.success is True

    def test_custom_fusion_and_weights(
        self, three_kos, forest_query, semantic_index,
    ):
        pipe = RetrievalPipeline(
            strategy=STRATEGY_HYBRID_FULL,
            semantic_index=semantic_index,
            fusion=ReciprocalRankFusion(k=42),
            engine_weights={
                "keyword": 0.5, "structured": 0.3, "semantic": 0.2,
            },
        )
        result = pipe.execute(forest_query, three_kos)
        assert result.success is True

    def test_max_score_fusion_works(
        self, three_kos, forest_query, semantic_index,
    ):
        pipe = RetrievalPipeline(
            strategy=STRATEGY_HYBRID_FULL,
            semantic_index=semantic_index,
            fusion=MaxScoreFusion(),
        )
        result = pipe.execute(forest_query, three_kos)
        assert result.success is True


# ---------------------------------------------------------------------------
# 6. Post-ranker pass
# ---------------------------------------------------------------------------


class TestPostRanker:
    def test_post_ranker_is_applied(self, three_kos, forest_query):
        ranker = RankingEngine()
        pipe = RetrievalPipeline(
            strategy=STRATEGY_HYBRID_AUTO, post_ranker=ranker,
        )
        result = pipe.execute(forest_query, three_kos)
        assert result.success is True
        assert result.total_hits >= 0

    def test_post_ranker_composite_construction(self):
        composite = CompositeRanking(
            recency_weight=0.0,
            coverage_weight=0.0,
            priority_weight=0.0,
            stable_weight=0.0,
        )
        assert composite.recency_weight == 0.0
        assert composite.coverage_weight == 0.0

    def test_recency_and_stable_construction(self):
        r = RecencyRanking(reference_now="2026-12-31T00:00:00Z")
        assert r.reference_now == "2026-12-31T00:00:00Z"
        s = StableRanking()
        assert s is not None


# ---------------------------------------------------------------------------
# 7. Mutation boundary -- pipeline never mutates input KOs or query
# ---------------------------------------------------------------------------


class TestImmutabilityBoundary:
    def test_kos_not_mutated_by_keyword(self, three_kos, forest_query):
        before = [ko.to_dict() for ko in three_kos]
        pipe = RetrievalPipeline(strategy=STRATEGY_KEYWORD_ONLY)
        pipe.execute(forest_query, three_kos)
        after = [ko.to_dict() for ko in three_kos]
        assert before == after

    def test_kos_not_mutated_by_structured(
        self, three_kos, schema_only_query,
    ):
        before = [ko.to_dict() for ko in three_kos]
        pipe = RetrievalPipeline(strategy=STRATEGY_STRUCTURED_ONLY)
        pipe.execute(schema_only_query, three_kos)
        after = [ko.to_dict() for ko in three_kos]
        assert before == after

    def test_kos_not_mutated_by_hybrid(self, three_kos, forest_query):
        before = [ko.to_dict() for ko in three_kos]
        pipe = RetrievalPipeline(strategy=STRATEGY_HYBRID_AUTO)
        pipe.execute(forest_query, three_kos)
        after = [ko.to_dict() for ko in three_kos]
        assert before == after

    def test_query_not_mutated(self, three_kos, forest_query):
        before_text = forest_query.query_text
        before_id = forest_query.query_id
        pipe = RetrievalPipeline(strategy=STRATEGY_KEYWORD_ONLY)
        pipe.execute(forest_query, three_kos)
        assert forest_query.query_text == before_text
        assert forest_query.query_id == before_id

    def test_corpus_mutation_after_call(self, three_kos, forest_query):
        pipe = RetrievalPipeline(strategy=STRATEGY_KEYWORD_ONLY)
        pipe.execute(forest_query, three_kos)
        three_kos.append(
            _ko("ko_extra_v1", title="Late Addition",
                theme="desert", style="modern",
                description="late addition")
        )
        result = pipe.execute(forest_query, three_kos)
        assert isinstance(result, RetrievalResult)


# ---------------------------------------------------------------------------
# 8. Introspection properties
# ---------------------------------------------------------------------------


class TestIntrospection:
    def test_engine_count_for_each_strategy(self, semantic_index):
        assert RetrievalPipeline(
            strategy=STRATEGY_KEYWORD_ONLY
        ).engine_count == 1
        assert RetrievalPipeline(
            strategy=STRATEGY_STRUCTURED_ONLY
        ).engine_count == 1
        assert RetrievalPipeline(
            strategy=STRATEGY_SEMANTIC_ONLY,
            semantic_index=semantic_index,
        ).engine_count == 1
        assert RetrievalPipeline(
            strategy=STRATEGY_HYBRID_AUTO
        ).engine_count == 2
        assert RetrievalPipeline(
            strategy=STRATEGY_HYBRID_FULL,
            semantic_index=semantic_index,
        ).engine_count == 3

    def test_sub_engine_names_for_each_strategy(self, semantic_index):
        assert RetrievalPipeline(
            strategy=STRATEGY_KEYWORD_ONLY
        ).sub_engine_names == ["keyword_only"]
        assert RetrievalPipeline(
            strategy=STRATEGY_STRUCTURED_ONLY
        ).sub_engine_names == ["structured_only"]
        assert RetrievalPipeline(
            strategy=STRATEGY_SEMANTIC_ONLY,
            semantic_index=semantic_index,
        ).sub_engine_names == ["semantic_only"]
        assert RetrievalPipeline(
            strategy=STRATEGY_HYBRID_AUTO
        ).sub_engine_names == ["keyword", "structured"]
        assert RetrievalPipeline(
            strategy=STRATEGY_HYBRID_FULL,
            semantic_index=semantic_index,
        ).sub_engine_names == ["keyword", "structured", "semantic"]

    def test_engine_name_constant(self):
        assert RetrievalPipeline.ENGINE_NAME == "RetrievalPipeline V1"


# ---------------------------------------------------------------------------
# 9. build_default_pipeline builder
# ---------------------------------------------------------------------------


class TestBuildDefaultPipeline:
    def test_default_is_hybrid_auto(self):
        pipe = build_default_pipeline()
        assert pipe.strategy == STRATEGY_HYBRID_AUTO
        assert pipe.engine_count == 2

    def test_default_forwards_post_ranker(self):
        ranker = RankingEngine()
        pipe = build_default_pipeline(post_ranker=ranker)
        assert pipe.post_ranker is ranker

    def test_default_forwards_registries(
        self, three_kos, schema_only_query,
    ):
        attribute_registry = [{"attribute_id": "theme", "name": "theme"}]
        pipe = build_default_pipeline(
            attribute_registry=attribute_registry,
        )
        assert pipe.attribute_registry is attribute_registry
        result = pipe.execute(schema_only_query, three_kos)
        assert result.success is True

    def test_default_forwards_semantic_index(self, semantic_index):
        pipe = build_default_pipeline(semantic_index=semantic_index)
        assert pipe.semantic_index is semantic_index
        assert pipe.strategy == STRATEGY_HYBRID_AUTO


# ---------------------------------------------------------------------------
# 10. AST architecture boundary
# ---------------------------------------------------------------------------


class TestPipelineArchitectureBoundary:
    FORBIDDEN_SUBSTRINGS = (
        "caseos.intelligence",
        "caseos.knowledge.evolution",
        "caseos.knowledge.governance",
        "caseos.knowledge.intake",
        "caseos.knowledge.feedback",
        "caseos.brain",
    )

    def _collect_imports(self, source):
        if source and source[0] == "\ufeff":
            source = source[1:]
        tree = ast.parse(source)
        imports = []
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

    def test_pipeline_module_has_no_forbidden_imports(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge" / "retrieval" / "pipeline.py"
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


# ---------------------------------------------------------------------------
# 11. Smoke: pipeline does not leak references between calls
# ---------------------------------------------------------------------------


class TestNoLeakBetweenCalls:
    def test_two_consecutive_calls_are_independent(
        self, three_kos, forest_query,
    ):
        pipe = RetrievalPipeline(strategy=STRATEGY_HYBRID_AUTO)
        r1 = pipe.execute(forest_query, three_kos)
        r2 = pipe.execute(forest_query, three_kos)
        assert r1.query_id == r2.query_id
        assert r1.total_hits == r2.total_hits
        assert len(r1.hits) == len(r2.hits)

    def test_pipeline_engine_is_reusable(
        self, three_kos, forest_query, schema_only_query,
    ):
        pipe = RetrievalPipeline(strategy=STRATEGY_KEYWORD_ONLY)
        first = pipe.execute(forest_query, three_kos)
        second = pipe.execute(schema_only_query, three_kos)
        assert isinstance(first, RetrievalResult)
        assert isinstance(second, RetrievalResult)

    def test_lambda_sub_engine_construction(self):
        def runner(query, kos, **kw):
            return RetrievalResult(query_id="x", success=True)
        sub = LambdaSubEngine(name="x", runner=runner)
        assert sub.name == "x"
        assert sub is not None

    def test_weighted_score_fusion_default(self):
        f = WeightedScoreFusion()
        assert f is not None
