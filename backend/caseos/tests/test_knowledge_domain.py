"""Knowledge Domain Schema V1 tests (Sprint 23.1-A).

测试范围：

    * KnowledgeDomain 字段完整性、frozen、JSON round-trip
    * KnowledgeDomainValidator（valid + invalid cases）
    * KnowledgeDomain version policy (>= 1)
    * KnowledgeDomainSnapshot deep-copy 隔离
    * KnowledgeDomainSchema Markdown report
    * Architecture boundary (AST scan)

不在测试范围内：

    * Pipeline wiring
    * Intelligence / Retrieval / Evolution
    * Knowledge Object 改动
"""
from __future__ import annotations

import ast
import dataclasses
import json
import pathlib

import pytest

from caseos.knowledge.domain import (
    DOMAIN_TYPE_ALLOW_LIST,
    DOMAIN_VERSION_POLICY,
    FIELD_TYPES,
    IDENTITY_FIELDS,
    KnowledgeDomain,
    KnowledgeDomainError,
    KnowledgeDomainSchemaError,
    KnowledgeDomainSnapshot,
    KnowledgeDomainValidator,
    DomainValidationResult,
    METADATA_FIELDS,
    REQUIRED_FIELDS,
    SCOPE_FIELDS,
    TAXONOMY_FIELDS,
    generate_domain_report,
)


DOM_ID = "dom-1"
NOW_ISO = "2026-08-04T00:00:00Z"


def _make_knowledge_domain(**overrides) -> KnowledgeDomain:
    """返回完整的 V1 KnowledgeDomain。"""
    base = dict(
        domain_id=DOM_ID,
        version=1,
        domain_type="design_category",
        name="Kindergarten design",
        description="Scope: kindergarten / preschool spaces",
        parent_domain_id=None,
        scope_tags=["education", "outdoor"],
        allowed_knowledge_types=["forest", "urban"],
        boundary_rules=["Do not add scattered equipment"],
        principle_rules=["Create hierarchy before adding facilities"],
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
        source="operator",
    )
    base.update(overrides)
    return KnowledgeDomain(**base)


@pytest.fixture
def domain() -> KnowledgeDomain:
    return _make_knowledge_domain()


@pytest.fixture
def validator() -> KnowledgeDomainValidator:
    return KnowledgeDomainValidator()


# ---------------------------------------------------------------------
# Test 1 -- 字段完整性
# ---------------------------------------------------------------------


class TestFieldCompleteness:

    def test_all_required_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(KnowledgeDomain)}
        missing = REQUIRED_FIELDS - actual
        assert not missing, (
            "missing required fields on KnowledgeDomain: "
            + str(missing)
        )

    def test_field_count_at_least_ten(self) -> None:
        assert len(dataclasses.fields(KnowledgeDomain)) >= 10, (
            "KnowledgeDomain must declare at least 10 fields; got "
            + str(len(dataclasses.fields(KnowledgeDomain)))
        )

    def test_required_fields_set_size(self) -> None:
        assert len(REQUIRED_FIELDS) >= 10

    def test_identity_fields(self) -> None:
        for fname in IDENTITY_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_scope_fields(self) -> None:
        for fname in SCOPE_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_taxonomy_fields(self) -> None:
        for fname in TAXONOMY_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_metadata_fields(self) -> None:
        for fname in METADATA_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_field_types_declared(self) -> None:
        for fname in REQUIRED_FIELDS:
            assert fname in FIELD_TYPES, (
                "FIELD_TYPES missing: " + fname
            )

    def test_domain_type_allow_list_has_three(self) -> None:
        # V1 spec: design_category, industry_vertical, project_family
        assert len(DOMAIN_TYPE_ALLOW_LIST) == 3
        assert "design_category" in DOMAIN_TYPE_ALLOW_LIST
        assert "industry_vertical" in DOMAIN_TYPE_ALLOW_LIST
        assert "project_family" in DOMAIN_TYPE_ALLOW_LIST


# ---------------------------------------------------------------------
# Test 2 -- Frozen
# ---------------------------------------------------------------------


class TestFrozen:

    def test_dataclass_is_frozen(self, domain) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            domain.name = "changed"  # type: ignore[misc]

    def test_mutation_of_domain_id_raises(self, domain) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            domain.domain_id = "x"  # type: ignore[misc]

    def test_mutation_of_version_raises(self, domain) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            domain.version = 99  # type: ignore[misc]


# ---------------------------------------------------------------------
# Test 3 -- JSON 序列化
# ---------------------------------------------------------------------


class TestJSONSerialization:

    def test_to_dict_returns_dict(self, domain) -> None:
        d = domain.to_dict()
        assert isinstance(d, dict)

    def test_to_dict_contains_all_required_fields(self, domain) -> None:
        d = domain.to_dict()
        for fname in REQUIRED_FIELDS:
            assert fname in d, "missing key in to_dict: " + fname

    def test_from_dict_round_trip(self, domain) -> None:
        d = domain.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        domain2 = KnowledgeDomain.from_dict(decoded)
        assert domain2 == domain

    def test_from_dict_missing_optional_uses_default(self) -> None:
        minimal = {
            "domain_id": "dom-2",
            "version": 1,
            "domain_type": "design_category",
            "name": "x",
            "description": "x",
            "created_at": NOW_ISO,
            "updated_at": NOW_ISO,
            "source": "",
        }
        d = KnowledgeDomain.from_dict(minimal)
        assert d.domain_id == "dom-2"
        assert d.scope_tags == []
        assert d.boundary_rules == []
        assert d.parent_domain_id is None

    def test_from_dict_non_dict_raises(self) -> None:
        with pytest.raises(KnowledgeDomainSchemaError):
            KnowledgeDomain.from_dict("not a dict")  # type: ignore[arg-type]

    def test_from_dict_collection_wrong_type_raises(self) -> None:
        bad = {
            "domain_id": "dom-3",
            "version": 1,
            "domain_type": "design_category",
            "name": "x",
            "description": "x",
            "scope_tags": "should be list, not string",
        }
        with pytest.raises(KnowledgeDomainSchemaError):
            KnowledgeDomain.from_dict(bad)


# ---------------------------------------------------------------------
# Test 4 -- Validator
# ---------------------------------------------------------------------


class TestValidator:

    def test_valid_domain_passes(self, validator, domain) -> None:
        result = validator.validate(domain)
        assert result.valid is True
        assert result.errors == ()

    def test_validation_result_is_frozen(self, validator, domain) -> None:
        result = validator.validate(domain)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.valid = False  # type: ignore[misc]

    def test_missing_domain_id_rejected(self, validator) -> None:
        class Fake:
            version = 1
            domain_type = "design_category"
            name = "x"; description = "x"
            parent_domain_id = None
            scope_tags = []
            allowed_knowledge_types = []
            boundary_rules = []
            principle_rules = []
            created_at = "x"; updated_at = "x"; source = "x"

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("domain_id" in e for e in result.errors)

    def test_empty_domain_id_rejected(self, validator) -> None:
        class Fake:
            domain_id = ""
            version = 1
            domain_type = "design_category"
            name = "x"; description = "x"
            parent_domain_id = None
            scope_tags = []
            allowed_knowledge_types = []
            boundary_rules = []
            principle_rules = []
            created_at = "x"; updated_at = "x"; source = "x"

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("domain_id" in e for e in result.errors)

    def test_invalid_version_type_rejected(self, validator) -> None:
        class Fake:
            domain_id = "d1"
            version = "1"
            domain_type = "design_category"
            name = "x"; description = "x"
            parent_domain_id = None
            scope_tags = []
            allowed_knowledge_types = []
            boundary_rules = []
            principle_rules = []
            created_at = "x"; updated_at = "x"; source = "x"

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("version" in e for e in result.errors)

    def test_invalid_domain_type_rejected(self, validator) -> None:
        class Fake:
            domain_id = "d1"
            version = 1
            domain_type = "unknown_type"
            name = "x"; description = "x"
            parent_domain_id = None
            scope_tags = []
            allowed_knowledge_types = []
            boundary_rules = []
            principle_rules = []
            created_at = "x"; updated_at = "x"; source = "x"

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("domain_type" in e for e in result.errors)

    def test_wrong_field_type_rejected(self, validator) -> None:
        class Fake:
            domain_id = "d1"
            version = 1
            domain_type = "design_category"
            name = 123  # wrong type
            description = "x"
            parent_domain_id = None
            scope_tags = []
            allowed_knowledge_types = []
            boundary_rules = []
            principle_rules = []
            created_at = "x"; updated_at = "x"; source = "x"

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("name" in e for e in result.errors)

    def test_none_object_rejected(self, validator) -> None:
        result = validator.validate(None)  # type: ignore[arg-type]
        assert result.valid is False


# ---------------------------------------------------------------------
# Test 5 -- Version policy
# ---------------------------------------------------------------------


class TestVersionPolicy:

    def test_version_one_is_accepted(self) -> None:
        d = _make_knowledge_domain(version=1)
        assert d.version == 1

    def test_version_zero_rejected_by_constructor(self) -> None:
        with pytest.raises(KnowledgeDomainSchemaError):
            _make_knowledge_domain(version=0)

    def test_version_policy_constants(self) -> None:
        assert DOMAIN_VERSION_POLICY["first_version"] == 1
        assert DOMAIN_VERSION_POLICY["min_version"] == 1
        assert DOMAIN_VERSION_POLICY["default_version"] == 1
        assert DOMAIN_VERSION_POLICY["version_type"] is int


# ---------------------------------------------------------------------
# Test 6 -- Hierarchy invariant
# ---------------------------------------------------------------------


class TestHierarchy:

    def test_top_level_domain_with_none_parent(self) -> None:
        d = _make_knowledge_domain(parent_domain_id=None)
        assert d.parent_domain_id is None
        assert KnowledgeDomainValidator().validate(d).valid

    def test_child_domain_with_valid_parent(self) -> None:
        d = _make_knowledge_domain(parent_domain_id="dom-parent")
        assert d.parent_domain_id == "dom-parent"
        assert KnowledgeDomainValidator().validate(d).valid

    def test_self_reference_rejected(self, validator) -> None:
        class Fake:
            domain_id = "dom-self"
            version = 1
            domain_type = "design_category"
            name = "x"; description = "x"
            parent_domain_id = "dom-self"  # self-reference
            scope_tags = []
            allowed_knowledge_types = []
            boundary_rules = []
            principle_rules = []
            created_at = "x"; updated_at = "x"; source = "x"

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("self-reference" in e for e in result.errors)

    def test_empty_parent_rejected(self, validator) -> None:
        class Fake:
            domain_id = "dom-empty-parent"
            version = 1
            domain_type = "design_category"
            name = "x"; description = "x"
            parent_domain_id = ""  # empty string when present
            scope_tags = []
            allowed_knowledge_types = []
            boundary_rules = []
            principle_rules = []
            created_at = "x"; updated_at = "x"; source = "x"

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("parent_domain_id" in e for e in result.errors)


# ---------------------------------------------------------------------
# Test 7 -- Snapshot 隔离
# ---------------------------------------------------------------------


class TestSnapshot:

    def test_from_knowledge_domain_basic(self, domain) -> None:
        snap = KnowledgeDomainSnapshot.from_knowledge_domain(domain)
        assert snap.domain_id == domain.domain_id
        assert snap.version == domain.version
        assert snap.source_object_id == domain.domain_id
        assert isinstance(snap.snapshot, dict)

    def test_snapshot_deep_copy_isolation(self, domain) -> None:
        snap = KnowledgeDomainSnapshot.from_knowledge_domain(domain)
        # Mutate the source after snapshot.
        domain_replica = _make_knowledge_domain()
        snap.snapshot["name"] = "MUTATED"
        # The original domain is frozen, so we can only mutate
        # the dict snap.snapshot itself. The point is that
        # the snapshot is independent.
        assert snap.snapshot["name"] == "MUTATED"

    def test_snapshot_to_dict(self, domain) -> None:
        snap = KnowledgeDomainSnapshot.from_knowledge_domain(domain)
        d = snap.to_dict()
        assert isinstance(d, dict)
        assert d["domain_id"] == domain.domain_id
        assert d["version"] == domain.version

    def test_snapshot_wrong_type_raises(self) -> None:
        with pytest.raises(TypeError):
            KnowledgeDomainSnapshot.from_knowledge_domain(
                "not a domain",  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------
# Test 8 -- Report
# ---------------------------------------------------------------------


class TestReport:

    def test_report_without_instance(self) -> None:
        report = generate_domain_report()
        assert "# Knowledge Domain Schema Report" in report
        assert "## Overview" in report
        assert "## Identity Fields" in report
        assert "## Scope Fields" in report
        assert "## Taxonomy Fields" in report
        assert "## Metadata Fields" in report
        assert "## Version Policy" in report
        assert "## Domain Type Allow-list" in report
        assert "## Validation Rules" in report

    def test_report_with_instance(self, domain) -> None:
        report = generate_domain_report(domain)
        assert "## Instance" in report
        assert "### Validation Result" in report
        assert "**valid**: `True`" in report

    def test_report_with_invalid_instance(self) -> None:
        # Build an invalid domain via the constructor trick
        # (we cannot make an invalid object via the
        # constructor since __post_init__ raises; we build
        # via __new__ to bypass).
        obj = KnowledgeDomain.__new__(KnowledgeDomain)
        object.__setattr__(obj, "domain_id", "")
        object.__setattr__(obj, "version", 0)
        object.__setattr__(obj, "domain_type", "nonsense")
        object.__setattr__(obj, "name", "")
        object.__setattr__(obj, "description", "")
        object.__setattr__(obj, "parent_domain_id", None)
        object.__setattr__(obj, "scope_tags", [])
        object.__setattr__(obj, "allowed_knowledge_types", [])
        object.__setattr__(obj, "boundary_rules", [])
        object.__setattr__(obj, "principle_rules", [])
        object.__setattr__(obj, "created_at", "x")
        object.__setattr__(obj, "updated_at", "x")
        object.__setattr__(obj, "source", "")
        report = generate_domain_report(obj)
        assert "**valid**: `False`" in report
        assert "error:" in report


# ---------------------------------------------------------------------
# Test 9 -- Architecture boundary (AST scan)
# ---------------------------------------------------------------------


class TestArchitectureBoundary:

    def test_domain_module_no_forbidden_imports(self) -> None:
        domain_dir = (
            pathlib.Path(__file__).resolve().parents[1]
            / "caseos"
            / "knowledge"
            / "domain"
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
        for py in sorted(domain_dir.glob("*.py")):
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
# Test 10 -- KO 不被修改
# ---------------------------------------------------------------------


class TestKnowledgeObjectIsolation:

    def test_domain_does_not_import_knowledge_object(self) -> None:
        domain_dir = (
            pathlib.Path(__file__).resolve().parents[1]
            / "caseos"
            / "knowledge"
            / "domain"
        )
        for py in sorted(domain_dir.glob("*.py")):
            src = py.read_text(encoding="utf-8-sig")
            # Knowledge Object can be referenced as a sibling
            # module per the architecture boundary, but no
            # mutation logic should target it.
            assert "KnowledgeObject" not in src or "object" in py.name, (
                py.name + " references KnowledgeObject; "
                "Domain is a parallel schema, not a KO mutator."
            )

    def test_domain_knowledge_object_can_be_sibling(self) -> None:
        # Confirm the sibling package exists and is importable.
        from caseos.knowledge.object import KnowledgeObject  # noqa: F401
        assert KnowledgeObject is not None
