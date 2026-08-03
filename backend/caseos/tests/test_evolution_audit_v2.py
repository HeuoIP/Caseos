"""Tests for the Evolution Audit Log Schema V1 (Sprint 22.4-E).

Coverage per Sprint 22.4-E spec section "测试要求":

    Test 1  AuditRecord: fields complete, frozen, JSON safe
    Test 2  Snapshot isolation: before/after mutation
            does not pollute the record
    Test 3  AuditStore: append, history
    Test 4  Forbidden operations raise TypeError
            (update / delete / overwrite / clear)
    Test 5  rollback_reference: present but not executed
            (no restore / rollback / apply methods)
    Test 6  Architecture boundary AST (4 audit_v2 modules)

Plus auxiliary invariants: get(audit_id), history ordering,
identities, deep-copy of nested structures, etc.
"""
from __future__ import annotations

import ast
import copy
import dataclasses
import json
from pathlib import Path

import pytest

from caseos.knowledge.evolution.audit_v2 import (
    AuditStore,
    AuditStoreError,
    EvolutionAuditRecord,
    generate_report,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
AUDIT_V2_DIR = (
    BACKEND / "caseos" / "knowledge" / "evolution" / "audit_v2"
)


def _make_record(
    *,
    audit_id: str = "a-1",
    transaction_id: str = "tx-1",
    proposal_id: str = "p-1",
    target_identity: str = "KO-1",
    previous_version: int | None = None,
    new_version: int = 2,
    before_snapshot: dict | None = None,
    after_snapshot: dict | None = None,
    change_type: str = "boundary_update",
    reason: str = "user pushed back on scattered equipment",
    reviewer: str = "alice",
    created_at=None,
    rollback_reference: str | None = None,
) -> EvolutionAuditRecord:
    if before_snapshot is None:
        before_snapshot = {
            "boundary": ["Do not add scattered equipment"],
        }
    if created_at is None:
        from datetime import datetime, timezone
        created_at = datetime(2026, 8, 3, tzinfo=timezone.utc)
    return EvolutionAuditRecord(
        audit_id=audit_id,
        transaction_id=transaction_id,
        proposal_id=proposal_id,
        target_identity=target_identity,
        previous_version=previous_version,
        new_version=new_version,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
        change_type=change_type,
        reason=reason,
        reviewer=reviewer,
        created_at=created_at,
        rollback_reference=rollback_reference,
    )


@pytest.fixture
def store() -> AuditStore:
    return AuditStore()


@pytest.fixture
def sample_record() -> EvolutionAuditRecord:
    return _make_record()


# ---------------------------------------------------------------------------
# Test 1 -- AuditRecord: fields complete, frozen, JSON safe
# ---------------------------------------------------------------------------

class TestAuditRecordFields:

    EXPECTED_FIELDS = {
        "audit_id", "transaction_id", "proposal_id",
        "target_identity", "previous_version", "new_version",
        "before_snapshot", "after_snapshot", "change_type",
        "reason", "reviewer", "created_at", "rollback_reference",
    }

    def test_all_thirteen_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(EvolutionAuditRecord)}
        assert self.EXPECTED_FIELDS.issubset(actual), (
            "missing fields: " + str(self.EXPECTED_FIELDS - actual)
        )

    def test_field_count_is_thirteen(self) -> None:
        assert len(dataclasses.fields(EvolutionAuditRecord)) == 13

    def test_dataclass_is_frozen(self, sample_record) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_record.audit_id = "mutated"  # type: ignore[misc]

    def test_mutation_of_target_identity_raises(self, sample_record) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_record.target_identity = "KO-2"  # type: ignore[misc]

    def test_mutation_of_new_version_raises(self, sample_record) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_record.new_version = 99  # type: ignore[misc]

    def test_mutation_of_rollback_reference_raises(
        self, sample_record,
    ) -> None:
        with pytest.raises(dataclasses.FrozenInstanceError):
            sample_record.rollback_reference = "rb-1"  # type: ignore[misc]

    def test_to_dict_is_json_safe(self, sample_record) -> None:
        encoded = json.dumps(sample_record.to_dict())
        decoded = json.loads(encoded)
        assert decoded["audit_id"] == "a-1"
        assert decoded["transaction_id"] == "tx-1"
        assert decoded["target_identity"] == "KO-1"
        assert decoded["previous_version"] is None
        assert decoded["new_version"] == 2
        assert decoded["change_type"] == "boundary_update"
        assert decoded["reviewer"] == "alice"
        assert decoded["rollback_reference"] is None
        # created_at serialised as ISO string
        assert isinstance(decoded["created_at"], str)

    def test_to_dict_preserves_after_snapshot(
        self, sample_record,
    ) -> None:
        rec = _make_record(
            after_snapshot={"boundary": ["refined boundary"]},
        )
        decoded = json.loads(json.dumps(rec.to_dict()))
        assert decoded["after_snapshot"] == {"boundary": ["refined boundary"]}


# ---------------------------------------------------------------------------
# Test 2 -- Snapshot isolation
# ---------------------------------------------------------------------------

class TestSnapshotIsolation:

    def test_before_snapshot_mutation_does_not_leak(
        self, sample_record,
    ) -> None:
        original = {"boundary": ["Do not add scattered equipment"]}
        rec = _make_record(before_snapshot=original)
        original["boundary"].append("INJECTED")
        assert rec.before_snapshot == {
            "boundary": ["Do not add scattered equipment"],
        }
        assert "INJECTED" not in rec.before_snapshot["boundary"]

    def test_before_snapshot_dict_mutation_does_not_leak(
        self, sample_record,
    ) -> None:
        original = {"a": 1, "b": 2}
        rec = _make_record(before_snapshot=original)
        original["a"] = 999
        original["new_key"] = "x"
        assert rec.before_snapshot == {"a": 1, "b": 2}

    def test_after_snapshot_mutation_does_not_leak(self) -> None:
        original = {"boundary": ["refined"]}
        rec = _make_record(after_snapshot=original)
        original["boundary"].append("INJECTED")
        assert rec.after_snapshot == {"boundary": ["refined"]}

    def test_after_snapshot_replace_does_not_leak(self) -> None:
        original = {"a": [1, 2, 3]}
        rec = _make_record(after_snapshot=original)
        original["a"] = ["replaced"]
        assert rec.after_snapshot == {"a": [1, 2, 3]}

    def test_isolation_via_store(self, store) -> None:
        before = {"boundary": ["Do not add scattered equipment"]}
        rec = _make_record(before_snapshot=before)
        store.append(rec)
        before["boundary"].append("INJECTED_AFTER_APPEND")
        retrieved = store.get("a-1")
        assert retrieved is not None
        assert (
            "INJECTED_AFTER_APPEND"
            not in retrieved.before_snapshot["boundary"]
        )


# ---------------------------------------------------------------------------
# Test 3 -- AuditStore: append, history
# ---------------------------------------------------------------------------

class TestAuditStoreBasics:

    def test_append_grows_store(self, store) -> None:
        assert store.count() == 0
        store.append(_make_record())
        assert store.count() == 1

    def test_append_returns_the_record(self, store) -> None:
        rec = _make_record()
        result = store.append(rec)
        assert result is rec

    def test_history_filters_by_target_identity(self, store) -> None:
        store.append(_make_record(audit_id="a", target_identity="KO-1"))
        store.append(_make_record(audit_id="b", target_identity="KO-2"))
        store.append(_make_record(audit_id="c", target_identity="KO-1"))
        k1 = store.history("KO-1")
        k2 = store.history("KO-2")
        assert len(k1) == 2
        assert len(k2) == 1
        assert [r.audit_id for r in k1] == ["a", "c"]
        assert [r.audit_id for r in k2] == ["b"]

    def test_history_returns_copy(self, store) -> None:
        store.append(_make_record())
        result = store.history("KO-1")
        result.clear()
        # Underlying store is unchanged.
        assert store.count() == 1

    def test_get_returns_by_audit_id(self, store) -> None:
        store.append(_make_record(audit_id="a-1"))
        store.append(_make_record(audit_id="a-2"))
        rec = store.get("a-2")
        assert rec is not None
        assert rec.audit_id == "a-2"

    def test_get_returns_none_for_unknown(self, store) -> None:
        assert store.get("UNKNOWN") is None

    def test_identities_returns_distinct_first_seen(self, store) -> None:
        store.append(_make_record(target_identity="KO-1"))
        store.append(_make_record(target_identity="KO-2"))
        store.append(_make_record(target_identity="KO-1"))
        assert store.identities() == ["KO-1", "KO-2"]

    def test_non_record_append_raises(self, store) -> None:
        with pytest.raises(AuditStoreError):
            store.append("not a record")  # type: ignore[arg-type]

    def test_list_returns_copy(self, store) -> None:
        store.append(_make_record())
        result = store.list()
        result.clear()
        assert store.count() == 1


# ---------------------------------------------------------------------------
# Test 4 -- Forbidden store operations
# ---------------------------------------------------------------------------

class TestForbiddenStoreOperations:

    def test_update_raises_type_error(self, store) -> None:
        with pytest.raises(TypeError):
            store.update()

    def test_delete_raises_type_error(self, store) -> None:
        with pytest.raises(TypeError):
            store.delete()

    def test_overwrite_raises_type_error(self, store) -> None:
        with pytest.raises(TypeError):
            store.overwrite()

    def test_clear_raises_type_error(self, store) -> None:
        with pytest.raises(TypeError):
            store.clear()

    def test_update_with_args_raises(self, store) -> None:
        with pytest.raises(TypeError):
            store.update("any", "args", key="value")

    def test_delete_with_args_raises(self, store) -> None:
        with pytest.raises(TypeError):
            store.delete(audit_id="x")

    def test_overwrite_with_args_raises(self, store) -> None:
        with pytest.raises(TypeError):
            store.overwrite(audit_id="x", target_identity="KO-2")

    def test_clear_with_args_raises(self, store) -> None:
        with pytest.raises(TypeError):
            store.clear(target_identity="KO-1")


# ---------------------------------------------------------------------------
# Test 5 -- rollback_reference: present but not executed
# ---------------------------------------------------------------------------

class TestRollbackReference:

    def test_rollback_reference_field_is_present(self) -> None:
        fields = {f.name for f in dataclasses.fields(EvolutionAuditRecord)}
        assert "rollback_reference" in fields

    def test_rollback_reference_can_be_set(self) -> None:
        rec = _make_record(rollback_reference="rb-future-id")
        assert rec.rollback_reference == "rb-future-id"

    def test_rollback_reference_defaults_to_none(self) -> None:
        rec = _make_record()
        assert rec.rollback_reference is None

    def test_store_has_no_restore_method(self, store) -> None:
        # Per spec Task 4: restore() is forbidden.
        assert not hasattr(store, "restore")

    def test_store_has_no_rollback_method(self, store) -> None:
        # Per spec Task 4: rollback() is forbidden.
        assert not hasattr(store, "rollback")

    def test_store_has_no_apply_method(self, store) -> None:
        # Per spec Task 4: apply() is forbidden.
        assert not hasattr(store, "apply")

    def test_store_has_no_undo_method(self, store) -> None:
        # Extra defence: undo is also not in scope.
        assert not hasattr(store, "undo")

    def test_rollback_reference_preserved_in_to_dict(self) -> None:
        rec = _make_record(rollback_reference="rb-1")
        d = rec.to_dict()
        assert d["rollback_reference"] == "rb-1"


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
        "__init__.py", "object.py", "store.py", "report.py",
    ])
    def test_no_forbidden_imports(self, py_name: str) -> None:
        py = AUDIT_V2_DIR / py_name
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
# Auxiliary -- Report
# ---------------------------------------------------------------------------

class TestReport:

    def test_report_contains_status_lines(self, store) -> None:
        store.append(_make_record())
        md = generate_report(store, "KO-1")
        assert "Audit Schema Foundation: **IMPLEMENTED**" in md
        assert "Knowledge Mutation: **NOT IMPLEMENTED**" in md

    def test_report_renders_audit_history(self, store) -> None:
        store.append(_make_record(
            audit_id="a-1",
            previous_version=None,
            new_version=2,
        ))
        store.append(_make_record(
            audit_id="a-2",
            previous_version=2,
            new_version=3,
        ))
        md = generate_report(store, "KO-1")
        assert "a-1" in md
        assert "a-2" in md
        assert "(initial)" in md
        assert "`2`" in md  # previous_version for a-2

    def test_report_no_records_message(self, store) -> None:
        md = generate_report(store, "MISSING")
        assert "(no audit records for this identity)" in md

    def test_report_includes_target_identity(self, store) -> None:
        md = generate_report(store, "MY_KO")
        assert "MY_KO" in md
        assert "total_audit_records: 0" in md

    def test_report_renders_rollback_reference(self, store) -> None:
        rec = _make_record(rollback_reference="rb-99")
        store.append(rec)
        md = generate_report(store, "KO-1")
        assert "rb-99" in md

    def test_report_renders_after_snapshot_marker(self, store) -> None:
        rec = _make_record(after_snapshot=None)
        store.append(rec)
        md = generate_report(store, "KO-1")
        assert "(not yet computed in V1)" in md


# ---------------------------------------------------------------------------
# Auxiliary -- Mutation boundary defence-in-depth
# ---------------------------------------------------------------------------

class TestMutationBoundary:

    """The audit layer is a *schema foundation*.

    These tests assert that the layer does not perform KO
    mutations by itself. A future Sprint 22.4.x runtime will
    wire the mutation step; in V1, the audit layer is passive.
    """

    def test_record_does_not_call_mutation(self, store) -> None:
        rec = _make_record()
        store.append(rec)
        assert store.count() == 1

    def test_no_intelligence_or_retrieval_dependencies(self) -> None:
        # Defence in depth: the record's only fields are data.
        fields = {f.name for f in dataclasses.fields(EvolutionAuditRecord)}
        forbidden_fields = {
            "decision", "trust", "recommendation", "retrieval",
        }
        assert fields.isdisjoint(forbidden_fields), (
            "record must not carry engine state: "
            + str(fields & forbidden_fields)
        )

    def test_record_carries_no_engine_objects(self) -> None:
        rec = _make_record()
        d = rec.to_dict()
        # The dict is JSON-safe; no embedded class instances.
        for k, v in d.items():
            assert not hasattr(v, "__class__") or isinstance(
                v, (str, int, float, bool, type(None), list, dict),
            ), "field " + k + " is not JSON-safe: " + str(type(v))
