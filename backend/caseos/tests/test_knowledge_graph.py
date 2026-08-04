"""Knowledge Graph Validation Runtime V1 tests (Sprint 23.2-A).

测试范围：

    * GraphValidationRequest / GraphValidationResult /
      GraphIssue (frozen, JSON-safe, deep-copy isolation)
    * KnowledgeGraphValidator happy path
    * G1 KO.category 在 Domain.allowed_knowledge_types
    * G2 required attribute 必须有非空值
    * G3 enum 值必须在 attribute.allowed_node_ids
    * G4 string 值匹配 attribute.pattern
    * G5 number 值在 [min_value, max_value]
    * G6 binding 必须引用存在的 Domain
    * G7 attribute.allowed_taxonomy_id 必须引用存在的 Taxonomy
    * G8 binding.knowledge_object_id 必须等于 request 的 KO id
    * 错误与警告分桶
    * Markdown 报告
    * Architecture boundary (AST scan)
    * 上游各层不被 graph validator 修改

不在测试范围内：

    * Pipeline wiring
    * Intelligence / Retrieval / Evolution
    * 自动分类 / 自动学习
"""
from __future__ import annotations

import ast
import copy
import dataclasses
import json
import pathlib

import pytest

from caseos.knowledge.attribute import KnowledgeAttribute
from caseos.knowledge.binding import KODomainBinding
from caseos.knowledge.domain import KnowledgeDomain
from caseos.knowledge.graph import (
    SEVERITY_ALLOW_LIST,
    TARGET_KIND_ALLOW_LIST,
    generate_graph_report,
    GraphIssue,
    GraphIssueError,
    GraphValidationError,
    GraphValidationRequest,
    GraphValidationResult,
    KnowledgeGraphValidator,
)
from caseos.knowledge.object import KnowledgeObject
from caseos.knowledge.taxonomy import Taxonomy


NOW_ISO = "2026-08-04T00:00:00Z"
KO_ID = "ko-graph-1"
DOM_ID = "dom-graph-1"
TAX_ID = "tax-graph-1"


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _make_ko(**overrides) -> KnowledgeObject:
    base = dict(
        knowledge_id=KO_ID,
        version=1,
        title="Forest kindergarten",
        description="x",
        category="education",
        project_type="kindergarten",
        site_type="suburban",
        location_type="outdoor",
        space_size="500sqm",
        theme="forest",
        style="scandinavian",
        color_system="earth-tones",
        interaction_type="exploratory",
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
        source="op",
    )
    base.update(overrides)
    return KnowledgeObject(**base)


def _make_domain(
    *,
    domain_id=DOM_ID,
    allowed_knowledge_types=None,
    **overrides,
) -> KnowledgeDomain:
    base = dict(
        domain_id=domain_id,
        version=1,
        domain_type="design_category",
        name="Kindergarten design",
        description="x",
        allowed_knowledge_types=(
            allowed_knowledge_types
            if allowed_knowledge_types is not None
            else ["education", "commercial"]
        ),
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )
    base.update(overrides)
    return KnowledgeDomain(**base)


def _make_binding(
    *,
    binding_id="bnd-1",
    knowledge_object_id=KO_ID,
    domain_id=DOM_ID,
    binding_type="primary",
    **overrides,
) -> KODomainBinding:
    base = dict(
        binding_id=binding_id,
        version=1,
        knowledge_object_id=knowledge_object_id,
        knowledge_object_version=1,
        domain_id=domain_id,
        binding_type=binding_type,
        priority=1,
        membership_reason="match",
    )
    base.update(overrides)
    return KODomainBinding(**base)


def _make_attribute(
    *,
    attribute_id="attr-style-1",
    name="style",
    data_type="enum",
    cardinality="single",
    required=True,
    allowed_taxonomy_id=None,
    allowed_node_ids=None,
    pattern=None,
    min_value=None,
    max_value=None,
    **overrides,
) -> KnowledgeAttribute:
    base = dict(
        attribute_id=attribute_id,
        version=1,
        name=name,
        description="d",
        attribute_type="property",
        data_type=data_type,
        cardinality=cardinality,
        required=required,
        default_value=None,
        allowed_taxonomy_id=allowed_taxonomy_id,
        allowed_node_ids=(
            allowed_node_ids
            if allowed_node_ids is not None
            else ["scandinavian", "industrial"]
        ),
        min_value=min_value,
        max_value=max_value,
        pattern=pattern,
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )
    base.update(overrides)
    return KnowledgeAttribute(**base)


def _make_taxonomy(
    *,
    taxonomy_id=TAX_ID,
    **overrides,
) -> Taxonomy:
    base = dict(
        taxonomy_id=taxonomy_id,
        version=1,
        name="Design Style Taxonomy",
        description="x",
        taxonomy_type="style",
        root_node_ids=[],
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
    )
    base.update(overrides)
    return Taxonomy(**base)


def _make_happy_request(
    *,
    bindings=None,
    domains=None,
    attributes=None,
    taxonomies=None,
    ko_attribute_values=None,
) -> GraphValidationRequest:
    ko = _make_ko()
    if bindings is None:
        bindings = [_make_binding()]
    if domains is None:
        domains = [_make_domain()]
    if attributes is None:
        attributes = [_make_attribute()]
    if taxonomies is None:
        taxonomies = []
    if ko_attribute_values is None:
        ko_attribute_values = {"style": "scandinavian"}
    return GraphValidationRequest(
        request_id="greq-1",
        knowledge_object=ko,
        bindings=bindings,
        domains=domains,
        taxonomies=taxonomies,
        taxonomy_nodes=[],
        attributes=attributes,
        ko_attribute_values=ko_attribute_values,
    )


@pytest.fixture
def validator() -> KnowledgeGraphValidator:
    return KnowledgeGraphValidator()


# ---------------------------------------------------------------------
# Test 1 -- 基础 frozen + JSON
# ---------------------------------------------------------------------


class TestFrozenContracts:

    def test_request_is_frozen(self) -> None:
        req = _make_happy_request()
        with pytest.raises(dataclasses.FrozenInstanceError):
            req.request_id = "x"  # type: ignore[misc]

    def test_result_is_frozen(self, validator) -> None:
        req = _make_happy_request()
        result = validator.validate(req)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.success = False  # type: ignore[misc]

    def test_issue_is_frozen(self, validator) -> None:
        req = GraphValidationRequest(
            request_id="greq-bad",
            knowledge_object=_make_ko(category="other"),
            bindings=[_make_binding()],
            domains=[_make_domain(
                allowed_knowledge_types=["education"],
            )],
            attributes=[_make_attribute()],
            ko_attribute_values={"style": "scandinavian"},
        )
        result = validator.validate(req)
        # Find the G1 issue.
        g1 = next(i for i in result.issues if i.rule_id == "G1")
        with pytest.raises(dataclasses.FrozenInstanceError):
            g1.severity = "warning"  # type: ignore[misc]

    def test_request_json_round_trip(self) -> None:
        req = _make_happy_request()
        d = req.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        assert decoded["request_id"] == req.request_id
        assert decoded["knowledge_object_id"] == KO_ID

    def test_result_json_round_trip(self, validator) -> None:
        req = _make_happy_request()
        result = validator.validate(req)
        d = result.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        assert decoded["success"] is True
        assert decoded["knowledge_object_id"] == KO_ID


# ---------------------------------------------------------------------
# Test 2 -- Severity / target_kind allow-lists
# ---------------------------------------------------------------------


class TestAllowLists:

    def test_severity_allow_list(self) -> None:
        assert "error" in SEVERITY_ALLOW_LIST
        assert "warning" in SEVERITY_ALLOW_LIST
        assert "info" in SEVERITY_ALLOW_LIST

    def test_target_kind_allow_list(self) -> None:
        assert "knowledge_object" in TARGET_KIND_ALLOW_LIST
        assert "binding" in TARGET_KIND_ALLOW_LIST
        assert "domain" in TARGET_KIND_ALLOW_LIST
        assert "attribute" in TARGET_KIND_ALLOW_LIST
        assert "taxonomy" in TARGET_KIND_ALLOW_LIST
        assert "taxonomy_node" in TARGET_KIND_ALLOW_LIST

    def test_invalid_severity_rejected(self) -> None:
        with pytest.raises(GraphValidationError):
            GraphIssue(
                issue_id="iss-1",
                rule_id="G1",
                severity="nonsense",
                target_kind="domain",
                target_id="dom-1",
                field_name=None,
                message="x",
            )

    def test_invalid_target_kind_rejected(self) -> None:
        with pytest.raises(GraphValidationError):
            GraphIssue(
                issue_id="iss-1",
                rule_id="G1",
                severity="error",
                target_kind="nonsense",
                target_id="x",
                field_name=None,
                message="x",
            )

    def test_missing_knowledge_object_rejected(self) -> None:
        with pytest.raises(GraphValidationError):
            GraphValidationRequest(
                request_id="greq-x",
                knowledge_object=None,  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------
# Test 3 -- Happy path
# ---------------------------------------------------------------------


class TestHappyPath:

    def test_happy_path_no_issues(self, validator) -> None:
        req = _make_happy_request()
        result = validator.validate(req)
        assert result.success is True
        assert result.issues == ()
        assert result.errors == ()
        assert result.warnings == ()

    def test_ko_unchanged_after_validate(self, validator) -> None:
        ko = _make_ko()
        before = ko.to_dict()
        req = _make_happy_request()
        validator.validate(req)
        assert ko.to_dict() == before

    def test_domain_unchanged_after_validate(self, validator) -> None:
        domain = _make_domain()
        before = domain.to_dict()
        req = _make_happy_request(domains=[domain])
        validator.validate(req)
        assert domain.to_dict() == before

    def test_binding_unchanged_after_validate(self, validator) -> None:
        binding = _make_binding()
        before = binding.to_dict()
        req = _make_happy_request(bindings=[binding])
        validator.validate(req)
        assert binding.to_dict() == before

    def test_attribute_unchanged_after_validate(self, validator) -> None:
        attr = _make_attribute()
        before = attr.to_dict()
        req = _make_happy_request(attributes=[attr])
        validator.validate(req)
        assert attr.to_dict() == before


# ---------------------------------------------------------------------
# Test 4 -- G1: KO.category in Domain.allowed_knowledge_types
# ---------------------------------------------------------------------


class TestRuleG1:

    def test_category_in_allow_list_passes(self, validator) -> None:
        req = _make_happy_request()  # category="education"
        result = validator.validate(req)
        assert not any(i.rule_id == "G1" for i in result.issues)

    def test_category_not_in_allow_list_emits_g1(
        self, validator,
    ) -> None:
        ko = _make_ko(category="other")
        req = GraphValidationRequest(
            request_id="greq-x",
            knowledge_object=ko,
            bindings=[_make_binding()],
            domains=[_make_domain(
                allowed_knowledge_types=["education"],
            )],
            attributes=[_make_attribute()],
            ko_attribute_values={"style": "scandinavian"},
        )
        result = validator.validate(req)
        g1 = [i for i in result.issues if i.rule_id == "G1"]
        assert len(g1) == 1
        assert g1[0].severity == "error"
        assert g1[0].target_kind == "domain"
        assert result.success is False

    def test_empty_allow_list_passes(self, validator) -> None:
        # Domain with empty allowed_knowledge_types imposes
        # no constraint, so G1 does NOT fire.
        req = _make_happy_request(
            domains=[_make_domain(allowed_knowledge_types=[])],
        )
        result = validator.validate(req)
        assert not any(i.rule_id == "G1" for i in result.issues)


# ---------------------------------------------------------------------
# Test 5 -- G2: required attribute must have non-empty value
# ---------------------------------------------------------------------


class TestRuleG2:

    def test_required_with_value_passes(self, validator) -> None:
        req = _make_happy_request(
            ko_attribute_values={"style": "scandinavian"},
        )
        result = validator.validate(req)
        assert not any(i.rule_id == "G2" for i in result.issues)

    def test_required_missing_value_emits_g2(self, validator) -> None:
        req = _make_happy_request(
            ko_attribute_values={},  # style is missing
        )
        result = validator.validate(req)
        g2 = [i for i in result.issues if i.rule_id == "G2"]
        assert len(g2) == 1
        assert g2[0].severity == "error"

    def test_required_empty_string_emits_g2(self, validator) -> None:
        req = _make_happy_request(
            ko_attribute_values={"style": "   "},
        )
        result = validator.validate(req)
        g2 = [i for i in result.issues if i.rule_id == "G2"]
        assert len(g2) == 1

    def test_optional_missing_value_passes(self, validator) -> None:
        req = _make_happy_request(
            attributes=[_make_attribute(required=False)],
            ko_attribute_values={},
        )
        result = validator.validate(req)
        assert not any(i.rule_id == "G2" for i in result.issues)


# ---------------------------------------------------------------------
# Test 6 -- G3: enum value in attribute.allowed_node_ids
# ---------------------------------------------------------------------


class TestRuleG3:

    def test_enum_value_in_allow_list_passes(self, validator) -> None:
        req = _make_happy_request(
            ko_attribute_values={"style": "scandinavian"},
        )
        result = validator.validate(req)
        assert not any(i.rule_id == "G3" for i in result.issues)

    def test_enum_value_not_in_allow_list_emits_g3(
        self, validator,
    ) -> None:
        req = _make_happy_request(
            ko_attribute_values={"style": "gothic"},
        )
        result = validator.validate(req)
        g3 = [i for i in result.issues if i.rule_id == "G3"]
        assert len(g3) == 1
        assert g3[0].severity == "error"

    def test_empty_allow_list_skips_g3(self, validator) -> None:
        # If allowed_node_ids is empty, G3 does NOT fire
        # (the constraint is meaningless).
        req = _make_happy_request(
            attributes=[_make_attribute(allowed_node_ids=[])],
            ko_attribute_values={"style": "anything"},
        )
        result = validator.validate(req)
        assert not any(i.rule_id == "G3" for i in result.issues)

    def test_non_enum_attribute_skips_g3(self, validator) -> None:
        req = _make_happy_request(
            attributes=[_make_attribute(data_type="string")],
            ko_attribute_values={"style": "anything"},
        )
        result = validator.validate(req)
        assert not any(i.rule_id == "G3" for i in result.issues)


# ---------------------------------------------------------------------
# Test 7 -- G4: string pattern
# ---------------------------------------------------------------------


class TestRuleG4:

    def test_pattern_match_passes(self, validator) -> None:
        req = _make_happy_request(
            attributes=[_make_attribute(
                data_type="string",
                pattern="scan",
                allowed_node_ids=[],
            )],
            ko_attribute_values={"style": "scandinavian"},
        )
        result = validator.validate(req)
        assert not any(i.rule_id == "G4" for i in result.issues)

    def test_pattern_mismatch_emits_g4(self, validator) -> None:
        req = _make_happy_request(
            attributes=[_make_attribute(
                data_type="string",
                pattern="^foo",
                allowed_node_ids=[],
            )],
            ko_attribute_values={"style": "scandinavian"},
        )
        result = validator.validate(req)
        g4 = [i for i in result.issues if i.rule_id == "G4"]
        assert len(g4) == 1
        assert g4[0].severity == "warning"

    def test_invalid_pattern_emits_g4_info(self, validator) -> None:
        req = _make_happy_request(
            attributes=[_make_attribute(
                data_type="string",
                pattern="[invalid(",
                allowed_node_ids=[],
            )],
            ko_attribute_values={"style": "scandinavian"},
        )
        result = validator.validate(req)
        g4 = [i for i in result.issues if i.rule_id == "G4"]
        assert len(g4) == 1
        assert g4[0].severity == "info"


# ---------------------------------------------------------------------
# Test 8 -- G5: number range
# ---------------------------------------------------------------------


class TestRuleG5:

    def test_in_range_passes(self, validator) -> None:
        req = _make_happy_request(
            attributes=[_make_attribute(
                data_type="number",
                name="capacity",
                allowed_node_ids=[],
                min_value=0,
                max_value=100,
            )],
            ko_attribute_values={"capacity": 50},
        )
        result = validator.validate(req)
        assert not any(i.rule_id == "G5" for i in result.issues)

    def test_below_min_emits_g5(self, validator) -> None:
        req = _make_happy_request(
            attributes=[_make_attribute(
                data_type="number",
                name="capacity",
                allowed_node_ids=[],
                min_value=10,
                max_value=100,
            )],
            ko_attribute_values={"capacity": 5},
        )
        result = validator.validate(req)
        g5 = [i for i in result.issues if i.rule_id == "G5"]
        assert len(g5) == 1
        assert "below min_value" in g5[0].message

    def test_above_max_emits_g5(self, validator) -> None:
        req = _make_happy_request(
            attributes=[_make_attribute(
                data_type="number",
                name="capacity",
                allowed_node_ids=[],
                min_value=0,
                max_value=10,
            )],
            ko_attribute_values={"capacity": 50},
        )
        result = validator.validate(req)
        g5 = [i for i in result.issues if i.rule_id == "G5"]
        assert len(g5) == 1
        assert "above max_value" in g5[0].message

    def test_non_number_value_emits_g5(self, validator) -> None:
        req = _make_happy_request(
            attributes=[_make_attribute(
                data_type="number",
                name="capacity",
                allowed_node_ids=[],
                min_value=0,
                max_value=10,
            )],
            ko_attribute_values={"capacity": "fifty"},
        )
        result = validator.validate(req)
        g5 = [i for i in result.issues if i.rule_id == "G5"]
        assert len(g5) == 1
        assert "not a number" in g5[0].message


# ---------------------------------------------------------------------
# Test 9 -- G6: binding must reference existing Domain
# ---------------------------------------------------------------------


class TestRuleG6:

    def test_existing_domain_passes(self, validator) -> None:
        req = _make_happy_request()
        result = validator.validate(req)
        assert not any(i.rule_id == "G6" for i in result.issues)

    def test_unknown_domain_emits_g6(self, validator) -> None:
        req = _make_happy_request(
            bindings=[_make_binding(domain_id="dom-missing")],
            domains=[_make_domain(domain_id="dom-other")],
        )
        result = validator.validate(req)
        g6 = [i for i in result.issues if i.rule_id == "G6"]
        assert len(g6) == 1
        assert g6[0].severity == "error"

    def test_empty_domain_id_emits_g6(self, validator) -> None:
        # The domain_id is None-equivalent (empty string).
        # We use a binding with empty domain_id; bypass the
        # KODomainBinding constructor via dataclasses.replace
        # is complex; instead, use a duck-typed Fake binding.
        class FakeBinding:
            binding_id = "bnd-x"
            knowledge_object_id = KO_ID
            domain_id = ""
            binding_type = "primary"

        req = GraphValidationRequest(
            request_id="greq-x",
            knowledge_object=_make_ko(),
            bindings=[FakeBinding()],
            domains=[_make_domain()],
            attributes=[_make_attribute()],
            ko_attribute_values={"style": "scandinavian"},
        )
        result = validator.validate(req)
        g6 = [i for i in result.issues if i.rule_id == "G6"]
        assert len(g6) == 1


# ---------------------------------------------------------------------
# Test 10 -- G7: attribute.allowed_taxonomy_id must exist
# ---------------------------------------------------------------------


class TestRuleG7:

    def test_existing_taxonomy_passes(self, validator) -> None:
        req = _make_happy_request(
            attributes=[_make_attribute(allowed_taxonomy_id=TAX_ID)],
            taxonomies=[_make_taxonomy()],
        )
        result = validator.validate(req)
        assert not any(i.rule_id == "G7" for i in result.issues)

    def test_unknown_taxonomy_emits_g7(self, validator) -> None:
        req = _make_happy_request(
            attributes=[_make_attribute(
                allowed_taxonomy_id="tax-missing",
            )],
            taxonomies=[_make_taxonomy()],
        )
        result = validator.validate(req)
        g7 = [i for i in result.issues if i.rule_id == "G7"]
        assert len(g7) == 1
        assert g7[0].severity == "error"

    def test_none_taxonomy_id_passes(self, validator) -> None:
        # When allowed_taxonomy_id is None, G7 does NOT fire.
        req = _make_happy_request(
            attributes=[_make_attribute(allowed_taxonomy_id=None)],
        )
        result = validator.validate(req)
        assert not any(i.rule_id == "G7" for i in result.issues)


# ---------------------------------------------------------------------
# Test 11 -- G8: binding.knowledge_object_id must equal KO id
# ---------------------------------------------------------------------


class TestRuleG8:

    def test_matching_ko_id_passes(self, validator) -> None:
        req = _make_happy_request()
        result = validator.validate(req)
        assert not any(i.rule_id == "G8" for i in result.issues)

    def test_mismatched_ko_id_emits_g8(self, validator) -> None:
        req = _make_happy_request(
            bindings=[_make_binding(
                knowledge_object_id="ko-other",
            )],
        )
        result = validator.validate(req)
        g8 = [i for i in result.issues if i.rule_id == "G8"]
        assert len(g8) == 1
        assert g8[0].severity == "error"


# ---------------------------------------------------------------------
# Test 12 -- 错误/警告分桶
# ---------------------------------------------------------------------


class TestBucketing:

    def test_errors_and_warnings_separated(self, validator) -> None:
        # Craft a request that triggers both an error and a
        # warning.
        ko = _make_ko(category="other")  # G1 error
        req = GraphValidationRequest(
            request_id="greq-mix",
            knowledge_object=ko,
            bindings=[_make_binding()],
            domains=[_make_domain(
                allowed_knowledge_types=["education"],
            )],
            attributes=[
                _make_attribute(),  # required
                _make_attribute(
                    attribute_id="attr-warn-1",
                    name="secondary",
                    data_type="string",
                    required=False,
                    pattern="^foo",
                    allowed_node_ids=[],
                ),
            ],
            ko_attribute_values={
                "style": "scandinavian",
                "secondary": "bar",  # does not match pattern
            },
        )
        result = validator.validate(req)
        assert result.success is False
        assert any(
            i.severity == "error" for i in result.errors
        )
        assert any(
            i.severity == "warning" for i in result.warnings
        )
        # Every issue appears in .issues exactly once.
        assert len(result.issues) == (
            len(result.errors) + len(result.warnings)
        )

    def test_no_errors_means_success(self, validator) -> None:
        req = _make_happy_request()
        result = validator.validate(req)
        assert result.errors == ()
        assert result.success is True


# ---------------------------------------------------------------------
# Test 13 -- Rule set override
# ---------------------------------------------------------------------


class TestRuleSetOverride:

    def test_disable_g1(self) -> None:
        validator = KnowledgeGraphValidator(
            rule_set=frozenset({"G2", "G3", "G4", "G5", "G6", "G7", "G8"}),
        )
        ko = _make_ko(category="other")
        req = GraphValidationRequest(
            request_id="greq-x",
            knowledge_object=ko,
            bindings=[_make_binding()],
            domains=[_make_domain(
                allowed_knowledge_types=["education"],
            )],
            attributes=[_make_attribute()],
            ko_attribute_values={"style": "scandinavian"},
        )
        result = validator.validate(req)
        assert not any(i.rule_id == "G1" for i in result.issues)


# ---------------------------------------------------------------------
# Test 14 -- Deep-copy isolation
# ---------------------------------------------------------------------


class TestInputIsolation:

    def test_request_input_lists_isolated(self, validator) -> None:
        # The validator must NOT mutate any of the supplied
        # graph components. Since KODomainBinding /
        # KnowledgeDomain / KnowledgeAttribute are frozen,
        # mutation is impossible regardless; the test
        # confirms the validator did not somehow replace
        # them in place.
        binding = _make_binding()
        domain = _make_domain()
        attr = _make_attribute()
        binding_before = binding.to_dict()
        domain_before = domain.to_dict()
        attr_before = attr.to_dict()
        req = GraphValidationRequest(
            request_id="greq-iso",
            knowledge_object=_make_ko(),
            bindings=[binding],
            domains=[domain],
            attributes=[attr],
        )
        validator.validate(req)
        assert binding.to_dict() == binding_before
        assert domain.to_dict() == domain_before
        assert attr.to_dict() == attr_before

# ---------------------------------------------------------------------
# Test 15 -- Report
# ---------------------------------------------------------------------


class TestReport:

    def test_report_without_result(self) -> None:
        report = generate_graph_report()
        assert "# Knowledge Graph Validation Report" in report
        assert "## Summary" in report
        assert "## Architecture Boundary" in report

    def test_report_with_happy_result(self, validator) -> None:
        req = _make_happy_request()
        result = validator.validate(req)
        report = generate_graph_report(result)
        assert "**success**: `True`" in report
        assert "no issues emitted" in report

    def test_report_with_issues(self, validator) -> None:
        ko = _make_ko(category="other")
        req = GraphValidationRequest(
            request_id="greq-x",
            knowledge_object=ko,
            bindings=[_make_binding()],
            domains=[_make_domain(
                allowed_knowledge_types=["education"],
            )],
            attributes=[_make_attribute()],
            ko_attribute_values={"style": "scandinavian"},
        )
        result = validator.validate(req)
        report = generate_graph_report(result)
        assert "**G1**" in report
        assert "errors**: 1" in report or "errors**: 1" in report
        assert "knowledge_object.category" in report


# ---------------------------------------------------------------------
# Test 16 -- Architecture boundary (AST scan)
# ---------------------------------------------------------------------


class TestArchitectureBoundary:

    def test_graph_module_no_forbidden_imports(self) -> None:
        graph_dir = (
            pathlib.Path(__file__).resolve().parents[1]
            / "caseos"
            / "knowledge"
            / "graph"
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
        for py in sorted(graph_dir.glob("*.py")):
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
