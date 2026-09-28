"""Tests for Knowledge Retrieval Contract V1 (Sprint 24.0-A).

Acceptance criteria coverage:

    * Frozen contracts (Q1..Q8 data guards)
    * RetrievalValidator rules Q1..Q8 (with duck-typed fakes
      for rules that ``__post_init__`` rejects on construction)
    * KeywordRetrievalEngine V1 happy path with multiple KOs
    * Match modes (any / all / exact)
    * Sort + limit
    * Filters + required attributes + bound domain
    * JSON round-trip for all three dataclasses
    * KO / Domain / Binding / Attribute are NOT mutated by
      retrieval
    * AST architecture boundary:
        The retrieval module does NOT import:
            caseos.intelligence.*
            caseos.knowledge.evolution
            caseos.knowledge.governance
            caseos.knowledge.intake
            caseos.knowledge.feedback

Architecture boundary (Sprint 24.0-A spec):

    These tests do NOT import from:
        * caseos.intelligence.*
        * caseos.knowledge.evolution
        * caseos.knowledge.governance
        * caseos.knowledge.intake
        * caseos.knowledge.feedback
    These tests MAY import from:
        * caseos.knowledge.object (KO schema)
        * caseos.knowledge.retrieval (this sprint's contract)
        * stdlib
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from caseos.knowledge.object.object import KnowledgeObject  # noqa: E402

from caseos.knowledge.retrieval.engine import (  # noqa: E402
    KeywordRetrievalEngine,
    _tokenize,
)
from caseos.knowledge.retrieval.object import (  # noqa: E402
    DEFAULT_LIMIT,
    DEFAULT_MATCH_MODE,
    DEFAULT_SORT_BY,
    DEFAULT_SORT_ORDER,
    RetrievalContractError,
    RetrievalHit,
    RetrievalQuery,
    RetrievalResult,
)
from caseos.knowledge.retrieval.report import (  # noqa: E402
    generate_retrieval_report,
)
from caseos.knowledge.retrieval.schema import (  # noqa: E402
    DEFAULT_QUERY_FIELDS,
    MATCH_MODE_ALLOW_LIST,
    MAX_LIMIT,
    MIN_LIMIT,
    SORT_BY_ALLOW_LIST,
    SORT_ORDER_ALLOW_LIST,
)
from caseos.knowledge.retrieval.validator import (  # noqa: E402
    RetrievalValidator,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ko(
    *,
    knowledge_id: str,
    title: str,
    description: str = "",
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
    image_refs=None,
    document_refs=None,
) -> KnowledgeObject:
    return KnowledgeObject(
        knowledge_id=knowledge_id,
        version=version,
        title=title,
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
def forest_kindergarten_ko() -> KnowledgeObject:
    return _ko(
        knowledge_id="ko_forest_kg_v1",
        title="Forest Kindergarten",
        description="An outdoor forest themed kindergarten with nature play",
        theme="forest",
        style="natural",
        color_system="green",
        function_tags=["forest", "outdoor", "nature"],
    )


@pytest.fixture
def ocean_kindergarten_ko() -> KnowledgeObject:
    return _ko(
        knowledge_id="ko_ocean_kg_v1",
        title="Ocean Kindergarten",
        description="An indoor ocean themed kindergarten with water play",
        theme="ocean",
        style="modern",
        color_system="blue",
        function_tags=["ocean", "indoor", "water"],
    )


@pytest.fixture
def city_park_ko() -> KnowledgeObject:
    return _ko(
        knowledge_id="ko_city_park_v1",
        title="City Park",
        description="An urban park with walking paths and benches",
        theme="park",
        style="modern",
        color_system="mixed",
        function_tags=["park", "city", "outdoor"],
    )


@pytest.fixture
def three_kos(
    forest_kindergarten_ko,
    ocean_kindergarten_ko,
    city_park_ko,
):
    return [
        forest_kindergarten_ko,
        ocean_kindergarten_ko,
        city_park_ko,
    ]


# ---------------------------------------------------------------------------
# 1. Frozen contract tests
# ---------------------------------------------------------------------------


class TestRetrievalQueryFrozenContract:
    def test_default_construction_yields_valid_query(self) -> None:
        q = RetrievalQuery(query_text="forest")
        assert q.query_id.startswith("QRY-")
        assert q.version == 1
        assert q.match_mode == DEFAULT_MATCH_MODE
        assert q.limit == DEFAULT_LIMIT
        assert q.sort_by == DEFAULT_SORT_BY
        assert q.sort_order == DEFAULT_SORT_ORDER

    def test_query_is_frozen(self) -> None:
        q = RetrievalQuery(query_text="forest")
        with pytest.raises(Exception):
            q.query_text = "ocean"  # type: ignore[misc]

    def test_query_post_init_rejects_empty_query_id(self) -> None:
        with pytest.raises(RetrievalContractError):
            RetrievalQuery(query_id="", query_text="forest")

    def test_query_post_init_rejects_version_zero(self) -> None:
        with pytest.raises(RetrievalContractError):
            RetrievalQuery(version=0, query_text="forest")

    def test_query_collection_fields_are_defensively_copied(self) -> None:
        fields = ["title"]
        q = RetrievalQuery(query_fields=fields)
        fields.append("theme")
        assert q.query_fields == ["title"]

    def test_query_filters_are_defensively_copied(self) -> None:
        filters = {"category": "kindergarten"}
        q = RetrievalQuery(filters=filters)
        filters["theme"] = "forest"
        assert q.filters == {"category": "kindergarten"}

    def test_query_to_dict_round_trip(self) -> None:
        q = RetrievalQuery(
            query_text="forest kindergarten",
            query_fields=["title", "theme"],
            filters={"category": "kindergarten"},
            match_mode="any",
            limit=5,
            sort_by="score",
            sort_order="desc",
            required_attributes=["style"],
            bound_domain_ids=["dom_kinder"],
        )
        d = q.to_dict()
        q2 = RetrievalQuery.from_dict(d)
        assert q == q2


class TestRetrievalHitFrozenContract:
    def test_default_hit_has_human_id(self) -> None:
        h = RetrievalHit(knowledge_id="ko_x")
        assert h.hit_id.startswith("HIT-")
        assert h.match_score == 0.0

    def test_hit_is_frozen(self) -> None:
        h = RetrievalHit(knowledge_id="ko_x", match_score=0.5)
        with pytest.raises(Exception):
            h.knowledge_id = "ko_y"  # type: ignore[misc]

    def test_hit_score_rejected_outside_unit_interval(self) -> None:
        with pytest.raises(RetrievalContractError):
            RetrievalHit(knowledge_id="ko_x", match_score=1.5)
        with pytest.raises(RetrievalContractError):
            RetrievalHit(knowledge_id="ko_x", match_score=-0.1)

    def test_hit_snapshot_is_defensively_copied(self) -> None:
        snap = {"title": "Forest"}
        h = RetrievalHit(
            knowledge_id="ko_x", knowledge_object_snapshot=snap
        )
        snap["title"] = "MODIFIED"
        assert h.knowledge_object_snapshot == {"title": "Forest"}

    def test_hit_to_dict_round_trip(self) -> None:
        h = RetrievalHit(
            knowledge_id="ko_x",
            knowledge_version=2,
            match_score=0.7,
            matched_fields=["title", "theme"],
            matched_snippets={"title": "Ocean"},
            knowledge_object_snapshot={"title": "Ocean"},
        )
        d = h.to_dict()
        h2 = RetrievalHit.from_dict(d)
        assert h == h2


class TestRetrievalResultFrozenContract:
    def test_default_result_is_zero_hit_failure(self) -> None:
        r = RetrievalResult()
        assert r.success is False
        assert r.total_hits == 0
        assert r.hits == ()

    def test_result_total_hits_must_match_hits(self) -> None:
        h = RetrievalHit(knowledge_id="ko_x")
        with pytest.raises(RetrievalContractError):
            RetrievalResult(
                query_id="q1", success=True, total_hits=5, hits=(h,)
            )

    def test_result_is_frozen(self) -> None:
        r = RetrievalResult(query_id="q1", success=True)
        with pytest.raises(Exception):
            r.success = False  # type: ignore[misc]

    def test_result_accepts_list_input_for_hits(self) -> None:
        h1 = RetrievalHit(knowledge_id="ko_x")
        h2 = RetrievalHit(knowledge_id="ko_y")
        r = RetrievalResult(
            query_id="q1",
            success=True,
            total_hits=2,
            hits=[h1, h2],  # type: ignore[arg-type]
        )
        assert r.total_hits == 2
        assert all(isinstance(h, RetrievalHit) for h in r.hits)

    def test_result_to_dict_round_trip(self) -> None:
        h = RetrievalHit(knowledge_id="ko_x", match_score=0.4)
        r = RetrievalResult(
            query_id="q1", success=True, total_hits=1,
            hits=(h,), execution_time_ms=1.23,
        )
        d = r.to_dict()
        r2 = RetrievalResult.from_dict(d)
        assert r == r2


# ---------------------------------------------------------------------------
# 2. Schema allow-list tests
# ---------------------------------------------------------------------------


class TestSchemaConstants:
    def test_match_mode_allow_list(self) -> None:
        assert MATCH_MODE_ALLOW_LIST == {"any", "all", "exact"}

    def test_sort_by_allow_list(self) -> None:
        assert SORT_BY_ALLOW_LIST == {
            "score", "knowledge_id", "version", "created_at"
        }

    def test_sort_order_allow_list(self) -> None:
        assert SORT_ORDER_ALLOW_LIST == {"asc", "desc"}

    def test_default_query_fields_include_textual_ko_fields(self) -> None:
        for field_name in ("title", "description", "theme", "style"):
            assert field_name in DEFAULT_QUERY_FIELDS

    def test_limit_bounds(self) -> None:
        assert MIN_LIMIT == 1
        assert MAX_LIMIT == 1000


# ---------------------------------------------------------------------------
# 3. Validator tests (Q1..Q8)
# ---------------------------------------------------------------------------


class FakeQuery:
    """Duck-typed RetrievalQuery that bypasses ``__post_init__``
    so we can supply invalid field values to the validator."""

    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestRetrievalValidator:
    def test_valid_query_passes(self) -> None:
        v = RetrievalValidator()
        q = RetrievalQuery(query_text="forest")
        r = v.validate(q)
        assert r.valid is True
        assert r.errors == ()
        assert r.rule_failures == ()

    def test_none_query(self) -> None:
        v = RetrievalValidator()
        r = v.validate(None)
        assert r.valid is False
        assert "Q0" in r.rule_failures or r.errors == ("query is None",)

    def test_q1_empty_query_id(self) -> None:
        v = RetrievalValidator()
        q = FakeQuery(
            query_id="   ", version=1, limit=10, query_text="x",
            match_mode="any", sort_by="score", sort_order="desc",
            query_fields=[], filters={}, required_attributes=[],
            bound_domain_ids=[], execution_time_ms=0.0,
        )
        r = v.validate(q)
        assert not r.valid
        assert "Q1" in r.rule_failures

    def test_q2_version_must_be_positive_int(self) -> None:
        v = RetrievalValidator()
        q = FakeQuery(
            query_id="q1", version=0, limit=10, query_text="x",
            match_mode="any", sort_by="score", sort_order="desc",
            query_fields=[], filters={}, required_attributes=[],
            bound_domain_ids=[],
        )
        r = v.validate(q)
        assert not r.valid
        assert "Q2" in r.rule_failures

    def test_q3_limit_above_max(self) -> None:
        v = RetrievalValidator()
        q = FakeQuery(
            query_id="q1", version=1, limit=2000, query_text="x",
            match_mode="any", sort_by="score", sort_order="desc",
            query_fields=[], filters={}, required_attributes=[],
            bound_domain_ids=[],
        )
        r = v.validate(q)
        assert not r.valid
        assert "Q3" in r.rule_failures

    def test_q3_limit_below_min(self) -> None:
        v = RetrievalValidator()
        q = FakeQuery(
            query_id="q1", version=1, limit=0, query_text="x",
            match_mode="any", sort_by="score", sort_order="desc",
            query_fields=[], filters={}, required_attributes=[],
            bound_domain_ids=[],
        )
        r = v.validate(q)
        assert not r.valid
        assert "Q3" in r.rule_failures

    def test_q4_unknown_match_mode(self) -> None:
        v = RetrievalValidator()
        q = FakeQuery(
            query_id="q1", version=1, limit=10, query_text="x",
            match_mode="fuzzy", sort_by="score", sort_order="desc",
            query_fields=[], filters={}, required_attributes=[],
            bound_domain_ids=[],
        )
        r = v.validate(q)
        assert not r.valid
        assert "Q4" in r.rule_failures

    def test_q5_unknown_sort_by(self) -> None:
        v = RetrievalValidator()
        q = FakeQuery(
            query_id="q1", version=1, limit=10, query_text="x",
            match_mode="any", sort_by="pop", sort_order="desc",
            query_fields=[], filters={}, required_attributes=[],
            bound_domain_ids=[],
        )
        r = v.validate(q)
        assert not r.valid
        assert "Q5" in r.rule_failures

    def test_q6_unknown_sort_order(self) -> None:
        v = RetrievalValidator()
        q = FakeQuery(
            query_id="q1", version=1, limit=10, query_text="x",
            match_mode="any", sort_by="score", sort_order="up",
            query_fields=[], filters={}, required_attributes=[],
            bound_domain_ids=[],
        )
        r = v.validate(q)
        assert not r.valid
        assert "Q6" in r.rule_failures

    def test_q7_requires_at_least_one_input(self) -> None:
        v = RetrievalValidator()
        q = FakeQuery(
            query_id="q1", version=1, limit=10, query_text="",
            match_mode="any", sort_by="score", sort_order="desc",
            query_fields=[], filters={}, required_attributes=[],
            bound_domain_ids=[],
        )
        r = v.validate(q)
        assert not r.valid
        assert "Q7" in r.rule_failures

    def test_q7_passes_when_query_fields_only(self) -> None:
        v = RetrievalValidator()
        q = FakeQuery(
            query_id="q1", version=1, limit=10, query_text="",
            match_mode="any", sort_by="score", sort_order="desc",
            query_fields=["title"], filters={}, required_attributes=[],
            bound_domain_ids=[],
        )
        r = v.validate(q)
        assert r.valid

    def test_q8_rejects_unknown_ko_field_in_filters(self) -> None:
        v = RetrievalValidator()
        q = FakeQuery(
            query_id="q1", version=1, limit=10, query_text="x",
            match_mode="any", sort_by="score", sort_order="desc",
            query_fields=[], filters={"unknown_field": "value"},
            required_attributes=[], bound_domain_ids=[],
        )
        r = v.validate(q)
        assert not r.valid
        assert "Q8" in r.rule_failures

    def test_q8_passes_with_known_ko_field(self) -> None:
        v = RetrievalValidator()
        q = FakeQuery(
            query_id="q1", version=1, limit=10, query_text="x",
            match_mode="any", sort_by="score", sort_order="desc",
            query_fields=[], filters={"category": "kindergarten"},
            required_attributes=[], bound_domain_ids=[],
        )
        r = v.validate(q)
        assert r.valid


# ---------------------------------------------------------------------------
# 4. Engine behavior tests
# ---------------------------------------------------------------------------


class TestKeywordRetrievalEngine:
    def test_engine_tokenizer_strips_stopwords_and_lowers(self) -> None:
        tokens = _tokenize("The Forest and the Ocean")
        assert "forest" in tokens
        assert "ocean" in tokens
        for t in tokens:
            assert t == t.lower()

    def test_invalid_query_returns_zero_hits_with_success_false(
        self, three_kos
    ) -> None:
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery()  # Q7 fails (no input at all)
        r = engine.execute(q, three_kos)
        assert r.success is False
        assert r.total_hits == 0
        assert r.hits == ()

    def test_happy_path_returns_relevant_match_first(
        self, three_kos
    ) -> None:
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery(query_text="forest kindergarten")
        r = engine.execute(q, three_kos)
        assert r.success is True
        assert r.total_hits >= 1
        # The forest KO has the highest combined score.
        first = r.hits[0]
        assert first.knowledge_id == "ko_forest_kg_v1"
        assert first.match_score > 0.0
        assert "title" in first.matched_fields

    def test_match_mode_any_passes_when_one_field_matches(
        self, three_kos
    ) -> None:
        engine = KeywordRetrievalEngine()
        # 'forest' only occurs in ko_forest_kg_v1's title and theme.
        q = RetrievalQuery(
            query_text="forest", match_mode="any",
            query_fields=["title", "theme", "style"],
        )
        r = engine.execute(q, three_kos)
        assert r.success is True
        ids = {h.knowledge_id for h in r.hits}
        assert "ko_forest_kg_v1" in ids

    def test_match_mode_all_requires_every_field_to_match_some_ko(
        self, three_kos
    ) -> None:
        engine = KeywordRetrievalEngine()
        # No KO matches title AND theme AND style on 'forest'.
        q = RetrievalQuery(
            query_text="forest", match_mode="all",
            query_fields=["title", "theme", "style"],
        )
        r = engine.execute(q, three_kos)
        # The query_text only matches one field per KO; 'all'
        # therefore produces 0 hits.
        assert r.total_hits == 0

    def test_match_mode_exact_requires_substring_match(
        self, three_kos
    ) -> None:
        engine = KeywordRetrievalEngine()
        # Use a phrase that exactly appears in the forest KO.
        q = RetrievalQuery(
            query_text="Forest Kindergarten", match_mode="exact",
        )
        r = engine.execute(q, three_kos)
        assert r.success is True
        ids = {h.knowledge_id for h in r.hits}
        assert "ko_forest_kg_v1" in ids

    def test_sort_by_score_descending(self, three_kos) -> None:
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery(
            query_text="outdoor kindergarten",
            sort_by="score", sort_order="desc", limit=10,
        )
        r = engine.execute(q, three_kos)
        scores = [h.match_score for h in r.hits]
        assert scores == sorted(scores, reverse=True)

    def test_sort_by_score_ascending(self, three_kos) -> None:
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery(
            query_text="outdoor kindergarten",
            sort_by="score", sort_order="asc", limit=10,
        )
        r = engine.execute(q, three_kos)
        scores = [h.match_score for h in r.hits]
        assert scores == sorted(scores)

    def test_sort_by_knowledge_id(self, three_kos) -> None:
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery(
            query_text="kindergarten", sort_by="knowledge_id",
            sort_order="asc", limit=10,
        )
        r = engine.execute(q, three_kos)
        ids = [h.knowledge_id for h in r.hits]
        assert ids == sorted(ids)

    def test_limit_caps_hits(self, three_kos) -> None:
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery(
            query_text="kindergarten", limit=1, sort_by="score", sort_order="desc",
        )
        r = engine.execute(q, three_kos)
        assert r.total_hits == 1

    def test_filters_exclude_non_matching_kos(
        self, three_kos
    ) -> None:
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery(
            query_text="ocean",
            filters={"theme": "ocean"},
            sort_by="score", sort_order="desc",
        )
        r = engine.execute(q, three_kos)
        ids = {h.knowledge_id for h in r.hits}
        assert ids == {"ko_ocean_kg_v1"}

    def test_required_attributes_pass_when_present(
        self, three_kos
    ) -> None:
        engine = KeywordRetrievalEngine()
        # 'theme' is a textual attribute that exists on every KO.
        q = RetrievalQuery(
            query_text="kindergarten",
            required_attributes=["theme"],
            sort_by="score", sort_order="desc",
        )
        r = engine.execute(q, three_kos)
        assert r.success is True
        assert r.total_hits >= 1

    def test_required_attributes_drop_missing(
        self, ocean_kindergarten_ko
    ) -> None:
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery(
            query_text="ocean",
            required_attributes=["nonexistent_attribute"],
            sort_by="score", sort_order="desc",
        )
        r = engine.execute(q, [ocean_kindergarten_ko])
        assert r.success is True
        assert r.total_hits == 0

    def test_bound_domain_ids_skips_unbound_kos(
        self, three_kos
    ) -> None:
        engine = KeywordRetrievalEngine()
        binding_lookup = {
            "ko_forest_kg_v1": ("dom_nature",),
            "ko_ocean_kg_v1": ("dom_aqua",),
            "ko_city_park_v1": ("dom_park",),
        }
        q = RetrievalQuery(
            query_text="kindergarten",
            bound_domain_ids=["dom_aqua"],
            sort_by="score", sort_order="desc",
        )
        r = engine.execute(q, three_kos, binding_lookup=binding_lookup)
        ids = {h.knowledge_id for h in r.hits}
        assert ids == {"ko_ocean_kg_v1"}

    def test_bound_domain_ids_open_when_empty(
        self, three_kos
    ) -> None:
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery(query_text="forest")
        r = engine.execute(q, three_kos)
        assert r.total_hits >= 1

    def test_knowledge_object_is_not_mutated_by_engine(
        self, forest_kindergarten_ko
    ) -> None:
        original_title = forest_kindergarten_ko.title
        original_theme = forest_kindergarten_ko.theme
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery(query_text="forest")
        engine.execute(q, [forest_kindergarten_ko])
        assert forest_kindergarten_ko.title == original_title
        assert forest_kindergarten_ko.theme == original_theme

    def test_kos_passed_in_are_not_mutated_by_engine(
        self, three_kos
    ) -> None:
        before = [
            (
                k.knowledge_id,
                k.title,
                k.theme,
                tuple(k.function_tags),
            )
            for k in three_kos
        ]
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery(query_text="outdoor")
        engine.execute(q, three_kos)
        after = [
            (
                k.knowledge_id,
                k.title,
                k.theme,
                tuple(k.function_tags),
            )
            for k in three_kos
        ]
        assert before == after

    def test_dict_shaped_ko_is_supported(self) -> None:
        # Engine reads fields duck-typed. A plain dict with the
        # right keys must work just like a KnowledgeObject.
        engine = KeywordRetrievalEngine()
        ko_dict = {
            "knowledge_id": "ko_dict_v1",
            "version": 3,
            "title": "Forest Camp",
            "description": "forest adventure",
            "category": "camp",
            "theme": "forest",
            "style": "natural",
            "color_system": "green",
            "interaction_type": "exploration",
            "function_tags": ["forest"],
            "project_type": "camp",
            "site_type": "outdoor",
            "location_type": "rural",
            "space_size": "large",
            "image_refs": [],
            "document_refs": [],
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
            "source": "human",
        }
        q = RetrievalQuery(query_text="forest")
        r = engine.execute(q, [ko_dict])
        assert r.success is True
        assert r.total_hits == 1
        h = r.hits[0]
        assert h.knowledge_id == "ko_dict_v1"
        assert h.knowledge_version == 3

    def test_empty_corpus_returns_zero_hits(
        self, forest_kindergarten_ko
    ) -> None:
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery(query_text="forest")
        r = engine.execute(q, [])
        assert r.success is True
        assert r.total_hits == 0

    def test_corpus_with_only_one_ko(self, forest_kindergarten_ko) -> None:
        engine = KeywordRetrievalEngine()
        q = RetrievalQuery(query_text="forest")
        r = engine.execute(q, [forest_kindergarten_ko])
        assert r.total_hits == 1
        h = r.hits[0]
        assert h.knowledge_id == "ko_forest_kg_v1"
        assert h.knowledge_version == 1


# ---------------------------------------------------------------------------
# 5. JSON round-trip across all three dataclasses
# ---------------------------------------------------------------------------


class TestJsonRoundTrip:
    def test_full_flow_json_safe(self) -> None:
        q = RetrievalQuery(
            query_text="forest kindergarten",
            filters={"category": "kindergarten"},
            match_mode="any",
            limit=3,
        )
        h = RetrievalHit(
            knowledge_id="ko_x",
            knowledge_version=1,
            match_score=0.7,
            matched_fields=["title"],
            matched_snippets={"title": "Forest Kindergarten"},
            knowledge_object_snapshot={"title": "Forest Kindergarten"},
        )
        r = RetrievalResult(
            query_id=q.query_id,
            success=True,
            total_hits=1,
            hits=(h,),
            execution_time_ms=0.5,
        )

        q_round = RetrievalQuery.from_dict(json.loads(
            json.dumps(q.to_dict())
        ))
        h_round = RetrievalHit.from_dict(json.loads(
            json.dumps(h.to_dict())
        ))
        r_round = RetrievalResult.from_dict(json.loads(
            json.dumps(r.to_dict())
        ))

        assert q == q_round
        assert h == h_round
        assert r == r_round


# ---------------------------------------------------------------------------
# 6. Report generator
# ---------------------------------------------------------------------------


class TestReportGenerator:
    def test_report_contains_expected_sections(self) -> None:
        q = RetrievalQuery(query_text="forest", match_mode="any")
        v = RetrievalValidator().validate(q)
        h = RetrievalHit(knowledge_id="ko_x", match_score=0.3)
        r = RetrievalResult(
            query_id=q.query_id,
            success=True,
            total_hits=1,
            hits=(h,),
        )
        md = generate_retrieval_report(q, r, validation=v)
        assert "# Knowledge Retrieval Report" in md
        assert "## 1. Query Summary" in md
        assert "## 2. Validation" in md
        assert "## 3. Engine Selection" in md
        assert "## 4. Hits" in md
        assert "## 5. Architecture Boundary" in md
        assert "## 6. Notes" in md
        assert "no LLM, no embedding" in md

    def test_report_handles_no_result(self) -> None:
        q = RetrievalQuery(query_text="forest")
        md = generate_retrieval_report(q, None, validation=None)
        assert "(no result -- engine was not executed)" in md


# ---------------------------------------------------------------------------
# 7. AST architecture boundary
# ---------------------------------------------------------------------------


class TestArchitectureBoundary:
    FORBIDDEN_SUBSTRINGS = (
        "caseos.intelligence",
        "caseos.knowledge.evolution",
        "caseos.knowledge.governance",
        "caseos.knowledge.intake",
        "caseos.knowledge.feedback",
    )

    def _collect_imports(self, source: str) -> list[str]:
        # Strip BOM + Windows line endings so the parser
        # handles files written by any toolchain.
        if source and source[0] == "﻿":
            source = source[1:]
        if source and source[:2] == "\xef\xbb":
            try:
                source = source.encode("utf-8").decode("utf-8-sig")
            except Exception:
                pass
        tree = ast.parse(source)
        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module and not module.startswith("."):
                    imports.append(module)
                for alias in node.names:
                    if module and not module.startswith("."):
                        imports.append(module + "." + alias.name)
        return imports

    def test_no_forbidden_imports_in_retrieval_module(self) -> None:
        pkg = (
            Path(__file__).resolve().parents[1] / "knowledge" / "retrieval"
        )
        offenders = []
        for path in sorted(pkg.glob("*.py")):
            if path.name == "__init__.py":
                continue
            source = path.read_text(encoding="utf-8-sig")
            for imp in self._collect_imports(source):
                for forbidden in self.FORBIDDEN_SUBSTRINGS:
                    if forbidden in imp:
                        offenders.append(
                            path.name + " -> " + imp
                        )
        assert offenders == [], (
            "Forbidden architecture boundary import detected: "
            + repr(offenders)
        )

    def test_object_py_only_imports_stdlib_and_ko_schema(self) -> None:
        path = (
            Path(__file__).resolve().parents[1] / "knowledge" / "retrieval"
            / "object.py"
        )
        source = path.read_text(encoding="utf-8-sig")
        imports = self._collect_imports(source)
        for forbidden in self.FORBIDDEN_SUBSTRINGS:
            for imp in imports:
                assert forbidden not in imp, (
                    "object.py imports forbidden module: " + imp
                )