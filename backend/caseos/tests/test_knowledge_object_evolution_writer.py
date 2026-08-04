"""Knowledge Object Evolution Writer V1 tests (Sprint 23.0-C).

Test scope:

    * WriteRequest / WriteResult (frozen, JSON-safe,
      deep-copy isolation)
    * WriterValidator (rules W1-W14)
    * KnowledgeObjectWriter happy path: appends a new
      KnowledgeVersion + EvolutionAuditRecord
    * Append-only contract: existing versions unchanged
      after the write
    * Writer rejects when before_version does not match
      the latest version in the store
    * Writer rejects when no prior history exists
      (no bootstrap)
    * Writer rejects empty writes (new == before)
    * Writer rejects KO V1 incompatible snapshots
    * Writer does NOT mutate input request
    * Audit record carries both before_snapshot and
      after_snapshot
    * mutation_executed is True on success and False on
      rejection
    * Architecture boundary (AST scan)
    * Writer does NOT import from intelligence.* or
      retrieval
    * Writer does NOT mutate or overwrite stores

Out of scope:

    * Pipeline wiring
    * Intelligence / Retrieval
    * Rollback / restore (Sprint 22.4-G is the rollback
      module; the writer only appends)
"""
from __future__ import annotations

import ast
import copy
import dataclasses
import json
import pathlib
from datetime import datetime, timezone

import pytest

from caseos.knowledge.evolution.adapter import (
    KnowledgeObjectAdapter,
    AdapterRequest,
)
from caseos.knowledge.evolution.audit_v2 import (
    AuditStore,
    EvolutionAuditRecord,
)
from caseos.knowledge.evolution.contracts.change_type import (
    EvolutionChangeType,
)
from caseos.knowledge.evolution.versioning import (
    KnowledgeVersion,
    VersionStore,
)
from caseos.knowledge.evolution.writer import (
    KnowledgeObjectWriter,
    WriteError,
    WriteRequest,
    WriteResult,
    WriterValidationResult,
    WriterValidator,
    generate_writer_report,
)
from caseos.knowledge.object import (
    KnowledgeObject,
    KnowledgeObjectValidator,
)


NOW_ISO = "2026-08-04T00:00:00Z"
KO_ID = "ko-writer-test"


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------


def _make_knowledge_object(**overrides) -> KnowledgeObject:
    base = dict(
        knowledge_id=KO_ID,
        version=1,
        title="Forest kindergarten",
        description="A nature-based preschool design",
        category="education",
        project_type="kindergarten",
        site_type="suburban",
        location_type="outdoor",
        space_size="500sqm",
        theme="forest",
        style="scandinavian",
        color_system="earth-tones",
        interaction_type="exploratory",
        function_tags=["nature", "play"],
        image_refs=[],
        document_refs=[],
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
        source="operator",
    )
    base.update(overrides)
    return KnowledgeObject(**base)


@pytest.fixture
def ko_v1() -> KnowledgeObject:
    return _make_knowledge_object()


@pytest.fixture
def version_store(ko_v1: KnowledgeObject) -> VersionStore:
    store = VersionStore()
    baseline = KnowledgeVersion(
        version_id="ver-baseline-1",
        target_identity=KO_ID,
        version_number=1,
        previous_version=None,
        snapshot=ko_v1.to_dict(),
        created_at=datetime.now(timezone.utc),
        created_by="system",
        change_reason="initial bootstrap",
        proposal_id="",
    )
    store.append(baseline)
    return store


@pytest.fixture
def audit_store() -> AuditStore:
    return AuditStore()


def _make_write_request(
    *,
    before_snapshot=None,
    new_snapshot=None,
    before_version=1,
    target_identity=KO_ID,
    change_type=EvolutionChangeType.BOUNDARY_UPDATE,
    reviewer="alice",
    change_reason="writer-test change",
    proposal_id="prop-1",
    transaction_id="tx-1",
    write_id="wrt-1",
    change_intent_id="ci-1",
) -> WriteRequest:
    if before_snapshot is None:
        before_snapshot = _make_knowledge_object().to_dict()
    if new_snapshot is None:
        new_snapshot = copy.deepcopy(before_snapshot)
        new_snapshot["version"] = before_version + 1
        new_snapshot["category"] = "commercial"
    return WriteRequest(
        write_id=write_id,
        transaction_id=transaction_id,
        proposal_id=proposal_id,
        change_intent_id=change_intent_id,
        target_identity=target_identity,
        change_type=change_type,
        before_version=before_version,
        before_snapshot=before_snapshot,
        new_snapshot=new_snapshot,
        reviewer=reviewer,
        change_reason=change_reason,
    )


# ---------------------------------------------------------------------
# Test 1 -- Frozen contracts
# ---------------------------------------------------------------------


class TestFrozenContracts:

    def test_write_request_is_frozen(self) -> None:
        req = _make_write_request()
        with pytest.raises(dataclasses.FrozenInstanceError):
            req.write_id = "mutated"  # type: ignore[misc]

    def test_write_result_is_frozen(self, version_store, audit_store) -> None:
        req = _make_write_request()
        result = KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.success = False  # type: ignore[misc]

    def test_validation_result_is_frozen(self) -> None:
        vr = WriterValidationResult(valid=True, errors=())
        with pytest.raises(dataclasses.FrozenInstanceError):
            vr.valid = False  # type: ignore[misc]


# ---------------------------------------------------------------------
# Test 2 -- JSON safety
# ---------------------------------------------------------------------


class TestJSONSafety:

    def test_write_request_round_trip(self) -> None:
        req = _make_write_request()
        d = req.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        assert decoded["write_id"] == req.write_id
        assert decoded["transaction_id"] == req.transaction_id
        assert decoded["change_type"] in {
            EvolutionChangeType.BOUNDARY_UPDATE.value,
            EvolutionChangeType.PRINCIPLE_UPDATE.value,
            EvolutionChangeType.APPLICABILITY_UPDATE.value,
        }

    def test_write_result_round_trip(self, version_store, audit_store) -> None:
        req = _make_write_request()
        result = KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        d = result.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        assert decoded["success"] is True
        assert decoded["mutation_executed"] is True
        assert decoded["new_version"] == 2


# ---------------------------------------------------------------------
# Test 3 -- Deep-copy isolation
# ---------------------------------------------------------------------


class TestDeepCopyIsolation:

    def test_before_snapshot_is_not_mutated(self) -> None:
        before_snapshot = _make_knowledge_object().to_dict()
        snapshot_copy = copy.deepcopy(before_snapshot)
        req = _make_write_request(before_snapshot=before_snapshot)
        # Mutating the original after construction must not
        # change the request.
        before_snapshot["category"] = "MUTATED"
        assert req.before_snapshot == snapshot_copy

    def test_new_snapshot_is_not_mutated(self) -> None:
        new_snapshot = _make_knowledge_object().to_dict()
        new_snapshot["version"] = 2
        new_snapshot["category"] = "commercial"
        snapshot_copy = copy.deepcopy(new_snapshot)
        req = _make_write_request(new_snapshot=new_snapshot)
        new_snapshot["category"] = "MUTATED"
        assert req.new_snapshot == snapshot_copy


# ---------------------------------------------------------------------
# Test 4 -- WriterValidator
# ---------------------------------------------------------------------


class TestWriterValidator:

    def test_valid_request_passes(self) -> None:
        validator = WriterValidator()
        req = _make_write_request()
        result = validator.validate(req)
        assert result.valid is True
        assert result.errors == ()

    def test_none_request_rejected(self) -> None:
        validator = WriterValidator()
        result = validator.validate(None)  # type: ignore[arg-type]
        assert result.valid is False

    def test_invalid_target_version_rejected(self) -> None:
        validator = WriterValidator()
        req = _make_write_request(before_version=0)
        result = validator.validate(req)
        assert result.valid is False
        assert any("before_version" in e for e in result.errors)

    def test_invalid_change_type_rejected(self) -> None:
        validator = WriterValidator()
        req = _make_write_request(change_type="nonsense")
        result = validator.validate(req)
        assert result.valid is False
        assert any("change_type" in e for e in result.errors)

    def test_empty_reviewer_rejected(self) -> None:
        validator = WriterValidator()
        req = _make_write_request(reviewer="")
        result = validator.validate(req)
        assert result.valid is False
        assert any("reviewer" in e for e in result.errors)

    def test_empty_change_reason_rejected(self) -> None:
        validator = WriterValidator()
        req = _make_write_request(change_reason="")
        result = validator.validate(req)
        assert result.valid is False
        assert any("change_reason" in e for e in result.errors)

    def test_version_must_be_before_plus_one(self) -> None:
        validator = WriterValidator()
        # new_snapshot.version must equal before_version + 1
        before_snapshot = _make_knowledge_object().to_dict()
        new_snapshot = copy.deepcopy(before_snapshot)
        new_snapshot["version"] = 99  # wrong
        req = _make_write_request(
            before_snapshot=before_snapshot,
            new_snapshot=new_snapshot,
        )
        result = validator.validate(req)
        assert result.valid is False
        assert any("before_version + 1" in e or "version" in e
                   for e in result.errors)

    def test_knowledge_id_must_match(self) -> None:
        validator = WriterValidator()
        before_snapshot = _make_knowledge_object().to_dict()
        new_snapshot = copy.deepcopy(before_snapshot)
        new_snapshot["version"] = 2
        new_snapshot["knowledge_id"] = "different"
        req = _make_write_request(
            before_snapshot=before_snapshot,
            new_snapshot=new_snapshot,
        )
        result = validator.validate(req)
        assert result.valid is False
        assert any("knowledge_id" in e for e in result.errors)

    def test_empty_write_rejected(self) -> None:
        validator = WriterValidator()
        snapshot = _make_knowledge_object().to_dict()
        req = _make_write_request(
            before_snapshot=snapshot,
            new_snapshot=snapshot,
        )
        result = validator.validate(req)
        assert result.valid is False
        assert any("must differ" in e for e in result.errors)

    def test_empty_before_snapshot_rejected(self) -> None:
        validator = WriterValidator()
        req = _make_write_request(before_snapshot={})
        result = validator.validate(req)
        assert result.valid is False

    def test_empty_new_snapshot_rejected(self) -> None:
        validator = WriterValidator()
        req = _make_write_request(new_snapshot={})
        result = validator.validate(req)
        assert result.valid is False


# ---------------------------------------------------------------------
# Test 5 -- Happy path
# ---------------------------------------------------------------------


class TestHappyPath:

    def test_write_appends_new_version(
        self, version_store, audit_store,
    ) -> None:
        req = _make_write_request()
        result = KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert result.success is True
        assert result.new_version == 2
        assert result.version_id is not None
        assert result.audit_id is not None
        assert result.version_appended is True
        assert result.audit_appended is True
        assert result.mutation_executed is True

    def test_write_appends_audit_record(
        self, version_store, audit_store,
    ) -> None:
        req = _make_write_request()
        result = KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert result.success is True
        # The audit_store should now have exactly one record
        # for KO_ID, with the correct before/after.
        history = audit_store.history(KO_ID)
        assert len(history) == 1
        record = history[0]
        assert record.target_identity == KO_ID
        assert record.previous_version == 1
        assert record.new_version == 2
        assert record.audit_id == result.audit_id
        assert record.before_snapshot == req.before_snapshot
        assert record.after_snapshot == req.new_snapshot

    def test_write_appends_knowledge_version_with_previous(
        self, version_store, audit_store,
    ) -> None:
        req = _make_write_request()
        result = KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        history = version_store.history(KO_ID)
        assert len(history) == 2  # baseline + new
        new_v = history[-1]
        assert new_v.version_number == 2
        assert new_v.previous_version == 1
        assert new_v.version_id == result.version_id


# ---------------------------------------------------------------------
# Test 6 -- Append-only contract
# ---------------------------------------------------------------------


class TestAppendOnly:

    def test_existing_versions_unchanged_after_write(
        self, version_store, audit_store,
    ) -> None:
        # Snapshot the existing baseline.
        baseline = version_store.get(KO_ID)
        assert baseline is not None
        baseline_snapshot = baseline.snapshot
        baseline_version_id = baseline.version_id

        req = _make_write_request()
        KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )

        # The baseline record must be the same instance and
        # its snapshot must be unchanged.
        baseline_after = version_store.get(KO_ID + "_v1")
        # (The store.get returns the LATEST, not the baseline.
        # Use history instead.)
        history = version_store.history(KO_ID)
        baseline_after = history[0]
        assert baseline_after.version_id == baseline_version_id
        assert baseline_after.snapshot == baseline_snapshot

    def test_version_store_count_increments(
        self, version_store, audit_store,
    ) -> None:
        before_count = version_store.count()
        req = _make_write_request()
        KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert version_store.count() == before_count + 1

    def test_audit_store_count_increments(
        self, version_store, audit_store,
    ) -> None:
        before_count = audit_store.count()
        req = _make_write_request()
        KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert audit_store.count() == before_count + 1


# ---------------------------------------------------------------------
# Test 7 -- Failure semantics
# ---------------------------------------------------------------------


class TestFailure:

    def test_no_prior_history_rejected(self, audit_store) -> None:
        # Empty store: writer must refuse (no bootstrap).
        empty_store = VersionStore()
        req = _make_write_request()
        result = KnowledgeObjectWriter().write(
            req,
            version_store=empty_store,
            audit_store=audit_store,
        )
        assert result.success is False
        assert result.version_appended is False
        assert result.audit_appended is False
        assert result.mutation_executed is False
        assert "no prior KnowledgeVersion" in result.rejection_reason

    def test_before_version_mismatch_rejected(
        self, version_store, audit_store,
    ) -> None:
        # Pretend the writer is asked to mutate from version
        # 5 even though the latest is 1.
        req = _make_write_request(before_version=5)
        result = KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert result.success is False
        assert "does not match" in result.rejection_reason
        # Neither store must be touched on rejection.
        assert version_store.count() == 1  # only baseline
        assert audit_store.count() == 0

    def test_invalid_request_rejected(
        self, version_store, audit_store,
    ) -> None:
        req = _make_write_request(reviewer="")
        result = KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert result.success is False
        assert result.mutation_executed is False
        # Neither store must be touched.
        assert version_store.count() == 1
        assert audit_store.count() == 0

    def test_ko_incompatible_snapshot_rejected(
        self, version_store, audit_store,
    ) -> None:
        # Craft a new_snapshot that fails KnowledgeObjectValidator.
        before_snapshot = _make_knowledge_object().to_dict()
        new_snapshot = copy.deepcopy(before_snapshot)
        new_snapshot["version"] = 2
        new_snapshot["knowledge_id"] = KO_ID
        new_snapshot["title"] = 123  # wrong type
        req = _make_write_request(
            before_snapshot=before_snapshot,
            new_snapshot=new_snapshot,
        )
        result = KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert result.success is False
        assert "KnowledgeObjectValidator" in result.rejection_reason
        # Stores untouched.
        assert version_store.count() == 1
        assert audit_store.count() == 0


# ---------------------------------------------------------------------
# Test 8 -- Input immutability
# ---------------------------------------------------------------------


class TestInputImmutability:

    def test_write_request_is_not_mutated(
        self, version_store, audit_store,
    ) -> None:
        req = _make_write_request()
        snapshot_id_before = id(req.before_snapshot)
        KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert id(req.before_snapshot) == snapshot_id_before
        assert req.write_id == "wrt-1"

    def test_input_dict_is_not_mutated(
        self, version_store, audit_store,
    ) -> None:
        before_snapshot = _make_knowledge_object().to_dict()
        new_snapshot = copy.deepcopy(before_snapshot)
        new_snapshot["version"] = 2
        new_snapshot["category"] = "commercial"
        before_copy = copy.deepcopy(before_snapshot)
        new_copy = copy.deepcopy(new_snapshot)
        req = _make_write_request(
            before_snapshot=before_snapshot,
            new_snapshot=new_snapshot,
        )
        KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert before_snapshot == before_copy
        assert new_snapshot == new_copy


# ---------------------------------------------------------------------
# Test 9 -- Audit before/after isolation
# ---------------------------------------------------------------------


class TestAuditIsolation:

    def test_audit_snapshot_isolated_from_input(
        self, version_store, audit_store,
    ) -> None:
        before_snapshot = _make_knowledge_object().to_dict()
        new_snapshot = copy.deepcopy(before_snapshot)
        new_snapshot["version"] = 2
        new_snapshot["category"] = "commercial"

        req = _make_write_request(
            before_snapshot=before_snapshot,
            new_snapshot=new_snapshot,
        )
        result = KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert result.success is True
        # Now mutate the original dicts.
        before_snapshot["category"] = "MUTATED"
        new_snapshot["category"] = "ALSO_MUTATED"
        # The audit record must still report the originals.
        record = audit_store.get(result.audit_id)
        assert record is not None
        assert record.before_snapshot["category"] == "education"
        assert record.after_snapshot["category"] == "commercial"


# ---------------------------------------------------------------------
# Test 10 -- End-to-end with Adapter
# ---------------------------------------------------------------------


class TestEndToEndWithAdapter:

    def test_adapter_then_writer_round_trip(
        self, version_store, audit_store,
    ) -> None:
        ko = _make_knowledge_object()
        adapter_req = AdapterRequest(
            request_id="adp-1",
            transaction_id="tx-1",
            change_intent_id="ci-1",
            target_identity=KO_ID,
            target_version=1,
            change_type=EvolutionChangeType.BOUNDARY_UPDATE,
            before_snapshot=ko.to_dict(),
            requested_change="commercial",
            reviewer="alice",
        )
        adapter_result = KnowledgeObjectAdapter().adapt(adapter_req)
        assert adapter_result.success is True

        write_req = WriteRequest(
            write_id="wrt-1",
            transaction_id="tx-1",
            proposal_id="prop-1",
            change_intent_id="ci-1",
            target_identity=KO_ID,
            change_type=EvolutionChangeType.BOUNDARY_UPDATE,
            before_version=1,
            before_snapshot=ko.to_dict(),
            new_snapshot=adapter_result.new_snapshot,
            reviewer="alice",
            change_reason="boundary update",
        )
        write_result = KnowledgeObjectWriter().write(
            write_req,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert write_result.success is True
        assert write_result.new_version == 2
        assert version_store.count() == 2
        assert audit_store.count() == 1


# ---------------------------------------------------------------------
# Test 11 -- Report
# ---------------------------------------------------------------------


class TestReport:

    def test_report_on_success(self, version_store, audit_store) -> None:
        req = _make_write_request()
        result = KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        report = generate_writer_report(result)
        assert "Knowledge Object Evolution Writer Report" in report
        assert "## Write Request" in report
        assert "## Store Appends" in report
        assert "## Audit Record" in report
        assert "## Mutation Status" in report
        assert "## Safety Boundary" in report
        assert "APPENDED to VersionStore + AuditStore" in report
        assert "NOT EXECUTED" not in report.split("## Safety Boundary")[1]

    def test_report_on_rejection(self, audit_store) -> None:
        empty_store = VersionStore()
        req = _make_write_request()
        result = KnowledgeObjectWriter().write(
            req,
            version_store=empty_store,
            audit_store=audit_store,
        )
        report = generate_writer_report(result)
        assert "NOT EXECUTED" in report
        assert result.success is False


# ---------------------------------------------------------------------
# Test 12 -- Architecture boundary
# ---------------------------------------------------------------------


class TestArchitectureBoundary:

    def test_writer_module_no_forbidden_imports(self) -> None:
        writer_dir = (
            pathlib.Path(__file__).resolve().parents[1]
            / "caseos"
            / "knowledge"
            / "evolution"
            / "writer"
        )
        forbidden_substrings = (
            "caseos.intelligence.decision",
            "caseos.intelligence.trust",
            "caseos.intelligence.recommendation",
            "caseos.knowledge.retrieval",
        )
        for py in sorted(writer_dir.glob("*.py")):
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

    def test_writer_does_not_overwrite_stores(
        self, version_store, audit_store,
    ) -> None:
        # The writer's public API must not expose
        # overwrite/update/delete/clear methods.
        writer = KnowledgeObjectWriter()
        forbidden_attrs = (
            "update", "delete", "overwrite", "clear",
            "rollback", "restore", "mutate_ko", "apply",
        )
        for attr in forbidden_attrs:
            assert not hasattr(writer, attr), (
                "KnowledgeObjectWriter unexpectedly exposes '"
                + attr + "'"
            )

    def test_writer_does_not_import_mutation_engine(self) -> None:
        writer_dir = (
            pathlib.Path(__file__).resolve().parents[1]
            / "caseos"
            / "knowledge"
            / "evolution"
            / "writer"
        )
        for py in sorted(writer_dir.glob("*.py")):
            src = py.read_text(encoding="utf-8-sig")
            assert "mutation.engine" not in src
            assert "KnowledgeMutationEngine" not in src


# ---------------------------------------------------------------------
# Test 13 -- Stores untouched on rejection
# ---------------------------------------------------------------------


class TestStoresUntouchedOnRejection:

    def test_no_audit_on_rejection(
        self, version_store, audit_store,
    ) -> None:
        req = _make_write_request(reviewer="")
        before_count = audit_store.count()
        KnowledgeObjectWriter().write(
            req,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert audit_store.count() == before_count

    def test_no_version_on_rejection(
        self, version_store, audit_store,
    ) -> None:
        empty_store = VersionStore()
        before_count = version_store.count()
        req = _make_write_request()
        KnowledgeObjectWriter().write(
            req,
            version_store=empty_store,
            audit_store=audit_store,
        )
        assert version_store.count() == before_count
