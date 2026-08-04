"""Evolution Contract Alignment tests (Sprint 22.4-I, ADR-020).

Verifies that the unified ``EvolutionChangeType`` enum
propagates correctly across the CaseOS Evolution Pipeline:

    LearningProposal (proposal_type)
        |
        v
    InterpretationPolicy
        |
        v
    ChangeIntent                <-- uses EvolutionChangeType
        |
        v
    EvolutionTransaction        <-- uses EvolutionChangeType
        |
        v
    EvolutionGovernanceGate
        |
        v
    KnowledgeMutationEngine     <-- uses EvolutionChangeType
        |
        v
    EvolutionAuditRecord        <-- uses EvolutionChangeType

Tests cover:

    Test 1   Enum fields
    Test 2   Feedback Interpretation output
    Test 3   Transaction propagation
    Test 4   Governance accepts all three V1 allowed types
    Test 5   Mutation accepts all three V1 allowed types
    Test 6   Forbidden types (identity_update, delete, rewrite,
             unknown, _candidate suffix) rejected across the
             pipeline
    Test 7   JSON compatibility (round-trip)
    Test 8   Architecture boundary (AST scan)

Out of scope:

    * Pipeline wiring
    * Decision / Trust / Recommendation / Retrieval
    * Knowledge Object mutation
    * LLM / NLP / embedding / vector DB
"""
from __future__ import annotations

import ast
import json
import pathlib
from datetime import datetime, timezone
from enum import Enum

import pytest

from caseos.knowledge.evolution.audit_v2 import (
    AuditStore,
    EvolutionAuditRecord,
)
from caseos.knowledge.evolution.contracts.change_type import (
    EvolutionChangeType,
)
from caseos.knowledge.evolution.governance import (
    EvolutionGovernanceGate,
    GovernanceResult,
)
from caseos.knowledge.evolution.mutation import (
    MUTATION_ALLOWED_CHANGE_TYPES,
    KnowledgeMutationEngine,
    MutationRequest,
    MutationValidator,
)
from caseos.knowledge.evolution.object import EvolutionTransaction
from caseos.knowledge.evolution.policy import (
    ALLOWED_CHANGE_TYPES,
    EvolutionChangePolicy,
)
from caseos.knowledge.evolution.versioning import (
    KnowledgeVersion,
    VersionStore,
)
from caseos.knowledge.feedback.interpretation import (
    ChangeIntent,
    InterpretationPolicy,
    validate_change_intent,
)
from caseos.knowledge.feedback.proposal import (
    PROPOSAL_TYPE_BOUNDARY,
    PROPOSAL_TYPE_PRINCIPLE,
)


# ---------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------


KO_ID = "KO-1"


def _ts() -> datetime:
    return datetime(2026, 8, 4, 12, 0, 0, tzinfo=timezone.utc)


def _make_proposal(
    *,
    proposal_type: str = PROPOSAL_TYPE_BOUNDARY,
    target_identity: str = KO_ID,
    reason: str = "boundary feedback",
):
    """Return a minimal LearningProposal object for InterpretationPolicy."""
    from caseos.knowledge.feedback.proposal import LearningProposal
    return LearningProposal(
        proposal_id="p-1",
        feedback_id="f-1",
        target_identity=target_identity,
        proposal_type=proposal_type,
        current_state={"boundary": ["x"]},
        suggested_change="update boundary",
        reason=reason,
        requires_human_review=True,
        status="APPROVED",
    )


def _make_knowledge_object() -> dict:
    return {"identity": KO_ID, "boundary": ["Do not add scattered equipment"]}


def _make_transaction(
    *,
    change_type=EvolutionChangeType.BOUNDARY_UPDATE,
    target_identity: str = KO_ID,
    reviewer: str = "alice",
    status: str = "APPROVED",
) -> EvolutionTransaction:
    return EvolutionTransaction(
        transaction_id="tx-1",
        proposal_id="p-1",
        change_intent_id="ci-1",
        target_identity=target_identity,
        target_version=2,
        change_type=change_type,
        before_snapshot={"boundary": ["x"]},
        requested_change="update boundary",
        reviewer=reviewer,
        status=status,
        created_at=_ts(),
    )


def _make_governance(*, approved: bool = True) -> GovernanceResult:
    return GovernanceResult(
        approved=approved, rule_id="", reason="",
        checked_at=_ts(),
    )


def _make_version_store() -> VersionStore:
    vs = VersionStore()
    vs.append(KnowledgeVersion(
        version_id="v-1", target_identity=KO_ID,
        version_number=1, previous_version=None,
        snapshot={"boundary": ["x"]},
        created_at=_ts(), created_by="seed",
        change_reason="seed", proposal_id="p-seed",
    ))
    return vs


def _make_request(
    *,
    change_type=EvolutionChangeType.BOUNDARY_UPDATE,
    before_version: int = 1,
) -> MutationRequest:
    return MutationRequest(
        mutation_id="mut-1",
        transaction_id="tx-1",
        target_identity=KO_ID,
        change_type=change_type,
        before_version=before_version,
        change_payload={
            "target_field": "boundary",
            "new_value": ["Do not add scattered equipment"],
        },
        reviewer="alice",
        created_at=_ts(),
    )


@pytest.fixture
def policy() -> InterpretationPolicy:
    return InterpretationPolicy()


@pytest.fixture
def governance_gate() -> EvolutionGovernanceGate:
    return EvolutionGovernanceGate()


@pytest.fixture
def mutation_engine() -> KnowledgeMutationEngine:
    return KnowledgeMutationEngine()


@pytest.fixture
def mutation_validator() -> MutationValidator:
    return MutationValidator()


# ---------------------------------------------------------------------
# Test 1 -- Enum fields
# ---------------------------------------------------------------------


class TestEnumFields:

    def test_three_members_present(self) -> None:
        assert hasattr(EvolutionChangeType, "BOUNDARY_UPDATE")
        assert hasattr(EvolutionChangeType, "PRINCIPLE_UPDATE")
        assert hasattr(EvolutionChangeType, "APPLICABILITY_UPDATE")

    def test_values_are_bare_strings(self) -> None:
        assert EvolutionChangeType.BOUNDARY_UPDATE.value == "boundary_update"
        assert EvolutionChangeType.PRINCIPLE_UPDATE.value == "principle_update"
        assert EvolutionChangeType.APPLICABILITY_UPDATE.value == (
            "applicability_update"
        )

    def test_no_candidate_suffix(self) -> None:
        for member in EvolutionChangeType:
            assert "_candidate" not in member.value, (
                "EvolutionChangeType values must not have _candidate suffix: "
                + member.name
            )

    def test_is_enum_subclass(self) -> None:
        assert issubclass(EvolutionChangeType, Enum)


# ---------------------------------------------------------------------
# Test 2 -- Feedback Interpretation output
# ---------------------------------------------------------------------


class TestInterpretationOutput:

    def test_boundary_proposal_maps_to_enum(
        self, policy,
    ) -> None:
        proposal = _make_proposal(proposal_type=PROPOSAL_TYPE_BOUNDARY)
        intent = policy.interpret(proposal, _make_knowledge_object())
        assert intent is not None
        assert intent.change_type == EvolutionChangeType.BOUNDARY_UPDATE

    def test_principle_proposal_maps_to_enum(
        self, policy,
    ) -> None:
        proposal = _make_proposal(proposal_type=PROPOSAL_TYPE_PRINCIPLE)
        intent = policy.interpret(proposal, _make_knowledge_object())
        assert intent is not None
        assert intent.change_type == EvolutionChangeType.PRINCIPLE_UPDATE

    def test_unknown_proposal_returns_none(
        self, policy,
    ) -> None:
        proposal = _make_proposal(proposal_type="metadata_update")
        intent = policy.interpret(proposal, _make_knowledge_object())
        assert intent is None

    def test_string_change_type_is_coerced(self, policy) -> None:
        # Construct a ChangeIntent directly with a string,
        # simulating a legacy caller; the dataclass must
        # coerce to the enum in __post_init__.
        intent = ChangeIntent(
            intent_id="i-1", proposal_id="p-1",
            target_identity=KO_ID,
            change_type="boundary_update",
            target_field="boundary",
            current_value="x", proposed_value=None,
            reason="r", risk_level="high",
            requires_human_review=True,
            created_at=_ts(),
        )
        assert intent.change_type == EvolutionChangeType.BOUNDARY_UPDATE


# ---------------------------------------------------------------------
# Test 3 -- Transaction propagation
# ---------------------------------------------------------------------


class TestTransactionPropagation:

    def test_transaction_keeps_enum(self) -> None:
        tx = _make_transaction(
            change_type=EvolutionChangeType.BOUNDARY_UPDATE,
        )
        assert tx.change_type == EvolutionChangeType.BOUNDARY_UPDATE

    def test_transaction_accepts_string(self) -> None:
        tx = _make_transaction(change_type="boundary_update")
        assert tx.change_type == EvolutionChangeType.BOUNDARY_UPDATE

    def test_intent_to_transaction_enum_match(self) -> None:
        intent = ChangeIntent(
            intent_id="i-1", proposal_id="p-1",
            target_identity=KO_ID,
            change_type=EvolutionChangeType.PRINCIPLE_UPDATE,
            target_field="principle",
            current_value="x", proposed_value=None,
            reason="r", risk_level="high",
            requires_human_review=True,
            created_at=_ts(),
        )
        tx = _make_transaction(change_type=intent.change_type)
        assert tx.change_type == intent.change_type
        assert tx.change_type == EvolutionChangeType.PRINCIPLE_UPDATE


# ---------------------------------------------------------------------
# Test 4 -- Governance accepts all three V1 allowed types
# ---------------------------------------------------------------------


class TestGovernanceAccepts:

    @pytest.mark.parametrize("allowed_type", [
        EvolutionChangeType.BOUNDARY_UPDATE,
        EvolutionChangeType.PRINCIPLE_UPDATE,
        EvolutionChangeType.APPLICABILITY_UPDATE,
    ])
    def test_allowed_change_type_approved(
        self, governance_gate, allowed_type,
    ) -> None:
        tx = _make_transaction(change_type=allowed_type)
        result = governance_gate.govern(tx)
        assert result.approved is True, (
            "expected approval for " + str(allowed_type)
            + ", got rule_id=" + result.rule_id
            + " reason=" + result.reason
        )

    def test_allowed_set_contains_all_three(self) -> None:
        assert (
            EvolutionChangeType.BOUNDARY_UPDATE in ALLOWED_CHANGE_TYPES
        )
        assert (
            EvolutionChangeType.PRINCIPLE_UPDATE in ALLOWED_CHANGE_TYPES
        )
        assert (
            EvolutionChangeType.APPLICABILITY_UPDATE in ALLOWED_CHANGE_TYPES
        )


# ---------------------------------------------------------------------
# Test 5 -- Mutation accepts all three V1 allowed types
# ---------------------------------------------------------------------


class TestMutationAccepts:

    @pytest.mark.parametrize("allowed_type", [
        EvolutionChangeType.BOUNDARY_UPDATE,
        EvolutionChangeType.PRINCIPLE_UPDATE,
        EvolutionChangeType.APPLICABILITY_UPDATE,
    ])
    def test_allowed_change_type_passes_validator(
        self, mutation_validator, allowed_type,
    ) -> None:
        req = _make_request(change_type=allowed_type)
        verdict = mutation_validator.validate(
            req,
            transaction=_make_transaction(change_type=allowed_type),
            governance=_make_governance(),
            version_store=_make_version_store(),
        )
        assert verdict.valid is True, (
            "expected valid for " + str(allowed_type)
            + ", got rule_id=" + verdict.rule_id
            + " reason=" + verdict.reason
        )

    def test_allowed_set_contains_all_three(self) -> None:
        assert (
            EvolutionChangeType.BOUNDARY_UPDATE
            in MUTATION_ALLOWED_CHANGE_TYPES
        )
        assert (
            EvolutionChangeType.PRINCIPLE_UPDATE
            in MUTATION_ALLOWED_CHANGE_TYPES
        )
        assert (
            EvolutionChangeType.APPLICABILITY_UPDATE
            in MUTATION_ALLOWED_CHANGE_TYPES
        )

    def test_happy_path_runs_through_to_mutation(
        self, mutation_engine,
    ) -> None:
        vs = _make_version_store()
        audit = AuditStore()
        req = _make_request()
        tx = _make_transaction(change_type=EvolutionChangeType.BOUNDARY_UPDATE)
        gov = _make_governance()
        result = mutation_engine.mutate(
            req, tx, gov,
            version_store=vs, audit_store=audit,
        )
        assert result.success is True
        assert result.mutation_executed is True


# ---------------------------------------------------------------------
# Test 6 -- Forbidden types rejected across the pipeline
# ---------------------------------------------------------------------


class TestForbiddenTypes:

    @pytest.mark.parametrize("forbidden", [
        "identity_update",
        "delete",
        "rewrite",
        "unknown",
        "boundary_update_candidate",  # legacy suffix must NOT pass
    ])
    def test_governance_rejects(
        self, governance_gate, forbidden,
    ) -> None:
        tx = _make_transaction(change_type=forbidden)
        result = governance_gate.govern(tx)
        assert result.approved is False, (
            "expected rejection for " + repr(forbidden)
        )

    @pytest.mark.parametrize("forbidden", [
        "identity_update",
        "delete",
        "rewrite",
        "unknown",
        "boundary_update_candidate",
    ])
    def test_mutation_rejects(
        self, mutation_validator, forbidden,
    ) -> None:
        req = _make_request(change_type=forbidden)
        verdict = mutation_validator.validate(
            req,
            transaction=_make_transaction(change_type=forbidden),
            governance=_make_governance(),
            version_store=_make_version_store(),
        )
        assert verdict.valid is False, (
            "expected rejection for " + repr(forbidden)
        )
        # M5 is the change_type allow-list rule.
        assert verdict.rule_id == "M5"

    def test_change_policy_is_allowed_returns_false(self) -> None:
        for forbidden in (
            "identity_update",
            "delete",
            "rewrite",
            "unknown",
            "boundary_update_candidate",
        ):
            assert EvolutionChangePolicy.is_allowed(forbidden) is False, (
                "is_allowed must reject " + forbidden
            )


# ---------------------------------------------------------------------
# Test 7 -- JSON compatibility (round-trip)
# ---------------------------------------------------------------------


class TestJSONCompatibility:

    def test_change_intent_json_round_trip(self) -> None:
        intent = ChangeIntent(
            intent_id="i-1", proposal_id="p-1",
            target_identity=KO_ID,
            change_type=EvolutionChangeType.BOUNDARY_UPDATE,
            target_field="boundary",
            current_value="x", proposed_value=None,
            reason="r", risk_level="high",
            requires_human_review=True,
            created_at=_ts(),
        )
        encoded = json.dumps(intent.to_dict())
        decoded = json.loads(encoded)
        assert decoded["change_type"] == "boundary_update"
        assert decoded["target_identity"] == KO_ID

    def test_transaction_json_round_trip(self) -> None:
        tx = _make_transaction(change_type=EvolutionChangeType.PRINCIPLE_UPDATE)
        encoded = json.dumps(tx.to_dict())
        decoded = json.loads(encoded)
        assert decoded["change_type"] == "principle_update"

    def test_mutation_request_json_round_trip(self) -> None:
        req = _make_request(change_type=EvolutionChangeType.APPLICABILITY_UPDATE)
        encoded = json.dumps(req.to_dict())
        decoded = json.loads(encoded)
        assert decoded["change_type"] == "applicability_update"

    def test_audit_record_json_round_trip(self) -> None:
        rec = EvolutionAuditRecord(
            audit_id="a-1",
            transaction_id="tx-1",
            proposal_id="p-1",
            target_identity=KO_ID,
            previous_version=1,
            new_version=2,
            before_snapshot={"k": "v"},
            after_snapshot={"k": "v2"},
            change_type=EvolutionChangeType.BOUNDARY_UPDATE,
            reason="r",
            reviewer="alice",
            created_at=_ts(),
            rollback_reference=None,
        )
        encoded = json.dumps(rec.to_dict())
        decoded = json.loads(encoded)
        assert decoded["change_type"] == "boundary_update"

    def test_enum_string_round_trip(self) -> None:
        # Enum -> string -> Enum
        s = EvolutionChangeType.BOUNDARY_UPDATE.value
        assert EvolutionChangeType(s) == EvolutionChangeType.BOUNDARY_UPDATE


# ---------------------------------------------------------------------
# Test 8 -- Architecture Boundary (AST)
# ---------------------------------------------------------------------


class TestArchitectureBoundary:

    FORBIDDEN_PREFIXES = (
        "caseos.intelligence.decision",
        "caseos.intelligence.trust",
        "caseos.intelligence.recommendation",
        "caseos.knowledge.retrieval",
    )

    def _collect_imports(self, path: pathlib.Path):
        src = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(src)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)
        return imports

    def _imported_modules(self, path: pathlib.Path):
        names = []
        for node in self._collect_imports(path):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    names.append(module + "." + alias.name)
        return names

    @pytest.mark.parametrize("relative_path", [
        "contracts/__init__.py",
        "contracts/change_type.py",
        "object.py",
        "policy.py",
        "governance.py",
        "transaction.py",
        "audit.py",
        "validator.py",
        "audit_v2/__init__.py",
        "audit_v2/object.py",
        "audit_v2/store.py",
        "versioning/__init__.py",
        "versioning/object.py",
        "versioning/store.py",
        "versioning/diff.py",
        "mutation/__init__.py",
        "mutation/object.py",
        "mutation/validator.py",
        "mutation/engine.py",
        "mutation/result.py",
    ])
    def test_evolution_module_no_forbidden_imports(
        self, relative_path,
    ) -> None:
        pkg_root = (
            pathlib.Path(__file__).resolve().parent.parent.joinpath(
                "knowledge", "evolution",
            )
        )
        py_file = pkg_root / relative_path
        if not py_file.exists():
            pytest.skip("file not present: " + str(py_file))
        imported = self._imported_modules(py_file)
        for mod in imported:
            for forbidden in self.FORBIDDEN_PREFIXES:
                assert not mod.startswith(forbidden), (
                    py_file.name + " imports forbidden module: "
                    + mod + " (prefix: " + forbidden + ")"
                )

    @pytest.mark.parametrize("relative_path", [
        "interpretation/__init__.py",
        "interpretation/object.py",
        "interpretation/policy.py",
        "interpretation/validator.py",
        "interpretation/report.py",
    ])
    def test_feedback_interpretation_module_no_forbidden_imports(
        self, relative_path,
    ) -> None:
        pkg_root = (
            pathlib.Path(__file__).resolve().parent.parent.joinpath(
                "knowledge", "feedback",
            )
        )
        py_file = pkg_root / relative_path
        if not py_file.exists():
            pytest.skip("file not present: " + str(py_file))
        imported = self._imported_modules(py_file)
        for mod in imported:
            for forbidden in self.FORBIDDEN_PREFIXES:
                assert not mod.startswith(forbidden), (
                    py_file.name + " imports forbidden module: "
                    + mod + " (prefix: " + forbidden + ")"
                )
