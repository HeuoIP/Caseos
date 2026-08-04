"""Knowledge Attribute Schema V1 tests (Sprint 23.1-D).

测试范围：

    * KnowledgeAttribute 字段完整性、frozen、JSON round-trip
    * KnowledgeAttributeValidator（单记录 + 跨记录）
    * AttributeRegistry append-only 契约
    * 值域约束（min/max/pattern/allowed_node_ids）
    * data_type=enum 必须有 allowed_node_ids
    * cardinality=set 必须有 allowed_node_ids
    * allowed_taxonomy_id 必须引用真实 taxonomy
    * Markdown 报告
    * Architecture boundary (AST scan)
    * KO / Domain / Binding / Taxonomy 不被 attribute 修改

不在测试范围内：

    * Pipeline wiring
    * Intelligence / Retrieval / Evolution
    * 自动分类 / 自动学习
"""
from __future__ import annotations

import ast
import dataclasses
import json
import pathlib

import pytest

from caseos.knowledge.attribute import (
    ATTRIBUTE_TYPE_ALLOW_LIST,
    CARDINALITY_ALLOW_LIST,
    CONTENT_FIELDS,
    CONSTRAINT_FIELDS,
    DATA_TYPE_ALLOW_LIST,
    FIELD_TYPES,
    IDENTITY_FIELDS,
    KnowledgeAttribute,
    KnowledgeAttributeError,
    KnowledgeAttributeSchemaError,
    METADATA_FIELDS,
    AttributeRegistry,
    AttributeRegistryError,
    AttributeValidationResult,
    KnowledgeAttributeValidator,
    REQUIRED_FIELDS,
    VERSION_POLICY,
    generate_attribute_report,
)


NOW_ISO = "2026-08-04T00:00:00Z"
ATTR_ID = "attr-style-1"


def _make_attribute(**overrides) -> KnowledgeAttribute:
    base = dict(
        attribute_id=ATTR_ID,
        version=1,
        name="style",
        description="Design style slot",
        attribute_type="property",
        data_type="enum",
        cardinality="single",
        required=True,
        default_value=None,
        allowed_taxonomy_id="tax-style-1",
        allowed_node_ids=["node-scandi", "node-industrial"],
        min_value=None,
        max_value=None,
        pattern=None,
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
        created_by="alice",
        source="operator",
    )
    base.update(overrides)
    return KnowledgeAttribute(**base)


@pytest.fixture
def attribute() -> KnowledgeAttribute:
    return _make_attribute()


@pytest.fixture
def registry() -> AttributeRegistry:
    return AttributeRegistry()


@pytest.fixture
def validator() -> KnowledgeAttributeValidator:
    return KnowledgeAttributeValidator()


# ---------------------------------------------------------------------
# Test 1 -- 字段完整性
# ---------------------------------------------------------------------


class TestFieldCompleteness:

    def test_all_required_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(KnowledgeAttribute)}
        missing = REQUIRED_FIELDS - actual
        assert not missing, (
            "missing required fields on KnowledgeAttribute: "
            + str(missing)
        )

    def test_field_count_at_least_ten(self) -> None:
        assert len(dataclasses.fields(KnowledgeAttribute)) >= 10, (
            "KnowledgeAttribute must declare at least 10 fields; got "
            + str(len(dataclasses.fields(KnowledgeAttribute)))
        )

    def test_required_fields_set_size(self) -> None:
        assert len(REQUIRED_FIELDS) >= 10

    def test_identity_fields(self) -> None:
        for fname in IDENTITY_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_content_fields(self) -> None:
        for fname in CONTENT_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_constraint_fields(self) -> None:
        for fname in CONSTRAINT_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_metadata_fields(self) -> None:
        for fname in METADATA_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_field_types_declared(self) -> None:
        for fname in REQUIRED_FIELDS:
            assert fname in FIELD_TYPES

    def test_attribute_type_allow_list_has_three(self) -> None:
        assert len(ATTRIBUTE_TYPE_ALLOW_LIST) == 3
        assert "property" in ATTRIBUTE_TYPE_ALLOW_LIST
        assert "tag" in ATTRIBUTE_TYPE_ALLOW_LIST
        assert "metric" in ATTRIBUTE_TYPE_ALLOW_LIST

    def test_data_type_allow_list_has_six(self) -> None:
        assert len(DATA_TYPE_ALLOW_LIST) == 6
        for t in (
            "string", "number", "boolean", "enum", "list", "object",
        ):
            assert t in DATA_TYPE_ALLOW_LIST

    def test_cardinality_allow_list_has_three(self) -> None:
        assert len(CARDINALITY_ALLOW_LIST) == 3
        for c in ("single", "list", "set"):
            assert c in CARDINALITY_ALLOW_LIST

    def test_version_policy_constants(self) -> None:
        assert VERSION_POLICY["first_version"] == 1
        assert VERSION_POLICY["min_version"] == 1
        assert VERSION_POLICY["default_version"] == 1
        assert VERSION_POLICY["version_type"] is int


# ---------------------------------------------------------------------
# Test 2 -- Frozen
# ---------------------------------------------------------------------


class TestFrozen:

    def test_dataclass_is_frozen(self, attribute) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            attribute.name = "x"  # type: ignore[misc]

    def test_mutation_of_attribute_id_raises(self, attribute) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            attribute.attribute_id = "x"  # type: ignore[misc]


# ---------------------------------------------------------------------
# Test 3 -- JSON 序列化
# ---------------------------------------------------------------------


class TestJSONSerialization:

    def test_to_dict_returns_dict(self, attribute) -> None:
        d = attribute.to_dict()
        assert isinstance(d, dict)

    def test_to_dict_contains_all_required_fields(
        self, attribute,
    ) -> None:
        d = attribute.to_dict()
        for fname in REQUIRED_FIELDS:
            assert fname in d

    def test_from_dict_round_trip(self, attribute) -> None:
        d = attribute.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        attr2 = KnowledgeAttribute.from_dict(decoded)
        assert attr2 == attribute

    def test_from_dict_non_dict_raises(self) -> None:
        with pytest.raises(KnowledgeAttributeSchemaError):
            KnowledgeAttribute.from_dict("not a dict")  # type: ignore[arg-type]


# ---------------------------------------------------------------------
# Test 4 -- Validator (单记录)
# ---------------------------------------------------------------------


class TestValidatorSingleRecord:

    def test_valid_attribute_passes(self, validator, attribute) -> None:
        result = validator.validate(attribute)
        assert result.valid is True

    def test_none_attribute_rejected(self, validator) -> None:
        result = validator.validate(None)  # type: ignore[arg-type]
        assert result.valid is False

    def test_empty_attribute_id_rejected(self, validator) -> None:
        class Fake:
            attribute_id = ""
            version = 1
            name = "x"; description = "x"
            attribute_type = "property"
            data_type = "string"
            cardinality = "single"
            required = False
            default_value = None
            allowed_taxonomy_id = None
            allowed_node_ids = []
            min_value = None; max_value = None
            pattern = None
            created_at = "x"; updated_at = "x"
            created_by = ""; source = ""

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("attribute_id" in e for e in result.errors)

    def test_invalid_version_rejected(self, validator) -> None:
        class Fake:
            attribute_id = "a"
            version = 0
            name = "x"; description = "x"
            attribute_type = "property"
            data_type = "string"
            cardinality = "single"
            required = False
            default_value = None
            allowed_taxonomy_id = None
            allowed_node_ids = []
            min_value = None; max_value = None
            pattern = None
            created_at = "x"; updated_at = "x"
            created_by = ""; source = ""

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("version" in e for e in result.errors)

    def test_invalid_attribute_type_rejected(self, validator) -> None:
        a = _make_attribute(attribute_type="nonsense")
        result = validator.validate(a)
        assert result.valid is False
        assert any("attribute_type" in e for e in result.errors)

    def test_invalid_data_type_rejected(self, validator) -> None:
        a = _make_attribute(data_type="nonsense")
        result = validator.validate(a)
        assert result.valid is False
        assert any("data_type" in e for e in result.errors)

    def test_invalid_cardinality_rejected(self, validator) -> None:
        a = _make_attribute(cardinality="nonsense")
        result = validator.validate(a)
        assert result.valid is False
        assert any("cardinality" in e for e in result.errors)

    def test_required_must_be_bool(self, validator) -> None:
        a = _make_attribute(required="yes")  # type: ignore[arg-type]
        result = validator.validate(a)
        assert result.valid is False
        assert any("required" in e for e in result.errors)

    def test_enum_requires_allowed_node_ids(self, validator) -> None:
        a = _make_attribute(
            data_type="enum",
            allowed_node_ids=[],
        )
        result = validator.validate(a)
        assert result.valid is False
        assert any(
            "data_type=enum" in e for e in result.errors
        )

    def test_set_cardinality_requires_allowed_node_ids(
        self, validator,
    ) -> None:
        a = _make_attribute(
            data_type="string",
            cardinality="set",
            allowed_node_ids=[],
        )
        result = validator.validate(a)
        assert result.valid is False
        assert any(
            "cardinality=set" in e for e in result.errors
        )

    def test_min_value_must_be_le_max(self, validator) -> None:
        a = _make_attribute(
            data_type="number",
            min_value=10.0,
            max_value=5.0,
        )
        result = validator.validate(a)
        assert result.valid is False
        assert any("min_value" in e for e in result.errors)

    def test_min_le_max_passes(self, validator) -> None:
        a = _make_attribute(
            data_type="number",
            min_value=1.0,
            max_value=10.0,
        )
        result = validator.validate(a)
        assert result.valid is True

    def test_validation_result_is_frozen(self, validator, attribute) -> None:
        result = validator.validate(attribute)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.valid = False  # type: ignore[misc]


# ---------------------------------------------------------------------
# Test 5 -- Validator (跨记录)
# ---------------------------------------------------------------------


class TestValidatorCrossRecord:

    def test_unique_attribute_id_passes(
        self, validator, attribute, registry,
    ) -> None:
        registry.append(attribute)
        new_attr = _make_attribute(
            attribute_id="attr-theme-1",
            name="theme",
            data_type="string",
            allowed_node_ids=[],
        )
        result = validator.validate(
            new_attr, existing_attributes=registry.list(),
        )
        assert result.valid is True

    def test_duplicate_attribute_id_rejected(
        self, validator, attribute, registry,
    ) -> None:
        registry.append(attribute)
        dup = _make_attribute(attribute_id=ATTR_ID)
        result = validator.validate(
            dup, existing_attributes=registry.list(),
        )
        assert result.valid is False
        assert any("attribute_id is not unique" in e
                   for e in result.errors)

    def test_allowed_taxonomy_id_must_exist(self, validator) -> None:
        # No taxonomies registered -> allowed_taxonomy_id is
        # unknown.
        a = _make_attribute(allowed_taxonomy_id="tax-nonexistent")
        result = validator.validate(
            a, existing_taxonomies=[],
        )
        assert result.valid is False
        assert any(
            "does not refer to any registered taxonomy" in e
            for e in result.errors
        )

    def test_allowed_taxonomy_id_passes_when_present(self, validator) -> None:
        # Build a Fake taxonomy that has the matching id.
        class FakeTaxonomy:
            taxonomy_id = "tax-style-1"

        a = _make_attribute(allowed_taxonomy_id="tax-style-1")
        result = validator.validate(
            a, existing_taxonomies=[FakeTaxonomy()],
        )
        assert result.valid is True

    def test_no_allowed_taxonomy_id_no_check(self, validator) -> None:
        a = _make_attribute(allowed_taxonomy_id=None)
        result = validator.validate(
            a, existing_taxonomies=[],
        )
        assert result.valid is True


# ---------------------------------------------------------------------
# Test 6 -- Registry
# ---------------------------------------------------------------------


class TestRegistry:

    def test_append_and_count(self, registry, attribute) -> None:
        assert registry.count() == 0
        registry.append(attribute)
        assert registry.count() == 1

    def test_append_wrong_type_rejected(self, registry) -> None:
        with pytest.raises(AttributeRegistryError):
            registry.append("not an attribute")  # type: ignore[arg-type]

    def test_get_by_id(self, registry, attribute) -> None:
        registry.append(attribute)
        assert registry.get(ATTR_ID) is attribute

    def test_get_returns_none_when_missing(self, registry) -> None:
        assert registry.get("nonexistent") is None

    def test_for_data_type(self, registry) -> None:
        registry.append(_make_attribute(
            attribute_id="a1", data_type="string",
            allowed_node_ids=[],
        ))
        registry.append(_make_attribute(
            attribute_id="a2", data_type="number",
            cardinality="single",
            allowed_node_ids=[],
        ))
        registry.append(_make_attribute(
            attribute_id="a3", data_type="string",
            allowed_node_ids=[],
        ))
        assert len(registry.for_data_type("string")) == 2
        assert len(registry.for_data_type("number")) == 1

    def test_for_attribute_type(self, registry) -> None:
        registry.append(_make_attribute(
            attribute_id="a1", attribute_type="property",
        ))
        registry.append(_make_attribute(
            attribute_id="a2", attribute_type="tag",
            data_type="string", allowed_node_ids=[],
        ))
        assert len(registry.for_attribute_type("property")) == 1
        assert len(registry.for_attribute_type("tag")) == 1

    def test_required_and_optional(self, registry) -> None:
        registry.append(_make_attribute(
            attribute_id="a1", required=True,
        ))
        registry.append(_make_attribute(
            attribute_id="a2", required=False,
            data_type="string", allowed_node_ids=[],
        ))
        assert len(registry.required()) == 1
        assert len(registry.optional()) == 1

    def test_attribute_ids(self, registry) -> None:
        registry.append(_make_attribute(attribute_id="a1"))
        registry.append(_make_attribute(
            attribute_id="a2",
            data_type="string", allowed_node_ids=[],
        ))
        assert registry.attribute_ids() == ["a1", "a2"]

    def test_list_returns_copy(self, registry, attribute) -> None:
        registry.append(attribute)
        snapshot = registry.list()
        snapshot.clear()
        assert registry.count() == 1


# ---------------------------------------------------------------------
# Test 7 -- Append-only contract
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

    def test_clear_rejected(self, registry, attribute) -> None:
        registry.append(attribute)
        with pytest.raises(TypeError):
            registry.clear()
        assert registry.count() == 1


# ---------------------------------------------------------------------
# Test 8 -- Report
# ---------------------------------------------------------------------


class TestReport:

    def test_report_without_registry(self) -> None:
        report = generate_attribute_report()
        assert "# Knowledge Attribute Schema Report" in report
        assert "## Overview" in report
        assert "## Identity Fields" in report
        assert "## Content Fields" in report
        assert "## Constraint Fields" in report
        assert "## Metadata Fields" in report
        assert "## Attribute Type Allow-list" in report
        assert "## Data Type Allow-list" in report
        assert "## Cardinality Allow-list" in report
        assert "## Validation Rules" in report
        assert "## Architecture Boundary" in report

    def test_report_with_populated_registry(
        self, registry, attribute,
    ) -> None:
        registry.append(attribute)
        report = generate_attribute_report(registry)
        assert "total attributes**" in report
        assert ATTR_ID in report
        assert "required attributes**" in report


# ---------------------------------------------------------------------
# Test 9 -- Architecture boundary (AST scan)
# ---------------------------------------------------------------------


class TestArchitectureBoundary:

    def test_attribute_module_no_forbidden_imports(self) -> None:
        attribute_dir = (
            pathlib.Path(__file__).resolve().parents[1]
            / "caseos"
            / "knowledge"
            / "attribute"
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
        for py in sorted(attribute_dir.glob("*.py")):
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
# Test 10 -- 上游隔离
# ---------------------------------------------------------------------


class TestUpstreamIsolation:

    def test_ko_domain_binding_taxonomy_can_be_siblings(self) -> None:
        from caseos.knowledge.object import KnowledgeObject  # noqa: F401
        from caseos.knowledge.domain import KnowledgeDomain  # noqa: F401
        from caseos.knowledge.binding import KODomainBinding  # noqa: F401
        from caseos.knowledge.taxonomy import TaxonomyNode  # noqa: F401
        assert KnowledgeObject is not None
        assert KnowledgeDomain is not None
        assert KODomainBinding is not None
        assert TaxonomyNode is not None

    def test_attribute_does_not_mutate_ko(self) -> None:
        from caseos.knowledge.object import KnowledgeObject

        ko = KnowledgeObject(
            knowledge_id="ko-attr-1",
            version=1,
            title="t", description="d", category="c",
            project_type="p", site_type="s",
            location_type="l", space_size="500sqm",
            theme="t", style="s",
            color_system="c", interaction_type="i",
            created_at=NOW_ISO, updated_at=NOW_ISO, source="op",
        )
        before = ko.to_dict()
        # Build an attribute that conceptually constrains
        # ko.style; the KO itself is not touched.
        attr = _make_attribute(
            attribute_id="attr-style-ko",
            name="style",
            data_type="enum",
            cardinality="single",
            allowed_taxonomy_id="tax-style-1",
            allowed_node_ids=[ko.style],
        )
        assert attr.allowed_node_ids[0] == ko.style
        assert ko.to_dict() == before
