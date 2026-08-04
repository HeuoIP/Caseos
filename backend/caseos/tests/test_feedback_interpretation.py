"""Tests for the Feedback Interpretation Policy Foundation (Sprint 22.3.2).

Coverage per Sprint 22.3.2 spec section "Tests":

    Test 1  Approved boundary proposal -> ChangeIntent
            (change_type="boundary_update", target_field="boundary")
    Test 2  Approved principle proposal -> change_type="principle_update"
    Test 3  Pending proposal (CREATED / PENDING_REVIEW) -> None
    Test 4  requires_human_review=False proposal -> None
    Test 5  Unknown proposal_type -> None
    Test 6  Knowledge Object immutable (deepcopy before/after)
    Test 7  ChangeIntent is frozen (FrozenInstanceError on mutation)
    Test 8  AST architecture boundary scan (5 interpretation modules)

Plus auxiliary invariants for the validator, report, JSON safety,
and to_dict roundtrip.
"""
from __future__ import annotations

import ast
import copy
import dataclasses
import json
from pathlib import Path

import pytest

from caseos.knowledge.feedback import (
    LearningProposal,
    PROPOSAL_TYPE_APPLICABILITY,
    PROPOSAL_TYPE_BOUNDARY,
    PROPOSAL_TYPE_PRINCIPLE,
    ProposalStatus,
)
from caseos.knowledge.feedback.interpretation import (
    ChangeIntent,
    InterpretationPolicy,
    VALID_CHANGE_TYPES,
    VALID_RISK_LEVELS,
    generate_report,
    validate_change_intent,
)
from caseos.knowledge.evolution.contracts.change_type import (
    EvolutionChangeType,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
INTERPRETATION_DIR = (
    BACKEND / "caseos" / "knowledge" / "feedback" / "interpretation"
)


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

def _make_proposal(
    *,
    proposal_id: str = "p-1",
    feedback_id: str = "fb-1",
    target_identity: str = "KO-1",
    proposal_type: str = PROPOSAL_TYPE_BOUNDARY,
    reason: str = "boundary violated",
    suggested_change: str = "refine boundary",
    requires_human_review: bool = True,
    status: str = "APPROVED",
    current_state: dict | None = None,
) -> LearningProposal:
    if current_state is None:
        current_state = {
            "boundary": ["Do not add scattered equipment"],
        }
    return LearningProposal(
        proposal_id=proposal_id,
        feedback_id=feedback_id,
        target_identity=target_identity,
        proposal_type=proposal_type,
        current_state=current_state,
        suggested_change=suggested_change,
        reason=reason,
        requires_human_review=requires_human_review,
        status=status,
    )


@pytest.fixture
def policy() -> InterpretationPolicy:
    return InterpretationPolicy()


@pytest.fixture
def knowledge_object_boundary() -> dict:
    return {
        "identity": "test_boundary",
        "boundary": ["Do not add scattered equipment"],
    }


@pytest.fixture
def knowledge_object_principle() -> dict:
    return {
        "identity": "test_principle",
        "principle": ["Create hierarchy before adding facilities"],
    }


# ---------------------------------------------------------------------------
# Test 1 -- Approved boundary proposal -> ChangeIntent
# ---------------------------------------------------------------------------

class TestApprovedBoundaryProposal:

    def test_returns_change_intent(
        self, policy, knowledge_object_boundary,
    ) -> None:
        proposal = _make_proposal(
            proposal_id="p-boundary",
            target_identity="test_boundary",
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
            reason="user pushed back on scattered equipment",
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is not None
        assert isinstance(intent, ChangeIntent)

    def test_change_type_and_field(
        self, policy, knowledge_object_boundary,
    ) -> None:
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is not None
        assert intent.change_type == EvolutionChangeType.BOUNDARY_UPDATE
        assert intent.change_type.value == "boundary_update"
        assert intent.target_field == "boundary"

    def test_current_value_snapshot(
        self, policy, knowledge_object_boundary,
    ) -> None:
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is not None
        assert intent.current_value is not None
        assert "Do not add scattered equipment" in intent.current_value

    def test_proposed_value_is_none_in_v1(
        self, policy, knowledge_object_boundary,
    ) -> None:
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is not None
        # V1 never invents the future value
        assert intent.proposed_value is None

    def test_requires_human_review_is_true(
        self, policy, knowledge_object_boundary,
    ) -> None:
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is not None
        assert intent.requires_human_review is True

    def test_risk_level_is_in_allowlist(
        self, policy, knowledge_object_boundary,
    ) -> None:
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is not None
        assert intent.risk_level in VALID_RISK_LEVELS

    def test_intent_id_is_non_empty_string(
        self, policy, knowledge_object_boundary,
    ) -> None:
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is not None
        assert isinstance(intent.intent_id, str)
        assert len(intent.intent_id) > 0

    def test_proposal_id_is_carried_through(
        self, policy, knowledge_object_boundary,
    ) -> None:
        proposal = _make_proposal(
            proposal_id="p-99",
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is not None
        assert intent.proposal_id == "p-99"

    def test_reason_is_carried_through(
        self, policy, knowledge_object_boundary,
    ) -> None:
        proposal = _make_proposal(
            reason="user rejected scattered equipment",
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is not None
        assert intent.reason == "user rejected scattered equipment"

    def test_target_identity_is_carried_through(
        self, policy, knowledge_object_boundary,
    ) -> None:
        proposal = _make_proposal(
            target_identity="test_boundary",
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is not None
        assert intent.target_identity == "test_boundary"


# ---------------------------------------------------------------------------
# Test 2 -- Approved principle proposal -> principle_update
# ---------------------------------------------------------------------------

class TestApprovedPrincipleProposal:

    def test_returns_change_intent(
        self, policy, knowledge_object_principle,
    ) -> None:
        proposal = _make_proposal(
            proposal_id="p-principle",
            target_identity="test_principle",
            proposal_type=PROPOSAL_TYPE_PRINCIPLE,
            reason="user added facilities without hierarchy",
            current_state={
                "principle": ["Create hierarchy before adding facilities"],
            },
        )
        intent = policy.interpret(proposal, knowledge_object_principle)
        assert intent is not None
        assert isinstance(intent, ChangeIntent)

    def test_change_type_is_principle_update(
        self, policy, knowledge_object_principle,
    ) -> None:
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_PRINCIPLE,
            current_state={
                "principle": ["Create hierarchy before adding facilities"],
            },
        )
        intent = policy.interpret(proposal, knowledge_object_principle)
        assert intent is not None
        assert intent.change_type == EvolutionChangeType.PRINCIPLE_UPDATE
        assert intent.change_type.value == "principle_update"
        assert intent.target_field == "principle"

    def test_current_value_snapshot(
        self, policy, knowledge_object_principle,
    ) -> None:
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_PRINCIPLE,
            current_state={
                "principle": ["Create hierarchy before adding facilities"],
            },
        )
        intent = policy.interpret(proposal, knowledge_object_principle)
        assert intent is not None
        assert intent.current_value is not None
        assert "Create hierarchy before adding facilities" in intent.current_value

    def test_requires_human_review_is_true(
        self, policy, knowledge_object_principle,
    ) -> None:
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_PRINCIPLE,
            current_state={
                "principle": ["Create hierarchy before adding facilities"],
            },
        )
        intent = policy.interpret(proposal, knowledge_object_principle)
        assert intent is not None
        assert intent.requires_human_review is True


# ---------------------------------------------------------------------------
# Test 3 -- Pending proposal -> None
# ---------------------------------------------------------------------------

class TestPendingProposalRejected:

    @pytest.mark.parametrize("non_approved_status", [
        ProposalStatus.CREATED.value,
        ProposalStatus.PENDING_REVIEW.value,
        ProposalStatus.REJECTED.value,
        "",
    ])
    def test_non_approved_status_returns_none(
        self,
        policy,
        knowledge_object_boundary,
        non_approved_status,
    ) -> None:
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
            status=non_approved_status,
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is None


# ---------------------------------------------------------------------------
# Test 4 -- requires_human_review=False -> None
# ---------------------------------------------------------------------------

class TestHumanReviewRequired:

    def test_proposal_without_human_review_returns_none(
        self, policy, knowledge_object_boundary,
    ) -> None:
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
            requires_human_review=False,
            status="APPROVED",
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is None

    def test_intent_always_requires_human_review_when_built(
        self, policy, knowledge_object_boundary,
    ) -> None:
        # Even when caller tries to flip it, the policy overrides.
        # (LearningProposal is frozen, so this is more of a contract
        # test: the policy never produces a False intent.)
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is not None
        assert intent.requires_human_review is True


# ---------------------------------------------------------------------------
# Test 5 -- Unknown proposal_type -> None
# ---------------------------------------------------------------------------

class TestUnknownProposalType:

    @pytest.mark.parametrize("unsupported_type", [
        PROPOSAL_TYPE_APPLICABILITY,
        "metadata_update_candidate",
        "trust_update_candidate",
        "unknown",
        "",
    ])
    def test_unsupported_type_returns_none(
        self,
        policy,
        knowledge_object_boundary,
        unsupported_type,
    ) -> None:
        proposal = _make_proposal(
            proposal_type=unsupported_type,
        )
        intent = policy.interpret(proposal, knowledge_object_boundary)
        assert intent is None


# ---------------------------------------------------------------------------
# Test 6 -- Knowledge Object immutable
# ---------------------------------------------------------------------------

class TestKnowledgeObjectImmutable:

    def test_ko_unchanged_after_successful_interpret(
        self, policy, knowledge_object_boundary,
    ) -> None:
        before = copy.deepcopy(knowledge_object_boundary)
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
        )
        _ = policy.interpret(proposal, knowledge_object_boundary)
        assert knowledge_object_boundary == before

    def test_ko_unchanged_when_interpret_returns_none(
        self, policy, knowledge_object_boundary,
    ) -> None:
        before = copy.deepcopy(knowledge_object_boundary)
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
            status="CREATED",
        )
        _ = policy.interpret(proposal, knowledge_object_boundary)
        assert knowledge_object_boundary == before

    def test_ko_unchanged_on_unsupported_type(
        self, policy, knowledge_object_boundary,
    ) -> None:
        before = copy.deepcopy(knowledge_object_boundary)
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_APPLICABILITY,
        )
        _ = policy.interpret(proposal, knowledge_object_boundary)
        assert knowledge_object_boundary == before

    def test_proposal_unchanged_after_interpret(
        self, policy, knowledge_object_boundary,
    ) -> None:
        proposal = _make_proposal(
            proposal_id="p-1",
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
        )
        before = copy.deepcopy(proposal.to_dict())
        _ = policy.interpret(proposal, knowledge_object_boundary)
        assert proposal.to_dict() == before

    def test_ko_principle_unchanged(
        self, policy, knowledge_object_principle,
    ) -> None:
        before = copy.deepcopy(knowledge_object_principle)
        proposal = _make_proposal(
            proposal_type=PROPOSAL_TYPE_PRINCIPLE,
            current_state={
                "principle": ["Create hierarchy before adding facilities"],
            },
        )
        _ = policy.interpret(proposal, knowledge_object_principle)
        assert knowledge_object_principle == before


# ---------------------------------------------------------------------------
# Test 7 -- ChangeIntent is frozen
# ---------------------------------------------------------------------------

class TestChangeIntentFrozen:

    EXPECTED_FIELDS = {
        "intent_id", "proposal_id", "target_identity",
        "change_type", "target_field", "current_value",
        "proposed_value", "reason", "risk_level",
        "requires_human_review", "created_at",
    }

    def test_all_eleven_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(ChangeIntent)}
        assert self.EXPECTED_FIELDS.issubset(actual), (
            "missing fields: "
            + str(self.EXPECTED_FIELDS - actual)
        )

    def test_mutation_raises_frozen_instance_error(self) -> None:
        intent = ChangeIntent(
            intent_id="i-1",
            proposal_id="p-1",
            target_identity="KO-1",
            change_type="boundary_update",
            target_field="boundary",
            current_value="x",
            proposed_value=None,
            reason="r",
            risk_level="high",
            requires_human_review=True,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            intent.change_type = "principle_update"  # type: ignore[misc]

    def test_mutation_of_requires_human_review_raises(self) -> None:
        intent = ChangeIntent(
            intent_id="i-1",
            proposal_id="p-1",
            target_identity="KO-1",
            change_type="boundary_update",
            target_field="boundary",
            current_value="x",
            proposed_value=None,
            reason="r",
            risk_level="high",
            requires_human_review=True,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            intent.requires_human_review = False  # type: ignore[misc]

    def test_to_dict_is_json_safe(self) -> None:
        intent = ChangeIntent(
            intent_id="i-1",
            proposal_id="p-1",
            target_identity="KO-1",
            change_type="boundary_update",
            target_field="boundary",
            current_value="x",
            proposed_value=None,
            reason="r",
            risk_level="high",
            requires_human_review=True,
        )
        encoded = json.dumps(intent.to_dict())
        decoded = json.loads(encoded)
        assert decoded["intent_id"] == "i-1"
        assert decoded["requires_human_review"] is True
        assert decoded["change_type"] == "boundary_update"
        # datetime is serialised as ISO string
        assert isinstance(decoded["created_at"], str)


# ---------------------------------------------------------------------------
# Test 8 -- AST architecture boundary
# ---------------------------------------------------------------------------

_FORBIDDEN_PREFIXES = (
    "caseos.intelligence.decision",
    "caseos.intelligence.trust",
    "caseos.intelligence.recommendation",
    "caseos.knowledge.retrieval",
    "caseos.knowledge.governance",
    "caseos.knowledge.intake",
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
        "__init__.py", "object.py", "policy.py",
        "validator.py", "report.py",
    ])
    def test_no_forbidden_imports(self, py_name: str) -> None:
        py = INTERPRETATION_DIR / py_name
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
# Auxiliary -- Validator
# ---------------------------------------------------------------------------

class TestValidator:

    def _valid_intent(self) -> ChangeIntent:
        return ChangeIntent(
            intent_id="i-1",
            proposal_id="p-1",
            target_identity="KO-1",
            change_type="boundary_update",
            target_field="boundary",
            current_value="x",
            proposed_value=None,
            reason="r",
            risk_level="high",
            requires_human_review=True,
        )

    def test_valid_intent_passes(self) -> None:
        ok, msg = validate_change_intent(self._valid_intent())
        assert ok is True
        assert msg == ""

    def test_none_intent_rejected(self) -> None:
        ok, msg = validate_change_intent(None)
        assert ok is False
        assert msg != ""

    def test_invalid_change_type_rejected(self) -> None:
        intent = ChangeIntent(
            intent_id="i-1",
            proposal_id="p-1",
            target_identity="KO-1",
            change_type="metadata_update",
            target_field="boundary",
            current_value="x",
            proposed_value=None,
            reason="r",
            risk_level="high",
            requires_human_review=True,
        )
        ok, msg = validate_change_intent(intent)
        assert ok is False
        assert "change_type" in msg

    def test_invalid_risk_level_rejected(self) -> None:
        intent = ChangeIntent(
            intent_id="i-1",
            proposal_id="p-1",
            target_identity="KO-1",
            change_type="boundary_update",
            target_field="boundary",
            current_value="x",
            proposed_value=None,
            reason="r",
            risk_level="catastrophic",
            requires_human_review=True,
        )
        ok, msg = validate_change_intent(intent)
        assert ok is False
        assert "risk_level" in msg

    def test_requires_human_review_false_rejected(self) -> None:
        intent = ChangeIntent(
            intent_id="i-1",
            proposal_id="p-1",
            target_identity="KO-1",
            change_type="boundary_update",
            target_field="boundary",
            current_value="x",
            proposed_value=None,
            reason="r",
            risk_level="high",
            requires_human_review=False,
        )
        ok, msg = validate_change_intent(intent)
        assert ok is False
        assert "requires_human_review" in msg

    def test_missing_intent_id_rejected(self) -> None:
        intent = ChangeIntent(
            intent_id="",
            proposal_id="p-1",
            target_identity="KO-1",
            change_type="boundary_update",
            target_field="boundary",
            current_value="x",
            proposed_value=None,
            reason="r",
            risk_level="high",
            requires_human_review=True,
        )
        ok, msg = validate_change_intent(intent)
        assert ok is False
        assert "intent_id" in msg


# ---------------------------------------------------------------------------
# Auxiliary -- Report
# ---------------------------------------------------------------------------

class TestReport:

    def test_report_contains_all_seven_sections(self) -> None:
        intent = ChangeIntent(
            intent_id="i-1",
            proposal_id="p-1",
            target_identity="KO-1",
            change_type="boundary_update",
            target_field="boundary",
            current_value="Do not add scattered equipment",
            proposed_value=None,
            reason="user rejected scattered equipment",
            risk_level="high",
            requires_human_review=True,
        )
        md = generate_report(intent)
        for section in (
            "## Target",
            "## Change Type",
            "## Target Field",
            "## Current Value",
            "## Proposed Value",
            "## Risk",
            "## Human Review Required",
        ):
            assert section in md, "missing section: " + section

    def test_report_renders_boundary_value(self) -> None:
        intent = ChangeIntent(
            intent_id="i-1",
            proposal_id="p-1",
            target_identity="KO-1",
            change_type="boundary_update",
            target_field="boundary",
            current_value="Do not add scattered equipment",
            proposed_value=None,
            reason="r",
            risk_level="high",
            requires_human_review=True,
        )
        md = generate_report(intent)
        assert "Do not add scattered equipment" in md
        assert "True" in md

    def test_report_handles_none_values(self) -> None:
        intent = ChangeIntent(
            intent_id="i-1",
            proposal_id="p-1",
            target_identity="KO-1",
            change_type="boundary_update",
            target_field="boundary",
            current_value=None,
            proposed_value=None,
            reason="r",
            risk_level="low",
            requires_human_review=True,
        )
        md = generate_report(intent)
        assert "(none)" in md

    def test_report_title_present(self) -> None:
        intent = ChangeIntent(
            intent_id="i-1",
            proposal_id="p-1",
            target_identity="KO-1",
            change_type="boundary_update",
            target_field="boundary",
            current_value="x",
            proposed_value=None,
            reason="r",
            risk_level="low",
            requires_human_review=True,
        )
        md = generate_report(intent)
        assert md.startswith("# Feedback Interpretation Report")
