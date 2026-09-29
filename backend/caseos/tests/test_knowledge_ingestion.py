"""Tests for the Case Knowledge Ingestion Contract V1 (Sprint 25.0-A, inferred).

Coverage:

    * CaseKnowledge shape + JSON round-trip + immutability.
    * IngestionContract default rule table + invariants.
    * IngestionValidator: each rule I1..I6 happy path + failures.
    * Source kind allow list guard.
    * new_case_knowledge convenience builder.
    * Report generator emits a non-empty Markdown string with
      every required section.
    * AST architecture boundary -- the package does NOT import
      from any forbidden module.

Architecture boundary (Sprint 25.0-A inferred scope):

    These tests do NOT import forbidden modules.
    These tests MAY import from:
        * caseos.knowledge.object
        * caseos.knowledge.attribute
        * caseos.knowledge.domain
        * caseos.knowledge.binding
        * caseos.knowledge.taxonomy
        * caseos.knowledge.ingestion (the package under test)
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

from caseos.knowledge.ingestion import (  # noqa: E402
    MAX_ASSET_COUNT,
    MAX_TAG_COUNT,
    MIN_ASSET_COUNT,
    MIN_TAG_COUNT,
    SOURCE_KIND_ALLOW_LIST,
    SOURCE_KIND_EXTERNAL,
    SOURCE_KIND_INTAKE,
    SOURCE_KIND_OPERATOR,
    CaseKnowledge,
    CaseKnowledgeError,
    IngestionContract,
    IngestionContractError,
    IngestionValidationResult,
    IngestionValidator,
    generate_report,
    new_case_knowledge,
)
from caseos.knowledge.ingestion.contract import (  # noqa: E402
    DEFAULT_INGESTION_CONTRACT,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _valid_record(**overrides) -> CaseKnowledge:
    base = dict(
        source="manual:test",
        source_kind=SOURCE_KIND_INTAKE,
        title="Forest kindergarten case",
        description="A baseline kindergarten case.",
        knowledge_id="ko_forest_v1",
        knowledge_version=1,
        tags=("kindergarten", "outdoor"),
        linked_assets=("assets/forest-1.png",),
        origin_reference="Sprint 25.0-A fixture",
        created_by="fixture",
        requires_human_review=True,
    )
    base.update(overrides)
    return new_case_knowledge(**base)


# ---------------------------------------------------------------------------
# 1. CaseKnowledge shape
# ---------------------------------------------------------------------------


class TestCaseKnowledgeShape:
    def test_default_construction_is_valid(self) -> None:
        r = _valid_record()
        assert isinstance(r, CaseKnowledge)
        assert r.case_id.startswith("CK-")
        assert r.source_kind == SOURCE_KIND_INTAKE
        assert r.requires_human_review is True

    def test_frozen_dataclass_blocks_mutation(self) -> None:
        r = _valid_record()
        with pytest.raises(Exception):
            r.title = "mutated"  # type: ignore[misc]

    def test_collection_fields_are_tuples(self) -> None:
        r = _valid_record(tags=["a", "b"], linked_assets=["x"])
        assert isinstance(r.tags, tuple)
        assert isinstance(r.linked_assets, tuple)
        assert r.tags == ("a", "b")
        assert r.linked_assets == ("x",)

    def test_collection_fields_are_defensively_copied(self) -> None:
        src_tags = ["a", "b"]
        r = new_case_knowledge(
            source="x", tags=src_tags, linked_assets=[],
        )
        src_tags.append("c")
        # The frozen record must not be affected by caller mutation.
        assert "c" not in r.tags

    def test_invalid_source_kind_rejected(self) -> None:
        with pytest.raises(CaseKnowledgeError):
            new_case_knowledge(
                source="x", source_kind="not_a_kind",
            )

    def test_non_positive_version_rejected(self) -> None:
        with pytest.raises(CaseKnowledgeError):
            CaseKnowledge(knowledge_version=0)
        with pytest.raises(CaseKnowledgeError):
            CaseKnowledge(knowledge_version=-1)

    def test_empty_case_id_rejected(self) -> None:
        with pytest.raises(CaseKnowledgeError):
            CaseKnowledge(case_id="")

    def test_to_dict_round_trip(self) -> None:
        r = _valid_record()
        d = r.to_dict()
        json.dumps(d)  # JSON-safe
        r2 = CaseKnowledge.from_dict(d)
        assert r2 == r

    def test_from_dict_rejects_non_dict(self) -> None:
        with pytest.raises(CaseKnowledgeError):
            CaseKnowledge.from_dict("not a dict")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 2. Source-kind constants
# ---------------------------------------------------------------------------


class TestSourceKindConstants:
    def test_allow_list_has_three_kinds(self) -> None:
        assert SOURCE_KIND_INTAKE in SOURCE_KIND_ALLOW_LIST
        assert SOURCE_KIND_EXTERNAL in SOURCE_KIND_ALLOW_LIST
        assert SOURCE_KIND_OPERATOR in SOURCE_KIND_ALLOW_LIST
        assert len(SOURCE_KIND_ALLOW_LIST) == 3

    def test_constants_are_strings(self) -> None:
        assert isinstance(SOURCE_KIND_INTAKE, str)
        assert isinstance(SOURCE_KIND_EXTERNAL, str)
        assert isinstance(SOURCE_KIND_OPERATOR, str)


# ---------------------------------------------------------------------------
# 3. IngestionContract defaults
# ---------------------------------------------------------------------------


class TestIngestionContract:
    def test_default_contract_is_frozen(self) -> None:
        c = IngestionContract()
        assert c.min_tag_count == MIN_TAG_COUNT
        assert c.max_tag_count == MAX_TAG_COUNT
        assert c.min_asset_count == MIN_ASSET_COUNT
        assert c.max_asset_count == MAX_ASSET_COUNT
        assert c.require_title_when_knowledge_id is True
        assert c.require_human_review is True

    def test_default_contract_singleton(self) -> None:
        assert DEFAULT_INGESTION_CONTRACT is not None
        assert isinstance(DEFAULT_INGESTION_CONTRACT, IngestionContract)

    def test_invalid_range_min_gt_max_rejected(self) -> None:
        with pytest.raises(IngestionContractError):
            IngestionContract(min_tag_count=10, max_tag_count=2)

    def test_negative_min_rejected(self) -> None:
        with pytest.raises(IngestionContractError):
            IngestionContract(min_tag_count=-1)
        with pytest.raises(IngestionContractError):
            IngestionContract(min_asset_count=-1)

    def test_predicates(self) -> None:
        c = IngestionContract()
        assert c.accepts_source_kind("intake")
        assert not c.accepts_source_kind("alien")
        assert c.tag_count_in_range(0)
        assert c.tag_count_in_range(MAX_TAG_COUNT)
        assert not c.tag_count_in_range(MAX_TAG_COUNT + 1)
        assert c.asset_count_in_range(0)
        assert c.asset_count_in_range(MAX_ASSET_COUNT)
        assert not c.asset_count_in_range(MAX_ASSET_COUNT + 1)

    def test_summary_lists_six_rules(self) -> None:
        c = IngestionContract()
        s = c.summary()
        assert len(s) == 6
        for prefix in ("I1", "I2", "I3", "I4", "I5", "I6"):
            assert any(r.startswith(prefix) for r in s)

    def test_describe_is_json_safe(self) -> None:
        c = IngestionContract()
        d = c.describe()
        json.dumps(d)


# ---------------------------------------------------------------------------
# 4. IngestionValidator -- happy path
# ---------------------------------------------------------------------------


class TestValidatorHappyPath:
    def test_valid_record_passes(self) -> None:
        v = IngestionValidator()
        r = _valid_record()
        res = v.validate(r)
        assert isinstance(res, IngestionValidationResult)
        assert res.valid is True
        assert res.rule_id == "OK"
        assert res.case_id == r.case_id

    def test_default_validator_uses_default_contract(self) -> None:
        v = IngestionValidator()
        assert v.contract is DEFAULT_INGESTION_CONTRACT

    def test_explicit_contract_override(self) -> None:
        c = IngestionContract(require_human_review=False)
        v = IngestionValidator(c)
        assert v.contract is c

    def test_non_caseknowledge_input_rejected(self) -> None:
        v = IngestionValidator()
        res = v.validate({"not": "a CaseKnowledge"})
        assert res.valid is False
        assert res.rule_id == "I0_type"


# ---------------------------------------------------------------------------
# 5. IngestionValidator -- per-rule failures
# ---------------------------------------------------------------------------


class TestValidatorFailures:
    def test_i1_source_kind_rejected(self) -> None:
        # Bypass the constructor guard by mutating after creation:
        # not allowed on frozen dataclass, so we go via __post_init__
        # would raise. Instead, build via CaseKnowledge() directly
        # with a deliberately unknown kind. The constructor guard
        # blocks this so we exercise the contract path instead.
        c = IngestionContract(
            source_kind_allow_list=frozenset({"external"}),
        )
        v = IngestionValidator(c)
        r = _valid_record(source_kind=SOURCE_KIND_INTAKE)
        res = v.validate(r)
        assert res.valid is False
        assert res.rule_id == "I1_source_kind_allow_list"

    def test_i2_non_positive_version_constructor_guard(self) -> None:
        # The constructor itself enforces a positive version
        # (V1 invariant). The validator rule I2 is the runtime
        # defensive check; the contract is the same: a
        # CaseKnowledge with knowledge_version <= 0 cannot be
        # constructed. We therefore assert the constructor guard.
        with pytest.raises(CaseKnowledgeError):
            CaseKnowledge(knowledge_version=0)
        with pytest.raises(CaseKnowledgeError):
            CaseKnowledge(knowledge_version=-1)
        with pytest.raises(CaseKnowledgeError):
            CaseKnowledge(knowledge_version="abc")  # type: ignore[arg-type]
    def test_i3_tag_count_out_of_range(self) -> None:
        too_many = [f"t{i}" for i in range(MAX_TAG_COUNT + 1)]
        r = _valid_record(tags=too_many)
        v = IngestionValidator()
        res = v.validate(r)
        assert res.valid is False
        assert res.rule_id == "I3_tag_count_in_range"

    def test_i4_asset_count_out_of_range(self) -> None:
        too_many = [f"a{i}" for i in range(MAX_ASSET_COUNT + 1)]
        r = _valid_record(linked_assets=too_many)
        v = IngestionValidator()
        res = v.validate(r)
        assert res.valid is False
        assert res.rule_id == "I4_asset_count_in_range"

    def test_i5_title_required_when_knowledge_id_set(self) -> None:
        r = _valid_record(title="", knowledge_id="ko_x_v1")
        v = IngestionValidator()
        res = v.validate(r)
        assert res.valid is False
        assert res.rule_id == "I5_title_required_when_knowledge_id"

    def test_i5_skipped_when_no_knowledge_id(self) -> None:
        r = _valid_record(title="", knowledge_id="")
        v = IngestionValidator()
        res = v.validate(r)
        assert res.valid is True

    def test_i6_human_review_required(self) -> None:
        import dataclasses
        r = _valid_record()
        bad = dataclasses.replace(r, requires_human_review=False)
        v = IngestionValidator()
        res = v.validate(bad)
        assert res.valid is False
        assert res.rule_id == "I6_human_review_required"

    def test_i6_relaxed_via_custom_contract(self) -> None:
        c = IngestionContract(require_human_review=False)
        v = IngestionValidator(c)
        import dataclasses
        r = _valid_record()
        ok = dataclasses.replace(r, requires_human_review=False)
        res = v.validate(ok)
        assert res.valid is True


# ---------------------------------------------------------------------------
# 6. Result immutability
# ---------------------------------------------------------------------------


class TestValidationResult:
    def test_result_is_frozen(self) -> None:
        r = _valid_record()
        res = IngestionValidator().validate(r)
        with pytest.raises(Exception):
            res.valid = False  # type: ignore[misc]

    def test_result_to_dict_is_json_safe(self) -> None:
        r = _valid_record()
        res = IngestionValidator().validate(r)
        json.dumps(res.to_dict())


# ---------------------------------------------------------------------------
# 7. Report
# ---------------------------------------------------------------------------


class TestReport:
    def test_report_with_record_and_result(self) -> None:
        r = _valid_record()
        res = IngestionValidator().validate(r)
        md = generate_report(record=r, result=res)
        assert md.startswith("# ")
        assert "Record" in md
        assert "Contract" in md
        assert "Validator Result" in md
        assert "Safety Boundary" in md
        assert r.case_id in md

    def test_report_without_record(self) -> None:
        md = generate_report()
        assert "No record provided" in md

    def test_report_title_is_customizable(self) -> None:
        md = generate_report(title="Custom Title")
        assert "# Custom Title" in md


# ---------------------------------------------------------------------------
# 8. AST architecture boundary
# ---------------------------------------------------------------------------


class TestArchitectureBoundary:
    FORBIDDEN_SUBSTRINGS = (
        "caseos.intelligence",
        "caseos.knowledge.retrieval",
        "caseos.knowledge.evolution",
        "caseos.knowledge.governance",
        "caseos.knowledge.intake",
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

    @pytest.mark.parametrize(
        "filename",
        ["__init__.py", "object.py", "contract.py",
         "validator.py", "report.py"],
    )
    def test_no_forbidden_imports(self, filename: str) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "ingestion"
            / filename
        )
        source = path.read_text(encoding="utf-8-sig")
        imports = self._collect_imports(source)
        offenders = [
            imp for imp in imports
            if any(f in imp for f in self.FORBIDDEN_SUBSTRINGS)
        ]
        assert offenders == [], (
            "Forbidden architecture boundary import in "
            + filename + ": " + repr(offenders)
        )
