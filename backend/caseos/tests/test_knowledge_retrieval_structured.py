"""Tests for Knowledge Retrieval Structured Engine V1 (Sprint 24.0-B).

Acceptance criteria coverage:

    * StructuredRetrievalEngine V1 happy path
    * Required attributes axis (registry-membership + value)
    * Domain binding axis (binding_lookup / binding_registry)
    * Filter axis (exact match gate)
    * Three-axis combined score
    * Sort / limit behavior
    * Duck-typed KO input (dict or KnowledgeObject)
    * KO + registries + lookup are NOT mutated
    * AST architecture boundary
        * The structured engine does NOT import from:
            caseos.intelligence.*
            caseos.knowledge.evolution
            caseos.knowledge.governance
            caseos.knowledge.intake
            caseos.knowledge.feedback
            caseos.brain.*

Architecture boundary (Sprint 24.0-B spec):

    These tests do NOT import forbidden modules.
    These tests MAY import:
        * caseos.knowledge.object (KO schema)
        * caseos.knowledge.{attribute,domain,binding,taxonomy}
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

from caseos.knowledge.retrieval.object import (  # noqa: E402
    RetrievalQuery,
)
from caseos.knowledge.retrieval.structured import (  # noqa: E402
    STRUCTURED_ATTRIBUTE_FIELDS,
    STRUCTURED_BINDING_FIELDS,
    STRUCTURED_DOMAIN_FIELDS,
    StructuredRetrievalEngine,
    _attribute_score,
    _build_binding_lookup,
    _collect_attribute_names,
    _collect_binding_pairs,
    _collect_domain_ids,
    _domain_score,
    _filter_score,
    _has_nonempty_value,
    _iter_optional_registry,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ko(
    knowledge_id: str,
    *,
    theme: str = "",
    style: str = "",
    color_system: str = "",
    interaction_type: str = "",
    category: str = "kindergarten",
    project_type: str = "",
    site_type: str = "",
    location_type: str = "",
    space_size: str = "",
    title: str = "",
    description: str = "",
    version: int = 1,
    function_tags=None,
    image_refs=None,
    document_refs=None,
    created_at: str = "2026-01-01T00:00:00Z",
    updated_at: str = "2026-01-01T00:00:00Z",
    source: str = "human",
) -> KnowledgeObject:
    return KnowledgeObject(
        knowledge_id=knowledge_id,
        version=version,
        title=title or knowledge_id,
        description=description,
        category=category,
        project_type=project_type or "kindergarten",
        site_type=site_type or "outdoor",
        location_type=location_type or "urban",
        space_size=space_size or "medium",
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
def forest_ko() -> KnowledgeObject:
    return _ko(
        "ko_forest_v1",
        theme="forest",
        style="natural",
        color_system="green",
        interaction_type="exploration",
    )


@pytest.fixture
def ocean_ko() -> KnowledgeObject:
    return _ko(
        "ko_ocean_v1",
        theme="ocean",
        style="modern",
        color_system="blue",
        interaction_type="sensory",
    )


@pytest.fixture
def city_park_ko() -> KnowledgeObject:
    return _ko(
        "ko_park_v1",
        theme="park",
        style="rustic",
        color_system="green",
        interaction_type="passive",
    )


@pytest.fixture
def three_kos(forest_ko, ocean_ko, city_park_ko):
    return [forest_ko, ocean_ko, city_park_ko]


@pytest.fixture
def attribute_registry():
    """A simple list-of-dicts registry shape -- the engine
    accepts this duck-typed form as well as full
    ``KnowledgeAttribute`` records."""
    return [
        {"attribute_id": "theme", "name": "theme"},
        {"attribute_id": "style", "name": "style"},
        {"attribute_id": "interaction_type", "name": "interaction_type"},
        {"attribute_id": "color_system", "name": "color_system"},
    ]


# ---------------------------------------------------------------------------
# 1. Helper-level tests
# ---------------------------------------------------------------------------


class TestValuePresence:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("hello", True),
            ("   ", False),
            ("", False),
            (None, False),
            ([], False),
            ([1, 2], True),
            ({}, False),
            ({"a": 1}, True),
            ((1, 2), True),
            (0, True),
            (0.0, True),
            (False, True),
        ],
    )
    def test_has_nonempty_value(self, value, expected) -> None:
        assert _has_nonempty_value(value) is expected


class TestIterOptionalRegistry:
    def test_none(self) -> None:
        assert _iter_optional_registry(None) is None

    def test_empty_iterable(self) -> None:
        assert _iter_optional_registry([]) is None

    def test_list(self) -> None:
        assert _iter_optional_registry([1, 2, 3]) == [1, 2, 3]

    def test_tuple(self) -> None:
        assert _iter_optional_registry((4, 5)) == [4, 5]

    def test_set(self) -> None:
        assert sorted(_iter_optional_registry({6, 7})) == [6, 7]

    def test_non_iterable_returns_none(self) -> None:
        # A bare int raises; engine treats it as missing.
        assert _iter_optional_registry(42) is None


class TestCollectAttributeNames:
    def test_none_returns_none(self) -> None:
        assert _collect_attribute_names(None) is None

    def test_dict_shaped_entries(self) -> None:
        registry = [
            {"attribute_id": "theme"},
            {"name": "style"},
            {"attribute_id": "interaction_type"},
        ]
        out = _collect_attribute_names(registry)
        assert out == {"theme", "style", "interaction_type"}

    def test_dataclass_shaped_entries(self) -> None:
        class FakeAttr:
            def __init__(self, name, attribute_id=None):
                self.name = name
                self.attribute_id = attribute_id or name

        out = _collect_attribute_names(
            [FakeAttr("a"), FakeAttr("b", "B")]
        )
        assert out == {"a", "B"}


class TestCollectDomainIds:
    def test_dict_shaped(self) -> None:
        registry = [{"domain_id": "dom_kinder"}, {"domain_id": "dom_park"}]
        out = _collect_domain_ids(registry)
        assert out == {"dom_kinder", "dom_park"}

    def test_id_fallback(self) -> None:
        registry = [{"id": "d1"}, {"id": "d2"}]
        out = _collect_domain_ids(registry)
        assert out == {"d1", "d2"}


class TestCollectBindingPairs:
    def test_pairs_extracted(self) -> None:
        registry = [
            {"knowledge_object_id": "ko_a", "domain_id": "dom_x"},
            {"knowledge_object_id": "ko_a", "domain_id": "dom_y"},
            {"knowledge_object_id": "ko_b", "domain_id": "dom_z"},
        ]
        out = _collect_binding_pairs(registry)
        assert sorted(out) == sorted(
            [
                ("ko_a", "dom_x"),
                ("ko_a", "dom_y"),
                ("ko_b", "dom_z"),
            ]
        )

    def test_skips_malformed_entries(self) -> None:
        registry = [
            {"knowledge_object_id": "ko_a", "domain_id": "dom_x"},
            {"knowledge_object_id": None, "domain_id": "dom_y"},
            {"knowledge_object_id": "ko_b"},
        ]
        out = _collect_binding_pairs(registry)
        assert out == [("ko_a", "dom_x")]


class TestBuildBindingLookup:
    def test_groups_by_ko_id(self) -> None:
        pairs = [
            ("ko_a", "dom_x"),
            ("ko_a", "dom_y"),
            ("ko_b", "dom_z"),
        ]
        out = _build_binding_lookup(pairs)
        assert out == {"ko_a": ["dom_x", "dom_y"], "ko_b": ["dom_z"]}

    def test_none(self) -> None:
        assert _build_binding_lookup(None) is None

    def test_empty(self) -> None:
        assert _build_binding_lookup([]) == {}


# ---------------------------------------------------------------------------
# 2. Score function tests
# ---------------------------------------------------------------------------


class TestAttributeScore:
    def test_required_attributes_pass_when_value_present(
        self, forest_ko
    ) -> None:
        score, sat, missing = _attribute_score(
            ["theme", "style"],
            attribute_names={"theme", "style"},
            ko=forest_ko,
            attribute_lookup=None,
        )
        assert score == 1.0
        assert set(sat) == {"theme", "style"}
        assert missing == []

    def test_required_attributes_drop_when_value_absent(
        self, forest_ko
    ) -> None:
        # 'foo' is a registered name but forest_ko has no
        # 'foo' attribute. The score is 0/1 = 0.0.
        score, sat, missing = _attribute_score(
            ["foo"],
            attribute_names={"foo"},
            ko=forest_ko,
            attribute_lookup=None,
        )
        assert score == 0.0
        assert sat == []
        assert missing == ["foo"]

    def test_required_attributes_unknown_to_registry(
        self, forest_ko
    ) -> None:
        score, sat, missing = _attribute_score(
            ["ghost"],
            attribute_names={"theme", "style"},
            ko=forest_ko,
            attribute_lookup=None,
        )
        assert score == 0.0
        assert missing == ["ghost"]

    def test_required_attributes_no_registry_still_works(
        self, forest_ko
    ) -> None:
        score, sat, missing = _attribute_score(
            ["theme"],
            attribute_names=None,
            ko=forest_ko,
            attribute_lookup=None,
        )
        assert score == 1.0
        assert "theme" in sat

    def test_required_attributes_via_attribute_lookup(
        self, forest_ko
    ) -> None:
        # The lookup supplies an out-of-band value for
        # 'theme' even though the KO's KO snapshot has it.
        score, sat, missing = _attribute_score(
            ["theme"],
            attribute_names=None,
            ko=forest_ko,
            attribute_lookup={
                "ko_forest_v1": {"theme": "from-lookup"},
            },
        )
        assert score == 1.0
        assert sat == ["theme"]


class TestDomainScore:
    def test_empty_bound_is_open(self) -> None:
        s, matched, missed = _domain_score(
            [], "ko_x", {"ko_x": ["dom_a"]}
        )
        assert s == 1.0
        assert matched == []
        assert missed == []

    def test_matching_domains(self) -> None:
        s, matched, missed = _domain_score(
            ["dom_a", "dom_b"], "ko_x", {"ko_x": ["dom_a"]}
        )
        assert s == 0.5
        assert matched == ["dom_a"]
        assert missed == ["dom_b"]

    def test_no_binding_lookup(self) -> None:
        s, matched, missed = _domain_score(["dom_a"], "ko_x", None)
        assert s == 0.0
        assert matched == []
        assert missed == ["dom_a"]


class TestFilterScore:
    def test_no_filters_is_open(self) -> None:
        s, matched, missed = _filter_score({}, {"a": 1})
        assert s == 1.0
        assert matched == []
        assert missed == []

    def test_all_filters_match(self) -> None:
        s, matched, missed = _filter_score(
            {"a": 1, "b": "x"}, {"a": 1, "b": "x"}
        )
        assert s == 1.0
        assert sorted(matched) == ["a", "b"]
        assert missed == []

    def test_any_filter_mismatch_drops_score(self) -> None:
        s, matched, missed = _filter_score(
            {"a": 1, "b": "x"}, {"a": 1, "b": "y"}
        )
        assert s == 0.0
        assert matched == ["a"]
        assert missed == ["b"]


# ---------------------------------------------------------------------------
# 3. Engine behavior tests
# ---------------------------------------------------------------------------


class TestStructuredRetrievalEngine:
    def test_engine_class_name_is_stable(self) -> None:
        assert (
            StructuredRetrievalEngine.ENGINE_NAME
            == "StructuredRetrievalEngine V1"
        )

    def test_invalid_query_short_circuits_to_failure(
        self, three_kos
    ) -> None:
        # Q7 fails because no input is provided.
        q = RetrievalQuery()
        engine = StructuredRetrievalEngine()
        r = engine.execute(q, three_kos)
        assert r.success is False
        assert r.total_hits == 0
        assert r.hits == ()

    def test_filters_alone_returns_matching_kos(
        self, three_kos
    ) -> None:
        q = RetrievalQuery(filters={"theme": "forest"})
        engine = StructuredRetrievalEngine()
        r = engine.execute(q, three_kos)
        assert r.success is True
        assert r.total_hits == 1
        assert r.hits[0].knowledge_id == "ko_forest_v1"

    def test_required_attributes_filters_all_kos_when_satisfied(
        self, three_kos, attribute_registry
    ) -> None:
        q = RetrievalQuery(
            required_attributes=["theme", "style"],
            filters={"category": "kindergarten"},
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(
            q, three_kos, attribute_registry=attribute_registry
        )
        # All three KOs have theme + style + category=kindergarten.
        assert r.success is True
        assert r.total_hits == 3
        for h in r.hits:
            assert h.match_score == 1.0

    def test_required_attributes_drop_unknown_attribute(
        self, three_kos, attribute_registry
    ) -> None:
        q = RetrievalQuery(
            required_attributes=["ghost_attribute"],
            filters={"category": "kindergarten"},
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(
            q, three_kos, attribute_registry=attribute_registry
        )
        assert r.success is True
        assert r.total_hits == 0

    def test_required_attributes_no_registry_uses_ko_value(
        self, three_kos
    ) -> None:
        # Without an attribute_registry, the engine still
        # accepts any required_attribute string and looks
        # up the value on the KO directly.
        q = RetrievalQuery(
            required_attributes=["theme"],
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(q, three_kos)
        # All three KOs satisfy 'theme'.
        assert r.success is True
        assert r.total_hits == 3

    def test_bound_domain_via_lookup(self, three_kos) -> None:
        binding_lookup = {
            "ko_forest_v1": ("dom_nature",),
            "ko_ocean_v1": ("dom_aqua",),
            "ko_park_v1": ("dom_park",),
        }
        q = RetrievalQuery(
            filters={"category": "kindergarten"},
            bound_domain_ids=["dom_aqua"],
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(
            q, three_kos, binding_lookup=binding_lookup
        )
        ids = {h.knowledge_id for h in r.hits}
        assert ids == {"ko_ocean_v1"}

    def test_bound_domain_via_registry(
        self, three_kos, attribute_registry
    ) -> None:
        binding_registry = [
            {
                "knowledge_object_id": "ko_forest_v1",
                "domain_id": "dom_nature",
            },
            {
                "knowledge_object_id": "ko_ocean_v1",
                "domain_id": "dom_aqua",
            },
            {
                "knowledge_object_id": "ko_park_v1",
                "domain_id": "dom_park",
            },
        ]
        q = RetrievalQuery(
            filters={"category": "kindergarten"},
            bound_domain_ids=["dom_park"],
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(
            q,
            three_kos,
            attribute_registry=attribute_registry,
            binding_registry=binding_registry,
        )
        ids = {h.knowledge_id for h in r.hits}
        assert ids == {"ko_park_v1"}

    def test_bound_domain_lookup_overrides_registry(
        self, three_kos
    ) -> None:
        # Registry says forest -> nature; lookup says
        # forest -> aqua. lookup wins.
        binding_registry = [
            {
                "knowledge_object_id": "ko_forest_v1",
                "domain_id": "dom_nature",
            },
        ]
        binding_lookup = {"ko_forest_v1": ("dom_aqua",)}
        q = RetrievalQuery(
            filters={"category": "kindergarten"},
            bound_domain_ids=["dom_aqua"],
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(
            q,
            three_kos,
            binding_registry=binding_registry,
            binding_lookup=binding_lookup,
        )
        ids = {h.knowledge_id for h in r.hits}
        assert ids == {"ko_forest_v1"}

    def test_sort_by_score_descending(self, three_kos) -> None:
        q = RetrievalQuery(
            filters={"category": "kindergarten"},
            sort_by="score", sort_order="desc", limit=10,
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(q, three_kos)
        scores = [h.match_score for h in r.hits]
        assert scores == sorted(scores, reverse=True)

    def test_sort_by_knowledge_id(self, three_kos) -> None:
        q = RetrievalQuery(
            filters={"category": "kindergarten"},
            sort_by="knowledge_id", sort_order="asc", limit=10,
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(q, three_kos)
        ids = [h.knowledge_id for h in r.hits]
        assert ids == sorted(ids)

    def test_limit_caps_hits(self, three_kos) -> None:
        q = RetrievalQuery(
            filters={"category": "kindergarten"},
            sort_by="score", sort_order="desc", limit=2,
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(q, three_kos)
        assert r.total_hits == 2

    def test_match_mode_all_requires_perfect_score(
        self, three_kos, attribute_registry
    ) -> None:
        # All three KOs achieve score==1.0 against
        # theme+style, so 'all' must keep them all.
        q = RetrievalQuery(
            required_attributes=["theme", "style"],
            filters={"category": "kindergarten"},
            match_mode="all",
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(
            q, three_kos, attribute_registry=attribute_registry
        )
        assert r.total_hits == 3

        # Same query without filters -> filter axis = 1.0
        # open, attribute axis full, domain 0 -> still 1.0
        # ... no wait, attribute_score=1.0, domain_score=1.0
        # (empty), filter_score=1.0 -> 1.0.
        q2 = RetrievalQuery(
            required_attributes=["theme"],
            match_mode="all",
        )
        r2 = engine.execute(q2, three_kos)
        assert r2.total_hits == 3

    def test_query_text_does_not_affect_score(
        self, three_kos, attribute_registry
    ) -> None:
        # Structured engine ignores query_text. Same query
        # with two different query_text values must yield
        # the same RetrievalResult total_hits (and same
        # knowledge ids).
        q1 = RetrievalQuery(
            query_text="totally unrelated",
            required_attributes=["theme"],
            filters={"category": "kindergarten"},
        )
        q2 = RetrievalQuery(
            query_text="forest kindergarten ocean park zoo",
            required_attributes=["theme"],
            filters={"category": "kindergarten"},
        )
        engine = StructuredRetrievalEngine()
        r1 = engine.execute(q1, three_kos)
        r2 = engine.execute(q2, three_kos)
        assert r1.total_hits == r2.total_hits
        assert {h.knowledge_id for h in r1.hits} == {
            h.knowledge_id for h in r2.hits
        }

    def test_knowledge_object_is_not_mutated(
        self, forest_ko, ocean_ko
    ) -> None:
        before_forest = (
            forest_ko.knowledge_id,
            forest_ko.theme,
            forest_ko.style,
        )
        before_ocean = (ocean_ko.knowledge_id, ocean_ko.theme)
        q = RetrievalQuery(
            required_attributes=["theme", "style"],
            filters={"category": "kindergarten"},
        )
        engine = StructuredRetrievalEngine()
        engine.execute(q, [forest_ko, ocean_ko])
        assert (forest_ko.knowledge_id, forest_ko.theme, forest_ko.style) == before_forest
        assert (ocean_ko.knowledge_id, ocean_ko.theme) == before_ocean

    def test_registries_are_not_mutated(
        self, three_kos, attribute_registry
    ) -> None:
        before_names = sorted(
            e["attribute_id"] for e in attribute_registry
        )
        before_len = len(attribute_registry)
        q = RetrievalQuery(
            required_attributes=["theme"],
            filters={"category": "kindergarten"},
        )
        engine = StructuredRetrievalEngine()
        engine.execute(
            q, three_kos, attribute_registry=attribute_registry
        )
        after_names = sorted(
            e["attribute_id"] for e in attribute_registry
        )
        assert before_names == after_names
        assert len(attribute_registry) == before_len

    def test_dict_shaped_ko_is_supported(self) -> None:
        ko_dict = {
            "knowledge_id": "ko_dict_v1",
            "version": 2,
            "title": "Forest Camp",
            "description": "n/a",
            "category": "camp",
            "project_type": "camp",
            "site_type": "outdoor",
            "location_type": "rural",
            "space_size": "large",
            "theme": "forest",
            "style": "natural",
            "color_system": "green",
            "interaction_type": "exploration",
            "function_tags": [],
            "image_refs": [],
            "document_refs": [],
            "created_at": "2026-01-01",
            "updated_at": "2026-01-01",
            "source": "human",
        }
        q = RetrievalQuery(required_attributes=["theme", "style"])
        engine = StructuredRetrievalEngine()
        r = engine.execute(q, [ko_dict])
        assert r.success is True
        assert r.total_hits == 1

    def test_empty_corpus_returns_zero_hits(
        self, three_kos, attribute_registry
    ) -> None:
        q = RetrievalQuery(
            required_attributes=["theme"],
            filters={"category": "kindergarten"},
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(
            q, [], attribute_registry=attribute_registry
        )
        assert r.success is True
        assert r.total_hits == 0

    def test_attribute_lookup_overrides_ko_value(
        self, three_kos, attribute_registry
    ) -> None:
        # The lookup marks ko_ocean_v1.theme = "forest",
        # so it should now satisfy a filter theme=forest
        # even though its KO attribute is "ocean".
        lookup = {"ko_ocean_v1": {"theme": "forest"}}
        q = RetrievalQuery(
            required_attributes=["theme"],
            filters={"theme": "forest"},
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(
            q, three_kos, attribute_lookup=lookup
        )
        ids = {h.knowledge_id for h in r.hits}
        assert ids == {"ko_forest_v1", "ko_ocean_v1"}

    def test_filters_required_attributes_bound_domain_combined(
        self, three_kos, attribute_registry
    ) -> None:
        binding_lookup = {
            "ko_forest_v1": ("dom_nature",),
            "ko_ocean_v1": ("dom_aqua",),
            "ko_park_v1": ("dom_park",),
        }
        q = RetrievalQuery(
            required_attributes=["theme", "style"],
            filters={"category": "kindergarten"},
            bound_domain_ids=["dom_nature", "dom_park"],
        )
        engine = StructuredRetrievalEngine()
        r = engine.execute(
            q,
            three_kos,
            attribute_registry=attribute_registry,
            binding_lookup=binding_lookup,
        )
        ids = {h.knowledge_id for h in r.hits}
        assert ids == {"ko_forest_v1", "ko_park_v1"}


# ---------------------------------------------------------------------------
# 4. Architecture boundary AST
# ---------------------------------------------------------------------------


class TestStructuredArchitectureBoundary:
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

    def test_structured_engine_has_no_forbidden_imports(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "retrieval"
            / "structured.py"
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

    def test_structured_engine_does_not_subclass_keyword_engine(
        self,
    ) -> None:
        # The structured engine must be a sibling, not a
        # subclass of KeywordRetrievalEngine.
        from caseos.knowledge.retrieval.engine import (
            KeywordRetrievalEngine,
        )

        assert not issubclass(
            StructuredRetrievalEngine, KeywordRetrievalEngine
        )
        # But it must still expose 'execute(query, kos, ...)'.

        assert hasattr(StructuredRetrievalEngine, "execute")
