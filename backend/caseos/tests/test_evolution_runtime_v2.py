"""Tests for the Evolution Runtime V2 Full Simulation (Sprint 22.4-F).

Coverage per Sprint 22.4-F spec section "测试要求":

    Test 1  Complete execution chain (happy path)
    Test 2  Governance reject: no version created
    Test 3  Audit created (happy path)
    Test 4  Version created (happy path)
    Test 5  mutation_executed always False
    Test 6  AST architecture boundary (3 runtime_v2 modules)

Plus auxiliary invariants: result fields, version_number
increment, audit record fields, multiple executions
accumulate, custom dependencies, report sections, etc.
"""
from __future__ import annotations

import ast
import copy
import dataclasses
import json
from pathlib import Path

import pytest

from caseos.knowledge.evolution import (
    EvolutionAuditStore as V1AuditStore,  # noqa: F401  (not used; clarity)
    EvolutionGovernanceGate,
    EvolutionStatus,
    EvolutionTransaction,
    EvolutionValidator,
)
from caseos.knowledge.evolution.audit_v2 import AuditStore
from caseos.knowledge.evolution.runtime_v2 import (
    EvolutionExecutionResult,
    EvolutionExecutor,
    generate_report,
)
from caseos.knowledge.evolution.versioning import (
    KnowledgeVersion,
    VersionStore,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
RUNTIME_V2_DIR = (
    BACKEND / "caseos" / "knowledge" / "evolution" / "runtime_v2"
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
def executor() -> EvolutionExecutor:
    return EvolutionExecutor()


@pytest.fixture
def passing_tx() -> EvolutionTransaction:
    return _make_transaction()


@pytest.fixture
def rejecting_tx() -> EvolutionTransaction:
    return _make_transaction(
        change_type="identity_update",  # G2
        reviewer="",  # also fails G5
    )


# ---------------------------------------------------------------------------
# Test 1 -- Complete execution chain
# ---------------------------------------------------------------------------

class TestCompleteChain:

    def test_happy_path_all_three_pass(
        self, executor, passing_tx,
    ) -> None:
        result = executor.execute(passing_tx)
        assert result.governance_passed is True
        assert result.version_created is True
        assert result.audit_created is True
        assert result.mutation_executed is False

    def test_happy_path_persists_one_version_and_one_audit(
        self, executor, passing_tx,
    ) -> None:
        executor.execute(passing_tx)
        assert executor.version_count() == 1
        assert executor.audit_count() == 1

    def test_happy_path_explicit_booleans(
        self, executor, passing_tx,
    ) -> None:
        result = executor.execute(passing_tx)
        assert result.transaction_id == passing_tx.transaction_id
        assert result.governance_passed is True
        assert result.version_created is True
        assert result.audit_created is True
        assert result.mutation_executed is False


# ---------------------------------------------------------------------------
# Test 2 -- Governance reject: no version created
# ---------------------------------------------------------------------------

class TestGovernanceReject:

    def test_rejection_creates_no_version(
        self, executor, rejecting_tx,
    ) -> None:
        executor.execute(rejecting_tx)
        assert executor.version_count() == 0

    def test_rejection_creates_no_audit(
        self, executor, rejecting_tx,
    ) -> None:
        executor.execute(rejecting_tx)
        assert executor.audit_count() == 0

    def test_rejection_result_booleans(
        self, executor, rejecting_tx,
    ) -> None:
        result = executor.execute(rejecting_tx)
        assert result.governance_passed is False
        assert result.version_created is False
        assert result.audit_created is False
        assert result.mutation_executed is False

    def test_validator_rejection_short_circuits(
        self, executor,
    ) -> None:
        # APPLIED status is rejected by the validator (R5).
        tx = _make_transaction(status=EvolutionStatus.APPLIED)
        result = executor.execute(tx)
        assert result.governance_passed is False
        assert result.version_created is False
        assert executor.version_count() == 0


# ---------------------------------------------------------------------------
# Test 3 -- Audit created
# ---------------------------------------------------------------------------

class TestAuditCreated:

    def test_audit_record_exists_in_store(
        self, executor, passing_tx,
    ) -> None:
        executor.execute(passing_tx)
        audits = executor.audit_store.list()
        assert len(audits) == 1
        audit = audits[0]
        # Required fields per spec Task 4.
        assert audit.transaction_id == passing_tx.transaction_id
        assert audit.proposal_id == passing_tx.proposal_id
        assert audit.target_identity == passing_tx.target_identity
        assert audit.reviewer == passing_tx.reviewer

    def test_audit_change_type_matches(
        self, executor, passing_tx,
    ) -> None:
        executor.execute(passing_tx)
        audit = executor.audit_store.list()[0]
        assert audit.change_type == "boundary_update"

    def test_audit_after_snapshot_is_none(
        self, executor, passing_tx,
    ) -> None:
        # V1: no real mutation, so after_snapshot is None.
        executor.execute(passing_tx)
        audit = executor.audit_store.list()[0]
        assert audit.after_snapshot is None

    def test_audit_before_snapshot_matches(
        self, executor, passing_tx,
    ) -> None:
        executor.execute(passing_tx)
        audit = executor.audit_store.list()[0]
        assert audit.before_snapshot == passing_tx.before_snapshot


# ---------------------------------------------------------------------------
# Test 4 -- Version created
# ---------------------------------------------------------------------------

class TestVersionCreated:

    def test_first_version_is_number_1(
        self, executor, passing_tx,
    ) -> None:
        executor.execute(passing_tx)
        versions = executor.version_store.list()
        assert len(versions) == 1
        v = versions[0]
        assert v.version_number == 1
        assert v.previous_version is None

    def test_second_version_increments_to_2(
        self, executor, passing_tx,
    ) -> None:
        executor.execute(passing_tx)
        executor.execute(
            _make_transaction(
                transaction_id="tx-2",
                target_identity="KO-1",
            ),
        )
        versions = executor.version_store.list()
        assert len(versions) == 2
        assert versions[0].version_number == 1
        assert versions[0].previous_version is None
        assert versions[1].version_number == 2
        assert versions[1].previous_version == 1

    def test_third_version_for_same_ko(
        self, executor, passing_tx,
    ) -> None:
        for i in range(3):
            executor.execute(
                _make_transaction(
                    transaction_id="tx-" + str(i),
                    target_identity="KO-1",
                ),
            )
        versions = executor.version_store.list()
        numbers = [v.version_number for v in versions]
        assert numbers == [1, 2, 3]
        previous = [v.previous_version for v in versions]
        assert previous == [None, 1, 2]

    def test_different_ko_starts_at_1(
        self, executor,
    ) -> None:
        executor.execute(
            _make_transaction(target_identity="KO-A"),
        )
        executor.execute(
            _make_transaction(transaction_id="tx-2", target_identity="KO-B"),
        )
        a = executor.version_store.history("KO-A")
        b = executor.version_store.history("KO-B")
        assert a[0].version_number == 1
        assert b[0].version_number == 1
        assert a[0].previous_version is None
        assert b[0].previous_version is None

    def test_version_snapshot_is_before_snapshot(
        self, executor, passing_tx,
    ) -> None:
        executor.execute(passing_tx)
        v = executor.version_store.list()[0]
        assert v.snapshot == passing_tx.before_snapshot

    def test_version_created_by_is_reviewer(
        self, executor, passing_tx,
    ) -> None:
        executor.execute(passing_tx)
        v = executor.version_store.list()[0]
        assert v.created_by == passing_tx.reviewer


# ---------------------------------------------------------------------------
# Test 5 -- mutation_executed always False
# ---------------------------------------------------------------------------

class TestMutationNeverExecuted:

    def test_mutation_false_on_happy_path(
        self, executor, passing_tx,
    ) -> None:
        result = executor.execute(passing_tx)
        assert result.mutation_executed is False

    def test_mutation_false_on_reject(
        self, executor, rejecting_tx,
    ) -> None:
        result = executor.execute(rejecting_tx)
        assert result.mutation_executed is False

    def test_mutation_false_on_validator_reject(self, executor) -> None:
        tx = _make_transaction(status=EvolutionStatus.APPLIED)
        result = executor.execute(tx)
        assert result.mutation_executed is False

    def test_mutation_false_on_none_transaction(self, executor) -> None:
        result = executor.execute(None)  # type: ignore[arg-type]
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
        self, executor, change_type: str,
    ) -> None:
        tx = _make_transaction(change_type=change_type)
        result = executor.execute(tx)
        assert result.mutation_executed is False


# ---------------------------------------------------------------------------
# Test 6 -- AST architecture boundary
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
        "__init__.py", "executor.py", "report.py",
    ])
    def test_no_forbidden_imports(self, py_name: str) -> None:
        py = RUNTIME_V2_DIR / py_name
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
        "transaction_id", "governance_passed",
        "version_created", "audit_created",
        "mutation_executed", "created_at",
    }

    def test_all_six_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(EvolutionExecutionResult)}
        assert self.EXPECTED_FIELDS.issubset(actual), (
            "missing fields: " + str(self.EXPECTED_FIELDS - actual)
        )

    def test_field_count_is_six(self) -> None:
        assert len(dataclasses.fields(EvolutionExecutionResult)) == 6

    def test_dataclass_is_frozen(self) -> None:
        result = EvolutionExecutionResult(
            transaction_id="tx-1",
            governance_passed=True,
            version_created=True,
            audit_created=True,
            mutation_executed=False,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.governance_passed = False  # type: ignore[misc]

    def test_mutation_executed_field_cannot_be_flipped_true(self) -> None:
        result = EvolutionExecutionResult(
            transaction_id="tx-1",
            governance_passed=True,
            version_created=True,
            audit_created=True,
            mutation_executed=False,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.mutation_executed = True  # type: ignore[misc]

    def test_to_dict_is_json_safe(self) -> None:
        result = EvolutionExecutionResult(
            transaction_id="tx-1",
            governance_passed=True,
            version_created=True,
            audit_created=True,
            mutation_executed=False,
        )
        encoded = json.dumps(result.to_dict())
        decoded = json.loads(encoded)
        assert decoded["transaction_id"] == "tx-1"
        assert decoded["governance_passed"] is True
        assert decoded["version_created"] is True
        assert decoded["audit_created"] is True
        assert decoded["mutation_executed"] is False
        assert isinstance(decoded["created_at"], str)


# ---------------------------------------------------------------------------
# Auxiliary -- Executor composition
# ---------------------------------------------------------------------------

class TestExecutorComposition:

    def test_default_dependencies(self) -> None:
        ex = EvolutionExecutor()
        assert isinstance(ex.validator, EvolutionValidator)
        assert isinstance(ex.governance_gate, EvolutionGovernanceGate)
        assert isinstance(ex.version_store, VersionStore)
        assert isinstance(ex.audit_store, AuditStore)

    def test_custom_dependencies(self) -> None:
        custom_versions = VersionStore()
        custom_audits = AuditStore()
        ex = EvolutionExecutor(
            version_store=custom_versions,
            audit_store=custom_audits,
        )
        assert ex.version_store is custom_versions
        assert ex.audit_store is custom_audits

    def test_independent_executors_have_independent_state(self) -> None:
        ex1 = EvolutionExecutor()
        ex2 = EvolutionExecutor()
        ex1.execute(_make_transaction(transaction_id="tx-a"))
        ex2.execute(_make_transaction(transaction_id="tx-b"))
        assert ex1.version_count() == 1
        assert ex2.version_count() == 1
        assert (
            ex1.version_store.list()[0].version_id
            != ex2.version_store.list()[0].version_id
        )


# ---------------------------------------------------------------------------
# Auxiliary -- Report
# ---------------------------------------------------------------------------

class TestReport:

    def test_report_contains_all_five_sections(
        self, executor, passing_tx,
    ) -> None:
        result = executor.execute(passing_tx)
        md = generate_report(
            result, transaction=passing_tx,
            versions=executor.version_store.list(),
            audits=executor.audit_store.list(),
        )
        for section in (
            "## Transaction",
            "## Governance",
            "## Version",
            "## Audit",
            "## Knowledge Mutation",
        ):
            assert section in md, "missing section: " + section

    def test_report_starts_with_correct_h1(
        self, executor, passing_tx,
    ) -> None:
        result = executor.execute(passing_tx)
        md = generate_report(result, transaction=passing_tx)
        assert md.startswith("# Evolution Runtime V2 Report")

    def test_report_knowledge_mutation_fixed_text(
        self, executor, passing_tx,
    ) -> None:
        result = executor.execute(passing_tx)
        md = generate_report(result, transaction=passing_tx)
        assert "NOT IMPLEMENTED" in md

    def test_report_status_markers(
        self, executor, passing_tx,
    ) -> None:
        result = executor.execute(passing_tx)
        md = generate_report(result, transaction=passing_tx)
        assert "Evolution Simulation: **IMPLEMENTED**" in md
        assert "Knowledge Mutation: **NOT IMPLEMENTED**" in md

    def test_report_includes_transaction_id(
        self, executor, passing_tx,
    ) -> None:
        result = executor.execute(passing_tx)
        md = generate_report(result, transaction=passing_tx)
        assert passing_tx.transaction_id in md

    def test_report_includes_version_and_audit_ids(
        self, executor, passing_tx,
    ) -> None:
        result = executor.execute(passing_tx)
        versions = executor.version_store.list()
        audits = executor.audit_store.list()
        md = generate_report(
            result, transaction=passing_tx,
            versions=versions, audits=audits,
        )
        assert versions[0].version_id in md
        assert audits[0].audit_id in md

    def test_report_rejection_marks_no_versions_no_audits(
        self, executor, rejecting_tx,
    ) -> None:
        result = executor.execute(rejecting_tx)
        md = generate_report(
            result, transaction=rejecting_tx,
            versions=executor.version_store.list(),
            audits=executor.audit_store.list(),
        )
        assert "version_created: **False**" in md
        assert "audit_created: **False**" in md
        assert "governance_passed: **False**" in md


# ---------------------------------------------------------------------------
# Auxiliary -- Multi-execution accumulation
# ---------------------------------------------------------------------------

class TestMultipleExecutions:

    def test_three_executions_accumulate(self, executor) -> None:
        for i in range(3):
            executor.execute(
                _make_transaction(transaction_id="tx-" + str(i)),
            )
        assert executor.version_count() == 3
        assert executor.audit_count() == 3

    def test_mixed_pass_and_reject(self, executor) -> None:
        executor.execute(_make_transaction(transaction_id="tx-1"))
        executor.execute(
            _make_transaction(
                transaction_id="tx-2", change_type="identity_update",
            ),
        )
        executor.execute(_make_transaction(transaction_id="tx-3"))
        # Two passes, one reject -> 2 versions + 2 audits.
        assert executor.version_count() == 2
        assert executor.audit_count() == 2

    def test_audit_version_linkage(self, executor) -> None:
        executor.execute(
            _make_transaction(transaction_id="tx-1", target_identity="KO-A"),
        )
        executor.execute(
            _make_transaction(transaction_id="tx-2", target_identity="KO-A"),
        )
        versions = executor.version_store.history("KO-A")
        audits = executor.audit_store.history("KO-A")
        assert len(versions) == 2
        assert len(audits) == 2
        # Each audit should reference the same transaction_id
        # as the version it accompanies.
        for v, a in zip(versions, audits):
            # The version's proposal_id and the audit's
            # proposal_id come from the same transaction.
            assert v.proposal_id == a.proposal_id
            assert v.target_identity == a.target_identity


# ---------------------------------------------------------------------------
# Auxiliary -- Transaction immutable through pipeline
# ---------------------------------------------------------------------------

class TestTransactionImmutable:

    def test_execute_does_not_mutate_passing_tx(
        self, executor, passing_tx,
    ) -> None:
        before = copy.deepcopy(passing_tx.to_dict())
        executor.execute(passing_tx)
        assert passing_tx.to_dict() == before

    def test_execute_does_not_mutate_failing_tx(
        self, executor, rejecting_tx,
    ) -> None:
        before = copy.deepcopy(rejecting_tx.to_dict())
        executor.execute(rejecting_tx)
        assert rejecting_tx.to_dict() == before
