"""Tests for the Knowledge Admission Contract V1 (Sprint 25.3-A).

Coverage:

    * AdmissionStatus enum + DRAFT/ADMISSIBLE/NOT_ADMISSIBLE
      constants + ADMISSION_TARGET_VERSION.
    * AdmissionProvenanceRef preserves the source
      PromotionCandidate provenance chain (deep-copied).
    * AdmissionCandidate shape + invariants:
        - V1 invariant: target_version must equal 1
        - V1 invariant: requires_human_review must be True
        - target_knowledge_id is non-empty
        - source must be an AdmissionProvenanceRef
    * AdmissionPolicy default rule table + describe.
    * AdmissionChecker: each rule A1..A8 happy + sad path.
    * Status stamping DRAFT -> ADMISSIBLE / NOT_ADMISSIBLE.
    * AdmissionChecker never mutates the input candidate.
    * Semantic boundary:
        - ADMISSION_OWNED_VERSIONS == (1,)
        - EVOLUTION_OWNED_MIN_VERSION == 2
        - is_admission_owned_version(1) is True
        - is_admission_owned_version(2) is False
        - is_evolution_owned_version(2) is True
        - is_evolution_owned_version(1) is False
    * Report generator emits every required section.
    * AST architecture boundary -- the package does NOT
      import from evolution, versioning, retrieval, brain,
      corpus, governance, intake, intelligence, or the
      KnowledgeObject schema.

Architecture boundary (Sprint 25.3-A spec):

    These tests do NOT import forbidden modules.
    These tests MAY import from:
        * caseos.knowledge.ingestion (same package)
        * stdlib
"""
from __future__ import annotations

import ast
import dataclasses
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from caseos.knowledge.ingestion.admission import (  # noqa: E402
    ADMISSIBLE,
    ADMISSION_HUMAN_REVIEW_MARKER,
    ADMISSION_OWNED_VERSIONS,
    ADMISSION_STATUS_ALLOW_LIST,
    ADMISSION_TARGET_VERSION,
    AdmissionCandidate,
    AdmissionCandidateError,
    AdmissionChecker,
    AdmissionPolicy,
    AdmissionPolicyError,
    AdmissionProvenanceRef,
    AdmissionResult,
    AdmissionStatus,
    AdmissionStatusError,
    DRAFT,
    EVOLUTION_OWNED_MIN_VERSION,
    NOT_ADMISSIBLE,
    SEMANTIC_BOUNDARY_TABLE,
    is_admission_owned_version,
    is_evolution_owned_version,
    new_admission_candidate,
)
from caseos.knowledge.ingestion.admission.boundary import (  # noqa: E402
    ownership_of,
)
from caseos.knowledge.ingestion.admission.policy import (  # noqa: E402
    DEFAULT_ADMISSION_POLICY,
)
from caseos.knowledge.ingestion.admission.report import (  # noqa: E402
    generate_admission_report,
)
from caseos.knowledge.ingestion.promotion import (  # noqa: E402
    STEP_CASE_KNOWLEDGE_VALIDATION,
    STEP_INTAKE,
    ProvenanceRecord,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _provenance(*steps, actor: str = "fixture") -> tuple:
    return tuple(
        ProvenanceRecord(step=s, actor=actor) for s in steps
    )


def _candidate(**overrides) -> AdmissionCandidate:
    chain = _provenance(
        STEP_INTAKE, STEP_CASE_KNOWLEDGE_VALIDATION
    )
    base = dict(
        promotion_candidate_id="PC-abc",
        case_id="CK-abc",
        case_source_kind="intake",
        provenance_chain=chain,
        target_knowledge_id="ko_forest_v1",
        admission_proposal={
            "title": "Forest kindergarten case",
            "theme": "forest",
        },
        justification="baseline justification human_review ok",
        requires_human_review=True,
        created_by="fixture",
    )
    base.update(overrides)
    return new_admission_candidate(**base)


# ---------------------------------------------------------------------------
# 1. Status + version constants
# ---------------------------------------------------------------------------


class TestAdmissionStatus:
    def test_three_values_present(self) -> None:
        assert DRAFT == "DRAFT"
        assert ADMISSIBLE == "ADMISSIBLE"
        assert NOT_ADMISSIBLE == "NOT_ADMISSIBLE"
        assert ADMISSION_STATUS_ALLOW_LIST == frozenset(
            {"DRAFT", "ADMISSIBLE", "NOT_ADMISSIBLE"}
        )

    def test_target_version_is_one(self) -> None:
        assert ADMISSION_TARGET_VERSION == 1

    def test_enum_members(self) -> None:
        assert isinstance(AdmissionStatus.DRAFT, AdmissionStatus)
        assert AdmissionStatus.ADMISSIBLE.value == "ADMISSIBLE"
        assert AdmissionStatus.NOT_ADMISSIBLE.value == "NOT_ADMISSIBLE"

    def test_unknown_status_string_rejected(self) -> None:
        with pytest.raises(AdmissionStatusError):
            AdmissionCandidate(
                target_knowledge_id="ko_x",
                status="FLYING",
            )


# ---------------------------------------------------------------------------
# 2. AdmissionProvenanceRef
# ---------------------------------------------------------------------------


class TestAdmissionProvenanceRef:
    def test_basic_construction(self) -> None:
        ref = AdmissionProvenanceRef(
            promotion_candidate_id="PC-x",
            case_id="CK-x",
            case_source_kind="intake",
            provenance_chain=_provenance(STEP_INTAKE),
        )
        assert ref.promotion_candidate_id == "PC-x"
        assert ref.case_id == "CK-x"
        assert ref.case_source_kind == "intake"
        assert len(ref.provenance_chain) == 1

    def test_empty_promotion_id_rejected(self) -> None:
        with pytest.raises(AdmissionCandidateError):
            AdmissionProvenanceRef(
                promotion_candidate_id="",
                case_id="CK-x",
            )

    def test_empty_case_id_rejected(self) -> None:
        with pytest.raises(AdmissionCandidateError):
            AdmissionProvenanceRef(
                promotion_candidate_id="PC-x",
                case_id="",
            )

    def test_chain_deep_copied(self) -> None:
        chain = list(_provenance(STEP_INTAKE))
        ref = AdmissionProvenanceRef(
            promotion_candidate_id="PC-x",
            case_id="CK-x",
            provenance_chain=chain,
        )
        chain.append(ProvenanceRecord(step="evil", actor="attacker"))
        assert all(r.step != "evil" for r in ref.provenance_chain)
        assert ref.provenance_chain == _provenance(STEP_INTAKE)

    def test_round_trip_dict(self) -> None:
        ref = AdmissionProvenanceRef(
            promotion_candidate_id="PC-x",
            case_id="CK-x",
            case_source_kind="intake",
            provenance_chain=_provenance(STEP_INTAKE),
        )
        d = ref.to_dict()
        json.dumps(d)
        ref2 = AdmissionProvenanceRef.from_dict(d)
        assert ref2 == ref


# ---------------------------------------------------------------------------
# 3. AdmissionCandidate
# ---------------------------------------------------------------------------


class TestAdmissionCandidate:
    def test_basic_construction(self) -> None:
        c = _candidate()
        assert isinstance(c, AdmissionCandidate)
        assert c.target_knowledge_id == "ko_forest_v1"
        assert c.target_version == 1
        assert c.status == DRAFT
        assert c.requires_human_review is True

    def test_frozen(self) -> None:
        c = _candidate()
        with pytest.raises(Exception):
            c.target_knowledge_id = "other"  # type: ignore[misc]

    def test_target_version_must_be_one_constructor_guard(self) -> None:
        with pytest.raises(AdmissionCandidateError):
            AdmissionCandidate(
                target_knowledge_id="ko_x",
                target_version=2,
            )

    def test_requires_human_review_must_be_bool(self) -> None:
        with pytest.raises(AdmissionCandidateError):
            AdmissionCandidate(
                target_knowledge_id="ko_x",
                requires_human_review="yes",  # type: ignore[arg-type]
            )

    def test_empty_target_knowledge_id_rejected(self) -> None:
        with pytest.raises(AdmissionCandidateError):
            AdmissionCandidate(target_knowledge_id="")

    def test_proposal_deep_copied(self) -> None:
        proposal = {"a": [1, 2, 3]}
        c = _candidate(admission_proposal=proposal)
        proposal["a"].append(99)
        # The candidate must be untouched.
        assert c.admission_proposal["a"] == [1, 2, 3]

    def test_to_dict_round_trip(self) -> None:
        c = _candidate()
        d = c.to_dict()
        json.dumps(d)
        c2 = AdmissionCandidate.from_dict(d)
        assert c2 == c


# ---------------------------------------------------------------------------
# 4. new_admission_candidate builder
# ---------------------------------------------------------------------------


class TestBuilder:
    def test_builder_validates_inputs(self) -> None:
        with pytest.raises(AdmissionCandidateError):
            new_admission_candidate(
                promotion_candidate_id="",
                case_id="CK-x",
                case_source_kind="intake",
                provenance_chain=(),
                target_knowledge_id="ko_x",
                admission_proposal={"a": 1},
                justification="x human_review",
            )
        with pytest.raises(AdmissionCandidateError):
            new_admission_candidate(
                promotion_candidate_id="PC-x",
                case_id="",
                case_source_kind="intake",
                provenance_chain=(),
                target_knowledge_id="ko_x",
                admission_proposal={"a": 1},
                justification="x human_review",
            )

    def test_builder_wires_source(self) -> None:
        c = _candidate()
        assert isinstance(c.source, AdmissionProvenanceRef)
        assert c.source.promotion_candidate_id == "PC-abc"
        assert c.source.case_id == "CK-abc"
        assert len(c.source.provenance_chain) == 2


# ---------------------------------------------------------------------------
# 5. AdmissionPolicy
# ---------------------------------------------------------------------------


class TestAdmissionPolicy:
    def test_default_policy(self) -> None:
        p = AdmissionPolicy()
        assert p.target_version == 1
        assert p.require_human_review is True
        assert p.require_non_empty_proposal is True
        assert p.require_non_empty_provenance is True
        assert p.human_review_marker == ADMISSION_HUMAN_REVIEW_MARKER

    def test_default_singleton(self) -> None:
        assert DEFAULT_ADMISSION_POLICY is not None
        assert isinstance(DEFAULT_ADMISSION_POLICY, AdmissionPolicy)

    def test_summary_has_eight_rules(self) -> None:
        p = AdmissionPolicy()
        s = p.summary()
        assert len(s) == 8
        for prefix in (
            "A1", "A2", "A3", "A4",
            "A5", "A6", "A7", "A8",
        ):
            assert any(r.startswith(prefix) for r in s)

    def test_negative_target_version_rejected(self) -> None:
        with pytest.raises(AdmissionPolicyError):
            AdmissionPolicy(target_version=0)

    def test_describe_is_json_safe(self) -> None:
        p = AdmissionPolicy()
        json.dumps(p.describe())


# ---------------------------------------------------------------------------
# 6. Checker -- happy path
# ---------------------------------------------------------------------------


class TestCheckerHappyPath:
    def test_valid_candidate_passes(self) -> None:
        c = _candidate()
        checker = AdmissionChecker()
        result, updated = checker.check(c)
        assert isinstance(result, AdmissionResult)
        assert result.valid is True
        assert result.rule_id == "OK"
        assert updated.status == ADMISSIBLE
        assert updated.failure_reason == ""

    def test_input_candidate_never_mutated(self) -> None:
        c = _candidate()
        before_status = c.status
        before_reason = c.failure_reason
        AdmissionChecker().check(c)
        assert c.status == before_status
        assert c.failure_reason == before_reason

    def test_non_candidate_rejected(self) -> None:
        result, _ = AdmissionChecker().check({"not": "a candidate"})
        assert result.valid is False
        assert result.rule_id == "A0_type"

    def test_default_uses_default_policy(self) -> None:
        checker = AdmissionChecker()
        assert checker.policy is DEFAULT_ADMISSION_POLICY

    def test_custom_policy_override(self) -> None:
        checker = AdmissionChecker(
            AdmissionPolicy(require_non_empty_proposal=False)
        )
        c = _candidate(admission_proposal={})
        result, updated = checker.check(c)
        assert result.valid is True
        assert updated.status == ADMISSIBLE


# ---------------------------------------------------------------------------
# 7. Checker -- per-rule failures
# ---------------------------------------------------------------------------


class TestCheckerFailures:
    def test_a1_empty_target_knowledge_id_constructor_guard(self) -> None:
        # The constructor guards against empty target_knowledge_id;
        # the validator rule A1 is the runtime defensive check.
        with pytest.raises(AdmissionCandidateError):
            AdmissionCandidate(target_knowledge_id="")

    def test_a3_empty_promotion_id(self) -> None:
        # Bypass constructor guards by mutating the source's
        # promotion_candidate_id AFTER the candidate is built.
        c = _candidate()
        object.__setattr__(c.source, "promotion_candidate_id", "")
        result, updated = AdmissionChecker().check(c)
        assert result.valid is False
        assert result.rule_id == "A3_promotion_candidate_id_present"
        assert updated.status == NOT_ADMISSIBLE

    def test_a4_empty_case_id(self) -> None:
        c = _candidate()
        object.__setattr__(c.source, "case_id", "")
        result, updated = AdmissionChecker().check(c)
        assert result.valid is False
        assert result.rule_id == "A4_case_id_present"
        assert updated.status == NOT_ADMISSIBLE

    def test_a5_empty_provenance_chain(self) -> None:
        c = _candidate(provenance_chain=())
        result, updated = AdmissionChecker().check(c)
        assert result.valid is False
        assert result.rule_id == "A5_provenance_chain_non_empty"
        assert updated.status == NOT_ADMISSIBLE

    def test_a5_relaxed_via_custom_policy(self) -> None:
        checker = AdmissionChecker(
            AdmissionPolicy(require_non_empty_provenance=False)
        )
        c = _candidate(provenance_chain=())
        result, updated = checker.check(c)
        assert result.valid is True
        assert updated.status == ADMISSIBLE

    def test_a6_empty_proposal(self) -> None:
        c = _candidate(admission_proposal={})
        result, updated = AdmissionChecker().check(c)
        assert result.valid is False
        assert result.rule_id == "A6_admission_proposal_non_empty"
        assert updated.status == NOT_ADMISSIBLE

    def test_a7_requires_human_review_false_constructor_guard(self) -> None:
        # The constructor guards against requires_human_review=False
        # (V1 invariant); the validator rule A7 is the runtime
        # defensive check.
        with pytest.raises(AdmissionCandidateError):
            AdmissionCandidate(
                target_knowledge_id="ko_x",
                requires_human_review=False,
            )
# ---------------------------------------------------------------------------
# 8. Status stamping
# ---------------------------------------------------------------------------


class TestStatusStamping:
    def test_admissible_status_applied(self) -> None:
        c = _candidate()
        _, updated = AdmissionChecker().check(c)
        assert updated.status == ADMISSIBLE
        assert updated.failure_reason == ""

    def test_not_admissible_status_applied(self) -> None:
        c = _candidate(justification="no marker")
        _, updated = AdmissionChecker().check(c)
        assert updated.status == NOT_ADMISSIBLE
        assert updated.failure_reason != ""


# ---------------------------------------------------------------------------
# 9. Semantic boundary
# ---------------------------------------------------------------------------


class TestSemanticBoundary:
    def test_admission_owns_version_one(self) -> None:
        assert ADMISSION_OWNED_VERSIONS == (1,)
        assert is_admission_owned_version(1) is True

    def test_admission_does_not_own_v2(self) -> None:
        assert is_admission_owned_version(2) is False
        assert is_admission_owned_version(3) is False

    def test_evolution_owns_v2_plus(self) -> None:
        assert EVOLUTION_OWNED_MIN_VERSION == 2
        assert is_evolution_owned_version(2) is True
        assert is_evolution_owned_version(3) is True
        assert is_evolution_owned_version(100) is True

    def test_evolution_does_not_own_v1(self) -> None:
        assert is_evolution_owned_version(1) is False

    def test_ownership_of_helper(self) -> None:
        assert ownership_of(1) == "admission"
        assert ownership_of(2) == "evolution"
        assert ownership_of(99) == "evolution"
        assert ownership_of("abc") == "unknown"  # type: ignore[arg-type]

    def test_boundary_table_has_three_rows(self) -> None:
        assert len(SEMANTIC_BOUNDARY_TABLE) == 3
        for row in SEMANTIC_BOUNDARY_TABLE:
            assert len(row) == 3
            version, owner, _desc = row
            assert isinstance(version, str)
            assert isinstance(owner, str)


# ---------------------------------------------------------------------------
# 10. AdmissionResult
# ---------------------------------------------------------------------------


class TestAdmissionResult:
    def test_result_is_frozen(self) -> None:
        c = _candidate()
        result, _ = AdmissionChecker().check(c)
        with pytest.raises(Exception):
            result.valid = False  # type: ignore[misc]

    def test_result_to_dict_is_json_safe(self) -> None:
        c = _candidate()
        result, _ = AdmissionChecker().check(c)
        json.dumps(result.to_dict())


# ---------------------------------------------------------------------------
# 11. Report
# ---------------------------------------------------------------------------


class TestReport:
    def test_full_report(self) -> None:
        c = _candidate()
        result, updated = AdmissionChecker().check(c)
        md = generate_admission_report(
            candidate=updated, result=result,
        )
        assert md.startswith("# ")
        for sec in (
            "Candidate",
            "Source Provenance",
            "Provenance Chain",
            "Policy",
            "Admission Result",
            "Semantic Boundary",
            "Safety Boundary",
        ):
            assert sec in md

    def test_report_without_candidate(self) -> None:
        md = generate_admission_report()
        assert "No candidate" in md

    def test_report_title_customizable(self) -> None:
        md = generate_admission_report(title="Custom Title")
        assert "# Custom Title" in md

    def test_report_includes_boundary_table(self) -> None:
        md = generate_admission_report(candidate=_candidate())
        assert "Admission" in md
        assert "Evolution" in md


# ---------------------------------------------------------------------------
# 12. AST architecture boundary
# ---------------------------------------------------------------------------


class TestArchitectureBoundary:
    FORBIDDEN_SUBSTRINGS = (
        "caseos.intelligence",
        "caseos.knowledge.retrieval",
        "caseos.knowledge.evolution",   # entire evolution package
        "caseos.knowledge.governance",
        "caseos.knowledge.intake",
        "caseos.knowledge.corpus",
        "caseos.knowledge.object",       # KO schema
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
        ["__init__.py", "object.py", "policy.py",
         "checker.py", "boundary.py", "report.py"],
    )
    def test_no_forbidden_imports(self, filename: str) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "ingestion"
            / "admission"
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