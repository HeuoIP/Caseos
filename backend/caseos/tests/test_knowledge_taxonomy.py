"""Knowledge Taxonomy Schema V1 tests (Sprint 23.1-C).

测试范围：

    * Taxonomy 字段完整性、frozen、JSON round-trip
    * TaxonomyNode 字段完整性、frozen、JSON round-trip
    * TaxonomyValidator（单记录 + 跨记录）
    * TaxonomyRegistry append-only 契约
    * 层级不变量：父子关系、无自引用
    * nodes_for_taxonomy / children_of / roots 查询
    * Markdown 报告
    * Architecture boundary (AST scan)
    * KO / Domain / Binding 不被 taxonomy 修改

不在测试范围内：

    * Pipeline wiring
    * Intelligence / Retrieval / Evolution
    * 自动分类 / 自动标签
"""
from __future__ import annotations

import ast
import dataclasses
import json
import pathlib

import pytest

from caseos.knowledge.taxonomy import (
    NODE_FIELD_TYPES,
    NODE_REQUIRED_FIELDS,
    NODE_TYPE_ALLOW_LIST,
    REQUIRED_FIELDS,
    TAXONOMY_CONTENT_FIELDS,
    TAXONOMY_IDENTITY_FIELDS,
    TAXONOMY_METADATA_FIELDS,
    TAXONOMY_TYPE_ALLOW_LIST,
    VERSION_POLICY,
    Taxonomy,
    TaxonomyError,
    TaxonomyNode,
    TaxonomyNodeError,
    TaxonomyNodeSchemaError,
    TaxonomyRegistry,
    TaxonomyRegistryError,
    TaxonomySchemaError,
    TaxonomyValidationResult,
    TaxonomyValidator,
    generate_taxonomy_report,
)


NOW_ISO = "2026-08-04T00:00:00Z"
TAX_ID = "tax-style-1"
NODE_SCANDI = "node-scandi"
NODE_INDUSTRIAL = "node-industrial"
NODE_WARM = "node-warm"


def _make_taxonomy(**overrides) -> Taxonomy:
    base = dict(
        taxonomy_id=TAX_ID,
        version=1,
        name="Design Style Taxonomy",
        description="Hierarchical design styles",
        taxonomy_type="style",
        root_node_ids=[NODE_SCANDI, NODE_INDUSTRIAL],
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
        created_by="alice",
        source="operator",
    )
    base.update(overrides)
    return Taxonomy(**base)


def _make_node(**overrides) -> TaxonomyNode:
    base = dict(
        node_id=NODE_SCANDI,
        version=1,
        label="Scandinavian",
        description="Nordic minimalism",
        node_type="category",
        aliases=["Scandi", "Nordic"],
        parent_node_id=None,
        depth=1,
        path=[],
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
        created_by="alice",
        source="operator",
    )
    base.update(overrides)
    return TaxonomyNode(**base)


@pytest.fixture
def taxonomy() -> Taxonomy:
    return _make_taxonomy()


@pytest.fixture
def node() -> TaxonomyNode:
    return _make_node()


@pytest.fixture
def registry() -> TaxonomyRegistry:
    return TaxonomyRegistry()


@pytest.fixture
def validator() -> TaxonomyValidator:
    return TaxonomyValidator()


# ---------------------------------------------------------------------
# Test 1 -- Taxonomy 字段完整性
# ---------------------------------------------------------------------


class TestTaxonomyFieldCompleteness:

    def test_all_required_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(Taxonomy)}
        missing = REQUIRED_FIELDS - actual
        assert not missing, (
            "missing required fields on Taxonomy: " + str(missing)
        )

    def test_field_count_at_least_ten(self) -> None:
        assert len(dataclasses.fields(Taxonomy)) >= 10, (
            "Taxonomy must declare at least 10 fields; got "
            + str(len(dataclasses.fields(Taxonomy)))
        )

    def test_required_fields_set_size(self) -> None:
        assert len(REQUIRED_FIELDS) >= 10

    def test_identity_fields(self) -> None:
        for fname in TAXONOMY_IDENTITY_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_content_fields(self) -> None:
        for fname in TAXONOMY_CONTENT_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_metadata_fields(self) -> None:
        for fname in TAXONOMY_METADATA_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_field_types_declared(self) -> None:
        for fname in REQUIRED_FIELDS:
            assert fname in {
                "taxonomy_id", "version", "name", "description",
                "taxonomy_type", "root_node_ids",
                "created_at", "updated_at", "created_by", "source",
            }

    def test_taxonomy_type_allow_list_has_six(self) -> None:
        assert len(TAXONOMY_TYPE_ALLOW_LIST) == 6
        assert "style" in TAXONOMY_TYPE_ALLOW_LIST
        assert "color" in TAXONOMY_TYPE_ALLOW_LIST
        assert "material" in TAXONOMY_TYPE_ALLOW_LIST
        assert "space_type" in TAXONOMY_TYPE_ALLOW_LIST
        assert "age_group" in TAXONOMY_TYPE_ALLOW_LIST
        assert "function" in TAXONOMY_TYPE_ALLOW_LIST

    def test_version_policy_constants(self) -> None:
        assert VERSION_POLICY["first_version"] == 1
        assert VERSION_POLICY["min_version"] == 1
        assert VERSION_POLICY["default_version"] == 1
        assert VERSION_POLICY["version_type"] is int


# ---------------------------------------------------------------------
# Test 2 -- TaxonomyNode 字段完整性
# ---------------------------------------------------------------------


class TestNodeFieldCompleteness:

    def test_all_required_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(TaxonomyNode)}
        missing = NODE_REQUIRED_FIELDS - actual
        assert not missing, (
            "missing required fields on TaxonomyNode: " + str(missing)
        )

    def test_field_count_at_least_ten(self) -> None:
        assert len(dataclasses.fields(TaxonomyNode)) >= 10, (
            "TaxonomyNode must declare at least 10 fields; got "
            + str(len(dataclasses.fields(TaxonomyNode)))
        )

    def test_field_types_declared(self) -> None:
        for fname in NODE_REQUIRED_FIELDS:
            assert fname in NODE_FIELD_TYPES

    def test_node_type_allow_list_has_four(self) -> None:
        assert len(NODE_TYPE_ALLOW_LIST) == 4
        assert "concept" in NODE_TYPE_ALLOW_LIST
        assert "category" in NODE_TYPE_ALLOW_LIST
        assert "instance" in NODE_TYPE_ALLOW_LIST
        assert "value" in NODE_TYPE_ALLOW_LIST


# ---------------------------------------------------------------------
# Test 3 -- Frozen
# ---------------------------------------------------------------------


class TestFrozen:

    def test_taxonomy_is_frozen(self, taxonomy) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            taxonomy.name = "x"  # type: ignore[misc]

    def test_node_is_frozen(self, node) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            node.label = "x"  # type: ignore[misc]


# ---------------------------------------------------------------------
# Test 4 -- JSON 序列化
# ---------------------------------------------------------------------


class TestJSONSerialization:

    def test_taxonomy_round_trip(self, taxonomy) -> None:
        d = taxonomy.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        tax2 = Taxonomy.from_dict(decoded)
        assert tax2 == taxonomy

    def test_node_round_trip(self, node) -> None:
        d = node.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        node2 = TaxonomyNode.from_dict(decoded)
        assert node2 == node

    def test_taxonomy_from_dict_non_dict_raises(self) -> None:
        with pytest.raises(TaxonomySchemaError):
            Taxonomy.from_dict("not a dict")  # type: ignore[arg-type]

    def test_node_from_dict_non_dict_raises(self) -> None:
        with pytest.raises(TaxonomyNodeSchemaError):
            TaxonomyNode.from_dict("not a dict")  # type: ignore[arg-type]


# ---------------------------------------------------------------------
# Test 5 -- Validator (Taxonomy)
# ---------------------------------------------------------------------


class TestTaxonomyValidator:

    def test_valid_taxonomy_passes(self, validator, taxonomy) -> None:
        result = validator.validate(taxonomy)
        assert result.valid is True
        assert result.target_kind == "taxonomy"

    def test_none_target_rejected(self, validator) -> None:
        result = validator.validate(None)  # type: ignore[arg-type]
        assert result.valid is False

    def test_invalid_target_type_rejected(self, validator) -> None:
        result = validator.validate("not a taxonomy")  # type: ignore[arg-type]
        assert result.valid is False

    def test_empty_taxonomy_id_rejected(self, validator) -> None:
        class Fake:
            taxonomy_id = ""
            version = 1
            name = "x"; description = "x"
            taxonomy_type = "style"
            root_node_ids = []
            created_at = "x"; updated_at = "x"
            created_by = ""; source = ""

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("taxonomy_id" in e for e in result.errors)

    def test_invalid_version_rejected(self, validator) -> None:
        class Fake:
            taxonomy_id = "tax-x"
            version = 0
            name = "x"; description = "x"
            taxonomy_type = "style"
            root_node_ids = []
            created_at = "x"; updated_at = "x"
            created_by = ""; source = ""

        result = validator.validate(Fake())
        assert result.valid is False

    def test_invalid_taxonomy_type_rejected(self, validator) -> None:
        t = _make_taxonomy(taxonomy_type="nonsense")
        result = validator.validate(t)
        assert result.valid is False
        assert any("taxonomy_type" in e for e in result.errors)

    def test_validation_result_is_frozen(self, validator, taxonomy) -> None:
        result = validator.validate(taxonomy)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.valid = False  # type: ignore[misc]


# ---------------------------------------------------------------------
# Test 6 -- Validator (TaxonomyNode)
# ---------------------------------------------------------------------


class TestNodeValidator:

    def test_valid_node_passes(self, validator, node) -> None:
        result = validator.validate(node)
        assert result.valid is True
        assert result.target_kind == "node"

    def test_empty_node_id_rejected(self, validator) -> None:
        class Fake:
            node_id = ""
            version = 1
            label = "x"; description = "x"
            node_type = "category"
            aliases = []
            parent_node_id = None
            depth = 1
            path = []
            created_at = "x"; updated_at = "x"
            created_by = ""; source = ""

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("node_id" in e for e in result.errors)

    def test_invalid_node_type_rejected(self, validator) -> None:
        n = _make_node(node_type="nonsense")
        result = validator.validate(n)
        assert result.valid is False
        assert any("node_type" in e for e in result.errors)

    def test_self_reference_rejected(self, validator) -> None:
        n = _make_node(node_id="n-self", parent_node_id="n-self")
        result = validator.validate(n)
        assert result.valid is False
        assert any("self-reference" in e for e in result.errors)

    def test_empty_parent_rejected(self, validator) -> None:
        n = _make_node(parent_node_id="")
        result = validator.validate(n)
        assert result.valid is False
        assert any("parent_node_id" in e for e in result.errors)

    def test_invalid_depth_rejected(self, validator) -> None:
        n = _make_node(depth=0)
        result = validator.validate(n)
        assert result.valid is False
        assert any("depth" in e for e in result.errors)

    def test_invalid_version_rejected(self, validator) -> None:
        class Fake:
            node_id = "n-x"
            version = 0
            label = "x"; description = "x"
            node_type = "category"
            aliases = []
            parent_node_id = None
            depth = 1
            path = []
            created_at = "x"; updated_at = "x"
            created_by = ""; source = ""

        result = validator.validate(Fake())
        assert result.valid is False


# ---------------------------------------------------------------------
# Test 7 -- Validator (跨记录)
# ---------------------------------------------------------------------


class TestCrossRecordValidation:

    def test_unique_taxonomy_id_passes(
        self, validator, taxonomy, registry,
    ) -> None:
        registry.append_taxonomy(taxonomy)
        new_tax = _make_taxonomy(taxonomy_id="tax-style-2")
        result = validator.validate(
            new_tax, existing_taxonomies=registry.list_taxonomies(),
        )
        assert result.valid is True

    def test_duplicate_taxonomy_id_rejected(
        self, validator, taxonomy, registry,
    ) -> None:
        registry.append_taxonomy(taxonomy)
        dup = _make_taxonomy(taxonomy_id=TAX_ID)
        result = validator.validate(
            dup, existing_taxonomies=registry.list_taxonomies(),
        )
        assert result.valid is False
        assert any("taxonomy_id is not unique" in e
                   for e in result.errors)

    def test_root_node_id_must_exist(
        self, validator, registry,
    ) -> None:
        # Register a node so the registry has one node.
        registry.append_node(_make_node(node_id=NODE_SCANDI))
        # Build a taxonomy that references an UNKNOWN root.
        t = _make_taxonomy(root_node_ids=["node-unknown"])
        result = validator.validate(
            t,
            existing_taxonomies=registry.list_taxonomies(),
            existing_nodes=registry.list_nodes(),
        )
        assert result.valid is False
        assert any("does not refer to any registered node" in e
                   for e in result.errors)

    def test_unique_node_id_passes(
        self, validator, node, registry,
    ) -> None:
        registry.append_node(node)
        new_node = _make_node(node_id="node-warm")
        result = validator.validate(
            new_node, existing_nodes=registry.list_nodes(),
        )
        assert result.valid is True

    def test_duplicate_node_id_rejected(
        self, validator, node, registry,
    ) -> None:
        registry.append_node(node)
        dup = _make_node(node_id=NODE_SCANDI)
        result = validator.validate(
            dup, existing_nodes=registry.list_nodes(),
        )
        assert result.valid is False
        assert any("node_id is not unique" in e
                   for e in result.errors)


# ---------------------------------------------------------------------
# Test 8 -- Registry
# ---------------------------------------------------------------------


class TestRegistry:

    def test_append_taxonomy_and_count(self, registry, taxonomy) -> None:
        assert registry.count_taxonomies() == 0
        registry.append_taxonomy(taxonomy)
        assert registry.count_taxonomies() == 1

    def test_append_node_and_count(self, registry, node) -> None:
        assert registry.count_nodes() == 0
        registry.append_node(node)
        assert registry.count_nodes() == 1

    def test_append_wrong_type_rejected(self, registry) -> None:
        with pytest.raises(TaxonomyRegistryError):
            registry.append_taxonomy("not a taxonomy")  # type: ignore[arg-type]
        with pytest.raises(TaxonomyRegistryError):
            registry.append_node("not a node")  # type: ignore[arg-type]

    def test_get_taxonomy(self, registry, taxonomy) -> None:
        registry.append_taxonomy(taxonomy)
        assert registry.get_taxonomy(TAX_ID) is taxonomy

    def test_get_taxonomy_missing(self, registry) -> None:
        assert registry.get_taxonomy("nonexistent") is None

    def test_get_node(self, registry, node) -> None:
        registry.append_node(node)
        assert registry.get_node(NODE_SCANDI) is node

    def test_roots(self, registry) -> None:
        # Root: parent_node_id is None.
        registry.append_node(_make_node(node_id="r1", parent_node_id=None))
        registry.append_node(
            _make_node(node_id="c1", parent_node_id="r1", depth=2),
        )
        roots = registry.roots()
        assert len(roots) == 1
        assert roots[0].node_id == "r1"

    def test_children_of(self, registry) -> None:
        registry.append_node(_make_node(node_id="p1", parent_node_id=None))
        registry.append_node(_make_node(node_id="c1", parent_node_id="p1"))
        registry.append_node(_make_node(node_id="c2", parent_node_id="p1"))
        children = registry.children_of("p1")
        assert len(children) == 2

    def test_nodes_for_taxonomy(self, registry) -> None:
        # Build a small tree: r1, r2 are roots of tax-1
        registry.append_taxonomy(_make_taxonomy(
            taxonomy_id="tax-1",
            root_node_ids=["r1", "r2"],
        ))
        registry.append_node(_make_node(node_id="r1", parent_node_id=None))
        registry.append_node(_make_node(node_id="r2", parent_node_id=None))
        registry.append_node(
            _make_node(node_id="c1", parent_node_id="r1", depth=2),
        )
        registry.append_node(
            _make_node(node_id="gc1", parent_node_id="c1", depth=3),
        )
        # Tax-1 should see r1, r2, c1, gc1
        nodes = registry.nodes_for_taxonomy("tax-1")
        ids = sorted([n.node_id for n in nodes])
        assert ids == ["c1", "gc1", "r1", "r2"]

    def test_nodes_for_unknown_taxonomy(self, registry) -> None:
        assert registry.nodes_for_taxonomy("nonexistent") == []

    def test_taxonomy_ids_and_node_ids(
        self, registry, taxonomy, node,
    ) -> None:
        registry.append_taxonomy(taxonomy)
        registry.append_node(node)
        assert registry.taxonomy_ids() == [TAX_ID]
        assert registry.node_ids() == [NODE_SCANDI]

    def test_list_returns_copy(self, registry, taxonomy) -> None:
        registry.append_taxonomy(taxonomy)
        snapshot = registry.list_taxonomies()
        snapshot.clear()
        assert registry.count_taxonomies() == 1


# ---------------------------------------------------------------------
# Test 9 -- Append-only contract
# ---------------------------------------------------------------------


class TestAppendOnly:

    def test_update_rejected(self, registry) -> None:
        with pytest.raises(TypeError):
            registry.update()

    def test_delete_rejected(self, registry) -> None:
        with pytest.raises(TypeError):
            registry.delete()

    def test_overwrite_rejected(self, registry) -> None:
        with pytest.raises(TypeError):
            registry.overwrite()

    def test_clear_rejected(self, registry, taxonomy, node) -> None:
        registry.append_taxonomy(taxonomy)
        registry.append_node(node)
        with pytest.raises(TypeError):
            registry.clear()
        assert registry.count_taxonomies() == 1
        assert registry.count_nodes() == 1


# ---------------------------------------------------------------------
# Test 10 -- Report
# ---------------------------------------------------------------------


class TestReport:

    def test_report_without_registry(self) -> None:
        report = generate_taxonomy_report()
        assert "# Knowledge Taxonomy Schema Report" in report
        assert "## Overview" in report
        assert "## Taxonomy Identity Fields" in report
        assert "## Taxonomy Content Fields" in report
        assert "## Taxonomy Type Allow-list" in report
        assert "## Node Identity Fields" in report
        assert "## Node Type Allow-list" in report
        assert "## Registry Snapshot" in report
        assert "## Architecture Boundary" in report

    def test_report_with_populated_registry(
        self, registry, taxonomy, node,
    ) -> None:
        registry.append_taxonomy(taxonomy)
        registry.append_node(node)
        report = generate_taxonomy_report(registry)
        assert "total taxonomies**" in report
        assert "total nodes**" in report
        assert TAX_ID in report
        assert NODE_SCANDI in report


# ---------------------------------------------------------------------
# Test 11 -- Architecture boundary (AST scan)
# ---------------------------------------------------------------------


class TestArchitectureBoundary:

    def test_taxonomy_module_no_forbidden_imports(self) -> None:
        taxonomy_dir = (
            pathlib.Path(__file__).resolve().parents[1]
            / "caseos"
            / "knowledge"
            / "taxonomy"
        )
        forbidden_substrings = (
            "caseos.intelligence.decision",
            "caseos.intelligence.trust",
            "caseos.intelligence.recommendation",
            "caseos.knowledge.retrieval",
            "caseos.knowledge.evolution",
            "caseos.knowledge.governance",
            "caseos.knowledge.intake",
            "caseos.knowledge.feedback",
        )
        for py in sorted(taxonomy_dir.glob("*.py")):
            src = py.read_text(encoding="utf-8-sig")
            tree = ast.parse(src, filename=str(py))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in forbidden_substrings:
                            assert not alias.name.startswith(forbidden), (
                                py.name + " imports forbidden module: "
                                + alias.name
                            )
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for forbidden in forbidden_substrings:
                        assert not module.startswith(forbidden), (
                            py.name + " imports from forbidden module: "
                            + module
                        )


# ---------------------------------------------------------------------
# Test 12 -- KO / Domain / Binding 隔离
# ---------------------------------------------------------------------


class TestKnowledgeIsolation:

    def test_ko_domain_binding_can_be_siblings(self) -> None:
        from caseos.knowledge.object import KnowledgeObject  # noqa: F401
        from caseos.knowledge.domain import KnowledgeDomain  # noqa: F401
        from caseos.knowledge.binding import KODomainBinding  # noqa: F401
        assert KnowledgeObject is not None
        assert KnowledgeDomain is not None
        assert KODomainBinding is not None

    def test_taxonomy_does_not_mutate_ko(self) -> None:
        from caseos.knowledge.object import KnowledgeObject

        ko = KnowledgeObject(
            knowledge_id="ko-tax-1",
            version=1,
            title="t", description="d", category="c",
            project_type="p", site_type="s",
            location_type="l", space_size="500sqm",
            theme="t", style="s",
            color_system="c", interaction_type="i",
            created_at=NOW_ISO, updated_at=NOW_ISO, source="op",
        )
        before = ko.to_dict()
        # Build a node that conceptually tags the KO; the KO
        # itself is not touched.
        n = _make_node(node_id="node-style-1", label=ko.style)
        assert n.label == ko.style
        assert ko.to_dict() == before
