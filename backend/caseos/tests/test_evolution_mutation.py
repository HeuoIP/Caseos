"""Knowledge Mutation Runtime tests (Sprint 22.4-H, ADR-020).

Test scope (Sprint 22.4-H spec):

    * KnowledgeMutationEngine.mutate
    * MutationValidator (M1-M5)
    * MutationRequest immutability, JSON serialisation
    * MutationResult success and failure paths
    * Snapshot isolation (old version unchanged after mutation)
    * AuditStore append-only invariant
    * AST architecture boundary
    * No apply / execute / restore / rollback / mutate / undo

Out of scope:

    * Pipeline wiring
    * Decision / Trust / Recommendation / Retrieval
    * KnowledgeObject in-place mutation
    * LLM / NLP / embedding / vector DB
"""
from __future__ import annotations

import ast
import dataclasses
import json
import pathlib
from datetime import datetime, timezone

import pytest

from caseos.knowledge.evolution.audit_v2 import (
    AuditStore,
    AuditStoreError,
    EvolutionAuditRecord,
)
from caseos.knowledge.evolution.governance import GovernanceResult
from caseos.knowledge.evolution.mutation import (
    MUTATION_ALLOWED_CHANGE_TYPES,
    KnowledgeMutationEngine,
    MutationRequest,
    MutationResult,
    MutationValidationResult,
    MutationValidator,
)
from caseos.knowledge.evolution.object import EvolutionTransaction
from caseos.knowledge.evolution.versioning import (
    KnowledgeVersion,
    VersionStore,
)


# ---------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------


KO_ID = "KO-1"
TX_ID = "tx-1"
MUT_ID = "mut-1"
REVIEWER = "alice"


def _ts() -> datetime:
    return datetime(2026, 8, 4, 12, 0, 0, tzinfo=timezone.utc)


def _seed_version(
    *,
    version_number: int = 1,
    previous_version: int | None = None,
    snapshot: dict | None = None,
) -> KnowledgeVersion:
    return KnowledgeVersion(
        version_id="v-" + str(version_number),
        target_identity=KO_ID,
        version_number=version_number,
        previous_version=previous_version,
        snapshot=dict(snapshot) if snapshot is not None else {
            "theme": "forest",
            "age": "3-6",
        },
        created_at=_ts(),
        created_by="seed",
        change_reason="seed",
        proposal_id="p-seed",
    )


def _seed_version_store(*, n: int = 1) -> VersionStore:
    vs = VersionStore()
    for i in range(1, n + 1):
        prev = i - 1 if i > 1 else None
        vs.append(_seed_version(version_number=i, previous_version=prev))
    return vs


def _seed_transaction(
    *,
    change_type: str = "boundary_update_candidate",
    target_identity: str = KO_ID,
    reviewer: str = REVIEWER,
    status: str = "APPROVED",
) -> EvolutionTransaction:
    return EvolutionTransaction(
        transaction_id=TX_ID,
        proposal_id="p-1",
        change_intent_id="ci-1",
        target_identity=target_identity,
        target_version=2,
        change_type=change_type,
        before_snapshot={"theme": "forest"},
        requested_change="update boundary field",
        reviewer=reviewer,
        status=status,
        created_at=_ts(),
    )


def _seed_governance(
    *, approved: bool = True,
) -> GovernanceResult:
    if approved:
        return GovernanceResult(
            approved=True,
            rule_id="",
            reason="",
            checked_at=_ts(),
        )
    return GovernanceResult(
        approved=False,
        rule_id="G5",
        reason="reviewer missing",
        checked_at=_ts(),
    )


def _seed_request(
    *,
    mutation_id: str = MUT_ID,
    target_identity: str = KO_ID,
    change_type: str = "boundary_update_candidate",
    before_version: int = 1,
    reviewer: str = REVIEWER,
    payload: dict | None = None,
) -> MutationRequest:
    if payload is None:
        payload = {
            "target_field": "boundary",
            "new_value": ["Do not add scattered equipment"],
        }
    return MutationRequest(
        mutation_id=mutation_id,
        transaction_id=TX_ID,
        target_identity=target_identity,
        change_type=change_type,
        before_version=before_version,
        change_payload=payload,
        reviewer=reviewer,
        created_at=_ts(),
    )


@pytest.fixture
def version_store() -> VersionStore:
    return _seed_version_store(n=1)


@pytest.fixture
def transaction() -> EvolutionTransaction:
    return _seed_transaction()


@pytest.fixture
def governance() -> GovernanceResult:
    return _seed_governance()


@pytest.fixture
def request_obj() -> MutationRequest:
    return _seed_request()


@pytest.fixture
def audit_store() -> AuditStore:
    return AuditStore()


@pytest.fixture
def engine() -> KnowledgeMutationEngine:
    return KnowledgeMutationEngine()


@pytest.fixture
def validator() -> MutationValidator:
    return MutationValidator()


# ---------------------------------------------------------------------
# Test 1 -- Happy Path Mutation
# ---------------------------------------------------------------------


class TestHappyPath:

    def test_happy_path_creates_version_and_audit(
        self, engine, request_obj, transaction,
        governance, version_store, audit_store,
    ) -> None:
        result = engine.mutate(
            request_obj, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert result.success is True
        assert result.mutation_executed is True
        assert result.mutation_id == MUT_ID
        assert result.transaction_id == TX_ID
        assert result.target_identity == KO_ID
        assert result.old_version == 1
        assert result.new_version == 2
        assert result.audit_id is not None

        # Version store should now have 2 versions for KO-1
        assert version_store.count() == 2
        assert len(version_store.history(KO_ID)) == 2

        # Audit store should have 1 record
        assert audit_store.count() == 1
        audit = audit_store.get(result.audit_id)
        assert audit is not None
        assert audit.transaction_id == TX_ID

    def test_happy_path_json_safe(
        self, engine, request_obj, transaction,
        governance, version_store, audit_store,
    ) -> None:
        result = engine.mutate(
            request_obj, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        encoded = json.dumps(result.to_dict())
        decoded = json.loads(encoded)
        assert decoded["mutation_id"] == MUT_ID
        assert decoded["mutation_executed"] is True
        assert decoded["success"] is True


# ---------------------------------------------------------------------
# Test 2 -- Old Version Immutable
# ---------------------------------------------------------------------


class TestOldVersionImmutable:

    def test_old_snapshot_unchanged_after_mutation(
        self, engine, request_obj, transaction,
        governance, version_store, audit_store,
    ) -> None:
        # Snapshot a reference to the old version's snapshot
        history_before = version_store.history(KO_ID)
        assert len(history_before) == 1
        old_version = history_before[0]
        old_snapshot_before = dict(old_version.snapshot)

        engine.mutate(
            request_obj, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )

        # Re-fetch the old version; its snapshot must not
        # have been modified.
        history_after = version_store.history(KO_ID)
        assert len(history_after) == 2
        old_version_after = history_after[0]
        assert old_version_after.version_number == 1
        assert old_version_after.snapshot == old_snapshot_before
        # Specifically: the new field must not leak into v1.
        assert "boundary" not in old_version_after.snapshot

    def test_old_version_record_is_same_instance(
        self, engine, request_obj, transaction,
        governance, version_store, audit_store,
    ) -> None:
        # The OLD KnowledgeVersion is frozen; the engine must
        # not even attempt to mutate it. Verify by checking
        # the version_id of v1 is unchanged after mutation.
        old_v1 = version_store.history(KO_ID)[0]
        v1_id_before = old_v1.version_id

        engine.mutate(
            request_obj, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )

        old_v1_after = version_store.history(KO_ID)[0]
        assert old_v1_after.version_id == v1_id_before


# ---------------------------------------------------------------------
# Test 3 -- New Version Created
# ---------------------------------------------------------------------


class TestNewVersionCreated:

    def test_new_version_is_one_more_than_old(
        self, engine, request_obj, transaction,
        governance, version_store, audit_store,
    ) -> None:
        result = engine.mutate(
            request_obj, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert result.new_version == 2
        new_version = version_store.get(KO_ID)
        assert new_version is not None
        assert new_version.version_number == 2

    def test_new_version_previous_version_points_to_old(
        self, engine, request_obj, transaction,
        governance, version_store, audit_store,
    ) -> None:
        engine.mutate(
            request_obj, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        history = version_store.history(KO_ID)
        assert len(history) == 2
        v1, v2 = history[0], history[1]
        assert v1.version_number == 1
        assert v2.version_number == 2
        assert v2.previous_version == 1
        assert v2.previous_version == v1.version_number

    def test_new_snapshot_has_applied_change(
        self, engine, request_obj, transaction,
        governance, version_store, audit_store,
    ) -> None:
        engine.mutate(
            request_obj, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        v2 = version_store.get(KO_ID)
        assert v2 is not None
        assert v2.snapshot.get("boundary") == [
            "Do not add scattered equipment",
        ]
        # Original fields preserved.
        assert v2.snapshot.get("theme") == "forest"
        assert v2.snapshot.get("age") == "3-6"


# ---------------------------------------------------------------------
# Test 4 -- Governance Reject
# ---------------------------------------------------------------------


class TestGovernanceReject:

    def test_governance_reject_creates_nothing(
        self, engine, request_obj, transaction,
        version_store, audit_store,
    ) -> None:
        bad_governance = _seed_governance(approved=False)
        result = engine.mutate(
            request_obj, transaction, bad_governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert result.success is False
        assert result.mutation_executed is False
        assert result.audit_id is None
        assert result.rejection_rule_id == "M2"

        # Stores must NOT have been touched.
        assert version_store.count() == 1
        assert audit_store.count() == 0

    def test_transaction_not_approved_creates_nothing(
        self, engine, request_obj, version_store,
        audit_store,
    ) -> None:
        bad_tx = _seed_transaction(status="PENDING")
        good_gov = _seed_governance(approved=True)
        result = engine.mutate(
            request_obj, bad_tx, good_gov,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert result.success is False
        assert result.mutation_executed is False
        assert result.rejection_rule_id == "M1"
        assert version_store.count() == 1
        assert audit_store.count() == 0


# ---------------------------------------------------------------------
# Test 5 -- Invalid Change Type
# ---------------------------------------------------------------------


class TestInvalidChangeType:

    @pytest.mark.parametrize("bad_type", [
        "identity_update",
        "delete",
        "rewrite",
        "unknown",
        "boundary_update",  # bare form is also rejected (M5 is literal)
    ])
    def test_bad_change_type_rejected(
        self, engine, transaction, governance,
        version_store, audit_store, bad_type,
    ) -> None:
        req = _seed_request(change_type=bad_type)
        result = engine.mutate(
            req, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert result.success is False
        assert result.mutation_executed is False
        assert result.rejection_rule_id == "M5"
        assert version_store.count() == 1
        assert audit_store.count() == 0


# ---------------------------------------------------------------------
# Test 6 -- Missing Reviewer
# ---------------------------------------------------------------------


class TestMissingReviewer:

    def test_empty_reviewer_rejected(
        self, engine, request_obj, governance,
        version_store, audit_store,
    ) -> None:
        # An empty reviewer on the TRANSACTION causes Governance
        # to reject (G5), which the mutation layer surfaces as
        # M2. This is the canonical rejection path; the mutation
        # layer never trusts a request whose transaction was
        # not properly reviewed.
        bad_tx = _seed_transaction(reviewer="")
        bad_gov = _seed_governance(approved=False)
        result = engine.mutate(
            request_obj, bad_tx, bad_gov,
            version_store=version_store,
            audit_store=audit_store,
        )
        assert result.success is False
        assert result.mutation_executed is False
        assert result.rejection_rule_id == "M2"
        assert version_store.count() == 1
        assert audit_store.count() == 0

    def test_missing_reviewer_on_transaction(
        self, engine, request_obj, governance,
        version_store, audit_store,
    ) -> None:
        # If the transaction has no reviewer, Governance would
        # normally reject (G5). For the mutation layer we
        # assume governance already approved it; the engine
        # only inspects the request. We document the current
        # behaviour: the request itself still has a reviewer,
        # so the mutation proceeds. (Future sprints may add a
        # rule that double-checks the transaction reviewer.)
        tx_no_reviewer = _seed_transaction(reviewer="")
        result = engine.mutate(
            request_obj, tx_no_reviewer, governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        # Engine does not cross-check the transaction reviewer
        # in V1; the mutation runs.
        assert result.success is True


# ---------------------------------------------------------------------
# Test 7 -- Audit Before / After
# ---------------------------------------------------------------------


class TestAuditBeforeAfter:

    def test_audit_records_before_and_after(
        self, engine, request_obj, transaction,
        governance, version_store, audit_store,
    ) -> None:
        result = engine.mutate(
            request_obj, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        audit = audit_store.get(result.audit_id)
        assert audit is not None
        assert isinstance(audit, EvolutionAuditRecord)
        assert audit.before_snapshot is not None
        assert audit.after_snapshot is not None
        # The new field exists in after but not in before.
        assert "boundary" not in audit.before_snapshot
        assert "boundary" in audit.after_snapshot
        assert audit.before_snapshot != audit.after_snapshot

    def test_audit_record_is_frozen(
        self, engine, request_obj, transaction,
        governance, version_store, audit_store,
    ) -> None:
        result = engine.mutate(
            request_obj, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        audit = audit_store.get(result.audit_id)
        assert audit is not None
        # The audit record is frozen; reassigning a field is
        # not allowed.
        import dataclasses
        with pytest.raises(dataclasses.FrozenInstanceError):
            audit.reviewer = "mallory"  # type: ignore[misc]

    def test_audit_records_required_fields(
        self, engine, request_obj, transaction,
        governance, version_store, audit_store,
    ) -> None:
        engine.mutate(
            request_obj, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        audit = audit_store.list()[0]
        assert audit.transaction_id == TX_ID
        assert audit.proposal_id == "p-1"
        assert audit.target_identity == KO_ID
        assert audit.reviewer == REVIEWER
        assert audit.previous_version == 1
        assert audit.new_version == 2


# ---------------------------------------------------------------------
# Test 8 -- Rollback Compatibility
# ---------------------------------------------------------------------


class TestRollbackCompatibility:

    def test_audit_has_old_and_new_versions(
        self, engine, request_obj, transaction,
        governance, version_store, audit_store,
    ) -> None:
        result = engine.mutate(
            request_obj, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        audit = audit_store.get(result.audit_id)
        assert audit.previous_version == 1
        assert audit.new_version == 2

    def test_no_rollback_methods_on_engine(self) -> None:
        # Sprint 22.4-H spec Task 6 forbids restore/rollback/
        # apply/undo on the mutation layer. mutate() is the
        # engine's primary entry point and is NOT forbidden.
        forbidden = {
            "apply", "restore", "rollback", "undo",
        }
        engine_methods = set(dir(KnowledgeMutationEngine))
        leaked = engine_methods & forbidden
        assert not leaked, (
            "engine exposes forbidden methods: " + str(leaked)
        )

    def test_no_rollback_methods_on_result(self) -> None:
        forbidden = {
            "apply", "restore", "rollback", "undo",
        }
        result_methods = set(dir(MutationResult))
        leaked = result_methods & forbidden
        assert not leaked, (
            "MutationResult exposes forbidden methods: "
            + str(leaked)
        )

    def test_rollback_not_invoked(
        self, engine, request_obj, transaction,
        governance, version_store, audit_store,
    ) -> None:
        # Run the mutation and verify that v1 is still
        # present in the store (no rollback consumed it).
        engine.mutate(
            request_obj, transaction, governance,
            version_store=version_store,
            audit_store=audit_store,
        )
        history = version_store.history(KO_ID)
        version_numbers = {v.version_number for v in history}
        assert 1 in version_numbers
        assert 2 in version_numbers


# ---------------------------------------------------------------------
# Test 9 -- Architecture Boundary (AST)
# ---------------------------------------------------------------------


class TestArchitectureBoundary:

    FORBIDDEN_PREFIXES = (
        "caseos.intelligence.decision",
        "caseos.intelligence.trust",
        "caseos.intelligence.recommendation",
        "caseos.knowledge.retrieval",
    )

    def _collect_imports(self, path: pathlib.Path) -> list[ast.Import | ast.ImportFrom]:
        src = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(src)
        imports: list[ast.Import | ast.ImportFrom] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.append(node)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node)
        return imports

    def _imported_modules(self, path: pathlib.Path) -> list[str]:
        names: list[str] = []
        for node in self._collect_imports(path):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    names.append(module + "." + alias.name)
        return names

    def test_mutation_package_no_forbidden_imports(self) -> None:
        pkg_root = pathlib.Path(__file__).resolve().parent.parent.joinpath(
            "knowledge", "evolution", "mutation"
        )
        for py_file in sorted(pkg_root.glob("*.py")):
            imported = self._imported_modules(py_file)
            for mod in imported:
                for forbidden in self.FORBIDDEN_PREFIXES:
                    assert not mod.startswith(forbidden), (
                        py_file.name
                        + " imports forbidden module: " + mod
                        + " (prefix: " + forbidden + ")"
                    )


# ---------------------------------------------------------------------
# Additional: Validator direct unit tests
# ---------------------------------------------------------------------


class TestValidatorDirect:

    def test_none_request_returns_M0(self, validator) -> None:
        r = validator.validate(None)
        assert r.valid is False
        assert r.rule_id == "M0"

    def test_valid_request(self, validator) -> None:
        r = validator.validate(
            _seed_request(),
            transaction=_seed_transaction(),
            governance=_seed_governance(),
            version_store=_seed_version_store(n=1),
        )
        assert r.valid is True

    def test_M1_unapproved_transaction(self, validator) -> None:
        r = validator.validate(
            _seed_request(),
            transaction=_seed_transaction(status="PENDING"),
            governance=_seed_governance(),
            version_store=_seed_version_store(n=1),
        )
        assert r.valid is False
        assert r.rule_id == "M1"

    def test_M2_governance_failed(self, validator) -> None:
        r = validator.validate(
            _seed_request(),
            transaction=_seed_transaction(),
            governance=_seed_governance(approved=False),
            version_store=_seed_version_store(n=1),
        )
        assert r.valid is False
        assert r.rule_id == "M2"

    def test_M3_identity_mismatch(self, validator) -> None:
        r = validator.validate(
            _seed_request(target_identity="KO-1"),
            transaction=_seed_transaction(target_identity="KO-2"),
            governance=_seed_governance(),
            version_store=_seed_version_store(n=1),
        )
        assert r.valid is False
        assert r.rule_id == "M3"

    def test_M5_change_type_not_allowed(self, validator) -> None:
        r = validator.validate(
            _seed_request(change_type="identity_update"),
            transaction=_seed_transaction(change_type="identity_update"),
            governance=_seed_governance(),
            version_store=_seed_version_store(n=1),
        )
        assert r.valid is False
        assert r.rule_id == "M5"

    def test_M4_version_not_in_history(self, validator) -> None:
        r = validator.validate(
            _seed_request(before_version=99),
            transaction=_seed_transaction(),
            governance=_seed_governance(),
            version_store=_seed_version_store(n=1),
        )
        assert r.valid is False
        assert r.rule_id == "M4"


# ---------------------------------------------------------------------
# Additional: MutationRequest contract
# ---------------------------------------------------------------------


class TestMutationRequestContract:

    def test_required_fields(self) -> None:
        actual = {f.name for f in dataclasses.fields(MutationRequest)}
        expected = {
            "mutation_id", "transaction_id", "target_identity",
            "change_type", "before_version", "change_payload",
            "reviewer", "created_at",
        }
        assert expected.issubset(actual), (
            "missing fields: " + str(expected - actual)
        )

    def test_frozen(self) -> None:
        r = _seed_request()
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.before_version = 99  # type: ignore[misc]

    def test_payload_isolation(self) -> None:
        original = {"target_field": "boundary", "new_value": ["x"]}
        r = _seed_request(payload=original)
        original["new_value"].append("INJECTED")
        assert r.change_payload["new_value"] == ["x"]

    def test_json_safe(self) -> None:
        r = _seed_request()
        encoded = json.dumps(r.to_dict())
        decoded = json.loads(encoded)
        assert decoded["mutation_id"] == MUT_ID
        assert decoded["transaction_id"] == TX_ID
        assert decoded["target_identity"] == KO_ID
        assert decoded["before_version"] == 1


# ---------------------------------------------------------------------
# Additional: Allow-list sanity
# ---------------------------------------------------------------------


class TestAllowList:

    def test_three_candidate_forms(self) -> None:
        assert MUTATION_ALLOWED_CHANGE_TYPES == frozenset({
            "boundary_update_candidate",
            "principle_update_candidate",
            "applicability_update_candidate",
        })
