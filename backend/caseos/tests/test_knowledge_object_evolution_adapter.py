"""Knowledge Object Evolution Adapter V1 tests (Sprint 23.0-B).

Test scope:

    * AdapterRequest / AdapterResult / FieldMapping
      (frozen, JSON-safe, deep-copy isolation)
    * Mapping table covers the V1 allow-list
    * AdapterValidator collects every rule failure
    * KnowledgeObjectAdapter happy path for every allowed
      change_type
    * Adapter rejects unknown change types
    * Adapter rejects missing requested_change
    * Adapter does NOT mutate input
    * mutation_executed is always False
    * next_version == before_version + 1 on success
    * Output snapshot round-trips through KnowledgeObject
    * Architecture boundary (AST scan)
    * Knowledge mutation never happens (audit-friendly)

Out of scope:

    * Pipeline wiring
    * Intelligence / Retrieval
    * KnowledgeMutationEngine (the adapter is a separate
      candidate-only layer)
"""
from __future__ import annotations

import ast
import dataclasses
import json
import pathlib
from datetime import datetime, timezone

import pytest

from caseos.knowledge.evolution.adapter import (
    AdapterError,
    AdapterRequest,
    AdapterResult,
    AdapterValidationResult,
    AdapterValidator,
    CHANGE_TYPE_TO_KO_FIELD,
    FieldMapping,
    KnowledgeObjectAdapter,
    V1_MAPPING_NOTE,
    generate_adapter_report,
    resolve_target_field,
)
from caseos.knowledge.evolution.contracts.change_type import (
    EvolutionChangeType,
)
from caseos.knowledge.object import (
    KnowledgeObject,
    KnowledgeObjectValidator,
)


NOW_ISO = "2026-08-04T00:00:00Z"
KO_ID = "ko-adapter-1"


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
        image_refs=["img/forest-1.jpg"],
        document_refs=["docs/brief.pdf"],
        created_at=NOW_ISO,
        updated_at=NOW_ISO,
        source="operator",
    )
    base.update(overrides)
    return KnowledgeObject(**base)


def _make_adapter_request(
    *,
    change_type=EvolutionChangeType.BOUNDARY_UPDATE,
    before_snapshot=None,
    requested_change="commercial",
    reviewer="alice",
    target_identity=KO_ID,
    target_version=1,
) -> AdapterRequest:
    if before_snapshot is None:
        ko = _make_knowledge_object()
        before_snapshot = ko.to_dict()
    return AdapterRequest(
        request_id="adp-test-1",
        transaction_id="tx-test-1",
        change_intent_id="ci-test-1",
        target_identity=target_identity,
        target_version=target_version,
        change_type=change_type,
        before_snapshot=before_snapshot,
        requested_change=requested_change,
        reviewer=reviewer,
    )


# ---------------------------------------------------------------------
# Test 1 -- Frozen contracts
# ---------------------------------------------------------------------


class TestFrozenContracts:

    def test_adapter_request_is_frozen(self) -> None:
        req = _make_adapter_request()
        with pytest.raises(dataclasses.FrozenInstanceError):
            req.request_id = "mutated"  # type: ignore[misc]

    def test_adapter_result_is_frozen(self) -> None:
        ko = _make_knowledge_object()
        req = _make_adapter_request(before_snapshot=ko.to_dict())
        result = KnowledgeObjectAdapter().adapt(req)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.success = False  # type: ignore[misc]

    def test_field_mapping_is_frozen(self) -> None:
        fm = FieldMapping(
            change_type=EvolutionChangeType.BOUNDARY_UPDATE,
            requested_target_field="boundary",
            resolved_target_field="category",
            applied=True,
            note="x",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            fm.applied = False  # type: ignore[misc]

    def test_validation_result_is_frozen(self) -> None:
        vr = AdapterValidationResult(valid=True, errors=())
        with pytest.raises(dataclasses.FrozenInstanceError):
            vr.valid = False  # type: ignore[misc]


# ---------------------------------------------------------------------
# Test 2 -- JSON safety
# ---------------------------------------------------------------------


class TestJSONSafety:

    def test_adapter_request_round_trip(self) -> None:
        req = _make_adapter_request()
        d = req.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        # The serialised shape is JSON-safe (no datetime,
        # no enum). We do NOT rehydrate back into a
        # AdapterRequest; we just confirm the wire format
        # is valid JSON.
        assert decoded["request_id"] == req.request_id
        assert decoded["transaction_id"] == req.transaction_id
        assert decoded["change_type"] in {
            EvolutionChangeType.BOUNDARY_UPDATE.value,
            EvolutionChangeType.PRINCIPLE_UPDATE.value,
            EvolutionChangeType.APPLICABILITY_UPDATE.value,
        }

    def test_adapter_result_round_trip(self) -> None:
        req = _make_adapter_request()
        result = KnowledgeObjectAdapter().adapt(req)
        d = result.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        assert decoded["success"] is True
        assert decoded["mutation_executed"] is False
        assert decoded["next_version"] == 2


# ---------------------------------------------------------------------
# Test 3 -- Mapping table coverage
# ---------------------------------------------------------------------


class TestMappingTable:

    def test_mapping_table_covers_all_allowed_change_types(self) -> None:
        allowed = {
            EvolutionChangeType.BOUNDARY_UPDATE,
            EvolutionChangeType.PRINCIPLE_UPDATE,
            EvolutionChangeType.APPLICABILITY_UPDATE,
        }
        assert set(CHANGE_TYPE_TO_KO_FIELD.keys()) == allowed

    def test_mapping_table_targets_existing_ko_fields(self) -> None:
        from caseos.knowledge.object.schema import REQUIRED_FIELDS
        for ct, field_name in CHANGE_TYPE_TO_KO_FIELD.items():
            assert field_name in REQUIRED_FIELDS, (
                "mapping for " + str(ct)
                + " targets '" + field_name
                + "' which is not in KnowledgeObject V1 REQUIRED_FIELDS"
            )

    def test_resolve_target_field(self) -> None:
        assert resolve_target_field(EvolutionChangeType.BOUNDARY_UPDATE) == "category"
        assert resolve_target_field(EvolutionChangeType.PRINCIPLE_UPDATE) == "theme"
        assert resolve_target_field(EvolutionChangeType.APPLICABILITY_UPDATE) == "interaction_type"

    def test_resolve_target_field_rejects_unknown(self) -> None:
        assert resolve_target_field("nonsense") is None

    def test_resolve_target_field_with_overridden_table(self) -> None:
        custom = {EvolutionChangeType.BOUNDARY_UPDATE: "style"}
        assert (
            resolve_target_field(
                EvolutionChangeType.BOUNDARY_UPDATE,
                mapping_table=custom,
            )
            == "style"
        )

    def test_v1_mapping_note_is_documented(self) -> None:
        assert V1_MAPPING_NOTE
        assert "BOUNDARY_UPDATE" in V1_MAPPING_NOTE
        assert "PRINCIPLE_UPDATE" in V1_MAPPING_NOTE
        assert "APPLICABILITY_UPDATE" in V1_MAPPING_NOTE


# ---------------------------------------------------------------------
# Test 4 -- AdapterValidator
# ---------------------------------------------------------------------


class TestAdapterValidator:

    def test_valid_request_passes(self) -> None:
        validator = AdapterValidator()
        req = _make_adapter_request()
        result = validator.validate(req)
        assert result.valid is True
        assert result.errors == ()

    def test_none_request_rejected(self) -> None:
        validator = AdapterValidator()
        result = validator.validate(None)  # type: ignore[arg-type]
        assert result.valid is False

    def test_invalid_target_version_rejected(self) -> None:
        validator = AdapterValidator()
        req = _make_adapter_request(target_version=0)
        result = validator.validate(req)
        assert result.valid is False
        assert any("target_version" in e for e in result.errors)

    def test_invalid_change_type_rejected(self) -> None:
        validator = AdapterValidator()
        req = _make_adapter_request(change_type="nonsense")
        result = validator.validate(req)
        assert result.valid is False
        assert any("change_type" in e for e in result.errors)

    def test_empty_reviewer_rejected(self) -> None:
        validator = AdapterValidator()
        req = _make_adapter_request(reviewer="")
        result = validator.validate(req)
        assert result.valid is False
        assert any("reviewer" in e for e in result.errors)

    def test_empty_before_snapshot_rejected(self) -> None:
        validator = AdapterValidator()
        req = _make_adapter_request(before_snapshot={})
        result = validator.validate(req)
        assert result.valid is False
        assert any("before_snapshot" in e for e in result.errors)

    def test_non_string_requested_change_rejected(self) -> None:
        validator = AdapterValidator()
        req = _make_adapter_request(requested_change=123)  # type: ignore[arg-type]
        result = validator.validate(req)
        assert result.valid is False
        assert any("requested_change" in e for e in result.errors)


# ---------------------------------------------------------------------
# Test 5 -- Happy path for every allowed change_type
# ---------------------------------------------------------------------


class TestHappyPath:

    def test_boundary_update_maps_to_category(self) -> None:
        req = _make_adapter_request(
            change_type=EvolutionChangeType.BOUNDARY_UPDATE,
            requested_change="commercial",
        )
        result = KnowledgeObjectAdapter().adapt(req)
        assert result.success is True
        assert result.mapping is not None
        assert result.mapping.resolved_target_field == "category"
        assert result.new_snapshot is not None
        assert result.new_snapshot["category"] == "commercial"
        assert result.next_version == 2
        assert result.mutation_executed is False

    def test_principle_update_maps_to_theme(self) -> None:
        req = _make_adapter_request(
            change_type=EvolutionChangeType.PRINCIPLE_UPDATE,
            requested_change="ocean",
        )
        result = KnowledgeObjectAdapter().adapt(req)
        assert result.success is True
        assert result.mapping is not None
        assert result.mapping.resolved_target_field == "theme"
        assert result.new_snapshot is not None
        assert result.new_snapshot["theme"] == "ocean"

    def test_applicability_update_maps_to_interaction_type(self) -> None:
        req = _make_adapter_request(
            change_type=EvolutionChangeType.APPLICABILITY_UPDATE,
            requested_change="guided",
        )
        result = KnowledgeObjectAdapter().adapt(req)
        assert result.success is True
        assert result.mapping is not None
        assert result.mapping.resolved_target_field == "interaction_type"
        assert result.new_snapshot is not None
        assert result.new_snapshot["interaction_type"] == "guided"


# ---------------------------------------------------------------------
# Test 6 -- Failure semantics
# ---------------------------------------------------------------------


class TestFailure:

    def test_unknown_change_type_rejected(self) -> None:
        adapter = KnowledgeObjectAdapter(
            mapping_table={},  # empty table -> nothing maps
        )
        req = _make_adapter_request(
            change_type=EvolutionChangeType.BOUNDARY_UPDATE,
        )
        result = adapter.adapt(req)
        assert result.success is False
        assert result.new_snapshot is None
        assert "no mapping" in result.rejection_reason
        assert result.mutation_executed is False

    def test_missing_requested_change_rejected(self) -> None:
        req = _make_adapter_request(
            requested_change=None,  # type: ignore[arg-type]
        )
        result = KnowledgeObjectAdapter().adapt(req)
        assert result.success is False
        assert result.new_snapshot is None
        assert result.mutation_executed is False

    def test_rejection_result_is_frozen(self) -> None:
        req = _make_adapter_request(requested_change=None)  # type: ignore[arg-type]
        result = KnowledgeObjectAdapter().adapt(req)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.rejection_reason = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------
# Test 7 -- Immutability of input
# ---------------------------------------------------------------------


class TestInputImmutability:

    def test_before_snapshot_is_not_mutated(self) -> None:
        ko = _make_knowledge_object()
        snapshot = ko.to_dict()
        snapshot_copy = json.loads(json.dumps(snapshot))
        req = _make_adapter_request(
            change_type=EvolutionChangeType.BOUNDARY_UPDATE,
            before_snapshot=snapshot,
            requested_change="commercial",
        )
        KnowledgeObjectAdapter().adapt(req)
        # Snapshot must be unchanged after the adapter ran.
        assert snapshot == snapshot_copy

    def test_adapter_request_is_not_mutated(self) -> None:
        req = _make_adapter_request(
            change_type=EvolutionChangeType.BOUNDARY_UPDATE,
            requested_change="commercial",
        )
        snapshot_id_before = id(req.before_snapshot)
        KnowledgeObjectAdapter().adapt(req)
        assert id(req.before_snapshot) == snapshot_id_before
        assert req.request_id == "adp-test-1"


# ---------------------------------------------------------------------
# Test 8 -- Output integrity (round-trips through KnowledgeObject)
# ---------------------------------------------------------------------


class TestOutputIntegrity:

    def test_output_snapshot_round_trips_through_ko(self) -> None:
        for ct, expected_field in (
            (EvolutionChangeType.BOUNDARY_UPDATE, "category"),
            (EvolutionChangeType.PRINCIPLE_UPDATE, "theme"),
            (EvolutionChangeType.APPLICABILITY_UPDATE, "interaction_type"),
        ):
            req = _make_adapter_request(
                change_type=ct,
                requested_change="new-value-for-" + expected_field,
            )
            result = KnowledgeObjectAdapter().adapt(req)
            assert result.success is True
            assert result.new_snapshot is not None
            candidate = KnowledgeObject.from_dict(result.new_snapshot)
            validator = KnowledgeObjectValidator()
            validation = validator.validate(candidate)
            assert validation.valid is True, (
                "Adapter output for " + str(ct)
                + " failed KO validation: " + str(validation.errors)
            )

    def test_output_snapshot_passes_validator(self) -> None:
        req = _make_adapter_request(
            change_type=EvolutionChangeType.PRINCIPLE_UPDATE,
            requested_change="industrial",
        )
        result = KnowledgeObjectAdapter().adapt(req)
        candidate = KnowledgeObject.from_dict(result.new_snapshot)
        validation = KnowledgeObjectValidator().validate(candidate)
        assert validation.valid is True


# ---------------------------------------------------------------------
# Test 9 -- Mutation invariant (the adapter never executes mutation)
# ---------------------------------------------------------------------


class TestMutationInvariant:

    def test_mutation_executed_is_always_false(self) -> None:
        # happy path
        req = _make_adapter_request()
        result = KnowledgeObjectAdapter().adapt(req)
        assert result.mutation_executed is False

    def test_mutation_executed_false_on_rejection(self) -> None:
        req = _make_adapter_request(requested_change=None)  # type: ignore[arg-type]
        result = KnowledgeObjectAdapter().adapt(req)
        assert result.mutation_executed is False

    def test_no_version_store_or_audit_store_touched(self) -> None:
        # The adapter must accept no store arguments; the
        # constructor signature must not expose them.
        adapter = KnowledgeObjectAdapter()
        assert not hasattr(adapter, "version_store")
        assert not hasattr(adapter, "audit_store")
        assert not hasattr(adapter, "apply")
        assert not hasattr(adapter, "execute")
        assert not hasattr(adapter, "mutate")
        assert not hasattr(adapter, "commit")


# ---------------------------------------------------------------------
# Test 10 -- Report
# ---------------------------------------------------------------------


class TestReport:

    def test_report_marks_mutation_not_executed(self) -> None:
        req = _make_adapter_request()
        result = KnowledgeObjectAdapter().adapt(req)
        report = generate_adapter_report(result)
        assert "Knowledge Object Evolution Adapter Report" in report
        assert "NOT EXECUTED" in report
        assert "## Mapping Decision" in report
        assert "## Output Snapshot" in report
        assert "## Safety Boundary" in report
        assert "## Architecture Boundary" in report

    def test_report_for_rejection(self) -> None:
        req = _make_adapter_request(requested_change=None)  # type: ignore[arg-type]
        result = KnowledgeObjectAdapter().adapt(req)
        report = generate_adapter_report(result)
        assert "NOT EXECUTED" in report


# ---------------------------------------------------------------------
# Test 11 -- Architecture boundary (AST scan)
# ---------------------------------------------------------------------


class TestArchitectureBoundary:

    def test_adapter_module_no_forbidden_imports(self) -> None:
        adapter_dir = (
            pathlib.Path(__file__).resolve().parents[1]
            / "caseos"
            / "knowledge"
            / "evolution"
            / "adapter"
        )
        forbidden_substrings = (
            "caseos.intelligence.decision",
            "caseos.intelligence.trust",
            "caseos.intelligence.recommendation",
            "caseos.knowledge.retrieval",
        )
        for py in sorted(adapter_dir.glob("*.py")):
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

    def test_adapter_does_not_depend_on_mutation_engine(self) -> None:
        adapter_dir = (
            pathlib.Path(__file__).resolve().parents[1]
            / "caseos"
            / "knowledge"
            / "evolution"
            / "adapter"
        )
        for py in sorted(adapter_dir.glob("*.py")):
            src = py.read_text(encoding="utf-8-sig")
            assert "mutation.engine" not in src, (
                py.name + " imports mutation.engine; "
                "the adapter must remain a separate layer."
            )
            assert "KnowledgeMutationEngine" not in src, (
                py.name + " references KnowledgeMutationEngine; "
                "the adapter must remain a separate layer."
            )


# ---------------------------------------------------------------------
# Test 12 -- Optional override behaviour
# ---------------------------------------------------------------------


class TestOverride:

    def test_custom_mapping_table_is_used(self) -> None:
        custom = {EvolutionChangeType.BOUNDARY_UPDATE: "style"}
        adapter = KnowledgeObjectAdapter(mapping_table=custom)
        req = _make_adapter_request(
            change_type=EvolutionChangeType.BOUNDARY_UPDATE,
            requested_change="modern",
        )
        result = adapter.adapt(req)
        assert result.success is True
        assert result.mapping is not None
        assert result.mapping.resolved_target_field == "style"
        assert result.new_snapshot is not None
        assert result.new_snapshot["style"] == "modern"

    def test_request_id_is_propagated(self) -> None:
        req = _make_adapter_request()
        req = dataclasses.replace(req, request_id="adp-special")
        result = KnowledgeObjectAdapter().adapt(req)
        assert result.request_id == "adp-special"

    def test_transaction_id_is_propagated(self) -> None:
        req = _make_adapter_request()
        req = dataclasses.replace(req, transaction_id="tx-special")
        result = KnowledgeObjectAdapter().adapt(req)
        assert result.transaction_id == "tx-special"
