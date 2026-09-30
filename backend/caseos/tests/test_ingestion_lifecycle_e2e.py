"""Case Knowledge Lifecycle E2E Integration V1 (Sprint 25.4-B).

This test file wires the existing V1 layers into a single
executable end-to-end chain and verifies every gate, every
guard, and the final retrieval visibility:

    RawCaseObject (Intake)
        |
        v
    IntakeAdapter.adapt()
        |
        v
    CaseKnowledge
        |
        v
    IngestionValidator.validate()
        |
        v
    (_glue_) PromotionCandidate  (DRAFT)
        |
        v
    PromotionEligibilityChecker.check()
        |
        v
    PromotionCandidate (ELIGIBLE)
        |
        v
    (_glue_) AdmissionCandidate  (DRAFT)
        |
        v
    AdmissionChecker.check()
        |
        v
    AdmissionCandidate (ADMISSIBLE)
        |
        v
    AdmissionWriter.write()
        |
        v
    KnowledgeObject v1
        + KnowledgeVersion baseline (VersionStore)
        + EvolutionAuditRecord (audit_store)
        |
    RetrievalPipeline.execute(query, [KO])
        |
        v
    RetrievalResult.total_hits >= 1

Scope discipline (Sprint 25.4-B spec)
-------------------------------------

    * Two ``_glue_`` arrows above are implemented as TEST-ONLY
      helper functions inside this file. No production glue
      module is added.
    * The legacy ``IntakeManager.promote()`` path
      (``governance_promote``) is intentionally NOT exercised;
      this sprint covers only the new V1 chain.
    * No existing production module is modified.

Architecture boundary (this test file)
--------------------------------------

    This file may import from:
        * caseos.knowledge.intake.object         (RawCaseObject / new_raw_case)
        * caseos.knowledge.ingestion             (CaseKnowledge / IngestionValidator)
        * caseos.knowledge.ingestion.adapters    (IntakeAdapter)
        * caseos.knowledge.ingestion.promotion   (PromotionCandidate + Checker)
        * caseos.knowledge.ingestion.admission   (AdmissionCandidate + Checker + Writer)
        * caseos.knowledge.evolution.audit       (EvolutionAuditStore)
        * caseos.knowledge.evolution.versioning  (VersionStore)
        * caseos.knowledge.object                (KnowledgeObject)
        * caseos.knowledge.retrieval.pipeline    (RetrievalPipeline)
        * caseos.knowledge.retrieval.object      (RetrievalQuery)
        * stdlib / pytest

    This file MUST NOT import from:
        * caseos.intelligence.*
        * caseos.brain.*
        * caseos.knowledge.governance
        * caseos.knowledge.feedback
        * caseos.knowledge.corpus
"""
from __future__ import annotations

import ast
import copy
import dataclasses
import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from caseos.knowledge.evolution.audit import EvolutionAuditStore  # noqa: E402
from caseos.knowledge.evolution.versioning import (  # noqa: E402
    KnowledgeVersion,
    VersionStore,
)

from caseos.knowledge.ingestion import (  # noqa: E402
    CaseKnowledge,
    IngestionValidator,
    new_case_knowledge,
)
from caseos.knowledge.ingestion.adapters import IntakeAdapter  # noqa: E402

from caseos.knowledge.ingestion.admission import (  # noqa: E402
    ADMISSIBLE,
    ADMISSION_TARGET_VERSION,
    CREATED,
    IDEMPOTENT,
    NOT_ADMISSIBLE,
    REJECTED,
    AdmissionCandidate,
    AdmissionChecker,
    AdmissionWriteResult,
    AdmissionWriter,
    DuplicateAdmissionError,
    new_admission_candidate,
)

from caseos.knowledge.ingestion.promotion import (  # noqa: E402
    ELIGIBLE,
    NOT_ELIGIBLE,
    ProvenanceRecord,
    PromotionCandidate,
    PromotionEligibilityChecker,
    STEP_CASE_KNOWLEDGE_VALIDATION,
    STEP_INTAKE,
    new_promotion_candidate,
)

from caseos.knowledge.intake.object import (  # noqa: E402
    RawCaseObject,
    new_raw_case,
)

from caseos.knowledge.object import KnowledgeObject  # noqa: E402
from caseos.knowledge.retrieval.object import RetrievalQuery  # noqa: E402
from caseos.knowledge.retrieval.pipeline import RetrievalPipeline  # noqa: E402


# ---------------------------------------------------------------------------
# E2E glue (test-only)
# ---------------------------------------------------------------------------
#
# Per Sprint 25.4-B spec, the two missing adapters
# (CaseKnowledge -> PromotionCandidate and
#  PromotionCandidate -> AdmissionCandidate) live ONLY in this
# test file. They are NOT production code.
#
# These helpers:
#   * never mutate the input
#   * use V1 contract defaults from each module
#   * inject the minimum required fields, letting the
#     downstream checkers enforce the rest


def _build_raw_case(**overrides):
    """Build a baseline RawCaseObject for the E2E flow."""
    base = dict(
        source="intake_e2e",
        title="Forest kindergarten case",
        description="Baseline kindergarten case from operator intake.",
        files=("assets/forest-1.png", "assets/forest-2.png"),
        notes="E2E fixture",
        candidate_tags=("kindergarten", "outdoor"),
        source_reference="Sprint 25.4-B fixture",
        candidate_identity_type="GoldenCase",
    )
    base.update(overrides)
    return new_raw_case(**base)


def _build_case_knowledge(raw, *, adapter=None):
    """Adapter glue: RawCaseObject -> CaseKnowledge.

    Thin wrapper around ``IntakeAdapter.adapt()``.
    """
    if adapter is None:
        adapter = IntakeAdapter()
    return adapter.adapt(raw)


def _build_provenance_chain():
    """Build the canonical V1 provenance chain (2 steps)."""
    return (
        ProvenanceRecord(step=STEP_INTAKE, actor="intake_e2e",
                         notes="raw case accepted"),
        ProvenanceRecord(step=STEP_CASE_KNOWLEDGE_VALIDATION,
                         actor="adapter", notes="CK contract OK"),
    )


def _build_promotion_candidate(
    case,
    *,
    proposed_knowledge_id="ko_forest_v1",
    justification="promotion human_review OK",
    chain=None,
):
    """Test-only glue: CaseKnowledge -> PromotionCandidate.

    Built with DRAFT status; downstream checker stamps it to
    ELIGIBLE / NOT_ELIGIBLE.
    """
    if chain is None:
        chain = _build_provenance_chain()
    return new_promotion_candidate(
        case_id=case.case_id,
        case_source_kind=case.source_kind,
        proposed_knowledge_id=proposed_knowledge_id,
        proposed_version=1,
        provenance_chain=chain,
        justification=justification,
        created_by="e2e_test",
    )


def _build_admission_proposal():
    """Build the admission_proposal mapping consumed by Writer.

    Provides the minimum set of fields the Writer's
    ``_KO_PROPOSAL_KEY_MAP`` reads; other KO fields fall back
    to ``_KO_FIELD_DEFAULTS`` inside the writer.
    """
    return {
        "title": "Forest kindergarten case",
        "description": "A baseline kindergarten case from operator intake.",
        "category": "case",
        "project_type": "kindergarten",
        "site_type": "outdoor",
        "location_type": "suburban",
        "space_size": "medium",
        "theme": "forest",
        "style": "natural",
        "color_system": "earth",
        "interaction_type": "physical",
        "function_tags": ["role_play", "outdoor"],
        "image_refs": ["assets/forest-1.png"],
        "document_refs": [],
        "source": "admission",
    }


def _build_admission_candidate(
    promotion,
    *,
    target_knowledge_id="ko_forest_v1",
    justification="admission human_review OK",
    proposal_overrides=None,
):
    """Test-only glue: PromotionCandidate -> AdmissionCandidate.

    Preserves the full provenance chain via AdmissionProvenanceRef.
    Forces V1 invariants (target_version=1, requires_human_review=True)
    by relying on the AdmissionCandidate constructor guards.
    """
    proposal = _build_admission_proposal()
    if proposal_overrides:
        proposal.update(proposal_overrides)
    return new_admission_candidate(
        promotion_candidate_id=promotion.candidate_id,
        case_id=promotion.case_id,
        case_source_kind=promotion.case_source_kind,
        provenance_chain=promotion.provenance_chain,
        target_knowledge_id=target_knowledge_id,
        admission_proposal=proposal,
        justification=justification,
        requires_human_review=True,
        created_by="e2e_test",
    )


# ---------------------------------------------------------------------------
# End-to-end orchestrator (test-only)
# ---------------------------------------------------------------------------


def _run_e2e_happy(
    *,
    promotion_chain=None,
    target_knowledge_id="ko_forest_v1",
    on_duplicate="idempotent",
):
    """Run the entire V1 chain and return every artifact.

    Returns a dict so individual tests can pick the artifacts
    they need. The orchestrator never mutates its inputs.
    """
    raw = _build_raw_case()
    case = _build_case_knowledge(raw)

    validator = IngestionValidator()
    ck_validation = validator.validate(case)

    promotion = _build_promotion_candidate(
        case,
        proposed_knowledge_id=target_knowledge_id,
        chain=promotion_chain,
    )
    checker = PromotionEligibilityChecker()
    eligibility, promotion_eligible = checker.check(promotion)

    admission = _build_admission_candidate(
        promotion_eligible,
        target_knowledge_id=target_knowledge_id,
    )
    admission_checker = AdmissionChecker()
    admission_result, admission_eligible = admission_checker.check(admission)

    version_store = VersionStore()
    audit_store = EvolutionAuditStore()
    writer = AdmissionWriter(
        version_store=version_store,
        audit_store=audit_store,
        on_duplicate=on_duplicate,
    )
    write_result = writer.write(admission_eligible)

    return {
        "raw": raw,
        "case": case,
        "ck_validation": ck_validation,
        "promotion": promotion,
        "eligibility": eligibility,
        "promotion_eligible": promotion_eligible,
        "admission": admission,
        "admission_result": admission_result,
        "admission_eligible": admission_eligible,
        "writer": writer,
        "version_store": version_store,
        "audit_store": audit_store,
        "write_result": write_result,
    }


# ===========================================================================
# 1. Happy path E2E
# ===========================================================================


class TestHappyPathE2E:
    """Walk every layer with V1 contract defaults; everything
    must come back green."""

    def test_full_chain_creates_ko_v1(self):
        out = _run_e2e_happy()
        assert out["ck_validation"].valid is True
        assert out["eligibility"].valid is True
        assert out["admission_result"].valid is True

        wr = out["write_result"]
        assert isinstance(wr, AdmissionWriteResult)
        assert wr.success is True
        assert wr.status == CREATED
        assert wr.version == ADMISSION_TARGET_VERSION == 1
        assert wr.knowledge_id == "ko_forest_v1"
        assert wr.knowledge_object is not None
        assert isinstance(wr.knowledge_object, KnowledgeObject)
        assert wr.knowledge_object.knowledge_id == "ko_forest_v1"
        assert wr.knowledge_object.version == 1
        assert wr.knowledge_object.title == "Forest kindergarten case"
        assert wr.knowledge_object.theme == "forest"
        assert wr.knowledge_object.source == "admission"

    def test_intake_adapter_produced_case_knowledge(self):
        """Intake endpoint must produce a CaseKnowledge with the
        IntakeAdapter's standard field mapping."""
        out = _run_e2e_happy()
        case = out["case"]
        assert isinstance(case, CaseKnowledge)
        assert case.case_id.startswith("CK-")
        assert case.source == "intake_e2e"
        assert case.source_kind == "intake"
        assert "kindergarten" in case.tags

    def test_promotion_status_flips_draft_to_eligible(self):
        out = _run_e2e_happy()
        assert out["promotion"].status == "DRAFT"
        assert out["promotion_eligible"].status == ELIGIBLE
        assert out["promotion_eligible"].failure_reason == ""

    def test_admission_status_flips_draft_to_admissible(self):
        out = _run_e2e_happy()
        assert out["admission"].status == "DRAFT"
        assert out["admission_eligible"].status == ADMISSIBLE
        assert out["admission_eligible"].failure_reason == ""


# ===========================================================================
# 2. Gate rejection paths
# ===========================================================================


class TestIngestionValidatorRejects:
    """IngestionValidator rejects invalid CaseKnowledge BEFORE
    the chain touches promotion / admission."""

    def test_case_without_human_review_rejected(self):
        raw = _build_raw_case()
        case = _build_case_knowledge(raw)
        # Bypass IntakeAdapter defaults to inject a bad record.
        bad_case = dataclasses.replace(
            case, requires_human_review=False,
        )
        result = IngestionValidator().validate(bad_case)
        assert result.valid is False
        assert result.rule_id == "I6_human_review_required"


class TestPromotionGateRejects:
    """PromotionEligibilityChecker refuses NOT_ELIGIBLE candidates.
    No admission / writer activity may happen downstream."""

    def test_missing_required_provenance_step(self):
        """Two steps present but neither is the required one;
        P4 must reject."""
        raw = _build_raw_case()
        case = _build_case_knowledge(raw)
        weak_chain = (
            ProvenanceRecord(step="custom_a", actor="intake_e2e"),
            ProvenanceRecord(step="custom_b", actor="intake_e2e"),
        )
        promotion = _build_promotion_candidate(case, chain=weak_chain)
        result, stamped = PromotionEligibilityChecker().check(promotion)
        assert result.valid is False
        assert result.rule_id == "P4_required_provenance_steps"
        assert stamped.status == NOT_ELIGIBLE

    def test_justification_without_human_review_marker(self):
        raw = _build_raw_case()
        case = _build_case_knowledge(raw)
        promotion = _build_promotion_candidate(
            case, justification="no marker here",
        )
        result, stamped = PromotionEligibilityChecker().check(promotion)
        assert result.valid is False
        assert result.rule_id == "P8_human_review_marker_required"
        assert stamped.status == NOT_ELIGIBLE

    def test_provenance_too_short(self):
        """One step fails P3 (min_provenance_steps=2)."""
        raw = _build_raw_case()
        case = _build_case_knowledge(raw)
        chain = (ProvenanceRecord(step=STEP_INTAKE, actor="intake_e2e"),)
        promotion = _build_promotion_candidate(case, chain=chain)
        result, stamped = PromotionEligibilityChecker().check(promotion)
        assert result.valid is False
        assert result.rule_id == "P3_min_provenance_steps"


class TestAdmissionGateRejects:
    """AdmissionChecker refuses NOT_ADMISSIBLE candidates."""

    def test_justification_missing_human_review_marker(self):
        # Build a fully eligible promotion first.
        out = _run_e2e_happy()
        promotion = out["promotion_eligible"]
        admission = _build_admission_candidate(
            promotion, justification="no marker here",
        )
        result, stamped = AdmissionChecker().check(admission)
        assert result.valid is False
        assert result.rule_id == "A8_human_review_marker_present"
        assert stamped.status == NOT_ADMISSIBLE

    def test_empty_admission_proposal_rejected(self):
        out = _run_e2e_happy()
        admission = _build_admission_candidate(out["promotion_eligible"])
        # Force-empty the proposal via dataclasses.replace.
        empty_proposal_admission = dataclasses.replace(
            admission, admission_proposal={},
        )
        result, stamped = AdmissionChecker().check(empty_proposal_admission)
        assert result.valid is False
        assert result.rule_id == "A6_admission_proposal_non_empty"
        assert stamped.status == NOT_ADMISSIBLE


# ===========================================================================
# 3. Writer V1 / version guards
# ===========================================================================


class TestWriterGuards:
    """The Writer must refuse anything other than ADMISSIBLE +
    target_version=1."""

    def test_not_admissible_status_rejected(self):
        # Use a FRESH version/audit store so we can assert that
        # a NOT_ADMISSIBLE write leaves them empty.
        vs = VersionStore()
        au = EvolutionAuditStore()
        writer = AdmissionWriter(
            version_store=vs, audit_store=au, on_duplicate="idempotent",
        )
        # Build a NOT_ADMISSIBLE candidate directly.
        raw = _build_raw_case()
        case = _build_case_knowledge(raw)
        promotion = _build_promotion_candidate(case)
        _, promotion_eligible = PromotionEligibilityChecker().check(promotion)
        admission = _build_admission_candidate(promotion_eligible)
        not_admissible = dataclasses.replace(admission, status=NOT_ADMISSIBLE)
        wr = writer.write(not_admissible)
        assert isinstance(wr, AdmissionWriteResult)
        assert wr.success is False
        assert wr.status == REJECTED
        assert wr.knowledge_object is None
        assert wr.audit_record is None
        # Fresh stores must remain empty.
        assert vs.count() == 0
        assert au.count() == 0

    def test_target_version_must_be_one(self):
        """target_version != 1 must be rejected at the
        AdmissionCandidate constructor (V1 invariant)."""
        out = _run_e2e_happy()
        with pytest.raises(Exception):
            dataclasses.replace(
                out["admission_eligible"], target_version=2,
            )


# ===========================================================================
# 4. Duplicate admission (idempotent + strict)
# ===========================================================================


class TestDuplicateAdmission:
    """The same identity must be admitted at most once."""

    def test_idempotent_second_write(self):
        out1 = _run_e2e_happy(on_duplicate="idempotent")
        assert out1["write_result"].status == CREATED

        # Second pass on a FRESH writer/stores to mimic a
        # second admission attempt hitting an existing identity.
        out2 = _run_e2e_happy(on_duplicate="idempotent")
        # Share the version_store + audit_store from out1 with
        # out2's writer so we model "same identity, different
        # writer call".
        shared_writer = AdmissionWriter(
            version_store=out1["version_store"],
            audit_store=out1["audit_store"],
            on_duplicate="idempotent",
        )
        wr = shared_writer.write(out2["admission_eligible"])
        assert wr.status == IDEMPOTENT
        # No new KO materialised.
        assert wr.knowledge_object is None
        # VersionStore baseline is still v1 (single record).
        history = out1["version_store"].history("ko_forest_v1")
        assert len(history) == 1
        # Audit log has both admission and idempotent records.
        all_actions = [r.action for r in out1["audit_store"].list()]
        assert "admission" in all_actions
        assert "admission_idempotent" in all_actions

    def test_strict_second_write_raises(self):
        out1 = _run_e2e_happy(on_duplicate="idempotent")
        assert out1["write_result"].status == CREATED

        out2 = _run_e2e_happy(on_duplicate="idempotent")
        strict_writer = AdmissionWriter(
            version_store=out1["version_store"],
            audit_store=out1["audit_store"],
            on_duplicate="strict",
        )
        with pytest.raises(DuplicateAdmissionError):
            strict_writer.write(out2["admission_eligible"])


# ===========================================================================
# 5. Provenance / audit / version traceability
# ===========================================================================


class TestProvenanceAuditVersionTraceability:
    """Every audit row must point back to the full provenance chain
    that produced it; VersionStore must have exactly one baseline."""

    def test_audit_record_carries_full_provenance_chain(self):
        out = _run_e2e_happy()
        wr = out["write_result"]
        audit = wr.audit_record
        assert audit is not None
        assert audit.action == "admission"
        assert audit.transaction_id == out["admission_eligible"].admission_id

        after = audit.after
        assert isinstance(after, dict)
        assert after["knowledge_id"] == "ko_forest_v1"
        assert after["version"] == 1
        assert after["admission_id"] == out["admission_eligible"].admission_id
        assert after["case_id"] == out["case"].case_id
        assert after["requires_human_review"] is True

        provenance_in_audit = after["provenance"]
        assert isinstance(provenance_in_audit, list)
        assert len(provenance_in_audit) == 2
        steps = {row["step"] for row in provenance_in_audit}
        assert steps == {STEP_INTAKE, STEP_CASE_KNOWLEDGE_VALIDATION}

    def test_version_store_has_baseline_v1(self):
        out = _run_e2e_happy()
        vs = out["version_store"]
        history = vs.history("ko_forest_v1")
        assert len(history) == 1
        v1 = history[0]
        assert isinstance(v1, KnowledgeVersion)
        assert v1.target_identity == "ko_forest_v1"
        assert v1.version_number == 1
        assert v1.previous_version is None
        assert v1.change_reason == "admission baseline (target_version=1)"
        assert v1.proposal_id == out["admission_eligible"].admission_id

    def test_snapshot_in_version_matches_ko_payload(self):
        out = _run_e2e_happy()
        v1 = out["version_store"].history("ko_forest_v1")[0]
        ko_dict = out["write_result"].knowledge_object.to_dict()
        for key in ("knowledge_id", "version", "title", "theme"):
            assert v1.snapshot[key] == ko_dict[key]
        # Snapshot must not share dict identity with the live KO.
        assert v1.snapshot is not ko_dict


# ===========================================================================
# 6. Immutability at every gate
# ===========================================================================


class TestImmutability:
    """Every gate must NOT mutate its inputs."""

    def test_case_knowledge_immutable_after_intake_adapter(self):
        raw = _build_raw_case()
        snap_raw = copy.deepcopy(raw.to_dict())
        case = _build_case_knowledge(raw)
        # Adapt must NOT mutate the raw record.
        assert raw.to_dict() == snap_raw
        # CaseKnowledge is a frozen dataclass.
        with pytest.raises(Exception):
            case.title = "mutated"  # type: ignore[misc]

    def test_promotion_candidate_not_mutated_by_checker(self):
        out = _run_e2e_happy()
        before = out["promotion"].to_dict()
        PromotionEligibilityChecker().check(out["promotion"])
        after = out["promotion"].to_dict()
        assert before == after

    def test_admission_candidate_not_mutated_by_checker(self):
        out = _run_e2e_happy()
        before = out["admission"].to_dict()
        AdmissionChecker().check(out["admission"])
        after = out["admission"].to_dict()
        assert before == after

    def test_writer_does_not_mutate_input(self):
        # Use fresh stores so the write produces CREATED, not IDEMPOTENT.
        vs = VersionStore()
        au = EvolutionAuditStore()
        writer = AdmissionWriter(version_store=vs, audit_store=au)
        # Build an ADMISSIBLE candidate directly.
        raw = _build_raw_case()
        case = _build_case_knowledge(raw)
        promotion = _build_promotion_candidate(case)
        _, promotion_eligible = PromotionEligibilityChecker().check(promotion)
        admission = _build_admission_candidate(promotion_eligible)
        _, admission_eligible = AdmissionChecker().check(admission)
        before = admission_eligible.to_dict()
        wr = writer.write(admission_eligible)
        after = admission_eligible.to_dict()
        assert before == after
        assert wr.status == CREATED


# ===========================================================================
# 7. Final Retrieval visibility
# ===========================================================================


class TestRetrievalVisibility:
    """After admission, the KO must be visible to the
    RetrievalPipeline through filters={knowledge_id: ...}."""

    def test_admitted_ko_retrievable_by_id(self):
        out = _run_e2e_happy()
        wr = out["write_result"]
        assert wr.status == CREATED
        ko = wr.knowledge_object
        assert ko is not None

        pipeline = RetrievalPipeline()
        query = RetrievalQuery(
            query_text="",
            filters={"knowledge_id": ko.knowledge_id},
            limit=10,
        )
        result = pipeline.execute(query, [ko])
        assert result.success is True
        assert result.total_hits == 1
        hit = result.hits[0]
        assert hit.knowledge_id == "ko_forest_v1"
        assert hit.knowledge_version == 1
        assert "knowledge_id" in hit.matched_fields

    def test_non_admitted_identity_not_retrievable(self):
        out = _run_e2e_happy()
        wr = out["write_result"]
        ko = wr.knowledge_object
        assert ko is not None

        pipeline = RetrievalPipeline()
        query = RetrievalQuery(
            query_text="",
            filters={"knowledge_id": "ko_does_not_exist"},
            limit=10,
        )
        result = pipeline.execute(query, [ko])
        assert result.success is True
        assert result.total_hits == 0

    def test_corpus_grows_only_via_writer(self):
        """The Writer is the ONLY code path that adds a KO to the
        retrieval corpus in V1. A ghost KO never written must NOT
        appear in retrieval results."""
        ghost_ko = KnowledgeObject(
            knowledge_id="ko_ghost",
            version=1,
            title="ghost",
            description="never admitted",
            category="case",
            project_type="kindergarten",
            site_type="outdoor",
            location_type="suburban",
            space_size="medium",
            theme="ghost",
            style="ghost",
            color_system="",
            interaction_type="physical",
            function_tags=[],
            image_refs=[],
            document_refs=[],
            source="never",
        )

        out = _run_e2e_happy()
        wr = out["write_result"]
        real_ko = wr.knowledge_object

        pipeline = RetrievalPipeline()
        q = RetrievalQuery(
            query_text="",
            filters={"knowledge_id": real_ko.knowledge_id},
            limit=10,
        )
        result = pipeline.execute(q, [real_ko, ghost_ko])
        assert result.total_hits == 1
        assert result.hits[0].knowledge_id == real_ko.knowledge_id


# ===========================================================================
# 8. Architecture boundary AST
# ===========================================================================


class TestArchitectureBoundary:
    """The E2E test file MUST NOT import forbidden modules."""

    FORBIDDEN_SUBSTRINGS = (
        "caseos.intelligence",
        "caseos.brain",
        "caseos.knowledge.governance",
        "caseos.knowledge.feedback",
        "caseos.knowledge.corpus",
    )

    def test_no_forbidden_imports(self):
        here = Path(__file__).resolve()
        tree = ast.parse(here.read_text(encoding="utf-8"))
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = alias.name
                    if any(target.startswith(s) for s in self.FORBIDDEN_SUBSTRINGS):
                        offenders.append((target, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if any(module.startswith(s) for s in self.FORBIDDEN_SUBSTRINGS):
                    offenders.append((module, node.lineno))
        assert offenders == [], (
            "forbidden imports detected: " + repr(offenders)
        )

    def test_intake_chain_does_not_promote_legacy(self):
        """The legacy intake promotion path (IntakeManager.promote
        -> governance_promote -> PromotionEvent) is NOT exercised
        anywhere in this test file.

        We scan imports only; the docstring is allowed to mention
        the names so the rationale stays readable.
        """
        here = Path(__file__).resolve()
        tree = ast.parse(here.read_text(encoding="utf-8"))
        legacy_symbols = ("IntakeManager", "governance_promote",
                          "PromotionEvent")
        offenders = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name in legacy_symbols:
                        offenders.append((alias.name, node.lineno))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in legacy_symbols:
                        offenders.append((alias.name, node.lineno))
        assert offenders == [], (
            "legacy intake symbols imported: " + repr(offenders)
        )



