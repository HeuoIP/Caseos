"""Tests for the Knowledge Evolution Transaction Foundation (Sprint 22.4-A).

Coverage per Sprint 22.4-A spec section "Required Tests":

    Test 1   EvolutionTransaction fields complete
    Test 2   EvolutionTransaction frozen
    Test 3   JSON serialization
    Test 4   Lifecycle: CREATED -> VALIDATING -> APPROVED
    Test 5   Illegal transitions rejected
    Test 6   Validator: missing proposal_id -> reject
    Test 7   Validator: missing reviewer -> reject
    Test 8   Validator: missing before_snapshot -> reject
    Test 9   APPLIED status forbidden
    Test 10  Audit append-only
    Test 11  AST architecture boundary (5 evolution modules)

Plus auxiliary invariants: 12 fields, status enum, validator on
None, audit store methods, report sections, report contains
"NOT EXECUTED" marker.
"""
from __future__ import annotations

import ast
import dataclasses
import json
import uuid
from pathlib import Path

_UNSET = object()

import pytest

from caseos.knowledge.evolution import (
    ALLOWED_TRANSITIONS,
    EvolutionAuditError,
    EvolutionAuditRecord,
    EvolutionAuditStore,
    EvolutionStatus,
    EvolutionTransaction,
    EvolutionValidator,
    ValidationResult,
    generate_report,
    is_valid_transition,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
EVOLUTION_DIR = BACKEND / "caseos" / "knowledge" / "evolution"


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

def _make_transaction(
    *,
    transaction_id: str = "tx-1",
    proposal_id: str = "p-1",
    change_intent_id: str = "i-1",
    target_identity: str = "KO-1",
    target_version: int = 2,
    change_type: str = "boundary_update",
    before_snapshot=_UNSET,
    requested_change: str | None = "refine boundary",
    reviewer: str = "alice",
    status: str = EvolutionStatus.CREATED,
) -> EvolutionTransaction:
    if before_snapshot is _UNSET:
        before_snapshot = {
            "boundary": ["Do not add scattered equipment"],
        }
    return EvolutionTransaction(
        transaction_id=transaction_id,
        proposal_id=proposal_id,
        change_intent_id=change_intent_id,
        target_identity=target_identity,
        target_version=target_version,
        change_type=change_type,
        before_snapshot=before_snapshot,
        requested_change=requested_change,
        reviewer=reviewer,
        status=status,
    )


@pytest.fixture
def transaction() -> EvolutionTransaction:
    return _make_transaction()


@pytest.fixture
def validator() -> EvolutionValidator:
    return EvolutionValidator()


@pytest.fixture
def audit_store() -> EvolutionAuditStore:
    return EvolutionAuditStore()


# ---------------------------------------------------------------------------
# Test 1 -- EvolutionTransaction fields complete
# ---------------------------------------------------------------------------

class TestTransactionFields:

    EXPECTED_FIELDS = {
        "transaction_id", "proposal_id", "change_intent_id",
        "target_identity", "target_version", "change_type",
        "before_snapshot", "requested_change", "reviewer",
        "status", "created_at",
    }

    def test_all_eleven_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(EvolutionTransaction)}
        assert self.EXPECTED_FIELDS.issubset(actual), (
            "missing fields: "
            + str(self.EXPECTED_FIELDS - actual)
        )

    def test_field_count_is_eleven(self) -> None:
        assert len(dataclasses.fields(EvolutionTransaction)) == 11


# ---------------------------------------------------------------------------
# Test 2 -- EvolutionTransaction frozen
# ---------------------------------------------------------------------------

class TestTransactionFrozen:

    def test_mutation_raises_frozen_instance_error(self) -> None:
        tx = _make_transaction()
        with pytest.raises(dataclasses.FrozenInstanceError):
            tx.status = EvolutionStatus.APPROVED  # type: ignore[misc]

    def test_mutation_of_target_version_raises(self) -> None:
        tx = _make_transaction()
        with pytest.raises(dataclasses.FrozenInstanceError):
            tx.target_version = 99  # type: ignore[misc]

    def test_mutation_of_reviewer_raises(self) -> None:
        tx = _make_transaction()
        with pytest.raises(dataclasses.FrozenInstanceError):
            tx.reviewer = "bob"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Test 3 -- JSON serialization
# ---------------------------------------------------------------------------

class TestJsonSerialization:

    def test_to_dict_is_json_safe(self) -> None:
        tx = _make_transaction()
        encoded = json.dumps(tx.to_dict())
        decoded = json.loads(encoded)
        assert decoded["transaction_id"] == "tx-1"
        assert decoded["proposal_id"] == "p-1"
        assert decoded["target_identity"] == "KO-1"
        assert decoded["target_version"] == 2
        assert decoded["change_type"] == "boundary_update"
        assert decoded["reviewer"] == "alice"
        assert decoded["status"] == EvolutionStatus.CREATED
        assert isinstance(decoded["created_at"], str)

    def test_before_snapshot_serialised_as_dict(self) -> None:
        tx = _make_transaction()
        encoded = json.dumps(tx.to_dict())
        decoded = json.loads(encoded)
        assert isinstance(decoded["before_snapshot"], dict)
        assert "boundary" in decoded["before_snapshot"]


# ---------------------------------------------------------------------------
# Test 4 -- Lifecycle: CREATED -> VALIDATING -> APPROVED
# ---------------------------------------------------------------------------

class TestLifecycleHappyPath:

    def test_created_to_validating_allowed(self) -> None:
        assert is_valid_transition(
            EvolutionStatus.CREATED, EvolutionStatus.VALIDATING
        ) is True

    def test_validating_to_approved_allowed(self) -> None:
        assert is_valid_transition(
            EvolutionStatus.VALIDATING, EvolutionStatus.APPROVED
        ) is True

    def test_full_happy_path(self) -> None:
        # CREATED -> VALIDATING -> APPROVED
        assert is_valid_transition(
            EvolutionStatus.CREATED, EvolutionStatus.VALIDATING,
        ) is True
        assert is_valid_transition(
            EvolutionStatus.VALIDATING, EvolutionStatus.APPROVED,
        ) is True

    def test_created_to_rejected_allowed(self) -> None:
        # CREATED -> REJECTED is the sad path; also allowed.
        assert is_valid_transition(
            EvolutionStatus.CREATED, EvolutionStatus.REJECTED,
        ) is True

    def test_validating_to_rejected_allowed(self) -> None:
        # VALIDATING -> REJECTED is allowed.
        assert is_valid_transition(
            EvolutionStatus.VALIDATING, EvolutionStatus.REJECTED,
        ) is True


# ---------------------------------------------------------------------------
# Test 5 -- Illegal transitions rejected
# ---------------------------------------------------------------------------

class TestIllegalTransitions:

    @pytest.mark.parametrize("from_status,to_status", [
        (EvolutionStatus.APPROVED, EvolutionStatus.CREATED),
        (EvolutionStatus.APPROVED, EvolutionStatus.VALIDATING),
        (EvolutionStatus.APPROVED, EvolutionStatus.REJECTED),
        (EvolutionStatus.APPROVED, EvolutionStatus.APPLIED),  # V1 hard-stop
        (EvolutionStatus.REJECTED, EvolutionStatus.CREATED),
        (EvolutionStatus.REJECTED, EvolutionStatus.VALIDATING),
        (EvolutionStatus.REJECTED, EvolutionStatus.APPROVED),
        (EvolutionStatus.REJECTED, EvolutionStatus.APPLIED),
        (EvolutionStatus.CREATED, EvolutionStatus.APPROVED),
        (EvolutionStatus.CREATED, EvolutionStatus.APPLIED),
        (EvolutionStatus.VALIDATING, EvolutionStatus.CREATED),
        (EvolutionStatus.VALIDATING, EvolutionStatus.APPLIED),
    ])
    def test_transition_rejected(
        self, from_status: str, to_status: str,
    ) -> None:
        assert is_valid_transition(from_status, to_status) is False

    def test_unknown_from_status_rejected(self) -> None:
        assert is_valid_transition("UNKNOWN", EvolutionStatus.VALIDATING) is False

    def test_unknown_to_status_rejected(self) -> None:
        assert is_valid_transition(
            EvolutionStatus.CREATED, "BOGUS",
        ) is False


# ---------------------------------------------------------------------------
# Test 6 -- Validator: missing proposal_id rejected
# ---------------------------------------------------------------------------

class TestValidatorMissingProposalId:

    def test_empty_proposal_id_rejected(self, validator) -> None:
        tx = _make_transaction(proposal_id="")
        result = validator.validate(tx)
        assert result.is_valid is False
        assert result.rule == "R1"
        assert "proposal_id" in result.reason

    def test_whitespace_proposal_id_rejected(self, validator) -> None:
        tx = _make_transaction(proposal_id="   ")
        result = validator.validate(tx)
        assert result.is_valid is False
        assert result.rule == "R1"


# ---------------------------------------------------------------------------
# Test 7 -- Validator: missing reviewer rejected
# ---------------------------------------------------------------------------

class TestValidatorMissingReviewer:

    def test_empty_reviewer_rejected(self, validator) -> None:
        tx = _make_transaction(reviewer="")
        result = validator.validate(tx)
        assert result.is_valid is False
        assert result.rule == "R2"
        assert "reviewer" in result.reason

    def test_whitespace_reviewer_rejected(self, validator) -> None:
        tx = _make_transaction(reviewer="\t\n")
        result = validator.validate(tx)
        assert result.is_valid is False
        assert result.rule == "R2"


# ---------------------------------------------------------------------------
# Test 8 -- Validator: missing before_snapshot rejected
# ---------------------------------------------------------------------------

class TestValidatorMissingBeforeSnapshot:

    def test_empty_dict_before_snapshot_rejected(self, validator) -> None:
        tx = _make_transaction(before_snapshot={})
        result = validator.validate(tx)
        assert result.is_valid is False
        assert result.rule == "R3"
        assert "before_snapshot" in result.reason

    def test_none_before_snapshot_rejected(self, validator) -> None:
        # None is not a dict, so the type check rejects it.
        tx = _make_transaction(before_snapshot=None)  # type: ignore[arg-type]
        result = validator.validate(tx)
        assert result.is_valid is False
        assert result.rule == "R3"

    def test_target_identity_missing_rejected(self, validator) -> None:
        tx = _make_transaction(target_identity="")
        result = validator.validate(tx)
        assert result.is_valid is False
        assert result.rule == "R4"

    def test_none_input_rejected(self, validator) -> None:
        result = validator.validate(None)  # type: ignore[arg-type]
        assert result.is_valid is False
        assert result.rule == "R0"


# ---------------------------------------------------------------------------
# Test 9 -- APPLIED status forbidden
# ---------------------------------------------------------------------------

class TestAppliedForbidden:

    def test_applied_status_rejected_by_validator(
        self, validator,
    ) -> None:
        tx = _make_transaction(status=EvolutionStatus.APPLIED)
        result = validator.validate(tx)
        assert result.is_valid is False
        assert result.rule == "R5"
        assert "APPLIED" in result.reason

    def test_approved_to_applied_transition_forbidden(self) -> None:
        # The lifecycle also forbids this.
        assert is_valid_transition(
            EvolutionStatus.APPROVED, EvolutionStatus.APPLIED,
        ) is False

    def test_applied_state_in_enum_but_unreachable(self) -> None:
        # The APPLIED state is declared in the enum so the lifecycle
        # is future-extensible, but no transition leads to it in V1.
        assert EvolutionStatus.APPLIED in EvolutionStatus.ALL
        # No from_status maps to APPLIED in V1.
        for from_status, to_set in ALLOWED_TRANSITIONS.items():
            assert EvolutionStatus.APPLIED not in to_set, (
                "APPLIED should not be reachable from "
                + str(from_status) + " in V1"
            )


# ---------------------------------------------------------------------------
# Test 10 -- Audit append-only
# ---------------------------------------------------------------------------

class TestAuditAppendOnly:

    def test_append_grows_the_store(self, audit_store) -> None:
        assert audit_store.count() == 0
        audit_store.make_and_append(
            transaction_id="tx-1", action="validated",
            actor="validator", reason="all rules passed",
        )
        assert audit_store.count() == 1
        audit_store.make_and_append(
            transaction_id="tx-1", action="transitioned",
            actor="lifecycle", reason="VALIDATING -> APPROVED",
        )
        assert audit_store.count() == 2

    def test_list_returns_copy(self, audit_store) -> None:
        audit_store.make_and_append(
            transaction_id="tx-1", action="validated", actor="x",
        )
        records = audit_store.list()
        assert len(records) == 1
        # Mutating the returned list must not affect the store.
        records.clear()
        assert audit_store.count() == 1

    def test_list_for_transaction_filters(self, audit_store) -> None:
        audit_store.make_and_append(
            transaction_id="tx-1", action="a", actor="x",
        )
        audit_store.make_and_append(
            transaction_id="tx-2", action="b", actor="y",
        )
        audit_store.make_and_append(
            transaction_id="tx-1", action="c", actor="z",
        )
        assert len(audit_store.list_for_transaction("tx-1")) == 2
        assert len(audit_store.list_for_transaction("tx-2")) == 1
        assert len(audit_store.list_for_transaction("tx-99")) == 0

    def test_forbidden_methods_raise_type_error(self, audit_store) -> None:
        with pytest.raises(TypeError):
            audit_store.update()
        with pytest.raises(TypeError):
            audit_store.delete()
        with pytest.raises(TypeError):
            audit_store.overwrite()
        with pytest.raises(TypeError):
            audit_store.clear()

    def test_forbidden_methods_reject_positional_and_keyword(
        self, audit_store,
    ) -> None:
        with pytest.raises(TypeError):
            audit_store.update("any", "args", key="value")
        with pytest.raises(TypeError):
            audit_store.delete(audit_id="x")

    def test_audit_record_is_frozen(self) -> None:
        rec = EvolutionAuditRecord(
            audit_id="a-1",
            transaction_id="tx-1",
            action="validated",
            actor="validator",
            before=None,
            after=None,
            reason="ok",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            rec.action = "mutated"  # type: ignore[misc]

    def test_audit_record_to_dict_is_json_safe(self) -> None:
        rec = EvolutionAuditRecord(
            audit_id="a-1",
            transaction_id="tx-1",
            action="validated",
            actor="validator",
            before={"status": "CREATED"},
            after={"status": "VALIDATING"},
            reason="transitioned",
        )
        encoded = json.dumps(rec.to_dict())
        decoded = json.loads(encoded)
        assert decoded["audit_id"] == "a-1"
        assert decoded["transaction_id"] == "tx-1"
        assert decoded["action"] == "validated"
        assert isinstance(decoded["timestamp"], str)

    def test_non_record_append_raises_audit_error(self, audit_store) -> None:
        with pytest.raises(EvolutionAuditError):
            audit_store.append("not a record")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Test 11 -- AST architecture boundary
# ---------------------------------------------------------------------------

_FORBIDDEN_PREFIXES = (
    "caseos.intelligence.decision",
    "caseos.intelligence.trust",
    "caseos.intelligence.recommendation",
    "caseos.knowledge.retrieval",
)


def _imports(py_path: Path) -> set:
    tree = ast.parse(py_path.read_text(encoding="utf-8-sig"))
    out: set = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


class TestArchitectureBoundary:

    @pytest.mark.parametrize("py_name", [
        "__init__.py", "object.py", "transaction.py",
        "validator.py", "audit.py", "report.py",
    ])
    def test_no_forbidden_imports(self, py_name: str) -> None:
        py = EVOLUTION_DIR / py_name
        if not py.exists():
            pytest.skip("missing module: " + py_name)
        seen = _imports(py)
        bad = [
            m for m in seen
            if any(m.startswith(p) for p in _FORBIDDEN_PREFIXES)
        ]
        assert bad == [], (
            py_name + " has forbidden imports: " + ", ".join(bad)
        )


# ---------------------------------------------------------------------------
# Auxiliary -- Validator happy path
# ---------------------------------------------------------------------------

class TestValidatorHappyPath:

    def test_valid_transaction_accepted(self, validator) -> None:
        tx = _make_transaction()
        result = validator.validate(tx)
        assert result.is_valid is True
        assert result.reason == ""
        assert result.rule == ""

    def test_approved_transaction_accepted(self, validator) -> None:
        tx = _make_transaction(status=EvolutionStatus.APPROVED)
        result = validator.validate(tx)
        assert result.is_valid is True

    def test_rejected_transaction_accepted_by_validator(
        self, validator,
    ) -> None:
        # The validator checks safety, not lifecycle position.
        # A REJECTED transaction is still "valid" in the safety
        # sense; its status just records the sad-path outcome.
        tx = _make_transaction(status=EvolutionStatus.REJECTED)
        result = validator.validate(tx)
        assert result.is_valid is True

    def test_validating_transaction_accepted(self, validator) -> None:
        tx = _make_transaction(status=EvolutionStatus.VALIDATING)
        result = validator.validate(tx)
        assert result.is_valid is True


# ---------------------------------------------------------------------------
# Auxiliary -- Report
# ---------------------------------------------------------------------------

class TestReport:

    def test_report_contains_all_five_sections(self) -> None:
        tx = _make_transaction()
        md = generate_report(tx)
        for section in (
            "## Transaction Summary",
            "## Validation Result",
            "## Audit History",
            "## Evolution Status",
            "## Safety Boundary",
        ):
            assert section in md, "missing section: " + section

    def test_report_starts_with_h1(self) -> None:
        tx = _make_transaction()
        md = generate_report(tx)
        assert md.startswith("# Evolution Transaction Report")

    def test_report_safety_boundary_contains_not_executed(self) -> None:
        tx = _make_transaction()
        md = generate_report(tx)
        assert "Knowledge mutation: NOT EXECUTED" in md

    def test_report_approved_status_marks_hard_stop(self) -> None:
        tx = _make_transaction(status=EvolutionStatus.APPROVED)
        md = generate_report(tx)
        assert "HARD-STOP" in md
        assert "Knowledge mutation: NOT EXECUTED" in md

    def test_report_with_validation_valid(self) -> None:
        tx = _make_transaction()
        validation = ValidationResult(is_valid=True)
        md = generate_report(tx, validation=validation)
        assert "verdict: **VALID**" in md

    def test_report_with_validation_rejected(self) -> None:
        tx = _make_transaction()
        validation = ValidationResult(
            is_valid=False, reason="missing proposal_id", rule="R1",
        )
        md = generate_report(tx, validation=validation)
        assert "verdict: **REJECTED**" in md
        assert "missing proposal_id" in md
        assert "R1" in md

    def test_report_with_audit_records(self) -> None:
        tx = _make_transaction()
        store = EvolutionAuditStore()
        store.make_and_append(
            transaction_id=tx.transaction_id,
            action="validated", actor="validator",
            reason="all rules passed",
        )
        store.make_and_append(
            transaction_id=tx.transaction_id,
            action="transitioned", actor="lifecycle",
            before=EvolutionStatus.VALIDATING,
            after=EvolutionStatus.APPROVED,
            reason="VALIDATING -> APPROVED",
        )
        md = generate_report(tx, audit_records=store.list())
        assert "validated" in md
        assert "transitioned" in md
        assert "validator" in md
        assert "lifecycle" in md

    def test_report_renders_before_snapshot(self) -> None:
        tx = _make_transaction()
        md = generate_report(tx)
        assert "before_snapshot" in md
        assert "Do not add scattered equipment" in md

    def test_report_handles_none_requested_change(self) -> None:
        tx = _make_transaction(requested_change=None)
        md = generate_report(tx)
        # No "### requested_change" subsection when None
        assert "### requested_change" not in md

    def test_report_renders_requested_change(self) -> None:
        tx = _make_transaction(requested_change="refine boundary to ...")
        md = generate_report(tx)
        assert "refine boundary to ..." in md
