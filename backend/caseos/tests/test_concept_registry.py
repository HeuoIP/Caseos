"""Tests for Semantic Concept Registry V1 (Sprint 24.1-B).

Coverage:

    * ConceptRecord frozen contract (frozen, JSON round-trip)
    * ConceptRecord structural guards
    * ConceptRegistry append-only contract
    * ConceptRegistry hierarchy traversal
    * ConceptAliasRecord + ConceptAliasRegistry
    * build_semantic_index bridge to Sprint 24.1-A
    * AST architecture boundary
        The concept registry does NOT import from:
            * caseos.intelligence.*
            * caseos.knowledge.evolution
            * caseos.knowledge.governance
            * caseos.knowledge.intake
            * caseos.knowledge.feedback
            * caseos.brain.*

Architecture boundary (Sprint 24.1-B spec):

    These tests do NOT import forbidden modules.
    These tests MAY import from:
        * caseos.knowledge.object
        * caseos.knowledge.{domain,binding,taxonomy,
                            attribute,graph}
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

from caseos.knowledge.retrieval.concept_registry import (  # noqa: E402
    CONCEPT_TYPE_ALLOW_LIST,
    DEFAULT_LOCALE,
    AliasRegistryError,
    ConceptAliasRecord,
    ConceptAliasRecordError,
    ConceptAliasRegistry,
    ConceptRecord,
    ConceptRecordError,
    ConceptRegistry,
    ConceptRegistryError,
    build_semantic_index,
)
from caseos.knowledge.retrieval.semantic import (  # noqa: E402
    SemanticIndex,
    SemanticRetrievalEngine,
)


# ---------------------------------------------------------------------------
# 1. ConceptRecord frozen contract
# ---------------------------------------------------------------------------


class TestConceptRecordFrozenContract:
    def test_default_construction(self) -> None:
        r = ConceptRecord(concept_id="forest")
        assert r.concept_id == "forest"
        assert r.version == 1
        assert r.concept_type == "theme"
        assert r.parent_concept_id is None
        assert r.knowledge_object_ids == ()
        assert r.aliases == ()

    def test_is_frozen(self) -> None:
        r = ConceptRecord(concept_id="forest")
        with pytest.raises(Exception):
            r.concept_id = "ocean"  # type: ignore[misc]

    def test_rejects_empty_concept_id(self) -> None:
        with pytest.raises(ConceptRecordError):
            ConceptRecord(concept_id="")

    def test_rejects_non_positive_version(self) -> None:
        with pytest.raises(ConceptRecordError):
            ConceptRecord(concept_id="forest", version=0)

    def test_rejects_unknown_concept_type(self) -> None:
        with pytest.raises(ConceptRecordError):
            ConceptRecord(concept_id="forest", concept_type="emotion")

    def test_accepts_all_allow_list_types(self) -> None:
        for ct in CONCEPT_TYPE_ALLOW_LIST:
            r = ConceptRecord(concept_id=f"c_{ct}", concept_type=ct)
            assert r.concept_type == ct

    def test_rejects_empty_parent_concept_id(self) -> None:
        with pytest.raises(ConceptRecordError):
            ConceptRecord(concept_id="x", parent_concept_id="")

    def test_collection_fields_are_defensively_copied(self) -> None:
        kos = ["ko_1", "ko_2"]
        aliases = ["wild"]
        r = ConceptRecord(
            concept_id="forest",
            knowledge_object_ids=kos,
            aliases=aliases,
        )
        kos.append("ko_3")
        aliases.append("wild-2")
        assert r.knowledge_object_ids == ("ko_1", "ko_2")
        assert r.aliases == ("wild",)

    def test_to_dict_round_trip(self) -> None:
        r = ConceptRecord(
            concept_id="forest",
            version=2,
            label="Forest",
            description="All forest designs",
            concept_type="theme",
            parent_concept_id="nature",
            knowledge_object_ids=("ko_1", "ko_2"),
            aliases=("wild", "wood"),
            created_by="alice",
        )
        d = r.to_dict()
        r2 = ConceptRecord.from_dict(d)
        assert r == r2

    def test_from_dict_rejects_non_mapping(self) -> None:
        with pytest.raises(ConceptRecordError):
            ConceptRecord.from_dict(["not", "a", "mapping"])  # type: ignore[arg-type]

    def test_from_dict_collection_field_wrong_type(self) -> None:
        with pytest.raises(ConceptRecordError):
            ConceptRecord.from_dict({
                "concept_id": "forest",
                "knowledge_object_ids": "not-a-list",
            })


# ---------------------------------------------------------------------------
# 2. ConceptRegistry append-only contract
# ---------------------------------------------------------------------------


class TestConceptRegistryAppendOnly:
    def test_empty_registry(self) -> None:
        r = ConceptRegistry()
        assert r.count() == 0
        assert r.list() == []
        assert r.concept_ids() == []
        assert r.roots() == []

    def test_append_returns_record(self) -> None:
        r = ConceptRegistry()
        rec = ConceptRecord(concept_id="forest")
        out = r.append(rec)
        assert out is rec
        assert r.count() == 1

    def test_append_rejects_non_record(self) -> None:
        r = ConceptRegistry()
        with pytest.raises(ConceptRegistryError):
            r.append({"concept_id": "x"})  # type: ignore[arg-type]

    def test_get_returns_first_match(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="forest", version=1))
        r.append(ConceptRecord(concept_id="forest", version=2))
        assert r.get("forest").version == 1
        assert r.get("ghost") is None

    def test_get_with_non_string_returns_none(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="forest"))
        assert r.get(42) is None  # type: ignore[arg-type]

    def test_for_concept_type_filters(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="a", concept_type="theme"))
        r.append(ConceptRecord(concept_id="b", concept_type="style"))
        r.append(ConceptRecord(concept_id="c", concept_type="theme"))
        themes = r.for_concept_type("theme")
        assert sorted(rec.concept_id for rec in themes) == ["a", "c"]

    def test_concept_ids_returns_in_registration_order(self) -> None:
        r = ConceptRegistry()
        for cid in ("z", "a", "m"):
            r.append(ConceptRecord(concept_id=cid))
        assert r.concept_ids() == ["z", "a", "m"]

    def test_concept_ids_dedups(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="forest", version=1))
        r.append(ConceptRecord(concept_id="forest", version=2))
        assert r.concept_ids() == ["forest"]

    def test_roots_returns_records_with_no_parent(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="root1"))
        r.append(ConceptRecord(concept_id="root2"))
        r.append(ConceptRecord(concept_id="child", parent_concept_id="root1"))
        roots = r.roots()
        assert sorted(rec.concept_id for rec in roots) == [
            "root1", "root2",
        ]

    def test_children_of(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="nature"))
        r.append(ConceptRecord(concept_id="forest", parent_concept_id="nature"))
        r.append(ConceptRecord(concept_id="ocean", parent_concept_id="nature"))
        r.append(ConceptRecord(concept_id="deep-forest", parent_concept_id="forest"))
        children = r.children_of("nature")
        assert sorted(rec.concept_id for rec in children) == [
            "forest", "ocean",
        ]

    def test_ancestors_of_single_step(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="nature"))
        r.append(ConceptRecord(concept_id="forest", parent_concept_id="nature"))
        anc = r.ancestors_of("forest", max_depth=1)
        assert [rec.concept_id for rec in anc] == ["nature"]

    def test_ancestors_of_two_steps(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="nature"))
        r.append(ConceptRecord(concept_id="forest", parent_concept_id="nature"))
        r.append(ConceptRecord(concept_id="deep", parent_concept_id="forest"))
        anc = r.ancestors_of("deep", max_depth=2)
        assert [rec.concept_id for rec in anc] == ["forest", "nature"]

    def test_ancestors_zero_depth(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="nature"))
        r.append(ConceptRecord(concept_id="forest", parent_concept_id="nature"))
        assert r.ancestors_of("forest", max_depth=0) == []

    def test_ancestors_of_root_is_empty(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="root"))
        assert r.ancestors_of("root", max_depth=3) == []

    def test_ancestors_unknown_concept(self) -> None:
        r = ConceptRegistry()
        assert r.ancestors_of("ghost", max_depth=1) == []

    def test_descendants_single_step(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="nature"))
        r.append(ConceptRecord(concept_id="forest", parent_concept_id="nature"))
        r.append(ConceptRecord(concept_id="ocean", parent_concept_id="nature"))
        r.append(ConceptRecord(concept_id="deep-forest", parent_concept_id="forest"))
        desc = r.descendants_of("nature", max_depth=1)
        assert sorted(rec.concept_id for rec in desc) == [
            "forest", "ocean",
        ]

    def test_descendants_two_steps_includes_grandchildren(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="nature"))
        r.append(ConceptRecord(concept_id="forest", parent_concept_id="nature"))
        r.append(ConceptRecord(concept_id="deep", parent_concept_id="forest"))
        desc = r.descendants_of("nature", max_depth=2)
        assert sorted(rec.concept_id for rec in desc) == [
            "deep", "forest",
        ]

    def test_descendants_zero_depth(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="nature"))
        assert r.descendants_of("nature", max_depth=0) == []

    def test_descendants_unknown_concept(self) -> None:
        r = ConceptRegistry()
        assert r.descendants_of("ghost", max_depth=1) == []

    def test_list_returns_shallow_copy(self) -> None:
        r = ConceptRegistry()
        r.append(ConceptRecord(concept_id="a"))
        snap = r.list()
        r.append(ConceptRecord(concept_id="b"))
        assert len(snap) == 1
        assert len(r.list()) == 2

    def test_forbidden_update(self) -> None:
        r = ConceptRegistry()
        with pytest.raises(TypeError):
            r.update()

    def test_forbidden_delete(self) -> None:
        r = ConceptRegistry()
        with pytest.raises(TypeError):
            r.delete("forest")

    def test_forbidden_overwrite(self) -> None:
        r = ConceptRegistry()
        with pytest.raises(TypeError):
            r.overwrite()

    def test_forbidden_clear(self) -> None:
        r = ConceptRegistry()
        with pytest.raises(TypeError):
            r.clear()


# ---------------------------------------------------------------------------
# 3. ConceptAliasRecord / AliasRegistry
# ---------------------------------------------------------------------------


class TestConceptAliasRecord:
    def test_default_construction(self) -> None:
        a = ConceptAliasRecord(
            alias_id="a1",
            alias="wild",
            canonical_concept_id="forest",
        )
        assert a.locale == DEFAULT_LOCALE
        assert a.alias == "wild"
        assert a.version == 1

    def test_alias_is_lowercased(self) -> None:
        a = ConceptAliasRecord(
            alias_id="a1",
            alias="WILD",
            canonical_concept_id="forest",
        )
        assert a.alias == "wild"

    def test_alias_is_stripped(self) -> None:
        a = ConceptAliasRecord(
            alias_id="a1",
            alias="  wild  ",
            canonical_concept_id="forest",
        )
        assert a.alias == "wild"

    def test_rejects_empty_alias_id(self) -> None:
        with pytest.raises(ConceptAliasRecordError):
            ConceptAliasRecord(
                alias_id="",
                alias="wild",
                canonical_concept_id="forest",
            )

    def test_rejects_empty_alias(self) -> None:
        with pytest.raises(ConceptAliasRecordError):
            ConceptAliasRecord(
                alias_id="a1",
                alias="",
                canonical_concept_id="forest",
            )

    def test_rejects_empty_canonical_id(self) -> None:
        with pytest.raises(ConceptAliasRecordError):
            ConceptAliasRecord(
                alias_id="a1",
                alias="wild",
                canonical_concept_id="",
            )

    def test_rejects_non_positive_version(self) -> None:
        with pytest.raises(ConceptAliasRecordError):
            ConceptAliasRecord(
                alias_id="a1",
                alias="wild",
                canonical_concept_id="forest",
                version=0,
            )

    def test_is_frozen(self) -> None:
        a = ConceptAliasRecord(
            alias_id="a1",
            alias="wild",
            canonical_concept_id="forest",
        )
        with pytest.raises(Exception):
            a.alias = "sea"  # type: ignore[misc]

    def test_to_dict_round_trip(self) -> None:
        a = ConceptAliasRecord(
            alias_id="a1",
            alias="wild",
            canonical_concept_id="forest",
            locale="zh",
        )
        d = a.to_dict()
        a2 = ConceptAliasRecord.from_dict(d)
        assert a == a2


class TestConceptAliasRegistry:
    def test_empty_registry(self) -> None:
        r = ConceptAliasRegistry()
        assert r.count() == 0
        assert r.list() == []
        assert r.alias_ids() == []

    def test_append(self) -> None:
        r = ConceptAliasRegistry()
        a = ConceptAliasRecord(
            alias_id="a1",
            alias="wild",
            canonical_concept_id="forest",
        )
        r.append(a)
        assert r.count() == 1

    def test_append_rejects_non_record(self) -> None:
        r = ConceptAliasRegistry()
        with pytest.raises(AliasRegistryError):
            r.append({"alias": "wild"})  # type: ignore[arg-type]

    def test_get(self) -> None:
        r = ConceptAliasRegistry()
        a = ConceptAliasRecord(
            alias_id="a1",
            alias="wild",
            canonical_concept_id="forest",
        )
        r.append(a)
        assert r.get("a1") is a
        assert r.get("missing") is None

    def test_resolve_case_insensitive(self) -> None:
        r = ConceptAliasRegistry()
        r.append(ConceptAliasRecord(
            alias_id="a1",
            alias="wild",
            canonical_concept_id="forest",
        ))
        assert r.resolve("wild") == "forest"
        assert r.resolve("WILD") == "forest"
        assert r.resolve(" Wild ") == "forest"

    def test_resolve_unknown(self) -> None:
        r = ConceptAliasRegistry()
        assert r.resolve("ghost") is None
        assert r.resolve(None) is None  # type: ignore[arg-type]
        assert r.resolve(42) is None  # type: ignore[arg-type]

    def test_resolve_empty(self) -> None:
        r = ConceptAliasRegistry()
        assert r.resolve("") is None
        assert r.resolve("   ") is None

    def test_for_concept(self) -> None:
        r = ConceptAliasRegistry()
        r.append(ConceptAliasRecord(
            alias_id="a1", alias="wild", canonical_concept_id="forest",
        ))
        r.append(ConceptAliasRecord(
            alias_id="a2", alias="wood", canonical_concept_id="forest",
        ))
        r.append(ConceptAliasRecord(
            alias_id="a3", alias="sea", canonical_concept_id="ocean",
        ))
        forest_aliases = r.for_concept("forest")
        assert sorted(a.alias for a in forest_aliases) == ["wild", "wood"]

    def test_forbidden_operations(self) -> None:
        r = ConceptAliasRegistry()
        with pytest.raises(TypeError):
            r.update()
        with pytest.raises(TypeError):
            r.delete("a1")
        with pytest.raises(TypeError):
            r.overwrite()
        with pytest.raises(TypeError):
            r.clear()


# ---------------------------------------------------------------------------
# 4. Bridge: build_semantic_index
# ---------------------------------------------------------------------------


class TestBuildSemanticIndexBridge:
    def test_bridge_produces_semantic_index(self) -> None:
        cr = ConceptRegistry()
        cr.append(ConceptRecord(
            concept_id="forest",
            concept_type="theme",
            label="Forest",
            knowledge_object_ids=("ko_forest_v1",),
            aliases=("wild",),
        ))
        ar = ConceptAliasRegistry()
        ar.append(ConceptAliasRecord(
            alias_id="a1", alias="wild", canonical_concept_id="forest",
        ))
        idx = build_semantic_index(cr, ar)
        assert isinstance(idx, SemanticIndex)

    def test_bridge_populates_concept_to_kos(self) -> None:
        cr = ConceptRegistry()
        cr.append(ConceptRecord(
            concept_id="forest",
            knowledge_object_ids=("ko_1", "ko_2"),
        ))
        cr.append(ConceptRecord(
            concept_id="ocean",
            knowledge_object_ids=("ko_3",),
        ))
        ar = ConceptAliasRegistry()
        idx = build_semantic_index(cr, ar)
        assert sorted(idx.concept_to_kos("forest")) == ["ko_1", "ko_2"]
        assert sorted(idx.concept_to_kos("ocean")) == ["ko_3"]

    def test_bridge_populates_aliases(self) -> None:
        cr = ConceptRegistry()
        cr.append(ConceptRecord(
            concept_id="forest",
            aliases=("wild", "wood"),
        ))
        ar = ConceptAliasRegistry()
        ar.append(ConceptAliasRecord(
            alias_id="a1", alias="sea", canonical_concept_id="ocean",
        ))
        idx = build_semantic_index(cr, ar)
        aliases = idx.aliases()
        assert aliases["wild"] == "forest"
        assert aliases["wood"] == "forest"
        assert aliases["sea"] == "ocean"

    def test_bridge_resolves_alias_via_index(self) -> None:
        cr = ConceptRegistry()
        cr.append(ConceptRecord(
            concept_id="forest",
            knowledge_object_ids=("ko_forest_v1",),
        ))
        ar = ConceptAliasRegistry()
        ar.append(ConceptAliasRecord(
            alias_id="a1", alias="wild", canonical_concept_id="forest",
        ))
        idx = build_semantic_index(cr, ar)
        assert idx.resolve_alias("wild") == "forest"
        assert idx.resolve_alias("WILD") == "forest"

    def test_bridge_populates_taxonomy_nodes(self) -> None:
        cr = ConceptRegistry()
        cr.append(ConceptRecord(
            concept_id="nature",
            label="Nature",
        ))
        cr.append(ConceptRecord(
            concept_id="forest",
            parent_concept_id="nature",
            label="Forest",
        ))
        ar = ConceptAliasRegistry()
        idx = build_semantic_index(cr, ar)
        nodes = idx.taxonomy_nodes()
        assert "nature" in nodes
        assert "forest" in nodes
        assert nodes["forest"]["parent_node_id"] == "nature"

    def test_bridge_rejects_non_registry_inputs(self) -> None:
        with pytest.raises(ConceptRegistryError):
            build_semantic_index("not-a-registry", ConceptAliasRegistry())
        with pytest.raises(AliasRegistryError):
            build_semantic_index(ConceptRegistry(), "not-a-registry")

    def test_bridge_dedups_concept_to_kos(self) -> None:
        # If the same ko_id appears twice (denormalized),
        # the bridge keeps only the first occurrence.
        cr = ConceptRegistry()
        cr.append(ConceptRecord(
            concept_id="forest",
            knowledge_object_ids=("ko_1", "ko_1", "ko_2"),
        ))
        ar = ConceptAliasRegistry()
        idx = build_semantic_index(cr, ar)
        assert sorted(idx.concept_to_kos("forest")) == ["ko_1", "ko_2"]

    def test_bridge_with_empty_registries(self) -> None:
        idx = build_semantic_index(ConceptRegistry(), ConceptAliasRegistry())
        assert isinstance(idx, SemanticIndex)
        assert idx.concepts() == ()
        assert idx.aliases() == {}


# ---------------------------------------------------------------------------
# 5. End-to-end: registry -> index -> engine
# ---------------------------------------------------------------------------


class TestRegistryToEngine:
    def test_registry_drives_semantic_engine(self) -> None:
        cr = ConceptRegistry()
        cr.append(ConceptRecord(
            concept_id="forest",
            concept_type="theme",
            label="Forest",
            knowledge_object_ids=("ko_forest_v1",),
            parent_concept_id="nature",
        ))
        cr.append(ConceptRecord(
            concept_id="ocean",
            concept_type="theme",
            label="Ocean",
            knowledge_object_ids=("ko_ocean_v1",),
            parent_concept_id="nature",
        ))
        cr.append(ConceptRecord(
            concept_id="nature",
            concept_type="theme",
            label="Nature",
        ))
        ar = ConceptAliasRegistry()
        ar.append(ConceptAliasRecord(
            alias_id="a1", alias="wild", canonical_concept_id="forest",
        ))
        idx = build_semantic_index(cr, ar)

        from caseos.knowledge.object.object import KnowledgeObject
        from caseos.knowledge.retrieval.object import RetrievalQuery

        kos = [
            KnowledgeObject(
                knowledge_id="ko_forest_v1", version=1,
                title="Forest KG", description="",
                category="kindergarten", project_type="kindergarten",
                site_type="outdoor", location_type="urban",
                space_size="medium", theme="forest",
                style="natural", color_system="green",
                interaction_type="exploration",
            ),
            KnowledgeObject(
                knowledge_id="ko_ocean_v1", version=1,
                title="Ocean KG", description="",
                category="kindergarten", project_type="kindergarten",
                site_type="outdoor", location_type="urban",
                space_size="medium", theme="ocean",
                style="modern", color_system="blue",
                interaction_type="sensory",
            ),
        ]
        engine = SemanticRetrievalEngine(idx)
        r = engine.execute(RetrievalQuery(query_text="wild"), kos)
        assert r.success is True
        assert r.total_hits == 1
        assert r.hits[0].knowledge_id == "ko_forest_v1"


# ---------------------------------------------------------------------------
# 6. AST architecture boundary
# ---------------------------------------------------------------------------


class TestConceptRegistryArchitectureBoundary:
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

    def test_concept_registry_has_no_forbidden_imports(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "retrieval"
            / "concept_registry.py"
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

    def test_no_third_party_ai_dependencies(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "retrieval"
            / "concept_registry.py"
        )
        source = path.read_text(encoding="utf-8-sig").lower()
        for forbidden in (
            "openai", "anthropic", "transformers", "torch",
            "tensorflow", "faiss", "chromadb", "pinecone",
            "weaviate", "sentence_transformers",
        ):
            pattern = (
                r"(?<![A-Za-z0-9_])" + forbidden + r"(?![A-Za-z0-9_])"
            )
            import re
            assert not re.search(pattern, source), (
                "Found forbidden dependency reference: " + forbidden
            )
