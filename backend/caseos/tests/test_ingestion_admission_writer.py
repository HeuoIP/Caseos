"""Tests for the Admission Writer V1 (Sprint 25.4-A).

Coverage (per Sprint 25.4-A spec section 14):

    1.  Happy path
    2.  Illegal status rejection
    3.  Version guard
    4.  Identity guard
    5.  Duplicate admission
    6.  Existing KO cannot be overwritten
    7.  VersionStore history(knowledge_id) -> [v1]
    8.  Audit traceability
    9.  Provenance preservation
    10. Input immutability
    11. Determinism
    12. Architecture boundary AST scan
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

from caseos.knowledge.evolution.audit import EvolutionAuditStore  # noqa: E402
from caseos.knowledge.evolution.versioning import (  # noqa: E402
    KnowledgeVersion,
    VersionStore,
)

from caseos.knowledge.ingestion.admission import (  # noqa: E402
    ADMISSIBLE,
    ADMISSION_TARGET_VERSION,
    CREATED,
    IDEMPOTENT,
    NOT_ADMISSIBLE,
    REJECTED,
    AdmissionCandidate,
    AdmissionCandidateError,
    AdmissionWriteResult,
    AdmissionWriter,
    AdmissionWriterError,
    DuplicateAdmissionError,
    new_admission_candidate,
)
from caseos.knowledge.ingestion.promotion import (  # noqa: E402
    ProvenanceRecord,
    STEP_CASE_KNOWLEDGE_VALIDATION,
    STEP_INTAKE,
)

from caseos.knowledge.object import KnowledgeObject  # noqa: E402


def _provenance(*steps, actor: str = "fixture") -> tuple:
    return tuple(ProvenanceRecord(step=s, actor=actor) for s in steps)


def _admissible_candidate(**overrides) -> AdmissionCandidate:
    """Build a candidate stamped as ADMISSIBLE by default."""
    chain = _provenance(STEP_INTAKE, STEP_CASE_KNOWLEDGE_VALIDATION)
    base = dict(
        promotion_candidate_id="PC-abc",
        case_id="CK-abc",
        case_source_kind="intake",
        provenance_chain=chain,
        target_knowledge_id="ko_forest_v1",
        admission_proposal={
            "title": "Forest kindergarten case",
            "description": "A baseline kindergarten case.",
            "theme": "forest",
            "style": "natural",
        },
        justification="admission human_review ok",
        requires_human_review=True,
        created_by="fixture",
    )
    # The builder does not accept status; pull it out and
    # apply it via dataclasses.replace after construction.
    status_override = overrides.pop("status", ADMISSIBLE)
    base.update(overrides)
    cand = new_admission_candidate(**base)
    return dataclasses.replace(cand, status=status_override)


def _make_writer(**overrides) -> AdmissionWriter:
    base = dict(version_store=VersionStore(), audit_store=EvolutionAuditStore())
    base.update(overrides)
    return AdmissionWriter(**base)


# ---------------------------------------------------------------------------
# 1. Constructor
# ---------------------------------------------------------------------------


class TestWriterConstruction:
    def test_basic_construction(self) -> None:
        w = _make_writer()
        assert w.actor == "admission_writer"
        assert w.on_duplicate == "idempotent"

    def test_custom_actor(self) -> None:
        w = _make_writer(actor="manual:operator1")
        assert w.actor == "manual:operator1"

    def test_invalid_version_store_rejected(self) -> None:
        with pytest.raises(AdmissionWriterError):
            AdmissionWriter(
                version_store="not a store",  # type: ignore[arg-type]
                audit_store=EvolutionAuditStore(),
            )

    def test_invalid_audit_store_rejected(self) -> None:
        with pytest.raises(AdmissionWriterError):
            AdmissionWriter(
                version_store=VersionStore(),
                audit_store="not a store",  # type: ignore[arg-type]
            )

    def test_invalid_on_duplicate_rejected(self) -> None:
        with pytest.raises(AdmissionWriterError):
            AdmissionWriter(
                version_store=VersionStore(),
                audit_store=EvolutionAuditStore(),
                on_duplicate="explode",
            )

    def test_invalid_existing_kos_rejected(self) -> None:
        with pytest.raises(AdmissionWriterError):
            AdmissionWriter(
                version_store=VersionStore(),
                audit_store=EvolutionAuditStore(),
                existing_kos=["not", "a", "mapping"],  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------------
# 2. Happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_admissible_candidate_creates_ko_v1(self) -> None:
        w = _make_writer()
        c = _admissible_candidate()
        result = w.write(c)
        assert isinstance(result, AdmissionWriteResult)
        assert result.success is True
        assert result.status == CREATED
        assert result.knowledge_id == "ko_forest_v1"
        assert result.version == ADMISSION_TARGET_VERSION == 1

    def test_knowledge_object_fields(self) -> None:
        w = _make_writer()
        c = _admissible_candidate()
        result = w.write(c)
        ko = result.knowledge_object
        assert isinstance(ko, KnowledgeObject)
        assert ko.knowledge_id == "ko_forest_v1"
        assert ko.version == 1
        assert ko.title == "Forest kindergarten case"
        assert ko.description == "A baseline kindergarten case."
        assert ko.theme == "forest"
        assert ko.style == "natural"
        assert ko.source == "admission"

    def test_version_store_baseline_present(self) -> None:
        vs = VersionStore()
        w = _make_writer(version_store=vs)
        c = _admissible_candidate()
        result = w.write(c)
        history = vs.history("ko_forest_v1")
        assert len(history) == 1
        v = history[0]
        assert isinstance(v, KnowledgeVersion)
        assert v.version_number == 1
        assert v.previous_version is None
        assert v.target_identity == "ko_forest_v1"
        assert v.snapshot["knowledge_id"] == "ko_forest_v1"
        assert v.snapshot["version"] == 1

    def test_audit_record_appended(self) -> None:
        astore = EvolutionAuditStore()
        w = _make_writer(audit_store=astore)
        c = _admissible_candidate()
        result = w.write(c)
        assert result.audit_record is not None
        assert result.audit_record.action == "admission"
        assert result.audit_record.transaction_id == c.admission_id
        assert result.audit_record.actor == "admission_writer"
        assert result.audit_record.before is None

    def test_audit_after_payload_carries_full_traceability(self) -> None:
        w = _make_writer()
        c = _admissible_candidate()
        result = w.write(c)
        after = result.audit_record.after
        assert after["knowledge_id"] == "ko_forest_v1"
        assert after["version"] == 1
        assert after["admission_id"] == c.admission_id
        assert after["candidate_id"] == "PC-abc"
        assert after["case_id"] == "CK-abc"
        assert after["source_kind"] == "intake"
        assert isinstance(after["provenance"], list)
        assert len(after["provenance"]) == 2

    def test_existing_kos_overlay_blocks_creation(self) -> None:
        existing = KnowledgeObject(
            knowledge_id="ko_forest_v1", version=1,
            title="pre-existing", description="", category="case",
            project_type="", site_type="", location_type="",
            space_size="", theme="", style="", color_system="",
            interaction_type="", source="legacy",
        )
        w = _make_writer(existing_kos={"ko_forest_v1": existing})
        c = _admissible_candidate()
        result = w.write(c)
        assert result.status == IDEMPOTENT
        assert result.success is True
        assert w.version_store.count() == 0


# ---------------------------------------------------------------------------
# 3. Illegal status
# ---------------------------------------------------------------------------


class TestIllegalStatus:
    def test_draft_rejected(self) -> None:
        w = _make_writer()
        c = _admissible_candidate(status="DRAFT")
        result = w.write(c)
        assert result.status == REJECTED
        assert result.success is False
        assert "DRAFT" in result.failure_reason

    def test_not_admissible_rejected(self) -> None:
        w = _make_writer()
        c = _admissible_candidate(status=NOT_ADMISSIBLE)
        result = w.write(c)
        assert result.status == REJECTED
        assert "NOT_ADMISSIBLE" in result.failure_reason

    def test_non_candidate_rejected(self) -> None:
        w = _make_writer()
        result = w.write({"not": "a candidate"})
        assert result.status == REJECTED
        assert "AdmissionCandidate" in result.failure_reason

    def test_none_rejected(self) -> None:
        w = _make_writer()
        result = w.write(None)  # type: ignore[arg-type]
        assert result.status == REJECTED


# ---------------------------------------------------------------------------
# 4. Version guard
# ---------------------------------------------------------------------------


class TestVersionGuard:
    def test_target_version_not_one_constructor_guard(self) -> None:
        with pytest.raises(AdmissionCandidateError):
            AdmissionCandidate(
                target_knowledge_id="ko_x",
                target_version=2,
            )

    def test_clean_candidate_passes_version_guard(self) -> None:
        w = _make_writer()
        c = _admissible_candidate()
        result = w.write(c)
        assert result.status == CREATED


# ---------------------------------------------------------------------------
# 5. Identity guard
# ---------------------------------------------------------------------------


class TestIdentityGuard:
    def test_empty_target_knowledge_id_constructor_guard(self) -> None:
        with pytest.raises(AdmissionCandidateError):
            AdmissionCandidate(target_knowledge_id="")


# ---------------------------------------------------------------------------
# 6. Duplicate admission
# ---------------------------------------------------------------------------


class TestDuplicateAdmission:
    def test_same_candidate_twice_idempotent(self) -> None:
        vs = VersionStore()
        astore = EvolutionAuditStore()
        w = _make_writer(version_store=vs, audit_store=astore)
        c = _admissible_candidate()
        r1 = w.write(c)
        r2 = w.write(c)
        assert r1.status == CREATED
        assert r2.status == IDEMPOTENT
        assert r2.success is True
        assert len(vs.history("ko_forest_v1")) == 1
        assert astore.count() == 2

    def test_idempotent_audit_action(self) -> None:
        astore = EvolutionAuditStore()
        w = _make_writer(audit_store=astore)
        c = _admissible_candidate()
        w.write(c)
        w.write(c)
        actions = sorted(r.action for r in astore.list())
        assert actions == ["admission", "admission_idempotent"]

    def test_strict_mode_raises_duplicate(self) -> None:
        vs = VersionStore()
        astore = EvolutionAuditStore()
        w = _make_writer(
            version_store=vs, audit_store=astore,
            on_duplicate="strict",
        )
        c = _admissible_candidate()
        w.write(c)
        with pytest.raises(DuplicateAdmissionError):
            w.write(c)
        assert len(vs.history("ko_forest_v1")) == 1

    def test_different_candidates_same_target_id_idempotent(self) -> None:
        vs = VersionStore()
        astore = EvolutionAuditStore()
        w = _make_writer(version_store=vs, audit_store=astore)
        c1 = _admissible_candidate()
        c2 = _admissible_candidate()
        assert c1.admission_id != c2.admission_id
        r1 = w.write(c1)
        r2 = w.write(c2)
        assert r1.status == CREATED
        assert r2.status == IDEMPOTENT
        assert len(vs.history("ko_forest_v1")) == 1


# ---------------------------------------------------------------------------
# 7. VersionStore integration
# ---------------------------------------------------------------------------


class TestVersionStoreIntegration:
    def test_history_after_write_contains_v1(self) -> None:
        vs = VersionStore()
        w = _make_writer(version_store=vs)
        c = _admissible_candidate()
        w.write(c)
        history = vs.history("ko_forest_v1")
        assert len(history) == 1
        assert history[0].version_number == 1
        assert history[0].previous_version is None

    def test_future_evolution_can_see_history(self) -> None:
        vs = VersionStore()
        w = _make_writer(version_store=vs)
        c = _admissible_candidate()
        w.write(c)
        latest = vs.get("ko_forest_v1")
        assert latest is not None
        assert latest.version_number == 1


# ---------------------------------------------------------------------------
# 8. Audit traceability
# ---------------------------------------------------------------------------


class TestAuditTraceability:
    def test_audit_links_back_to_case_knowledge(self) -> None:
        w = _make_writer()
        c = _admissible_candidate(case_id="CK-specific")
        result = w.write(c)
        assert result.audit_record.after["case_id"] == "CK-specific"

    def test_audit_links_back_to_promotion_candidate(self) -> None:
        w = _make_writer()
        c = _admissible_candidate(promotion_candidate_id="PC-specific")
        result = w.write(c)
        assert result.audit_record.after["candidate_id"] == "PC-specific"

    def test_audit_action_is_admission(self) -> None:
        w = _make_writer()
        c = _admissible_candidate()
        result = w.write(c)
        assert result.audit_record.action == "admission"

    def test_audit_records_source_kind(self) -> None:
        w = _make_writer()
        c = _admissible_candidate(case_source_kind="operator")
        result = w.write(c)
        assert result.audit_record.after["source_kind"] == "operator"

    def test_audit_records_actor(self) -> None:
        w = _make_writer(actor="custom:actor")
        c = _admissible_candidate()
        result = w.write(c)
        assert result.audit_record.actor == "custom:actor"


# ---------------------------------------------------------------------------
# 9. Provenance preservation
# ---------------------------------------------------------------------------


class TestProvenancePreservation:
    def test_provenance_chain_carried_into_audit(self) -> None:
        w = _make_writer()
        c = _admissible_candidate()
        result = w.write(c)
        steps = [r["step"] for r in result.audit_record.after["provenance"]]
        assert steps == [STEP_INTAKE, STEP_CASE_KNOWLEDGE_VALIDATION]


# ---------------------------------------------------------------------------
# 10. Input immutability
# ---------------------------------------------------------------------------


class TestInputImmutability:
    def test_candidate_not_mutated(self) -> None:
        w = _make_writer()
        c = _admissible_candidate()
        before = c.to_dict()
        w.write(c)
        after = c.to_dict()
        assert before == after

    def test_provenance_chain_not_mutated(self) -> None:
        w = _make_writer()
        c = _admissible_candidate()
        before = [r.step for r in c.source.provenance_chain]
        w.write(c)
        after = [r.step for r in c.source.provenance_chain]
        assert before == after
        assert len(c.source.provenance_chain) == 2

    def test_proposal_not_mutated(self) -> None:
        w = _make_writer()
        c = _admissible_candidate()
        before_keys = sorted(c.admission_proposal.keys())
        w.write(c)
        assert sorted(c.admission_proposal.keys()) == before_keys

    def test_version_store_internal_list_not_mutated_externally(self) -> None:
        vs = VersionStore()
        w = _make_writer(version_store=vs)
        w.write(_admissible_candidate())
        vs.list().clear()
        assert len(vs.history("ko_forest_v1")) == 1

    def test_audit_store_internal_list_not_mutated_externally(self) -> None:
        astore = EvolutionAuditStore()
        w = _make_writer(audit_store=astore)
        w.write(_admissible_candidate())
        astore.list().clear()
        assert astore.count() == 1


# ---------------------------------------------------------------------------
# 11. Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_same_input_same_logical_outcome(self) -> None:
        r1 = _make_writer().write(_admissible_candidate())
        r2 = _make_writer().write(_admissible_candidate())
        assert r1.status == r2.status == CREATED
        assert r1.knowledge_id == r2.knowledge_id == "ko_forest_v1"
        assert r1.version == r2.version == 1

    def test_two_writes_same_candidate_first_created_then_idempotent(self) -> None:
        w = _make_writer()
        c = _admissible_candidate()
        r1 = w.write(c)
        r2 = w.write(c)
        assert r1.status == CREATED
        assert r2.status == IDEMPOTENT


# ---------------------------------------------------------------------------
# 12. Architecture boundary
# ---------------------------------------------------------------------------


class TestArchitectureBoundary:
    FORBIDDEN_SUBSTRINGS = (
        "caseos.intelligence",
        "caseos.knowledge.retrieval",
        "caseos.knowledge.intake",
        "caseos.knowledge.governance",
        "caseos.knowledge.feedback",
        "caseos.brain",
    )

    MUTATION_PATH_FRAGMENTS = (
        "caseos.knowledge.evolution.mutation",
        "caseos.knowledge.evolution.adapter",
        "caseos.knowledge.evolution.writer",
        "caseos.knowledge.evolution.runtime_v2",
        "caseos.knowledge.evolution.rollback",
        "caseos.knowledge.evolution.integration",
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

    def test_writer_module_has_no_forbidden_imports(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "ingestion"
            / "admission"
            / "writer.py"
        )
        source = path.read_text(encoding="utf-8-sig")
        imports = self._collect_imports(source)
        offenders = [
            imp for imp in imports
            if any(f in imp for f in self.FORBIDDEN_SUBSTRINGS)
        ]
        assert offenders == [], (
            "Forbidden import in writer.py: " + repr(offenders)
        )

    def test_writer_does_not_import_evolution_mutation_path(self) -> None:
        path = (
            Path(__file__).resolve().parents[1]
            / "knowledge"
            / "ingestion"
            / "admission"
            / "writer.py"
        )
        source = path.read_text(encoding="utf-8-sig")
        for forbidden in self.MUTATION_PATH_FRAGMENTS:
            assert forbidden not in source, (
                "writer.py must not import from " + forbidden
            )


# ---------------------------------------------------------------------------
# 13. WriteResult
# ---------------------------------------------------------------------------


class TestWriteResult:
    def test_result_is_frozen(self) -> None:
        w = _make_writer()
        result = w.write(_admissible_candidate())
        with pytest.raises(Exception):
            result.status = "MUTATED"  # type: ignore[misc]

    def test_result_to_dict_is_json_safe(self) -> None:
        w = _make_writer()
        result = w.write(_admissible_candidate())
        json.dumps(result.to_dict(), default=str)
