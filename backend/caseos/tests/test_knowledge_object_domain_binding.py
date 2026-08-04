"""Knowledge Object Domain Binding V1 tests (Sprint 23.1-B).

测试范围：

    * KODomainBinding 字段完整性、frozen、JSON round-trip
    * BindingValidator（单记录 + 跨记录唯一性）
    * BindingRegistry append-only 契约
    * 跨记录不变量：每个 KO 最多一个 primary binding
    * binding_id 全局唯一
    * Markdown 报告生成
    * Architecture boundary (AST scan)
    * KO / Domain 不被 binding 修改

不在测试范围内：

    * Pipeline wiring
    * Intelligence / Retrieval / Evolution
    * KO / Domain mutation
"""
from __future__ import annotations

import ast
import dataclasses
import json
import pathlib

import pytest

from caseos.knowledge.binding import (
    BINDING_TYPE_ALLOW_LIST,
    BINDING_VERSION_POLICY,
    FIELD_TYPES,
    IDENTITY_FIELDS,
    KODomainBinding,
    KODomainBindingError,
    KODomainBindingSchemaError,
    METADATA_FIELDS,
    BindingRegistry,
    BindingRegistryError,
    BindingValidationResult,
    BindingValidator,
    REFERENCE_FIELDS,
    REQUIRED_FIELDS,
    generate_binding_report,
)


NOW_ISO = "2026-08-04T00:00:00Z"
KO_ID = "ko-bind-1"
DOM_ID = "dom-bind-1"


def _make_kodomain_binding(**overrides) -> KODomainBinding:
    """返回完整的 V1 KODomainBinding。"""
    base = dict(
        binding_id="bnd-1",
        version=1,
        knowledge_object_id=KO_ID,
        knowledge_object_version=1,
        domain_id=DOM_ID,
        binding_type="primary",
        priority=1,
        membership_reason="ko.category matches domain.allowed_knowledge_types",
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
        created_by="alice",
        proposal_id="prop-1",
    )
    base.update(overrides)
    return KODomainBinding(**base)


@pytest.fixture
def binding() -> KODomainBinding:
    return _make_kodomain_binding()


@pytest.fixture
def registry() -> BindingRegistry:
    return BindingRegistry()


@pytest.fixture
def validator() -> BindingValidator:
    return BindingValidator()


# ---------------------------------------------------------------------
# Test 1 -- 字段完整性
# ---------------------------------------------------------------------


class TestFieldCompleteness:

    def test_all_required_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(KODomainBinding)}
        missing = REQUIRED_FIELDS - actual
        assert not missing, (
            "missing required fields on KODomainBinding: "
            + str(missing)
        )

    def test_field_count_at_least_ten(self) -> None:
        assert len(dataclasses.fields(KODomainBinding)) >= 10, (
            "KODomainBinding must declare at least 10 fields; got "
            + str(len(dataclasses.fields(KODomainBinding)))
        )

    def test_required_fields_set_size(self) -> None:
        assert len(REQUIRED_FIELDS) >= 10

    def test_identity_fields(self) -> None:
        for fname in IDENTITY_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_reference_fields(self) -> None:
        for fname in REFERENCE_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_metadata_fields(self) -> None:
        for fname in METADATA_FIELDS:
            assert fname in REQUIRED_FIELDS

    def test_field_types_declared(self) -> None:
        for fname in REQUIRED_FIELDS:
            assert fname in FIELD_TYPES

    def test_binding_type_allow_list_has_three(self) -> None:
        # V1: primary, secondary, derived
        assert len(BINDING_TYPE_ALLOW_LIST) == 3
        assert "primary" in BINDING_TYPE_ALLOW_LIST
        assert "secondary" in BINDING_TYPE_ALLOW_LIST
        assert "derived" in BINDING_TYPE_ALLOW_LIST


# ---------------------------------------------------------------------
# Test 2 -- Frozen
# ---------------------------------------------------------------------


class TestFrozen:

    def test_dataclass_is_frozen(self, binding) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            binding.priority = 99  # type: ignore[misc]

    def test_mutation_of_binding_id_raises(self, binding) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            binding.binding_id = "x"  # type: ignore[misc]

    def test_mutation_of_version_raises(self, binding) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            binding.version = 99  # type: ignore[misc]


# ---------------------------------------------------------------------
# Test 3 -- JSON 序列化
# ---------------------------------------------------------------------


class TestJSONSerialization:

    def test_to_dict_returns_dict(self, binding) -> None:
        d = binding.to_dict()
        assert isinstance(d, dict)

    def test_to_dict_contains_all_required_fields(self, binding) -> None:
        d = binding.to_dict()
        for fname in REQUIRED_FIELDS:
            assert fname in d, "missing key in to_dict: " + fname

    def test_from_dict_round_trip(self, binding) -> None:
        d = binding.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        binding2 = KODomainBinding.from_dict(decoded)
        assert binding2 == binding

    def test_from_dict_missing_optional_uses_default(self) -> None:
        minimal = {
            "binding_id": "bnd-2",
            "version": 1,
            "knowledge_object_id": "ko-2",
            "knowledge_object_version": 1,
            "domain_id": "dom-2",
            "binding_type": "primary",
            "priority": 1,
            "membership_reason": "match",
        }
        b = KODomainBinding.from_dict(minimal)
        assert b.binding_id == "bnd-2"
        assert b.created_by == ""
        assert b.proposal_id == ""

    def test_from_dict_non_dict_raises(self) -> None:
        with pytest.raises(KODomainBindingSchemaError):
            KODomainBinding.from_dict("not a dict")  # type: ignore[arg-type]


# ---------------------------------------------------------------------
# Test 4 -- Validator (single-record)
# ---------------------------------------------------------------------


class TestValidatorSingleRecord:

    def test_valid_binding_passes(self, validator, binding) -> None:
        result = validator.validate(binding)
        assert result.valid is True
        assert result.errors == ()

    def test_validation_result_is_frozen(self, validator, binding) -> None:
        result = validator.validate(binding)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.valid = False  # type: ignore[misc]

    def test_none_binding_rejected(self, validator) -> None:
        result = validator.validate(None)  # type: ignore[arg-type]
        assert result.valid is False

    def test_empty_binding_id_rejected(self, validator) -> None:
        class Fake:
            binding_id = ""
            version = 1
            knowledge_object_id = "ko-x"
            knowledge_object_version = 1
            domain_id = "dom-x"
            binding_type = "primary"
            priority = 1
            membership_reason = "x"
            created_at = "x"; updated_at = "x"
            created_by = ""; proposal_id = ""

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("binding_id" in e for e in result.errors)

    def test_invalid_version_rejected(self, validator) -> None:
        class Fake:
            binding_id = "bnd-x"
            version = 0
            knowledge_object_id = "ko-x"
            knowledge_object_version = 1
            domain_id = "dom-x"
            binding_type = "primary"
            priority = 1
            membership_reason = "x"
            created_at = "x"; updated_at = "x"
            created_by = ""; proposal_id = ""

        result = validator.validate(Fake())
        assert result.valid is False
        assert any("version" in e for e in result.errors)

    def test_invalid_binding_type_rejected(self, validator) -> None:
        b = _make_kodomain_binding(binding_type="nonsense")
        result = validator.validate(b)
        assert result.valid is False
        assert any("binding_type" in e for e in result.errors)

    def test_invalid_priority_rejected(self, validator) -> None:
        b = _make_kodomain_binding(priority=0)
        result = validator.validate(b)
        assert result.valid is False
        assert any("priority" in e for e in result.errors)

    def test_empty_membership_reason_rejected(self, validator) -> None:
        b = _make_kodomain_binding(membership_reason="")
        result = validator.validate(b)
        assert result.valid is False
        assert any("membership_reason" in e for e in result.errors)

    def test_empty_knowledge_object_id_rejected(self, validator) -> None:
        b = _make_kodomain_binding(knowledge_object_id="")
        result = validator.validate(b)
        assert result.valid is False
        assert any("knowledge_object_id" in e for e in result.errors)

    def test_empty_domain_id_rejected(self, validator) -> None:
        b = _make_kodomain_binding(domain_id="")
        result = validator.validate(b)
        assert result.valid is False
        assert any("domain_id" in e for e in result.errors)


# ---------------------------------------------------------------------
# Test 5 -- Validator (cross-record)
# ---------------------------------------------------------------------


class TestValidatorCrossRecord:

    def test_unique_binding_id_passes(
        self, validator, binding, registry,
    ) -> None:
        registry.append(binding)
        # A different binding_id is allowed.
        new_binding = _make_kodomain_binding(
            binding_id="bnd-2",
            binding_type="secondary",
            priority=2,
        )
        result = validator.validate(
            new_binding, existing_bindings=registry.list(),
        )
        assert result.valid is True

    def test_duplicate_binding_id_rejected(
        self, validator, binding, registry,
    ) -> None:
        registry.append(binding)
        # Same binding_id -> rejected.
        new_binding = _make_kodomain_binding(
            binding_id=binding.binding_id,
            binding_type="secondary",
            priority=2,
        )
        result = validator.validate(
            new_binding, existing_bindings=registry.list(),
        )
        assert result.valid is False
        assert any("binding_id is not unique" in e for e in result.errors)

    def test_second_primary_for_same_ko_rejected(
        self, validator, binding, registry,
    ) -> None:
        # Insert one primary binding for KO_ID.
        registry.append(binding)
        # Attempt to insert another primary binding for the
        # SAME KO.
        new_primary = _make_kodomain_binding(
            binding_id="bnd-2",
            binding_type="primary",
            priority=1,
        )
        result = validator.validate(
            new_primary, existing_bindings=registry.list(),
        )
        assert result.valid is False
        assert any(
            "only one primary per KO" in e for e in result.errors
        )

    def test_secondary_after_primary_passes(
        self, validator, binding, registry,
    ) -> None:
        registry.append(binding)
        # A second binding with binding_type=secondary is
        # allowed for the same KO.
        secondary = _make_kodomain_binding(
            binding_id="bnd-2",
            binding_type="secondary",
            priority=2,
            domain_id="dom-bind-2",
        )
        result = validator.validate(
            secondary, existing_bindings=registry.list(),
        )
        assert result.valid is True


# ---------------------------------------------------------------------
# Test 6 -- Registry
# ---------------------------------------------------------------------


class TestRegistry:

    def test_append_and_count(self, registry, binding) -> None:
        assert registry.count() == 0
        registry.append(binding)
        assert registry.count() == 1

    def test_append_wrong_type_rejected(self, registry) -> None:
        with pytest.raises(BindingRegistryError):
            registry.append("not a binding")  # type: ignore[arg-type]

    def test_get_by_binding_id(self, registry, binding) -> None:
        registry.append(binding)
        got = registry.get(binding.binding_id)
        assert got is binding

    def test_get_returns_none_when_missing(self, registry) -> None:
        assert registry.get("nonexistent") is None

    def test_for_knowledge_object(self, registry, binding) -> None:
        registry.append(binding)
        registry.append(
            _make_kodomain_binding(
                binding_id="bnd-2",
                binding_type="secondary",
                priority=2,
                domain_id="dom-2",
            )
        )
        registry.append(
            _make_kodomain_binding(
                binding_id="bnd-3",
                knowledge_object_id="ko-other",
                binding_type="primary",
                priority=1,
            )
        )
        found = registry.for_knowledge_object(KO_ID)
        assert len(found) == 2
        assert all(b.knowledge_object_id == KO_ID for b in found)

    def test_for_domain(self, registry, binding) -> None:
        registry.append(binding)
        registry.append(
            _make_kodomain_binding(
                binding_id="bnd-2",
                binding_type="secondary",
                priority=2,
                domain_id="dom-other",
            )
        )
        found = registry.for_domain(DOM_ID)
        assert len(found) == 1

    def test_list_returns_copy(self, registry, binding) -> None:
        registry.append(binding)
        snapshot = registry.list()
        snapshot.clear()
        # The registry's internal list is NOT cleared.
        assert registry.count() == 1

    def test_distinct_ids(self, registry) -> None:
        registry.append(_make_kodomain_binding(binding_id="bnd-a"))
        registry.append(_make_kodomain_binding(binding_id="bnd-b"))
        registry.append(
            _make_kodomain_binding(
                binding_id="bnd-c",
                binding_type="secondary",
                priority=2,
            )
        )
        assert registry.binding_ids() == ["bnd-a", "bnd-b", "bnd-c"]
        assert registry.knowledge_object_ids() == [KO_ID]
        assert registry.domain_ids() == [DOM_ID]


# ---------------------------------------------------------------------
# Test 7 -- Append-only contract
# ---------------------------------------------------------------------


class TestAppendOnly:

    def test_update_rejected(self, registry) -> None:
        with pytest.raises(TypeError):
            registry.update("bnd-1", binding=None)

    def test_delete_rejected(self, registry) -> None:
        with pytest.raises(TypeError):
            registry.delete("bnd-1")

    def test_overwrite_rejected(self, registry) -> None:
        with pytest.raises(TypeError):
            registry.overwrite("bnd-1", binding=None)

    def test_clear_rejected(self, registry, binding) -> None:
        registry.append(binding)
        with pytest.raises(TypeError):
            registry.clear()
        # The binding is still there.
        assert registry.count() == 1

    def test_existing_bindings_unchanged(self, registry, binding) -> None:
        registry.append(binding)
        original_count = registry.count()
        # Attempting forbidden operations does not change
        # state.
        try:
            registry.update()
        except TypeError:
            pass
        try:
            registry.delete()
        except TypeError:
            pass
        assert registry.count() == original_count


# ---------------------------------------------------------------------
# Test 8 -- Deep-copy isolation
# ---------------------------------------------------------------------


class TestInputIsolation:

    def test_registry_input_isolation(
        self, registry, binding,
    ) -> None:
        # The binding is frozen, so we cannot mutate it
        # anyway; the test confirms the registry stores
        # the SAME object reference (which is desired for
        # append-only semantics).
        registry.append(binding)
        assert registry.get(binding.binding_id) is binding


# ---------------------------------------------------------------------
# Test 9 -- Report
# ---------------------------------------------------------------------


class TestReport:

    def test_report_without_registry(self) -> None:
        report = generate_binding_report()
        assert "# KODomainBinding Schema Report" in report
        assert "## Overview" in report
        assert "## Identity Fields" in report
        assert "## Reference Fields" in report
        assert "## Metadata Fields" in report
        assert "## Version Policy" in report
        assert "## Binding Type Allow-list" in report
        assert "## Validation Rules" in report
        assert "## Registry Snapshot" in report
        assert "## Architecture Boundary" in report

    def test_report_with_empty_registry(self) -> None:
        report = generate_binding_report(BindingRegistry())
        assert "registry is empty" in report

    def test_report_with_populated_registry(
        self, registry, binding,
    ) -> None:
        registry.append(binding)
        report = generate_binding_report(registry)
        assert "total bindings**" in report
        assert "1" in report
        assert KO_ID in report
        assert DOM_ID in report


# ---------------------------------------------------------------------
# Test 10 -- Architecture boundary (AST scan)
# ---------------------------------------------------------------------


class TestArchitectureBoundary:

    def test_binding_module_no_forbidden_imports(self) -> None:
        binding_dir = (
            pathlib.Path(__file__).resolve().parents[1]
            / "caseos"
            / "knowledge"
            / "binding"
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
        for py in sorted(binding_dir.glob("*.py")):
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
# Test 11 -- KO / Domain 隔离
# ---------------------------------------------------------------------


class TestKnowledgeObjectAndDomainIsolation:

    def test_ko_and_domain_can_be_siblings(self) -> None:
        # Confirm the sibling packages exist and are importable.
        from caseos.knowledge.object import KnowledgeObject  # noqa: F401
        from caseos.knowledge.domain import KnowledgeDomain  # noqa: F401
        assert KnowledgeObject is not None
        assert KnowledgeDomain is not None

    def test_binding_does_not_mutate_ko(self) -> None:
        from caseos.knowledge.object import KnowledgeObject

        ko = KnowledgeObject(
            knowledge_id=KO_ID,
            version=1,
            title="t",
            description="d",
            category="c",
            project_type="p",
            site_type="s",
            location_type="l",
            space_size="500sqm",
            theme="t",
            style="s",
            color_system="c",
            interaction_type="i",
            created_at=NOW_ISO,
            updated_at=NOW_ISO,
            source="op",
        )
        before = ko.to_dict()
        # Create a binding that targets this KO. The KO is
        # frozen; verify the binding does not affect it.
        b = _make_kodomain_binding(
            knowledge_object_id=ko.knowledge_id,
            knowledge_object_version=ko.version,
        )
        assert b.knowledge_object_id == ko.knowledge_id
        # The KO is untouched.
        assert ko.to_dict() == before

    def test_binding_does_not_mutate_domain(self) -> None:
        from caseos.knowledge.domain import KnowledgeDomain

        d = KnowledgeDomain(
            domain_id=DOM_ID,
            version=1,
            domain_type="design_category",
            name="Kindergarten design",
            description="x",
            created_at=NOW_ISO,
            updated_at=NOW_ISO,
        )
        before = d.to_dict()
        b = _make_kodomain_binding(domain_id=d.domain_id)
        assert b.domain_id == d.domain_id
        assert d.to_dict() == before
