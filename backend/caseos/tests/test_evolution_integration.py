"""Tests for the Evolution Integration Verification (Sprint 22.4-C).

Coverage per Sprint 22.4-C spec section "Task 4 -- Tests":

    Test 1  Successful flow (governance PASS -> audit created)
    Test 2  Governance reject (e.g. identity_update without reviewer)
    Test 3  Mutation never executed (any path)
    Test 4  Transaction immutable (deepcopy before/after)
    Test 5  Audit append-only (forbidden methods raise)
    Test 6  Architecture Boundary AST (3 integration modules)

Plus auxiliary invariants: result fields, frozen, JSON-safe,
custom dependencies, report sections, etc.
"""
from __future__ import annotations

import ast
import copy
import dataclasses
import json
from pathlib import Path

import pytest

from caseos.knowledge.evolution import (
    EvolutionAuditStore,
    EvolutionGovernanceGate,
    EvolutionStatus,
    EvolutionTransaction,
    EvolutionValidator,
)
from caseos.knowledge.evolution.integration import (
    EvolutionExecutionResult,
    EvolutionRuntime,
    generate_report,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
INTEGRATION_DIR = (
    BACKEND / "caseos" / "knowledge" / "evolution" / "integration"
)


_UNSET = object()


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
    status: str = EvolutionStatus.VALIDATING,
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
def runtime() -> EvolutionRuntime:
    return EvolutionRuntime()


@pytest.fixture
def passing_tx() -> EvolutionTransaction:
    return _make_transaction()


@pytest.fixture
def rejecting_tx() -> EvolutionTransaction:
    # identity_update fails G2; also no reviewer fails G5/V2.
    return _make_transaction(
        change_type="identity_update",
        reviewer="",
    )


# ---------------------------------------------------------------------------
# Test 1 -- Successful flow
# ---------------------------------------------------------------------------

class TestSuccessfulFlow:

    def test_happy_path_returns_success(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        assert result.success is True
        assert result.audit_created is True
        # Critical: even on success, mutation_executed is False.
        assert result.mutation_executed is False

    def test_happy_path_governance_approved(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        assert result.governance_result.approved is True
        assert result.governance_result.rule_id == ""

    def test_happy_path_audit_record_appended(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        assert runtime.audit_count() == 1
        records = runtime.audit_records()
        assert records[0].transaction_id == passing_tx.transaction_id
        assert records[0].action == "evolution_passed_governance"

    def test_happy_path_uses_transaction_reviewer_as_actor(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        records = runtime.audit_records()
        assert records[0].actor == "alice"

    def test_happy_path_execute_with_reviewer_override(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(
            passing_tx, change_intent=None, reviewer="bob",
        )
        assert result.success is True
        records = runtime.audit_records()
        assert records[0].actor == "bob"


# ---------------------------------------------------------------------------
# Test 2 -- Governance reject
# ---------------------------------------------------------------------------

class TestGovernanceReject:

    def test_identity_update_without_reviewer_rejected(
        self, runtime, rejecting_tx,
    ) -> None:
        result = runtime.execute(rejecting_tx)
        assert result.success is False
        assert result.audit_created is False
        assert result.mutation_executed is False

    def test_governance_reject_preserves_failure_info(
        self, runtime, rejecting_tx,
    ) -> None:
        result = runtime.execute(rejecting_tx)
        assert result.governance_result.approved is False
        # The first failure is reported in the rule_id.
        assert result.governance_result.rule_id != ""

    def test_governance_reject_creates_no_audit(
        self, runtime, rejecting_tx,
    ) -> None:
        runtime.execute(rejecting_tx)
        assert runtime.audit_count() == 0

    def test_validator_failure_creates_no_audit(
        self, runtime,
    ) -> None:
        # APPLIED status is rejected by the validator (R5).
        tx = _make_transaction(status=EvolutionStatus.APPLIED)
        result = runtime.execute(tx)
        assert result.success is False
        assert result.audit_created is False
        assert runtime.audit_count() == 0

    def test_governance_g1_change_type_rejected(
        self, runtime,
    ) -> None:
        # unknown_update is not in the allow list -> G1.
        tx = _make_transaction(change_type="custom_unknown_change")
        result = runtime.execute(tx)
        assert result.success is False
        assert result.governance_result.rule_id == "G1"
        assert result.audit_created is False


# ---------------------------------------------------------------------------
# Test 3 -- Mutation never executed
# ---------------------------------------------------------------------------

class TestMutationNeverExecuted:

    def test_mutation_false_on_happy_path(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        assert result.mutation_executed is False

    def test_mutation_false_on_governance_reject(
        self, runtime, rejecting_tx,
    ) -> None:
        result = runtime.execute(rejecting_tx)
        assert result.mutation_executed is False

    def test_mutation_false_on_validator_reject(self, runtime) -> None:
        tx = _make_transaction(status=EvolutionStatus.APPLIED)
        result = runtime.execute(tx)
        assert result.mutation_executed is False

    def test_mutation_false_on_none_transaction(self, runtime) -> None:
        result = runtime.execute(None)  # type: ignore[arg-type]
        assert result.mutation_executed is False

    @pytest.mark.parametrize("change_type", [
        "boundary_update",
        "principle_update",
        "applicability_update",
        "identity_update",
        "rewrite_evidence",
        "modify_trust",
    ])
    def test_mutation_false_for_every_change_type(
        self, runtime, change_type: str,
    ) -> None:
        tx = _make_transaction(change_type=change_type)
        result = runtime.execute(tx)
        assert result.mutation_executed is False


# ---------------------------------------------------------------------------
# Test 4 -- Transaction immutable
# ---------------------------------------------------------------------------

class TestTransactionImmutable:

    def test_execute_does_not_mutate_passing_tx(
        self, runtime, passing_tx,
    ) -> None:
        before = copy.deepcopy(passing_tx.to_dict())
        runtime.execute(passing_tx)
        assert passing_tx.to_dict() == before

    def test_execute_does_not_mutate_failing_tx(
        self, runtime, rejecting_tx,
    ) -> None:
        before = copy.deepcopy(rejecting_tx.to_dict())
        runtime.execute(rejecting_tx)
        assert rejecting_tx.to_dict() == before

    def test_execute_does_not_mutate_reviewer_field(
        self, runtime, passing_tx,
    ) -> None:
        before_reviewer = passing_tx.reviewer
        runtime.execute(passing_tx, reviewer="bob")
        assert passing_tx.reviewer == before_reviewer

    def test_execute_does_not_mutate_status_field(
        self, runtime, passing_tx,
    ) -> None:
        before_status = passing_tx.status
        runtime.execute(passing_tx)
        assert passing_tx.status == before_status


# ---------------------------------------------------------------------------
# Test 5 -- Audit append-only
# ---------------------------------------------------------------------------

class TestAuditAppendOnly:

    def test_update_raises_type_error(self, runtime) -> None:
        with pytest.raises(TypeError):
            runtime.audit_store.update()

    def test_delete_raises_type_error(self, runtime) -> None:
        with pytest.raises(TypeError):
            runtime.audit_store.delete()

    def test_overwrite_raises_type_error(self, runtime) -> None:
        with pytest.raises(TypeError):
            runtime.audit_store.overwrite()

    def test_clear_raises_type_error(self, runtime) -> None:
        with pytest.raises(TypeError):
            runtime.audit_store.clear()

    def test_update_with_args_raises(self, runtime) -> None:
        with pytest.raises(TypeError):
            runtime.audit_store.update("any", "args", key="value")

    def test_delete_with_args_raises(self, runtime) -> None:
        with pytest.raises(TypeError):
            runtime.audit_store.delete(audit_id="x")

    def test_audit_records_grow_monotonically(
        self, runtime, passing_tx,
    ) -> None:
        assert runtime.audit_count() == 0
        for i in range(3):
            tx = _make_transaction(transaction_id="tx-" + str(i))
            result = runtime.execute(tx)
            assert result.success is True
            assert runtime.audit_count() == i + 1


# ---------------------------------------------------------------------------
# Test 6 -- Architecture Boundary AST
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
        "__init__.py", "runtime.py", "report.py",
    ])
    def test_no_forbidden_imports(self, py_name: str) -> None:
        py = INTEGRATION_DIR / py_name
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
# Auxiliary -- EvolutionExecutionResult invariants
# ---------------------------------------------------------------------------

class TestExecutionResultFields:

    EXPECTED_FIELDS = {
        "transaction_id", "success", "governance_result",
        "audit_created", "mutation_executed", "created_at",
    }

    def test_all_six_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(EvolutionExecutionResult)}
        assert self.EXPECTED_FIELDS.issubset(actual), (
            "missing fields: " + str(self.EXPECTED_FIELDS - actual)
        )

    def test_field_count_is_six(self) -> None:
        assert len(dataclasses.fields(EvolutionExecutionResult)) == 6


class TestExecutionResultFrozen:

    def test_mutation_raises(self) -> None:
        gov = type("G", (), {"approved": True, "rule_id": "", "reason": ""})()
        result = EvolutionExecutionResult(
            transaction_id="tx-1",
            success=True,
            governance_result=gov,  # type: ignore[arg-type]
            audit_created=True,
            mutation_executed=False,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.success = False  # type: ignore[misc]

    def test_mutation_of_mutation_executed_raises(self) -> None:
        gov = type("G", (), {"approved": True, "rule_id": "", "reason": ""})()
        result = EvolutionExecutionResult(
            transaction_id="tx-1",
            success=True,
            governance_result=gov,  # type: ignore[arg-type]
            audit_created=True,
            mutation_executed=False,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.mutation_executed = True  # type: ignore[misc]


class TestExecutionResultJsonSafe:

    def test_to_dict_is_json_safe(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        encoded = json.dumps(result.to_dict())
        decoded = json.loads(encoded)
        assert decoded["transaction_id"] == passing_tx.transaction_id
        assert decoded["success"] is True
        assert decoded["audit_created"] is True
        assert decoded["mutation_executed"] is False
        assert decoded["governance_result"]["approved"] is True
        assert isinstance(decoded["created_at"], str)

    def test_failure_to_dict_is_json_safe(
        self, runtime, rejecting_tx,
    ) -> None:
        result = runtime.execute(rejecting_tx)
        encoded = json.dumps(result.to_dict())
        decoded = json.loads(encoded)
        assert decoded["success"] is False
        assert decoded["audit_created"] is False
        assert decoded["mutation_executed"] is False
        assert decoded["governance_result"]["approved"] is False


# ---------------------------------------------------------------------------
# Auxiliary -- Runtime composition
# ---------------------------------------------------------------------------

class TestRuntimeComposition:

    def test_default_dependencies(self) -> None:
        rt = EvolutionRuntime()
        assert isinstance(rt.validator, EvolutionValidator)
        assert isinstance(rt.governance_gate, EvolutionGovernanceGate)
        assert isinstance(rt.audit_store, EvolutionAuditStore)

    def test_custom_dependencies(self) -> None:
        custom_audit = EvolutionAuditStore()
        rt = EvolutionRuntime(audit_store=custom_audit)
        assert rt.audit_store is custom_audit

    def test_independent_runtimes_have_independent_audit(self) -> None:
        rt1 = EvolutionRuntime()
        rt2 = EvolutionRuntime()
        rt1.execute(_make_transaction(transaction_id="tx-a"))
        rt2.execute(_make_transaction(transaction_id="tx-b"))
        assert rt1.audit_count() == 1
        assert rt2.audit_count() == 1
        assert (
            rt1.audit_records()[0].transaction_id
            != rt2.audit_records()[0].transaction_id
        )


# ---------------------------------------------------------------------------
# Auxiliary -- Report
# ---------------------------------------------------------------------------

class TestReport:

    def test_report_contains_all_five_sections(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        md = generate_report(
            result, transaction=passing_tx,
            audit_records=runtime.audit_records(),
        )
        for section in (
            "## Transaction",
            "## Governance Result",
            "## Audit Status",
            "## Knowledge Mutation",
            "## Safety Boundary",
        ):
            assert section in md, "missing section: " + section

    def test_report_starts_with_correct_h1(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        md = generate_report(result, transaction=passing_tx)
        assert md.startswith(
            "# Evolution Integration Verification Report"
        )

    def test_report_knowledge_mutation_fixed_text(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        md = generate_report(result, transaction=passing_tx)
        # The "NOT EXECUTED" string is the V1 hard-stop marker.
        assert "NOT EXECUTED" in md

    def test_report_safety_boundary_marks_mutation_false(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        md = generate_report(result, transaction=passing_tx)
        assert "mutation_executed: `False`" in md

    def test_report_includes_transaction_id(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        md = generate_report(result, transaction=passing_tx)
        assert passing_tx.transaction_id in md

    def test_report_approved_verdict(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        md = generate_report(result, transaction=passing_tx)
        assert "verdict: **APPROVED**" in md

    def test_report_rejected_verdict(
        self, runtime, rejecting_tx,
    ) -> None:
        result = runtime.execute(rejecting_tx)
        md = generate_report(result, transaction=rejecting_tx)
        assert "verdict: **REJECTED**" in md

    def test_report_includes_audit_records(
        self, runtime, passing_tx,
    ) -> None:
        result = runtime.execute(passing_tx)
        records = runtime.audit_records()
        md = generate_report(
            result, transaction=passing_tx, audit_records=records,
        )
        assert "evolution_passed_governance" in md
        assert "alice" in md

    def test_report_no_audit_records_marker(
        self, runtime, rejecting_tx,
    ) -> None:
        result = runtime.execute(rejecting_tx)
        md = generate_report(result, transaction=rejecting_tx)
        assert "audit_created: **False**" in md


# ---------------------------------------------------------------------------
# Auxiliary -- Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_change_intent_cross_check_uses_governance_path(
        self, runtime, passing_tx,
    ) -> None:
        # Mismatched change_type change_intent -> G1.
        class _StubIntent:
            change_type = "principle_update"

        result = runtime.execute(
            passing_tx, change_intent=_StubIntent(),
        )
        assert result.success is False
        assert result.governance_result.rule_id == "G1"
        assert "mismatch" in result.governance_result.reason.lower()

    def test_reviewer_override_uses_overridden_value(
        self, runtime, passing_tx,
    ) -> None:
        runtime.execute(passing_tx, reviewer="charlie")
        assert runtime.audit_records()[0].actor == "charlie"

    def test_multiple_executions_accumulate(
        self, runtime,
    ) -> None:
        for i in range(5):
            runtime.execute(
                _make_transaction(transaction_id="tx-" + str(i)),
            )
        assert runtime.audit_count() == 5

    def test_mixed_pass_and_fail(
        self, runtime, passing_tx, rejecting_tx,
    ) -> None:
        runtime.execute(passing_tx)
        runtime.execute(rejecting_tx)
        runtime.execute(passing_tx)
        # Two passes, one reject -> 2 audit records.
        assert runtime.audit_count() == 2
