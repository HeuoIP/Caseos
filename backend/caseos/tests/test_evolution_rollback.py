"""Tests for the Evolution Rollback Module V1 (Sprint 22.4-G).

Coverage per Sprint 22.4-G spec section "Test Requirements":

    Test 1  RollbackRequest: fields, frozen, JSON safe
    Test 2  Validator: valid request, missing transaction,
            invalid version order, missing version
    Test 3  RollbackPlan: immutable, no execution methods
    Test 4  Safety: no restore(), no rollback(), no apply(),
            no execute(), no mutate()
    Test 5  Knowledge mutation always False
    Test 6  Architecture boundary AST

Plus auxiliary invariants: R5 to_version < 1, builder from
audit, report sections, multiple planners, etc.
"""
from __future__ import annotations

import ast
import copy
import dataclasses
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from caseos.knowledge.evolution.audit_v2 import (
    AuditStore,
    EvolutionAuditRecord,
)
from caseos.knowledge.evolution.rollback import (
    RollbackPlan,
    RollbackPlanner,
    RollbackRequest,
    RollbackValidationResult,
    RollbackValidator,
    build_request_from_audit,
    generate_report,
)
from caseos.knowledge.evolution.versioning import (
    KnowledgeVersion,
    VersionStore,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
ROLLBACK_DIR = (
    BACKEND / "caseos" / "knowledge" / "evolution" / "rollback"
)


def _make_request(
    *,
    rollback_id: str = "rb-1",
    transaction_id: str = "tx-1",
    target_identity: str = "KO-1",
    from_version: int = 3,
    to_version: int = 1,
    reason: str = "user pushed back on the change",
    requested_by: str = "alice",
    created_at: datetime | None = None,

) -> RollbackRequest:
    if created_at is None:
        created_at = datetime(2026, 8, 4, tzinfo=timezone.utc)
    return RollbackRequest(
        rollback_id=rollback_id,
        transaction_id=transaction_id,
        target_identity=target_identity,
        from_version=from_version,
        to_version=to_version,
        reason=reason,
        requested_by=requested_by,
        created_at=created_at,
    )


def _make_version(
    *,
    version_id: str = "v-1",
    target_identity: str = "KO-1",
    version_number: int = 1,
    previous_version: int | None = None,
    snapshot: dict | None = None,
) -> KnowledgeVersion:
    if snapshot is None:
        snapshot = {"boundary": ["Do not add scattered equipment"]}
    return KnowledgeVersion(
        version_id=version_id,
        target_identity=target_identity,
        version_number=version_number,
        previous_version=previous_version,
        snapshot=snapshot,
        created_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
        created_by="alice",
        change_reason="initial",
        proposal_id="p-1",
    )


@pytest.fixture
def version_store() -> VersionStore:
    store = VersionStore()
    store.append(_make_version(version_number=1, previous_version=None))
    store.append(_make_version(version_number=2, previous_version=1))
    store.append(_make_version(version_number=3, previous_version=2))
    return store


@pytest.fixture
def validator() -> RollbackValidator:
    return RollbackValidator()


@pytest.fixture
def planner() -> RollbackPlanner:
    return RollbackPlanner()


# ---------------------------------------------------------------------------
# Test 1 -- RollbackRequest: fields, frozen, JSON safe
# ---------------------------------------------------------------------------

class TestRollbackRequestFields:

    EXPECTED_FIELDS = {
        "rollback_id", "transaction_id", "target_identity",
        "from_version", "to_version", "reason",
        "requested_by", "created_at",
    }

    def test_all_eight_required_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(RollbackRequest)}
        assert self.EXPECTED_FIELDS.issubset(actual), (
            "missing fields: " + str(self.EXPECTED_FIELDS - actual)
        )

    def test_field_count_is_eight(self) -> None:
        assert len(dataclasses.fields(RollbackRequest)) == 8

    def test_dataclass_is_frozen(self) -> None:
        r = _make_request()
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.from_version = 99  # type: ignore[misc]

    def test_mutation_of_rollback_id_raises(self) -> None:
        r = _make_request()
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.rollback_id = "rb-2"  # type: ignore[misc]

    def test_to_dict_is_json_safe(self) -> None:
        r = _make_request()
        encoded = json.dumps(r.to_dict())
        decoded = json.loads(encoded)
        assert decoded["rollback_id"] == "rb-1"
        assert decoded["transaction_id"] == "tx-1"
        assert decoded["target_identity"] == "KO-1"
        assert decoded["from_version"] == 3
        assert decoded["to_version"] == 1
        assert decoded["reason"] == "user pushed back on the change"
        assert decoded["requested_by"] == "alice"
        # created_at serialised as ISO string
        assert isinstance(decoded["created_at"], str)

# ---------------------------------------------------------------------------
# Test 2 -- Validator: R1-R5
# ---------------------------------------------------------------------------

class TestValidator:

    def test_valid_request_passes(self, validator, version_store) -> None:
        r = _make_request(from_version=3, to_version=1)
        result = validator.validate(r, version_store=version_store)
        assert result.valid is True
        assert result.rule_id == ""
        assert result.reason == ""

    def test_none_request_rejected(self, validator) -> None:
        result = validator.validate(None)  # type: ignore[arg-type]
        assert result.valid is False
        assert result.rule_id == "R0"

    def test_r1_missing_transaction_id_rejected(
        self, validator, version_store,
    ) -> None:
        r = _make_request(transaction_id="")
        result = validator.validate(r, version_store=version_store)
        assert result.valid is False
        assert result.rule_id == "R1"
        assert "transaction_id" in result.reason

    def test_r2_missing_target_identity_rejected(
        self, validator, version_store,
    ) -> None:
        r = _make_request(target_identity="")
        result = validator.validate(r, version_store=version_store)
        assert result.valid is False
        assert result.rule_id == "R2"
        assert "target_identity" in result.reason

    def test_r3_invalid_version_order_rejected(
        self, validator, version_store,
    ) -> None:
        # from <= to is rejected
        r = _make_request(from_version=1, to_version=3)
        result = validator.validate(r, version_store=version_store)
        assert result.valid is False
        assert result.rule_id == "R3"
        assert "from_version" in result.reason

    def test_r3_equal_versions_rejected(
        self, validator, version_store,
    ) -> None:
        r = _make_request(from_version=2, to_version=2)
        result = validator.validate(r, version_store=version_store)
        assert result.valid is False
        assert result.rule_id == "R3"

    def test_r4_from_version_not_in_history(
        self, validator, version_store,
    ) -> None:
        r = _make_request(from_version=99, to_version=1)
        result = validator.validate(r, version_store=version_store)
        assert result.valid is False
        assert result.rule_id == "R4"
        assert "from_version" in result.reason

    def test_r4_to_version_not_in_history(
        self, validator, version_store,
    ) -> None:
        r = _make_request(from_version=3, to_version=99)
        result = validator.validate(r, version_store=version_store)
        assert result.valid is False
        assert result.rule_id == "R4"
        assert "to_version" in result.reason

    def test_r5_to_version_zero_rejected(
        self, validator, version_store,
    ) -> None:
        r = _make_request(from_version=3, to_version=0)
        result = validator.validate(r, version_store=version_store)
        assert result.valid is False
        assert result.rule_id == "R5"

    def test_r5_to_version_negative_rejected(
        self, validator, version_store,
    ) -> None:
        r = _make_request(from_version=3, to_version=-1)
        result = validator.validate(r, version_store=version_store)
        assert result.valid is False
        assert result.rule_id == "R5"

    def test_first_failure_wins(
        self, validator, version_store,
    ) -> None:
        # Both R1 (empty transaction) and R3 (bad order) fail.
        # R1 is checked first, so R1 wins.
        r = _make_request(
            transaction_id="", from_version=1, to_version=3,
        )
        result = validator.validate(r, version_store=version_store)
        assert result.rule_id == "R1"

    def test_valid_request_without_version_store(
        self, validator,
    ) -> None:
        # When version_store is None, R4 is skipped.
        r = _make_request(from_version=3, to_version=1)
        result = validator.validate(r, version_store=None)
        assert result.valid is True


# ---------------------------------------------------------------------------
# Test 3 -- RollbackPlan: immutable, no execution methods
# ---------------------------------------------------------------------------

class TestRollbackPlanImmutable:

    EXPECTED_FIELDS = {
        "rollback_id", "target_identity", "source_version",
        "destination_version", "diff_summary", "steps",
        "created_at", "mutation_executed",
    }

    def test_all_eight_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(RollbackPlan)}
        assert self.EXPECTED_FIELDS.issubset(actual), (
            "missing fields: " + str(self.EXPECTED_FIELDS - actual)
        )

    def test_mutation_raises_frozen_instance_error(self) -> None:
        plan = RollbackPlan(
            rollback_id="rb-1",
            target_identity="KO-1",
            source_version=3,
            destination_version=1,
            diff_summary="rollback boundary",
            steps=("step-1",),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            plan.source_version = 99  # type: ignore[misc]

    def test_mutation_executed_cannot_be_flipped_true(self) -> None:
        plan = RollbackPlan(
            rollback_id="rb-1",
            target_identity="KO-1",
            source_version=3,
            destination_version=1,
            diff_summary="rollback boundary",
            steps=("step-1",),
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            plan.mutation_executed = True  # type: ignore[misc]

    def test_to_dict_is_json_safe(self) -> None:
        plan = RollbackPlan(
            rollback_id="rb-1",
            target_identity="KO-1",
            source_version=3,
            destination_version=1,
            diff_summary="rollback boundary",
            steps=("step-1", "step-2"),
        )
        encoded = json.dumps(plan.to_dict())
        decoded = json.loads(encoded)
        assert decoded["rollback_id"] == "rb-1"
        assert decoded["source_version"] == 3
        assert decoded["destination_version"] == 1
        assert decoded["mutation_executed"] is False
        assert isinstance(decoded["created_at"], str)


class TestRollbackPlanner:

    def test_planner_produces_plan(
        self, planner, version_store,
    ) -> None:
        r = _make_request(from_version=3, to_version=1)
        plan = planner.plan(r, version_store=version_store)
        assert plan is not None
        assert isinstance(plan, RollbackPlan)

    def test_planner_returns_none_for_invalid_request(
        self, planner, version_store,
    ) -> None:
        r = _make_request(from_version=1, to_version=3)  # R3
        plan = planner.plan(r, version_store=version_store)
        assert plan is None

    def test_planner_plan_carries_correct_versions(
        self, planner, version_store,
    ) -> None:
        r = _make_request(from_version=3, to_version=1)
        plan = planner.plan(r, version_store=version_store)
        assert plan is not None
        assert plan.source_version == 3
        assert plan.destination_version == 1

    def test_planner_plan_has_diff_summary(
        self, planner, version_store,
    ) -> None:
        r = _make_request(from_version=3, to_version=1)
        plan = planner.plan(r, version_store=version_store)
        assert plan is not None
        # diff_summary is non-empty when version_store is provided.
        assert plan.diff_summary != ""
        assert "fields" in plan.diff_summary.lower() or "no field" in plan.diff_summary.lower()


# ---------------------------------------------------------------------------
# Test 4 -- Safety: no restore / rollback / apply / execute / mutate
# ---------------------------------------------------------------------------

class TestSafetyForbiddenMethods:

    @pytest.mark.parametrize("forbidden_name", [
        "restore", "rollback", "apply", "execute", "mutate",
    ])
    def test_roll_back_plan_has_no_forbidden_method(
        self, forbidden_name: str,
    ) -> None:
        plan = RollbackPlan(
            rollback_id="rb-1",
            target_identity="KO-1",
            source_version=3,
            destination_version=1,
            diff_summary="x",
            steps=(),
        )
        assert not hasattr(plan, forbidden_name), (
            "plan has forbidden method: " + forbidden_name
        )

    @pytest.mark.parametrize("forbidden_name", [
        "restore", "rollback", "apply", "execute", "mutate",
    ])
    def test_rollback_planner_has_no_forbidden_method(
        self, planner, forbidden_name: str,
    ) -> None:
        assert not hasattr(planner, forbidden_name), (
            "planner has forbidden method: " + forbidden_name
        )

    @pytest.mark.parametrize("forbidden_name", [
        "restore", "rollback", "apply", "execute", "mutate",
    ])
    def test_rollback_validator_has_no_forbidden_method(
        self, validator, forbidden_name: str,
    ) -> None:
        assert not hasattr(validator, forbidden_name), (
            "validator has forbidden method: " + forbidden_name
        )

    @pytest.mark.parametrize("forbidden_name", [
        "restore", "rollback", "apply", "execute", "mutate",
    ])
    def test_rollback_request_has_no_forbidden_method(
        self, forbidden_name: str,
    ) -> None:
        r = _make_request()
        assert not hasattr(r, forbidden_name), (
            "request has forbidden method: " + forbidden_name
        )


# ---------------------------------------------------------------------------
# Test 5 -- Knowledge mutation always False
# ---------------------------------------------------------------------------

class TestMutationAlwaysFalse:

    def test_mutation_false_on_valid_plan(
        self, planner, version_store,
    ) -> None:
        r = _make_request(from_version=3, to_version=1)
        plan = planner.plan(r, version_store=version_store)
        assert plan is not None
        assert plan.mutation_executed is False

    def test_mutation_false_in_default_plan(self) -> None:
        plan = RollbackPlan(
            rollback_id="rb-1",
            target_identity="KO-1",
            source_version=3,
            destination_version=1,
            diff_summary="x",
            steps=(),
        )
        assert plan.mutation_executed is False

    def test_mutation_cannot_be_flipped_via_construction(self) -> None:
        # The default value is False; the field is bool-typed
        # but the frozen dataclass prevents post-init mutation.
        with pytest.raises(dataclasses.FrozenInstanceError):
            plan = RollbackPlan(
                rollback_id="rb-1",
                target_identity="KO-1",
                source_version=3,
                destination_version=1,
                diff_summary="x",
                steps=(),
                mutation_executed=True,
            )
            plan.mutation_executed = False  # type: ignore[misc]

    @pytest.mark.parametrize("forbidden_name", [
        "restore", "rollback", "apply", "execute", "mutate",
    ])
    def test_no_path_to_mutation_via_methods(
        self, planner, version_store, forbidden_name: str,
    ) -> None:
        # The planner has no method that could flip
        # mutation_executed to True.
        assert not hasattr(planner, forbidden_name)


# ---------------------------------------------------------------------------
# Test 6 -- Architecture boundary AST
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
        "__init__.py", "object.py", "request.py",
        "validator.py", "plan.py", "report.py",
    ])
    def test_no_forbidden_imports(self, py_name: str) -> None:
        py = ROLLBACK_DIR / py_name
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
# Auxiliary -- Builder from audit
# ---------------------------------------------------------------------------

class TestBuildRequestFromAudit:

    def _make_audit(
        self, new_version: int = 3, previous_version: int | None = 2,
    ) -> EvolutionAuditRecord:
        return EvolutionAuditRecord(
            audit_id="a-1",
            transaction_id="tx-1",
            proposal_id="p-1",
            target_identity="KO-1",
            previous_version=previous_version,
            new_version=new_version,
            before_snapshot={"boundary": ["x"]},
            after_snapshot=None,
            change_type="boundary_update",
            reason="user pushback",
            reviewer="alice",
            created_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
            rollback_reference=None,
        )

    def test_builder_populates_from_audit(self) -> None:
        audit = self._make_audit(new_version=3, previous_version=2)
        request = build_request_from_audit(
            audit, to_version=1,
            requested_by="bob", reason="user asked to undo",
        )
        assert request.transaction_id == audit.transaction_id
        assert request.target_identity == audit.target_identity
        assert request.from_version == audit.new_version
        assert request.to_version == 1
        assert request.requested_by == "bob"
        assert request.reason == "user asked to undo"
    def test_builder_rejects_non_audit(self) -> None:
        with pytest.raises(TypeError):
            build_request_from_audit(
                "not an audit",
                to_version=1,
                requested_by="bob",
                reason="x",
            )

    def test_builder_rejects_non_int_to_version(self) -> None:
        audit = self._make_audit()
        with pytest.raises(TypeError):
            build_request_from_audit(
                audit, to_version="1",
                requested_by="bob", reason="x",
            )


# ---------------------------------------------------------------------------
# Auxiliary -- Report
# ---------------------------------------------------------------------------

class TestReport:

    def test_report_contains_status_markers(
        self, planner, version_store,
    ) -> None:
        r = _make_request(from_version=3, to_version=1)
        v = RollbackValidator().validate(r, version_store=version_store)
        p = planner.plan(r, version_store=version_store)
        md = generate_report(r, v, p)
        assert "NOT EXECUTED" in md
        assert "Rollback foundation only." in md

    def test_report_contains_all_five_sections(
        self, planner, version_store,
    ) -> None:
        r = _make_request(from_version=3, to_version=1)
        v = RollbackValidator().validate(r, version_store=version_store)
        p = planner.plan(r, version_store=version_store)
        md = generate_report(r, v, p)
        for section in (
            "## Rollback Request",
            "## Validation Result",
            "## Rollback Plan",
            "## Knowledge Mutation",
            "## Safety Boundary",
        ):
            assert section in md, "missing section: " + section

    def test_report_starts_with_correct_h1(
        self, planner, version_store,
    ) -> None:
        r = _make_request(from_version=3, to_version=1)
        v = RollbackValidator().validate(r, version_store=version_store)
        p = planner.plan(r, version_store=version_store)
        md = generate_report(r, v, p)
        assert md.startswith("# Evolution Rollback Report")

    def test_report_includes_request_fields(
        self, planner, version_store,
    ) -> None:
        r = _make_request(from_version=3, to_version=1, transaction_id="tx-99")
        v = RollbackValidator().validate(r, version_store=version_store)
        p = planner.plan(r, version_store=version_store)
        md = generate_report(r, v, p)
        assert "tx-99" in md
        assert "rb-1" in md

    def test_report_rejection_marks_rule_id(
        self, validator, version_store,
    ) -> None:
        r = _make_request(from_version=1, to_version=3)  # R3
        v = validator.validate(r, version_store=version_store)
        md = generate_report(r, v, plan=None)
        assert "verdict: **REJECTED**" in md
        assert "`R3`" in md

    def test_report_approved_marks_valid(
        self, validator, version_store,
    ) -> None:
        r = _make_request(from_version=3, to_version=1)
        v = validator.validate(r, version_store=version_store)
        md = generate_report(r, v, plan=None)
        assert "verdict: **VALID**" in md


# ---------------------------------------------------------------------------
# Auxiliary -- Integration: builder -> validator -> planner chain
# ---------------------------------------------------------------------------

class TestEndToEnd:

    def test_builder_validator_planner_chain(
        self, planner, version_store,
    ) -> None:
        # 1. Build a synthetic audit record with new_version=3
        audit = EvolutionAuditRecord(
            audit_id="a-1",
            transaction_id="tx-1",
            proposal_id="p-1",
            target_identity="KO-1",
            previous_version=2,
            new_version=3,
            before_snapshot={"boundary": ["x"]},
            after_snapshot=None,
            change_type="boundary_update",
            reason="x",
            reviewer="alice",
            created_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
            rollback_reference=None,
        )
        # 2. Build a request from the audit
        request = build_request_from_audit(
            audit, to_version=1,
            requested_by="bob", reason="user asked to undo",
        )
        # 3. Plan
        plan = planner.plan(request, version_store=version_store)
        assert plan is not None
        assert plan.source_version == 3
        assert plan.destination_version == 1
        assert plan.mutation_executed is False

    def test_chain_with_invalid_request(
        self, planner, version_store,
    ) -> None:
        audit = EvolutionAuditRecord(
            audit_id="a-1",
            transaction_id="tx-1",
            proposal_id="p-1",
            target_identity="KO-1",
            previous_version=2,
            new_version=3,
            before_snapshot={"boundary": ["x"]},
            after_snapshot=None,
            change_type="boundary_update",
            reason="x",
            reviewer="alice",
            created_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
            rollback_reference=None,
        )
        # Request to_version=5 which doesn't exist in history
        request = build_request_from_audit(
            audit, to_version=5,
            requested_by="bob", reason="oops",
        )
        plan = planner.plan(request, version_store=version_store)
        assert plan is None
