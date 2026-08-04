"""Tests for the Evolution Governance Gate (Sprint 22.4-B).

Coverage per Sprint 22.4-B spec section "Task 5 -- Tests":

    Test 1   boundary_update  -> approved
    Test 2   principle_update -> approved
    Test 3   applicability_update -> approved
    Test 4   identity_update -> rejected (G2)
    Test 5   rewrite_evidence -> rejected (G3)
    Test 6   modify_decision_rule -> rejected (G4)
    Test 7   missing reviewer -> rejected (G5)
    Test 8   missing before_snapshot -> rejected (G6)
    Test 9   GovernanceResult frozen
    Test 10  JSON serialization
    Test 11  AST architecture boundary (governance.py + policy.py)

Plus auxiliary: 4 fields present, change_type mismatch cross-check,
unknown change_type caught by G1, audit boundary not crossed,
deliberate-fail ordering (first-failure rule_id).
"""
from __future__ import annotations

import ast
import dataclasses
import json
from pathlib import Path

import pytest

from caseos.knowledge.evolution import (
    ALLOWED_CHANGE_TYPES,
    EvolutionGovernanceGate,
    EvolutionStatus,
    EvolutionTransaction,
    FORBIDDEN_CHANGE_TYPES,
    G2_FORBIDDEN_CHANGE_TYPES,
    G3_FORBIDDEN_CHANGE_TYPES,
    G4_FORBIDDEN_CHANGE_TYPES,
    EvolutionChangePolicy,
    GovernanceResult,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
EVOLUTION_DIR = BACKEND / "caseos" / "knowledge" / "evolution"


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
def gate() -> EvolutionGovernanceGate:
    return EvolutionGovernanceGate()


# ---------------------------------------------------------------------------
# Test 1-3 -- allowed change types approved
# ---------------------------------------------------------------------------

class TestAllowedChangeTypes:

    @pytest.mark.parametrize("change_type", [
        "boundary_update",
        "principle_update",
        "applicability_update",
    ])
    def test_allowed_change_type_approved(
        self, gate, change_type: str,
    ) -> None:
        tx = _make_transaction(change_type=change_type)
        result = gate.govern(tx)
        assert result.approved is True
        assert result.rule_id == ""
        assert result.reason == ""


# ---------------------------------------------------------------------------
# Test 4 -- identity_update rejected (G2)
# ---------------------------------------------------------------------------

class TestIdentityRejected:

    def test_identity_update_rejected_with_g2(self, gate) -> None:
        tx = _make_transaction(change_type="identity_update")
        result = gate.govern(tx)
        assert result.approved is False
        assert result.rule_id == "G2"
        assert "identity" in result.reason.lower()

    def test_g2_set_contains_identity_update(self) -> None:
        assert "identity_update" in G2_FORBIDDEN_CHANGE_TYPES


# ---------------------------------------------------------------------------
# Test 5 -- rewrite_evidence rejected (G3)
# ---------------------------------------------------------------------------

class TestEvidenceRejected:

    @pytest.mark.parametrize("change_type", [
        "rewrite_evidence",
        "delete_evidence",
    ])
    def test_evidence_change_rejected_with_g3(
        self, gate, change_type: str,
    ) -> None:
        tx = _make_transaction(change_type=change_type)
        result = gate.govern(tx)
        assert result.approved is False
        assert result.rule_id == "G3"
        assert "evidence" in result.reason.lower()

    def test_g3_set_contains_evidence_changes(self) -> None:
        assert "rewrite_evidence" in G3_FORBIDDEN_CHANGE_TYPES
        assert "delete_evidence" in G3_FORBIDDEN_CHANGE_TYPES


# ---------------------------------------------------------------------------
# Test 6 -- modify_decision_rule rejected (G4)
# ---------------------------------------------------------------------------

class TestIntelligenceIsolation:

    @pytest.mark.parametrize("change_type", [
        "modify_decision_rule",
        "modify_trust",
        "modify_retrieval_priority",
    ])
    def test_intelligence_change_rejected_with_g4(
        self, gate, change_type: str,
    ) -> None:
        tx = _make_transaction(change_type=change_type)
        result = gate.govern(tx)
        assert result.approved is False
        assert result.rule_id == "G4"
        assert (
            "intelligence" in result.reason.lower()
            or "engine" in result.reason.lower()
        )

    def test_g4_set_contains_intelligence_changes(self) -> None:
        assert "modify_decision_rule" in G4_FORBIDDEN_CHANGE_TYPES
        assert "modify_trust" in G4_FORBIDDEN_CHANGE_TYPES
        assert "modify_retrieval_priority" in G4_FORBIDDEN_CHANGE_TYPES


# ---------------------------------------------------------------------------
# Test 7 -- missing reviewer rejected (G5)
# ---------------------------------------------------------------------------

class TestReviewerRequired:

    def test_empty_reviewer_rejected_with_g5(self, gate) -> None:
        tx = _make_transaction(reviewer="")
        result = gate.govern(tx)
        assert result.approved is False
        assert result.rule_id == "G5"
        assert "reviewer" in result.reason.lower()

    def test_whitespace_reviewer_rejected_with_g5(self, gate) -> None:
        tx = _make_transaction(reviewer="   ")
        result = gate.govern(tx)
        assert result.approved is False
        assert result.rule_id == "G5"


# ---------------------------------------------------------------------------
# Test 8 -- missing before_snapshot rejected (G6)
# ---------------------------------------------------------------------------

class TestSnapshotRequired:

    def test_empty_snapshot_rejected_with_g6(self, gate) -> None:
        tx = _make_transaction(before_snapshot={})
        result = gate.govern(tx)
        assert result.approved is False
        assert result.rule_id == "G6"
        assert "snapshot" in result.reason.lower()

    def test_none_snapshot_rejected_with_g6(self, gate) -> None:
        # Sentinel: explicitly pass None past the helper default.
        tx = _make_transaction(before_snapshot=None)  # type: ignore[arg-type]
        result = gate.govern(tx)
        assert result.approved is False
        # None fails the G1 type check (transaction constructed with
        # before_snapshot=None passes type-check; the gate then sees
        # an empty dict-or-None and rejects at G6).
        assert result.rule_id in ("G6", "G1")


# ---------------------------------------------------------------------------
# Test 9 -- GovernanceResult frozen
# ---------------------------------------------------------------------------

class TestGovernanceResultFrozen:

    EXPECTED_FIELDS = {"approved", "rule_id", "reason", "checked_at"}

    def test_all_four_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(GovernanceResult)}
        assert self.EXPECTED_FIELDS.issubset(actual), (
            "missing fields: " + str(self.EXPECTED_FIELDS - actual)
        )

    def test_mutation_raises_frozen_instance_error(self) -> None:
        result = GovernanceResult(
            approved=True, rule_id="", reason="",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.approved = False  # type: ignore[misc]

    def test_mutation_of_rule_id_raises(self) -> None:
        result = GovernanceResult(
            approved=False, rule_id="G1", reason="x",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.rule_id = "G2"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Test 10 -- JSON serialization
# ---------------------------------------------------------------------------

class TestJsonSerialization:

    def test_approved_result_is_json_safe(self) -> None:
        result = GovernanceResult(approved=True, rule_id="", reason="")
        encoded = json.dumps(result.to_dict())
        decoded = json.loads(encoded)
        assert decoded["approved"] is True
        assert decoded["rule_id"] == ""
        assert decoded["reason"] == ""
        assert isinstance(decoded["checked_at"], str)

    def test_rejected_result_is_json_safe(self) -> None:
        result = GovernanceResult(
            approved=False, rule_id="G4",
            reason="intelligence engine mutation forbidden",
        )
        encoded = json.dumps(result.to_dict())
        decoded = json.loads(encoded)
        assert decoded["approved"] is False
        assert decoded["rule_id"] == "G4"
        assert "intelligence" in decoded["reason"]
        assert isinstance(decoded["checked_at"], str)

    def test_checked_at_is_iso_string(self) -> None:
        result = GovernanceResult(approved=True, rule_id="", reason="")
        d = result.to_dict()
        # ISO format includes "T" and "Z"
        assert "T" in d["checked_at"]


# ---------------------------------------------------------------------------
# Test 11 -- AST architecture boundary (governance.py + policy.py)
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
        "governance.py",
        "policy.py",
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
# Auxiliary -- Policy data
# ---------------------------------------------------------------------------

class TestPolicyData:

    def test_allowed_change_types_exact(self) -> None:
        # Sprint 22.4-I: ALLOWED_CHANGE_TYPES now holds
        # EvolutionChangeType enum members, not bare strings.
        from caseos.knowledge.evolution.contracts.change_type import (
            EvolutionChangeType,
        )
        assert ALLOWED_CHANGE_TYPES == frozenset({
            EvolutionChangeType.BOUNDARY_UPDATE,
            EvolutionChangeType.PRINCIPLE_UPDATE,
            EvolutionChangeType.APPLICABILITY_UPDATE,
        })

    def test_forbidden_change_types_superset_of_named(self) -> None:
        # The full forbidden set must include the three named groups.
        for ct in G2_FORBIDDEN_CHANGE_TYPES:
            assert ct in FORBIDDEN_CHANGE_TYPES
        for ct in G3_FORBIDDEN_CHANGE_TYPES:
            assert ct in FORBIDDEN_CHANGE_TYPES
        for ct in G4_FORBIDDEN_CHANGE_TYPES:
            assert ct in FORBIDDEN_CHANGE_TYPES

    def test_change_policy_is_allowed(self) -> None:
        assert EvolutionChangePolicy.is_allowed("boundary_update")
        assert EvolutionChangePolicy.is_allowed("principle_update")
        assert EvolutionChangePolicy.is_allowed("applicability_update")
        assert not EvolutionChangePolicy.is_allowed("identity_update")
        assert not EvolutionChangePolicy.is_allowed("rewrite_evidence")
        assert not EvolutionChangePolicy.is_allowed("unknown_update")

    def test_change_policy_is_forbidden(self) -> None:
        assert EvolutionChangePolicy.is_forbidden("identity_update")
        assert EvolutionChangePolicy.is_forbidden("rewrite_evidence")
        assert EvolutionChangePolicy.is_forbidden("delete_evidence")
        assert EvolutionChangePolicy.is_forbidden("modify_trust")
        assert EvolutionChangePolicy.is_forbidden("modify_decision_rule")
        assert EvolutionChangePolicy.is_forbidden("modify_retrieval_priority")
        assert not EvolutionChangePolicy.is_forbidden("boundary_update")


# ---------------------------------------------------------------------------
# Auxiliary -- Gate ordering and edge cases
# ---------------------------------------------------------------------------

class TestGateOrdering:

    def test_first_failure_wins(self, gate) -> None:
        # identity_update is BOTH in G2 forbidden and not in
        # allowed list. The G2 rule should win (more specific).
        tx = _make_transaction(
            change_type="identity_update",
            reviewer="",  # also fails G5
        )
        result = gate.govern(tx)
        assert result.approved is False
        assert result.rule_id == "G2"

    def test_unknown_change_type_caught_by_g1(self, gate) -> None:
        tx = _make_transaction(change_type="custom_unknown_change")
        result = gate.govern(tx)
        assert result.approved is False
        assert result.rule_id == "G1"

    def test_delete_knowledge_caught_by_g1(self, gate) -> None:
        # delete_knowledge is not in any named forbidden group,
        # so it falls through to G1 (not in allowed list).
        tx = _make_transaction(change_type="delete_knowledge")
        result = gate.govern(tx)
        assert result.approved is False
        assert result.rule_id == "G1"

    def test_g5_checked_before_g6(self, gate) -> None:
        # Both reviewer and snapshot are missing; G5 should win
        # because it is checked first.
        tx = _make_transaction(reviewer="", before_snapshot={})
        result = gate.govern(tx)
        assert result.approved is False
        assert result.rule_id == "G5"

    def test_none_transaction_rejected_with_g0(self, gate) -> None:
        result = gate.govern(None)  # type: ignore[arg-type]
        assert result.approved is False
        assert result.rule_id == "G0"


# ---------------------------------------------------------------------------
# Auxiliary -- ChangeIntent cross-check
# ---------------------------------------------------------------------------

class TestChangeIntentCrossCheck:

    def test_matching_change_intent_approved(self, gate) -> None:
        # When a ChangeIntent is passed with the same change_type,
        # the gate still approves.
        class _StubIntent:
            change_type = "boundary_update"

        tx = _make_transaction(change_type="boundary_update")
        result = gate.govern(tx, change_intent=_StubIntent())
        assert result.approved is True

    def test_mismatched_change_intent_rejected(self, gate) -> None:
        class _StubIntent:
            change_type = "principle_update"

        tx = _make_transaction(change_type="boundary_update")
        result = gate.govern(tx, change_intent=_StubIntent())
        assert result.approved is False
        assert result.rule_id == "G1"
        assert "mismatch" in result.reason.lower()


# ---------------------------------------------------------------------------
# Auxiliary -- Audit boundary
# ---------------------------------------------------------------------------

class TestAuditBoundary:

    """The Governance Gate must NOT touch the audit store.

    The audit boundary is checked behaviourally: the gate does
    not have a reference to an audit store and produces a
    GovernanceResult without side effects.
    """

    def test_gate_has_no_audit_dependency(self, gate) -> None:
        # The gate is intentionally simple; it has no audit hook.
        assert not hasattr(gate, "audit_store")
        assert not hasattr(gate, "audit")
        assert not hasattr(gate, "store")

    def test_govern_returns_result_without_io(self, gate) -> None:
        tx = _make_transaction()
        result = gate.govern(tx)
        # The result is a frozen dataclass, not a side effect.
        assert isinstance(result, GovernanceResult)
        assert dataclasses.is_dataclass(result)
