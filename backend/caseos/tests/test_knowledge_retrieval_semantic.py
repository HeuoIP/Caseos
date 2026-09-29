"""Tests for Knowledge Retrieval Semantic Foundation V1 (Sprint 24.1-A).

Coverage:

    * SemanticIndex: register / resolve / hierarchy
    * SemanticRetrievalEngine:
        - alias resolution path
        - literal concept path
        - ancestor / descendant expansion
        - per-KO max score aggregation
        - filters gate
        - sort / limit
        - KO not mutated, index not mutated
    * AST architecture boundary
        The semantic engine does NOT import from:
            * caseos.intelligence.*
            * caseos.knowledge.evolution
            * caseos.knowledge.governance
            * caseos.knowledge.intake
            * caseos.knowledge.feedback
            * caseos.brain.*

Architecture boundary (Sprint 24.1-A spec):

    These tests do NOT import from forbidden modules.
    These tests MAY import from:
        * caseos.knowledge.object
        * caseos.knowledge.{domain,binding,taxonomy,
                            attribute,graph}
        * caseos.knowledge.retrieval
        * stdlib
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from caseos.knowledge.object.object import KnowledgeObject  # noqa: E402

from caseos.knowledge.retrieval.object import (  # noqa: E402
    RetrievalQuery,
)
from caseos.knowledge.retrieval.semantic import (  # noqa: E402
    SCORE_ALIAS,
    SCORE_ANCESTOR,
    SCORE_DESCENDANT,
    SCORE_EXACT,
    SemanticIndex,
    SemanticRetrievalEngine,
    _tokenize,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ko(
    knowledge_id: str,
    *,
    theme: str = "",
    category: str = "kindergarten",
    project_type: str = "kindergarten",
    site_type: str = "outdoor",
    location_type: str = "urban",
    space_size: str = "medium",
    style: str = "",
    color_system: str = "",
    interaction_type: str = "",
    title: str = "",
    description: str = "",
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
        _ko("ko_forest_v1", theme="forest", title="Forest Kindergarten"),
        _ko("ko_ocean_v1", theme="ocean", title="Ocean Kindergarten"),
        _ko("ko_park_v1", theme="park", title="City Park"),
    ]


@pytest.fixture
def built_index():
    """A canonical index used by most tests.

    Taxonomy:

        nature
           +-- forest
           |     +-- deep-forest
           +-- ocean
           +-- park

    Concept -> KO mapping (curated):

        forest      -> [ko_forest_v1]
        ocean       -> [ko_ocean_v1]
        park        -> [ko_park_v1]
        nature      -> [ko_forest_v1, ko_ocean_v1, ko_park_v1]
        deep-forest -> [ko_forest_v1]

    Aliases:

        wild -> forest
        sea  -> ocean
        outdoor -> park
    """
    idx = SemanticIndex()
    idx.register_taxonomy_nodes([
        {"node_id": "nature", "parent_node_id": None,
         "aliases": [], "label": "Nature"},
        {"node_id": "forest", "parent_node_id": "nature",
         "aliases": [], "label": "Forest"},
        {"node_id": "deep-forest", "parent_node_id": "forest",
         "aliases": [], "label": "Deep Forest"},
        {"node_id": "ocean", "parent_node_id": "nature",
         "aliases": [], "label": "Ocean"},
        {"node_id": "park", "parent_node_id": "nature",
         "aliases": [], "label": "Park"},
    ])
    idx.register_concept_to_kos({
        "forest": ("ko_forest_v1",),
        "ocean": ("ko_ocean_v1",),
        "park": ("ko_park_v1",),
                "deep-forest": ("ko_forest_v1",),
    })
    idx.register_aliases({
        "wild": "forest",
        "sea": "ocean",
        "outdoor": "park",
    })
    return idx


# ---------------------------------------------------------------------------
# 1. Tokenizer
# ---------------------------------------------------------------------------


class TestTokenizer:
    def test_lowercases(self) -> None:
        assert _tokenize("FOREST Kindergarten") == ["forest", "kindergarten"]

    def test_strips_stopwords(self) -> None:
        tokens = _tokenize("the forest and the ocean")
        assert "forest" in tokens
        assert "ocean" in tokens
        assert "the" not in tokens
        assert "and" not in tokens

    def test_non_string_returns_empty(self) -> None:
        assert _tokenize(None) == []
        assert _tokenize(42) == []


# ---------------------------------------------------------------------------
# 2. SemanticIndex -- registration / introspection
# ---------------------------------------------------------------------------


class TestSemanticIndexRegistration:
    def test_register_concept_to_kos(self) -> None:
        idx = SemanticIndex()
        idx.register_concept_to_kos({"forest": ["ko_1", "ko_2"]})
        assert idx.concept_to_kos("forest") == ("ko_1", "ko_2")

    def test_register_concept_replaces_previous(self) -> None:
        idx = SemanticIndex()
        idx.register_concept_to_kos({"forest": ["ko_1"]})
        idx.register_concept_to_kos({"forest": ["ko_2", "ko_3"]})
        assert idx.concept_to_kos("forest") == ("ko_2", "ko_3")

    def test_add_concept_to_ko(self) -> None:
        idx = SemanticIndex()
        idx.add_concept_to_ko("forest", "ko_1")
        idx.add_concept_to_ko("forest", "ko_2")
        idx.add_concept_to_ko("forest", "ko_2")  # duplicate -> ignored
        assert sorted(idx.concept_to_kos("forest")) == ["ko_1", "ko_2"]

    def test_register_aliases_lowercases(self) -> None:
        idx = SemanticIndex()
        idx.register_aliases({"WILD": "forest"})
        assert idx.resolve_alias("wild") == "forest"
        assert idx.resolve_alias("WILD") == "forest"

    def test_register_alias_skips_empty_keys(self) -> None:
        idx = SemanticIndex()
        idx.register_aliases({"": "forest", "  ": "forest"})
        assert idx.resolve_alias("") is None
        assert idx.resolve_alias("  ") is None

    def test_resolve_alias_unknown_returns_none(self) -> None:
        idx = SemanticIndex()
        idx.register_aliases({"wild": "forest"})
        assert idx.resolve_alias("not_there") is None

    def test_register_taxonomy_nodes(self) -> None:
        idx = SemanticIndex()
        idx.register_taxonomy_nodes([
            {"node_id": "a", "parent_node_id": "b",
             "aliases": ["alpha"], "label": "A"},
            {"node_id": "b", "parent_node_id": None,
             "aliases": [], "label": "B"},
        ])
        nodes = idx.taxonomy_nodes()
        assert "a" in nodes
        assert "b" in nodes
        assert nodes["a"]["parent_node_id"] == "b"

    def test_register_taxonomy_skips_invalid(self) -> None:
        idx = SemanticIndex()
        idx.register_taxonomy_nodes([
            {"node_id": "", "parent_node_id": None},
            {"node_id": 42, "parent_node_id": None},
            {"no_node_id_field": True},
        ])
        assert idx.taxonomy_nodes() == {}

    def test_concepts_returns_sorted(self) -> None:
        idx = SemanticIndex()
        idx.register_concept_to_kos({
            "zoo": [],
            "alpha": [],
            "mike": [],
        })
        assert idx.concepts() == ("alpha", "mike", "zoo")

    def test_len_reflects_total_registrations(self) -> None:
        idx = SemanticIndex()
        idx.register_concept_to_kos({"a": ["x"], "b": ["y"]})
        idx.register_aliases({"k1": "a", "k2": "b"})
        idx.register_taxonomy_nodes([
            {"node_id": "n1", "parent_node_id": None},
            {"node_id": "n2", "parent_node_id": "n1"},
        ])
        assert len(idx) == 6  # 2 concepts + 2 aliases + 2 nodes


# ---------------------------------------------------------------------------
# 3. Hierarchy traversal
# ---------------------------------------------------------------------------


class TestHierarchyTraversal:
    def test_ancestors_single_step(self, built_index) -> None:
        assert built_index.ancestors_of("forest", max_depth=1) == ["nature"]
        assert built_index.ancestors_of("deep-forest", max_depth=1) == [
            "forest"
        ]

    def test_ancestors_two_steps(self, built_index) -> None:
        # deep-forest -> forest -> nature
        assert built_index.ancestors_of(
            "deep-forest", max_depth=2
        ) == ["forest", "nature"]

    def test_ancestors_zero_depth(self, built_index) -> None:
        assert built_index.ancestors_of("forest", max_depth=0) == []

    def test_ancestors_root_has_no_parent(self, built_index) -> None:
        assert built_index.ancestors_of("nature", max_depth=3) == []

    def test_ancestors_unknown_concept(self, built_index) -> None:
        assert built_index.ancestors_of("ghost", max_depth=1) == []

    def test_descendants_single_step(self, built_index) -> None:
        # forest's child is deep-forest; nature has
        # forest / ocean / park as direct children.
        assert built_index.descendants_of(
            "forest", max_depth=1
        ) == ["deep-forest"]
        assert sorted(built_index.descendants_of("nature", max_depth=1)) == [
            "forest",
            "ocean",
            "park",
        ]

    def test_descendants_zero_depth(self, built_index) -> None:
        assert built_index.descendants_of("forest", max_depth=0) == []

    def test_descendants_no_children(self, built_index) -> None:
        assert built_index.descendants_of("deep-forest", max_depth=1) == []

    def test_descendants_unknown_concept(self, built_index) -> None:
        assert built_index.descendants_of("ghost", max_depth=1) == []


# ---------------------------------------------------------------------------
# 4. Engine scoring paths
# ---------------------------------------------------------------------------


class TestSemanticEngineScoring:
    def test_engine_class_name(self) -> None:
        idx = SemanticIndex()
        engine = SemanticRetrievalEngine(idx)
        assert engine.ENGINE_NAME == "SemanticRetrievalEngine V1"

    def test_index_type_check(self) -> None:
        with pytest.raises(TypeError):
            SemanticRetrievalEngine("not-an-index")  # type: ignore[arg-type]

    def test_alias_resolution_path(
        self, three_kos, built_index
    ) -> None:
        # "wild" -> alias -> forest -> ko_forest_v1
        # Score = SCORE_ALIAS = 0.85
        engine = SemanticRetrievalEngine(built_index)
        q = RetrievalQuery(query_text="wild")
        r = engine.execute(q, three_kos)
        assert r.success is True
        assert r.total_hits == 1
        assert r.hits[0].knowledge_id == "ko_forest_v1"
        assert r.hits[0].match_score == SCORE_ALIAS

    def test_literal_concept_path(
        self, three_kos, built_index
    ) -> None:
        # "forest" token is a registered concept -> exact
        # Score = SCORE_EXACT = 1.0
        engine = SemanticRetrievalEngine(built_index)
        q = RetrievalQuery(query_text="forest")
        r = engine.execute(q, three_kos)
        assert r.success is True
        assert r.total_hits == 1
        assert r.hits[0].knowledge_id == "ko_forest_v1"
        assert r.hits[0].match_score == SCORE_EXACT

    def test_ancestor_expansion(self, three_kos, built_index) -> None:
        # "deep-forest" -> ancestor forest -> ancestor nature.
        # KOs from "forest" (exact) win, but if we ask
        # only for an unknown concept that has a known
        # parent in concept_to_kos, ancestor still hits.
        # Use "deep-forest" which is registered; its
        # ancestor "forest" maps to ko_forest_v1.
        engine = SemanticRetrievalEngine(built_index, ancestor_depth=1)
        q = RetrievalQuery(query_text="deep-forest")
        r = engine.execute(q, three_kos)
        assert r.success is True
        assert r.total_hits == 1
        assert r.hits[0].knowledge_id == "ko_forest_v1"
        # deep-forest -> exact -> SCORE_EXACT
        # forest (ancestor) -> SCORE_ANCESTOR
        # max wins: SCORE_EXACT
        assert r.hits[0].match_score == SCORE_EXACT

    def test_descendant_expansion(self, three_kos, built_index) -> None:
        # "nature" concept -> descendants include forest /
        # ocean / park. Each maps to a KO. All three
        # KOs hit with SCORE_DESCENDANT.
        engine = SemanticRetrievalEngine(
            built_index, ancestor_depth=0, descendant_depth=1
        )
        q = RetrievalQuery(query_text="nature")
        r = engine.execute(q, three_kos)
        assert r.success is True
        assert r.total_hits == 3
        for h in r.hits:
            assert h.match_score == SCORE_DESCENDANT

    def test_descendant_ancestor_combined(
        self, three_kos, built_index
    ) -> None:
        # "nature" with both depths -> descendants hit
        # SCORE_DESCENDANT; ancestors (none) skipped.
        engine = SemanticRetrievalEngine(
            built_index, ancestor_depth=1, descendant_depth=1
        )
        q = RetrievalQuery(query_text="nature")
        r = engine.execute(q, three_kos)
        # All three KOs from descendant expansion;
        # ancestor expansion has no parent.
        assert r.total_hits == 3
        assert all(
            h.match_score == SCORE_DESCENDANT for h in r.hits
        )

    def test_per_ko_max_aggregation(
        self, three_kos, built_index
    ) -> None:
        # ko_forest_v1 is associated with both "forest"
        # (exact) and "nature" (descendant). The max score
        # wins -> 1.0.
        engine = SemanticRetrievalEngine(
            built_index, ancestor_depth=0, descendant_depth=1
        )
        q = RetrievalQuery(query_text="forest nature")
        r = engine.execute(q, three_kos)
        forest_hit = next(
            h for h in r.hits if h.knowledge_id == "ko_forest_v1"
        )
        assert forest_hit.match_score == SCORE_EXACT

    def test_filter_gate_excludes(self, three_kos, built_index) -> None:
        # Force ocean KO out via filter theme=forest.
        engine = SemanticRetrievalEngine(
            built_index, ancestor_depth=0, descendant_depth=1,
        )
        q = RetrievalQuery(
            query_text="nature", filters={"theme": "ocean"}
        )
        r = engine.execute(q, three_kos)
        # Only ko_ocean_v1 has theme=ocean.
        assert r.total_hits == 1
        assert r.hits[0].knowledge_id == "ko_ocean_v1"
        # nature is descendant -> SCORE_DESCENDANT
        assert r.hits[0].match_score == SCORE_DESCENDANT

    def test_limit_caps_output(self, three_kos, built_index) -> None:
        engine = SemanticRetrievalEngine(
            built_index, ancestor_depth=0, descendant_depth=1
        )
        q = RetrievalQuery(query_text="nature", limit=1)
        r = engine.execute(q, three_kos)
        assert r.total_hits == 1

    def test_sort_by_score_descending(self, three_kos, built_index) -> None:
        engine = SemanticRetrievalEngine(
            built_index, ancestor_depth=0, descendant_depth=1
        )
        q = RetrievalQuery(
            query_text="forest nature ocean",
            sort_by="score", sort_order="desc", limit=10,
        )
        r = engine.execute(q, three_kos)
        scores = [h.match_score for h in r.hits]
        assert scores == sorted(scores, reverse=True)

    def test_sort_by_score_ascending(self, three_kos, built_index) -> None:
        engine = SemanticRetrievalEngine(
            built_index, ancestor_depth=0, descendant_depth=1
        )
        q = RetrievalQuery(
            query_text="forest ocean",
            sort_by="score", sort_order="asc", limit=10,
        )
        r = engine.execute(q, three_kos)
        scores = [h.match_score for h in r.hits]
        assert scores == sorted(scores)

    def test_unknown_query_returns_empty(
        self, three_kos, built_index
    ) -> None:
        engine = SemanticRetrievalEngine(built_index)
        q = RetrievalQuery(query_text="xyzzy")
        r = engine.execute(q, three_kos)
        assert r.success is True
        assert r.total_hits == 0

    def test_kos_not_mutated(self, three_kos, built_index) -> None:
        before = [
            (k.knowledge_id, k.title, k.theme) for k in three_kos
        ]
        engine = SemanticRetrievalEngine(built_index)
        engine.execute(
            RetrievalQuery(query_text="forest"), three_kos
        )
        after = [
            (k.knowledge_id, k.title, k.theme) for k in three_kos
        ]
        assert before == after

    def test_index_not_mutated(self, three_kos, built_index) -> None:
        # Capture the index's current state.
        before_concepts = sorted(built_index.concepts())
        before_aliases = dict(built_index.aliases())
        before_nodes = dict(built_index.taxonomy_nodes())
        engine = SemanticRetrievalEngine(built_index)
        engine.execute(
            RetrievalQuery(query_text="forest"), three_kos
        )
        # The engine only reads; nothing should change.
        assert sorted(built_index.concepts()) == before_concepts
        assert dict(built_index.aliases()) == before_aliases
        assert dict(built_index.taxonomy_nodes()) == before_nodes

    def test_dict_shaped_ko_supported(
        self, built_index
    ) -> None:
        ko_dict = {
            "knowledge_id": "ko_forest_v1",
            "version": 2,
            "title": "Forest",
            "description": "",
            "category": "kindergarten",
            "project_type": "kindergarten",
            "site_type": "outdoor",
            "location_type": "urban",
            "space_size": "medium",
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
        engine = SemanticRetrievalEngine(built_index)
        r = engine.execute(
            RetrievalQuery(query_text="forest"), [ko_dict]
        )
        assert r.success is True
        assert r.total_hits == 1
        assert r.hits[0].knowledge_id == "ko_forest_v1"
        assert r.hits[0].knowledge_version == 2

    def test_ko_not_in_corpus_but_in_index_is_skipped(
        self, built_index
    ) -> None:
        # The index says ko_phantom belongs to "forest",
        # but the corpus does not include it. The engine
        # must not fabricate a KO.
        idx = SemanticIndex()
        idx.register_concept_to_kos({"forest": ["ko_phantom"]})
        idx.register_taxonomy_nodes([
            {"node_id": "forest", "parent_node_id": None},
        ])
        engine = SemanticRetrievalEngine(idx)
        r = engine.execute(
            RetrievalQuery(query_text="forest"), []
        )
        assert r.success is True
        assert r.total_hits == 0

    def test_invalid_query_short_circuits(
        self, three_kos, built_index
    ) -> None:
        # Q7 fails -- no input signal of any kind.
        engine = SemanticRetrievalEngine(built_index)
        q = RetrievalQuery()  # no text, no fields, no filters
        r = engine.execute(q, three_kos)
        assert r.success is False
        assert r.total_hits == 0

    def test_score_constants_match_design(self) -> None:
        # The V1 contract pins these scores -- they are
        # part of the foundation's surface.
        assert SCORE_EXACT == 1.00
        assert SCORE_ALIAS == 0.85
        assert SCORE_ANCESTOR == 0.70
        assert SCORE_DESCENDANT == 0.60


# ---------------------------------------------------------------------------
# 5. End-to-end smoke (with hybrid layer)
# ---------------------------------------------------------------------------


class TestSemanticEndToEnd:
    def test_semantic_engine_plugs_into_hybrid(
        self, three_kos, built_index
    ) -> None:
        from caseos.knowledge.retrieval.hybrid import (
            HybridRetrievalEngine,
            LambdaSubEngine,
            MaxScoreFusion,
        )

        sem = SemanticRetrievalEngine(built_index)
        hybrid = HybridRetrievalEngine(
            sub_engines=[
                LambdaSubEngine("semantic", sem.execute),
            ],
            fusion=MaxScoreFusion(),
        )
        q = RetrievalQuery(query_text="wild")
        r = hybrid.execute(q, three_kos)
        assert r.success is True
        assert r.total_hits >= 1


# ---------------------------------------------------------------------------
# 6. AST architecture boundary
# ---------------------------------------------------------------------------


class TestSemanticArchitectureBoundary:
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

    def test_semantic_engine_has_no_forbidden_imports(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "retrieval"
            / "semantic.py"
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

    def test_does_not_import_embedding_or_vector_modules(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "retrieval"
            / "semantic.py"
        )
        source = path.read_text(encoding="utf-8-sig").lower()
        # Use word-boundary regex so substrings inside
        # longer identifiers / docstring prose do not
        # produce false positives.
        for forbidden in (
            "openai", "anthropic", "transformers", "torch",
            "tensorflow", "faiss", "chromadb", "pinecone",
            "weaviate", "sentence_transformers",
        ):
            pattern = r"(?<![A-Za-z0-9_])" + re.escape(forbidden) + r"(?![A-Za-z0-9_])"
            assert not re.search(pattern, source), (
                "Found forbidden dependency reference: " + forbidden
            )
