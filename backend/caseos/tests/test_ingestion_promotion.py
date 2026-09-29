"""Tests for the Promotion Eligibility Contract V1 (Sprint 25.2-A).
        )
            + filename + ": " + repr(offenders)
    def test_p5_non_positive_version_constructor_guard(self) -> None:
        # The constructor guards against non-positive
        # proposed_version; the validator rule P5 is the
        # runtime defensive check.
        with pytest.raises(PromotionCandidateError):
            PromotionCandidate(case_id="CK-x", proposed_version=0)
        with pytest.raises(PromotionCandidateError):
            PromotionCandidate(case_id="CK-x", proposed_version=-1)
    * The checker never mutates the input candidate.
    * Report generator emits a Markdown string with every
      required section.
    * AST architecture boundary -- the package does NOT
      import from any forbidden module (including the
      KnowledgeObject schema and Intake).

Architecture boundary (Sprint 25.2-A spec):

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

from caseos.knowledge.ingestion.promotion import (  # noqa: E402
    DEFAULT_PROVENANCE_STEPS,
    DRAFT,
    ELIGIBLE,
    NOT_ELIGIBLE,
    PROMOTION_STATUS_ALLOW_LIST,
    ProvenanceRecord,
    PromotionCandidate,
    PromotionCandidateError,
    PromotionEligibilityChecker,
    PromotionPolicy,
    PromotionPolicyError,
    PromotionStatus,
    PromotionStatusError,
    STEP_CASE_KNOWLEDGE_VALIDATION,
    STEP_INTAKE,
    new_promotion_candidate,
)
from caseos.knowledge.ingestion.promotion.eligibility import (  # noqa: E402
    EligibilityResult,
)
from caseos.knowledge.ingestion.promotion.policy import (  # noqa: E402
    DEFAULT_PROMOTION_POLICY,
    HUMAN_REVIEW_MARKER,
)
from caseos.knowledge.ingestion.promotion.report import (  # noqa: E402
    generate_promotion_report,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _provenance(*steps, actor: str = "fixture") -> tuple:
    return tuple(
        ProvenanceRecord(step=s, actor=actor) for s in steps
    )


def _candidate(**overrides) -> PromotionCandidate:
    chain = _provenance(
        STEP_INTAKE, STEP_CASE_KNOWLEDGE_VALIDATION
    )
    base = dict(
        case_id="CK-abc",
        case_source_kind="intake",
        provenance_chain=chain,
        justification="baseline justification human_review ok",
        proposed_knowledge_id="ko_forest_v1",
        proposed_version=1,
        created_by="fixture",
    )
    base.update(overrides)
    return new_promotion_candidate(**base)


# ---------------------------------------------------------------------------
# 1. Status enum + constants
# ---------------------------------------------------------------------------


class TestPromotionStatus:
    def test_three_values_present(self) -> None:
        assert DRAFT == "DRAFT"
        assert ELIGIBLE == "ELIGIBLE"
        assert NOT_ELIGIBLE == "NOT_ELIGIBLE"
        assert PROMOTION_STATUS_ALLOW_LIST == frozenset(
            {"DRAFT", "ELIGIBLE", "NOT_ELIGIBLE"}
        )

    def test_enum_members(self) -> None:
        assert isinstance(PromotionStatus.DRAFT, PromotionStatus)
        assert PromotionStatus.ELIGIBLE.value == "ELIGIBLE"
        assert PromotionStatus.NOT_ELIGIBLE.value == "NOT_ELIGIBLE"

    def test_unknown_status_string_rejected(self) -> None:
        # _coerce_status is private; exercise it indirectly
        # via the candidate constructor guard.
        with pytest.raises(PromotionStatusError):
            PromotionCandidate(
                case_id="CK-x",
                status="FLYING",
            )


# ---------------------------------------------------------------------------
# 2. ProvenanceRecord
# ---------------------------------------------------------------------------


class TestProvenanceRecord:
    def test_basic_construction(self) -> None:
        r = ProvenanceRecord(step="intake", actor="operator1")
        assert r.step == "intake"
        assert r.actor == "operator1"
        assert r.timestamp  # auto
        assert r.reference == ""
        assert r.notes == ""

    def test_frozen(self) -> None:
        r = ProvenanceRecord(step="intake", actor="x")
        with pytest.raises(Exception):
            r.step = "other"  # type: ignore[misc]

    def test_empty_step_rejected(self) -> None:
        with pytest.raises(PromotionCandidateError):
            ProvenanceRecord(step="", actor="x")

    def test_round_trip_dict(self) -> None:
        r = ProvenanceRecord(
            step="intake", actor="x",
            reference="ref1", notes="hello",
        )
        d = r.to_dict()
        json.dumps(d)
        r2 = ProvenanceRecord.from_dict(d)
        assert r2 == r

    def test_from_dict_rejects_non_dict(self) -> None:
        with pytest.raises(PromotionCandidateError):
            ProvenanceRecord.from_dict("not a dict")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# 3. PromotionCandidate
# ---------------------------------------------------------------------------


class TestPromotionCandidate:
    def test_basic_construction(self) -> None:
        c = _candidate()
        assert isinstance(c, PromotionCandidate)
        assert c.case_id == "CK-abc"
        assert c.case_source_kind == "intake"
        assert c.proposed_version == 1
        assert c.status == DRAFT

    def test_frozen(self) -> None:
        c = _candidate()
        with pytest.raises(Exception):
            c.case_id = "other"  # type: ignore[misc]

    def test_empty_case_id_rejected(self) -> None:
        with pytest.raises(PromotionCandidateError):
            PromotionCandidate(case_id="")

    def test_provenance_chain_deep_copied(self) -> None:
        chain = list(_provenance(STEP_INTAKE))
        c = new_promotion_candidate(case_id="CK-x", provenance_chain=chain)
        chain.append(ProvenanceRecord(step="evil", actor="attacker"))
        # The candidate must be untouched.
        assert all(r.step != "evil" for r in c.provenance_chain)
        assert c.provenance_chain == _provenance(STEP_INTAKE)

    def test_to_dict_round_trip(self) -> None:
        c = _candidate()
        d = c.to_dict()
        json.dumps(d)
        c2 = PromotionCandidate.from_dict(d)
        assert c2 == c

    def test_new_promotion_candidate_validates_id(self) -> None:
        with pytest.raises(PromotionCandidateError):
            new_promotion_candidate(case_id="")


# ---------------------------------------------------------------------------
# 4. PromotionPolicy defaults
# ---------------------------------------------------------------------------


class TestPromotionPolicy:
    def test_default_policy_is_frozen(self) -> None:
        p = PromotionPolicy()
        assert p.min_provenance_steps == 2
        assert p.required_provenance_steps == DEFAULT_PROVENANCE_STEPS
        assert p.require_justification is True
        assert p.require_proposed_knowledge_id is False
        assert p.require_human_review is True
        assert p.human_review_marker == HUMAN_REVIEW_MARKER

    def test_default_singleton(self) -> None:
        assert DEFAULT_PROMOTION_POLICY is not None

    def test_summary_has_eight_rules(self) -> None:
        p = PromotionPolicy()
        s = p.summary()
        assert len(s) == 8
        for prefix in ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"):
            assert any(r.startswith(prefix) for r in s)

    def test_negative_min_steps_rejected(self) -> None:
        with pytest.raises(PromotionPolicyError):
            PromotionPolicy(min_provenance_steps=-1)

    def test_required_steps_iterable_accepted(self) -> None:
        p = PromotionPolicy(required_provenance_steps=["intake"])
        assert p.required_provenance_steps == ("intake",)

    def test_describe_is_json_safe(self) -> None:
        p = PromotionPolicy()
        json.dumps(p.describe())

    def test_accepts_source_kind(self) -> None:
        p = PromotionPolicy()
        assert p.accepts_source_kind("intake")
        assert not p.accepts_source_kind("alien")


# ---------------------------------------------------------------------------
# 5. Eligibility -- happy path
# ---------------------------------------------------------------------------


class TestEligibilityHappyPath:
    def test_valid_candidate_passes(self) -> None:
        c = _candidate()
        checker = PromotionEligibilityChecker()
        result, updated = checker.check(c)
        assert isinstance(result, EligibilityResult)
        assert result.valid is True
        assert result.rule_id == "OK"
        assert updated.status == ELIGIBLE
        assert updated.failure_reason == ""

    def test_input_candidate_never_mutated(self) -> None:
        c = _candidate()
        before_status = c.status
        before_reason = c.failure_reason
        PromotionEligibilityChecker().check(c)
        assert c.status == before_status
        assert c.failure_reason == before_reason

    def test_non_promotioncandidate_rejected(self) -> None:
        result, _ = PromotionEligibilityChecker().check({"not": "a candidate"})
        assert result.valid is False
        assert result.rule_id == "P0_type"

    def test_default_uses_default_policy(self) -> None:
        checker = PromotionEligibilityChecker()
        assert checker.policy is DEFAULT_PROMOTION_POLICY

    def test_custom_policy_override(self) -> None:
        checker = PromotionEligibilityChecker(
            PromotionPolicy(require_human_review=False)
        )
        c = _candidate(justification="plain justification")
        result, updated = checker.check(c)
        assert result.valid is True
        assert updated.status == ELIGIBLE


# ---------------------------------------------------------------------------
# 6. Eligibility -- per-rule failures
# ---------------------------------------------------------------------------


class TestEligibilityFailures:
    def test_p1_empty_case_id_constructor_guard(self) -> None:
        # The constructor guards against an empty case_id; the
        # validator rule P1 is the runtime defensive check.
        # We therefore assert the constructor guard.
        with pytest.raises(PromotionCandidateError):
            PromotionCandidate(case_id="")

    def test_p2_source_kind_rejected(self) -> None:
        c = _candidate(case_source_kind="alien")
        result, updated = PromotionEligibilityChecker().check(c)
        assert result.valid is False
        assert result.rule_id == "P2_source_kind_allowed"
        assert updated.status == NOT_ELIGIBLE

    def test_p3_too_few_provenance_steps(self) -> None:
        c = _candidate(provenance_chain=_provenance(STEP_INTAKE))
        result, _ = PromotionEligibilityChecker().check(c)
        assert result.valid is False
        assert result.rule_id == "P3_min_provenance_steps"

    def test_p4_missing_required_step(self) -> None:
        # Two steps present (clears P3) but the required
        # `case_knowledge_validation` step is missing, so
        # P4 fires.
        c = _candidate(
            provenance_chain=_provenance(STEP_INTAKE, "extra_step"),
        )
        result, updated = PromotionEligibilityChecker().check(c)
        assert result.valid is False
        assert result.rule_id == "P4_required_provenance_steps"
        assert STEP_CASE_KNOWLEDGE_VALIDATION in result.missing_steps
        assert updated.status == NOT_ELIGIBLE

    def test_p5_non_positive_version_constructor_guard(self) -> None:
        # The constructor guards against non-positive
        # proposed_version; the validator rule P5 is the
        # runtime defensive check.
        with pytest.raises(PromotionCandidateError):
            PromotionCandidate(case_id="CK-x", proposed_version=0)
        with pytest.raises(PromotionCandidateError):
            PromotionCandidate(case_id="CK-x", proposed_version=-1)

    def test_p6_justification_required_and_empty(self) -> None:
        c = _candidate(justification="")
        result, _ = PromotionEligibilityChecker().check(c)
        assert result.valid is False
        assert result.rule_id == "P6_justification_required"

    def test_p7_proposed_id_required(self) -> None:
        c = _candidate(proposed_knowledge_id="")
        checker = PromotionEligibilityChecker(
            PromotionPolicy(require_proposed_knowledge_id=True)
        )
        result, _ = checker.check(c)
        assert result.valid is False
        assert result.rule_id == "P7_proposed_knowledge_id_required"

    def test_p8_human_review_marker_required(self) -> None:
        c = _candidate(justification="no marker here")
        result, _ = PromotionEligibilityChecker().check(c)
        assert result.valid is False
        assert result.rule_id == "P8_human_review_marker_required"

    def test_p8_relaxed_via_custom_policy(self) -> None:
        c = _candidate(justification="no marker here")
        checker = PromotionEligibilityChecker(
            PromotionPolicy(require_human_review=False)
        )
        result, updated = checker.check(c)
        assert result.valid is True
        assert updated.status == ELIGIBLE

class TestStatusStamping:
    def test_eligible_status_applied(self) -> None:
        c = _candidate()
        _, updated = PromotionEligibilityChecker().check(c)
        assert updated.status == ELIGIBLE
        assert updated.failure_reason == ""

    def test_not_eligible_status_applied(self) -> None:
        c = _candidate(case_source_kind="alien")
        _, updated = PromotionEligibilityChecker().check(c)
        assert updated.status == NOT_ELIGIBLE
        assert updated.failure_reason != ""


# ---------------------------------------------------------------------------
# 8. EligibilityResult
# ---------------------------------------------------------------------------


class TestEligibilityResult:
    def test_result_is_frozen(self) -> None:
        c = _candidate()
        result, _ = PromotionEligibilityChecker().check(c)
        with pytest.raises(Exception):
            result.valid = False  # type: ignore[misc]

    def test_result_to_dict_is_json_safe(self) -> None:
        c = _candidate()
        result, _ = PromotionEligibilityChecker().check(c)
        json.dumps(result.to_dict())


# ---------------------------------------------------------------------------
# 9. Report
# ---------------------------------------------------------------------------


class TestReport:
    def test_full_report(self) -> None:
        c = _candidate()
        result, updated = PromotionEligibilityChecker().check(c)
        md = generate_promotion_report(
            candidate=updated, result=result,
        )
        assert md.startswith("# ")
        for sec in ("Candidate", "Provenance Chain", "Policy",
                    "Eligibility Result", "Safety Boundary"):
            assert sec in md

    def test_report_without_candidate(self) -> None:
        md = generate_promotion_report()
        assert "No candidate" in md

    def test_report_title_customizable(self) -> None:
        md = generate_promotion_report(title="Custom Title")
        assert "# Custom Title" in md


# ---------------------------------------------------------------------------
# 10. AST architecture boundary
# ---------------------------------------------------------------------------


class TestArchitectureBoundary:
    FORBIDDEN_SUBSTRINGS = (
        "caseos.intelligence",
        "caseos.knowledge.retrieval",
        "caseos.knowledge.evolution",
        "caseos.knowledge.governance",
        "caseos.knowledge.intake",
        "caseos.knowledge.corpus",
        "caseos.knowledge.object",  # KnowledgeObject schema
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
         "eligibility.py", "report.py"],
    )
    def test_no_forbidden_imports(self, filename: str) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "ingestion"
            / "promotion"
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