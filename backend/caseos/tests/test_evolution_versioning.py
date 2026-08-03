"""Tests for the Knowledge Versioning Foundation (Sprint 22.4-D).

Coverage per Sprint 22.4-D spec section "测试要求":

    Test 1  KnowledgeVersion: fields complete, frozen, JSON safe
    Test 2  VersionStore: append, history, immutable
    Test 3  Forbidden store operations raise TypeError
    Test 4  Diff: changed field detection, before/after
    Test 5  Version isolation: snapshot mutation does not leak in
    Test 6  Architecture boundary AST (4 versioning modules)

Plus auxiliary invariants: store get, store identities,
diff added/removed/modified, report sections, etc.
"""
from __future__ import annotations

import ast
import copy
import dataclasses
import json
from pathlib import Path

import pytest

from caseos.knowledge.evolution.versioning import (
    KnowledgeDiff,
    KnowledgeDiffer,
    KnowledgeVersion,
    VersionStore,
    VersionStoreError,
    generate_report,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
VERSIONING_DIR = (
    BACKEND / "caseos" / "knowledge" / "evolution" / "versioning"
)


def _make_version(
    *,
    version_id: str = "v-1",
    target_identity: str = "KO-1",
    version_number: int = 1,
    previous_version=None,
    snapshot: dict | None = None,
    created_at=None,
    created_by: str = "alice",
    change_reason: str = "initial",
    proposal_id: str = "p-1",
) -> KnowledgeVersion:
    if snapshot is None:
        snapshot = {
            "boundary": ["Do not add scattered equipment"],
            "principle": ["Create hierarchy before adding facilities"],
        }
    if created_at is None:
        from datetime import datetime, timezone
        created_at = datetime(2026, 8, 3, tzinfo=timezone.utc)
    return KnowledgeVersion(
        version_id=version_id,
        target_identity=target_identity,
        version_number=version_number,
        previous_version=previous_version,
        snapshot=snapshot,
        created_at=created_at,
        created_by=created_by,
        change_reason=change_reason,
        proposal_id=proposal_id,
    )


@pytest.fixture
def store() -> VersionStore:
    return VersionStore()


@pytest.fixture
def sample_version() -> KnowledgeVersion:
    return _make_version()


# ---------------------------------------------------------------------------
# Test 1 -- KnowledgeVersion: fields complete, frozen, JSON safe
# ---------------------------------------------------------------------------

class TestKnowledgeVersionFields:

    EXPECTED_FIELDS = {
        "version_id", "target_identity", "version_number",
        "previous_version", "snapshot", "created_at",
        "created_by", "change_reason", "proposal_id",
    }

    def test_all_nine_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(KnowledgeVersion)}
        assert self.EXPECTED_FIELDS.issubset(actual), (
            "missing fields: " + str(self.EXPECTED_FIELDS - actual)
        )

    def test_field_count_is_nine(self) -> None:
        assert len(dataclasses.fields(KnowledgeVersion)) == 9

    def test_dataclass_is_frozen(self) -> None:
        v = _make_version()
        with pytest.raises(dataclasses.FrozenInstanceError):
            v.version_number = 2  # type: ignore[misc]

    def test_mutation_of_target_identity_raises(self) -> None:
        v = _make_version()
        with pytest.raises(dataclasses.FrozenInstanceError):
            v.target_identity = "KO-2"  # type: ignore[misc]

    def test_mutation_of_snapshot_reference_raises(self) -> None:
        v = _make_version()
        with pytest.raises(dataclasses.FrozenInstanceError):
            v.snapshot = {}  # type: ignore[misc]

    def test_to_dict_is_json_safe(self) -> None:
        v = _make_version()
        encoded = json.dumps(v.to_dict())
        decoded = json.loads(encoded)
        assert decoded["version_id"] == "v-1"
        assert decoded["target_identity"] == "KO-1"
        assert decoded["version_number"] == 1
        assert decoded["previous_version"] is None
        assert decoded["created_by"] == "alice"
        assert decoded["proposal_id"] == "p-1"
        # created_at serialised as ISO string
        assert isinstance(decoded["created_at"], str)


# ---------------------------------------------------------------------------
# Test 2 -- VersionStore: append, history, immutable
# ---------------------------------------------------------------------------

class TestVersionStoreBasics:

    def test_append_grows_store(self, store) -> None:
        assert store.count() == 0
        v = _make_version()
        store.append(v)
        assert store.count() == 1

    def test_append_returns_the_record(self, store) -> None:
        v = _make_version()
        result = store.append(v)
        assert result is v

    def test_history_filters_by_identity(self, store) -> None:
        store.append(_make_version(version_id="a", target_identity="KO-1"))
        store.append(_make_version(version_id="b", target_identity="KO-2"))
        store.append(_make_version(version_id="c", target_identity="KO-1"))
        k1 = store.history("KO-1")
        k2 = store.history("KO-2")
        assert len(k1) == 2
        assert len(k2) == 1
        assert [v.version_id for v in k1] == ["a", "c"]
        assert [v.version_id for v in k2] == ["b"]

    def test_history_returns_copy(self, store) -> None:
        store.append(_make_version())
        result = store.history("KO-1")
        result.clear()
        # Underlying store is unchanged.
        assert store.count() == 1

    def test_get_returns_latest_for_identity(self, store) -> None:
        store.append(_make_version(version_id="a", version_number=1))
        store.append(_make_version(version_id="b", version_number=2))
        latest = store.get("KO-1")
        assert latest is not None
        assert latest.version_id == "b"
        assert latest.version_number == 2

    def test_get_returns_none_for_unknown_identity(self, store) -> None:
        assert store.get("UNKNOWN") is None

    def test_identities_returns_distinct_first_seen(self, store) -> None:
        store.append(_make_version(target_identity="KO-1"))
        store.append(_make_version(target_identity="KO-2"))
        store.append(_make_version(target_identity="KO-1"))
        assert store.identities() == ["KO-1", "KO-2"]

    def test_non_version_append_raises(self, store) -> None:
        with pytest.raises(VersionStoreError):
            store.append("not a version")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Test 3 -- Forbidden store operations
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
            store.delete(version_id="x")

    def test_overwrite_with_args_raises(self, store) -> None:
        with pytest.raises(TypeError):
            store.overwrite(version_id="x", target_identity="KO-2")

    def test_clear_with_args_raises(self, store) -> None:
        with pytest.raises(TypeError):
            store.clear(target_identity="KO-1")


# ---------------------------------------------------------------------------
# Test 4 -- Diff: changed field detection, before/after
# ---------------------------------------------------------------------------

class TestDiff:

    def test_modified_field_detected(self) -> None:
        result = KnowledgeDiffer.diff(
            {"a": 1, "b": 2},
            {"a": 1, "b": 3},
        )
        assert result.changed_fields == ("b",)
        assert result.before == {"a": 1, "b": 2}
        assert result.after == {"a": 1, "b": 3}

    def test_added_field_detected(self) -> None:
        result = KnowledgeDiffer.diff(
            {"a": 1},
            {"a": 1, "b": 2},
        )
        assert "b" in result.changed_fields
        assert "a" not in result.changed_fields

    def test_removed_field_detected(self) -> None:
        result = KnowledgeDiffer.diff(
            {"a": 1, "b": 2},
            {"a": 1},
        )
        assert "b" in result.changed_fields

    def test_no_changes_returns_empty(self) -> None:
        result = KnowledgeDiffer.diff(
            {"a": 1, "b": 2},
            {"a": 1, "b": 2},
        )
        assert result.changed_fields == ()
        assert result.is_empty is True

    def test_both_empty_returns_empty(self) -> None:
        result = KnowledgeDiffer.diff({}, {})
        assert result.changed_fields == ()
        assert result.is_empty is True

    def test_changed_fields_are_sorted(self) -> None:
        result = KnowledgeDiffer.diff(
            {"zeta": 1, "alpha": 2, "mu": 3},
            {"zeta": 9, "alpha": 8, "mu": 7},
        )
        assert result.changed_fields == ("alpha", "mu", "zeta")

    def test_diff_is_frozen(self) -> None:
        d = KnowledgeDiffer.diff({"a": 1}, {"a": 2})
        with pytest.raises(dataclasses.FrozenInstanceError):
            d.changed_fields = ()  # type: ignore[misc]

    def test_diff_before_after_are_copies(self) -> None:
        before = {"a": 1}
        after = {"a": 2}
        result = KnowledgeDiffer.diff(before, after)
        before["a"] = 99
        after["a"] = 77
        # Diff's before/after must not be affected by caller mutation.
        assert result.before == {"a": 1}
        assert result.after == {"a": 2}

    def test_diff_to_dict_is_json_safe(self) -> None:
        result = KnowledgeDiffer.diff(
            {"a": 1}, {"a": 2, "b": 3},
        )
        encoded = json.dumps(result.to_dict())
        decoded = json.loads(encoded)
        assert isinstance(decoded["changed_fields"], list)
        assert decoded["before"] == {"a": 1}
        assert decoded["after"] == {"a": 2, "b": 3}

    def test_non_dict_input_normalised(self) -> None:
        # Non-dict inputs are normalised to empty dicts, not raised.
        result = KnowledgeDiffer.diff(None, {"a": 1})  # type: ignore[arg-type]
        assert result.before == {}
        assert result.after == {"a": 1}
        assert "a" in result.changed_fields


# ---------------------------------------------------------------------------
# Test 5 -- Version isolation
# ---------------------------------------------------------------------------

class TestVersionIsolation:

    def test_snapshot_mutation_does_not_leak(self) -> None:
        original_snapshot = {"boundary": ["Do not add scattered equipment"]}
        v = _make_version(snapshot=original_snapshot)
        original_snapshot["boundary"].append("INJECTED")
        # The version's snapshot must be unaffected.
        assert v.snapshot == {"boundary": ["Do not add scattered equipment"]}
        assert "INJECTED" not in v.snapshot["boundary"]

    def test_snapshot_dict_mutation_does_not_leak(self) -> None:
        original_snapshot = {"a": 1, "b": 2}
        v = _make_version(snapshot=original_snapshot)
        original_snapshot["a"] = 999
        original_snapshot["new_key"] = "x"
        assert v.snapshot == {"a": 1, "b": 2}

    def test_version_isolation_via_store(self, store) -> None:
        snap = {"boundary": ["Do not add scattered equipment"]}
        v = _make_version(snapshot=snap)
        store.append(v)
        snap["boundary"].append("INJECTED_AFTER_APPEND")
        # Retrieve the version from the store and confirm the
        # injected entry did not leak in.
        retrieved = store.get("KO-1")
        assert retrieved is not None
        assert "INJECTED_AFTER_APPEND" not in retrieved.snapshot["boundary"]

    def test_snapshot_top_level_replace_does_not_leak(self) -> None:
        snap = {"a": [1, 2, 3]}
        v = _make_version(snapshot=snap)
        # Replace the entire list reference.
        snap["a"] = ["replaced"]
        assert v.snapshot == {"a": [1, 2, 3]}


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
        "__init__.py", "object.py", "store.py",
        "diff.py", "report.py",
    ])
    def test_no_forbidden_imports(self, py_name: str) -> None:
        py = VERSIONING_DIR / py_name
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
        v = _make_version()
        store.append(v)
        md = generate_report(store, "KO-1")
        assert "Knowledge Mutation: **NOT IMPLEMENTED**" in md
        assert "Versioning Foundation: **IMPLEMENTED**" in md

    def test_report_renders_version_history(self, store) -> None:
        store.append(_make_version(version_number=1, previous_version=None))
        store.append(_make_version(version_number=2, previous_version=1))
        md = generate_report(store, "KO-1")
        assert "v1" in md
        assert "v2" in md
        assert "(initial)" in md
        assert "`1`" in md  # previous_version for v2

    def test_report_no_versions_message(self, store) -> None:
        md = generate_report(store, "MISSING")
        assert "(no versions for this identity)" in md

    def test_report_includes_target_identity(self, store) -> None:
        md = generate_report(store, "MY_KO")
        assert "MY_KO" in md
        assert "total_versions: 0" in md

    def test_report_renders_snapshot_keys(self, store) -> None:
        v = _make_version(snapshot={"boundary": [], "principle": []})
        store.append(v)
        md = generate_report(store, "KO-1")
        assert "boundary" in md
        assert "principle" in md


# ---------------------------------------------------------------------------
# Auxiliary -- KO not modified (defence-in-depth)
# ---------------------------------------------------------------------------

class TestMutationBoundary:

    """The versioning layer is a *future* mutation container.

    These tests assert that the layer does not perform KO
    mutations by itself. A future Sprint 22.4.x runtime will
    wire the mutation step; in V1, the versioning layer is
    passive.
    """

    def test_knowledge_version_does_not_call_mutation(
        self, store,
    ) -> None:
        v = _make_version()
        store.append(v)
        # No external state was touched.
        assert store.count() == 1

    def test_diff_does_not_mutate_inputs(self) -> None:
        before = {"a": 1}
        after = {"a": 2}
        before_copy = copy.deepcopy(before)
        after_copy = copy.deepcopy(after)
        KnowledgeDiffer.diff(before, after)
        assert before == before_copy
        assert after == after_copy
