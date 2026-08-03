"""Tests for the Feedback Learning Proposal Integration (Sprint 22.3).

Scope per Sprint 22.3 spec Task 7:

    Test 1  Boundary contradiction -> proposal generated
    Test 2  Proposal has all 10 contract fields
    Test 3  Lifecycle CREATED -> PENDING_REVIEW -> APPROVED passes
    Test 4  Illegal transitions are rejected (APPROVED -> CREATED etc.)
    Test 5  Proposal does NOT modify the Knowledge Object
    Test 6  AST boundary scan (no forbidden imports)

Plus auxiliary invariants for the proposal store and the
integration bridge.
"""
from __future__ import annotations

import ast
import copy
import dataclasses
from pathlib import Path
from typing import Any

import pytest

from caseos.knowledge.feedback import (
    LearningProposal,
    PROPOSAL_TYPE_APPLICABILITY,
    PROPOSAL_TYPE_BOUNDARY,
    PROPOSAL_TYPE_PRINCIPLE,
    ProposalEvent,
    ProposalStatus,
    ProposalStore,
    is_valid_proposal_transition,
    propose_from_contradiction,
)
from caseos.knowledge.feedback.evaluation.analyzer import (
    ContradictionAnalyzer,
)
from caseos.knowledge.feedback.evaluation.contradiction import (
    ContradictionResult,
)
from caseos.knowledge.objects.loader import (
    DEFAULT_CORPUS_DIR,
    load_corpus,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
FEEDBACK_DIR = BACKEND / "caseos" / "knowledge" / "feedback"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real_ko() -> dict:
    objects = load_corpus(DEFAULT_CORPUS_DIR)
    assert objects, "corpus must be non-empty"
    ko = dict(objects[0])
    ko.setdefault("boundary", [])
    ko.setdefault("principle", "")
    return ko


@pytest.fixture(scope="module")
def analyzer() -> ContradictionAnalyzer:
    return ContradictionAnalyzer()


def _make_contradiction(
    *,
    feedback_id: str = "fb-1",
    target_identity: str = "test_boundary",
    has_conflict: bool = True,
    conflict_type: str = "boundary_conflict",
    matched_field: str = "boundary",
    explanation: str = "boundary violation",
) -> ContradictionResult:
    return ContradictionResult(
        feedback_id=feedback_id,
        target_identity=target_identity,
        has_conflict=has_conflict,
        conflict_type=conflict_type,
        matched_field=matched_field,
        explanation=explanation,
        requires_human_review=True,
    )


# ---------------------------------------------------------------------------
# Test 1 -- Feedback contradiction -> proposal generated
# ---------------------------------------------------------------------------

class TestContradictionProducesProposal:

    def test_boundary_conflict_yields_boundary_proposal(
        self, analyzer: ContradictionAnalyzer, real_ko: dict,
    ) -> None:
        ko = {**real_ko, "boundary": ["Do not add scattered equipment"]}
        cr = analyzer.analyze(
            {"content": "Add scattered equipment everywhere"}, ko,
        )
        assert cr.has_conflict is True
        proposal = propose_from_contradiction(
            {"id": "fb-1"}, cr, ko,
        )
        assert isinstance(proposal, LearningProposal)
        assert proposal.proposal_type == PROPOSAL_TYPE_BOUNDARY
        assert proposal.requires_human_review is True
        assert proposal.status == ProposalStatus.CREATED.value

    def test_principle_conflict_yields_principle_proposal(
        self, analyzer: ContradictionAnalyzer, real_ko: dict,
    ) -> None:
        ko = {**real_ko,
              "principle": "Create hierarchy before adding facilities"}
        cr = analyzer.analyze(
            {"content": "Add facilities without hierarchy"}, ko,
        )
        assert cr.has_conflict is True
        proposal = propose_from_contradiction(
            {"id": "fb-2"}, cr, ko,
        )
        assert proposal is not None
        assert proposal.proposal_type == PROPOSAL_TYPE_PRINCIPLE
        assert proposal.requires_human_review is True

    def test_no_conflict_yields_no_proposal(
        self, analyzer: ContradictionAnalyzer, real_ko: dict,
    ) -> None:
        cr = analyzer.analyze({"content": "Looks good"}, real_ko)
        assert cr.has_conflict is False
        proposal = propose_from_contradiction({"id": "fb-3"}, cr, real_ko)
        assert proposal is None

    def test_spec_example_payload_round_trip(
        self, analyzer: ContradictionAnalyzer,
    ) -> None:
        """Spec Task 3 example verbatim."""
        ko = {
            "identity": "test_boundary",
            "boundary": ["Do not add scattered equipment"],
        }
        feedback = {"id": "fb-spec",
                    "content": "Add scattered equipment everywhere"}
        cr = analyzer.analyze(feedback, ko)
        proposal = propose_from_contradiction(feedback, cr, ko)
        assert proposal is not None
        assert proposal.proposal_type == "boundary_update_candidate"
        assert proposal.requires_human_review is True


# ---------------------------------------------------------------------------
# Test 2 -- Proposal has all 10 contract fields
# ---------------------------------------------------------------------------

class TestProposalFields:

    EXPECTED_FIELDS = {
        "proposal_id", "feedback_id", "target_identity",
        "proposal_type", "current_state", "suggested_change",
        "reason", "requires_human_review", "status", "created_at",
    }

    def test_all_ten_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(LearningProposal)}
        assert self.EXPECTED_FIELDS.issubset(actual), (
            "missing fields: " + str(self.EXPECTED_FIELDS - actual)
        )

    def test_dataclass_is_frozen(self) -> None:
        proposal = self._sample_proposal()
        with pytest.raises(dataclasses.FrozenInstanceError):
            proposal.requires_human_review = False  # type: ignore[misc]

    def test_to_dict_is_json_safe(self) -> None:
        import json
        proposal = self._sample_proposal()
        encoded = json.dumps(proposal.to_dict())
        assert json.loads(encoded) == proposal.to_dict()

    def _sample_proposal(self) -> LearningProposal:
        return LearningProposal(
            proposal_id="p-1",
            feedback_id="fb-1",
            target_identity="KO-1",
            proposal_type=PROPOSAL_TYPE_BOUNDARY,
            current_state={"boundary": ["Do not add scattered equipment"]},
            suggested_change="Candidate update for boundary.",
            reason="boundary violation",
            requires_human_review=True,
            status=ProposalStatus.CREATED.value,
        )


# ---------------------------------------------------------------------------
# Test 3 -- Lifecycle CREATED -> PENDING_REVIEW -> APPROVED passes
# ---------------------------------------------------------------------------

class TestProposalLifecycle:

    def test_forward_lifecycle_allowed(self) -> None:
        assert is_valid_proposal_transition(
            ProposalStatus.CREATED, ProposalStatus.PENDING_REVIEW,
        )
        assert is_valid_proposal_transition(
            ProposalStatus.PENDING_REVIEW, ProposalStatus.APPROVED,
        )
        assert is_valid_proposal_transition(
            ProposalStatus.PENDING_REVIEW, ProposalStatus.REJECTED,
        )

    def test_full_path_creates_lifecycle_events(self) -> None:
        store = ProposalStore()
        store.append(ProposalEvent(
            proposal_id="p-1", feedback_id="fb-1",
            target_identity="KO-1",
            from_status=None,
            to_status=ProposalStatus.CREATED.value,
            timestamp="2026-01-01T00:00:00Z",
        ))
        store.append(ProposalEvent(
            proposal_id="p-1", feedback_id="fb-1",
            target_identity="KO-1",
            from_status=ProposalStatus.CREATED.value,
            to_status=ProposalStatus.PENDING_REVIEW.value,
            timestamp="2026-01-01T00:01:00Z",
        ))
        store.append(ProposalEvent(
            proposal_id="p-1", feedback_id="fb-1",
            target_identity="KO-1",
            from_status=ProposalStatus.PENDING_REVIEW.value,
            to_status=ProposalStatus.APPROVED.value,
            timestamp="2026-01-01T00:02:00Z",
            note="looks fine",
        ))
        history = store.history_for("p-1")
        assert [h.to_status for h in history] == [
            "CREATED", "PENDING_REVIEW", "APPROVED",
        ]
        assert store.latest_for("p-1").to_status == "APPROVED"


# ---------------------------------------------------------------------------
# Test 4 -- Illegal transitions are rejected
# ---------------------------------------------------------------------------

class TestIllegalTransitions:

    @pytest.mark.parametrize("from_status,to_status", [
        (ProposalStatus.APPROVED, ProposalStatus.CREATED),
        (ProposalStatus.REJECTED, ProposalStatus.APPROVED),
        (ProposalStatus.PENDING_REVIEW, ProposalStatus.CREATED),
        (ProposalStatus.APPROVED, ProposalStatus.REJECTED),
        (ProposalStatus.CREATED, ProposalStatus.APPROVED),
        (ProposalStatus.CREATED, ProposalStatus.REJECTED),
        (ProposalStatus.APPROVED, ProposalStatus.APPROVED),
        (ProposalStatus.REJECTED, ProposalStatus.REJECTED),
    ])
    def test_transition_is_rejected(
        self, from_status, to_status,
    ) -> None:
        assert not is_valid_proposal_transition(from_status, to_status)


# ---------------------------------------------------------------------------
# Test 5 -- Proposal does NOT modify the Knowledge Object
# ---------------------------------------------------------------------------

class TestKnowledgeObjectImmutability:

    def test_propose_does_not_mutate_ko(
        self, analyzer: ContradictionAnalyzer,
    ) -> None:
        ko = {
            "identity": "test_boundary",
            "boundary": ["Do not add scattered equipment"],
        }
        snapshot = copy.deepcopy(ko)
        cr = analyzer.analyze(
            {"content": "Add scattered equipment everywhere"}, ko,
        )
        propose_from_contradiction({"id": "fb-1"}, cr, ko)
        assert ko == snapshot

    def test_propose_does_not_mutate_ko_with_real_corpus(
        self, analyzer: ContradictionAnalyzer, real_ko: dict,
    ) -> None:
        ko = {**real_ko, "boundary": ["Do not add scattered equipment"]}
        snapshot = copy.deepcopy(ko)
        cr = analyzer.analyze(
            {"content": "Add scattered equipment everywhere"}, ko,
        )
        propose_from_contradiction({"id": "fb-2"}, cr, ko)
        assert ko == snapshot

    def test_propose_does_not_modify_feedback(self) -> None:
        cr = _make_contradiction()
        fb = {"id": "fb-1", "content": "Add scattered equipment"}
        before = copy.deepcopy(fb)
        propose_from_contradiction(fb, cr, {"identity": "KO-1"})
        assert fb == before

    def test_current_state_is_a_snapshot(self) -> None:
        cr = _make_contradiction()
        ko = {
            "identity": "KO-1",
            "boundary": ["Do not add scattered equipment"],
            "principle": "P",
        }
        proposal = propose_from_contradiction({"id": "fb-1"}, cr, ko)
        # The snapshot is detached; mutating the KO later must not
        # change the proposal.
        ko["boundary"].append("New mutation")
        assert proposal is not None
        assert proposal.current_state["boundary"] == [
            "Do not add scattered equipment",
        ]


# ---------------------------------------------------------------------------
# Test 6 -- AST boundary scan
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
        "proposal.py",
        "proposal_lifecycle.py",
        "proposal_store.py",
        "proposal_integration.py",
        "manager.py",
        "store.py",
        "validator.py",
        "object.py",
        "event.py",
        "report.py",
    ])
    def test_no_forbidden_imports(self, py_name: str) -> None:
        py = FEEDBACK_DIR / py_name
        if not py.exists():
            pytest.skip("missing module: " + py_name)
        seen = _imports(py)
        bad = [
            m for m in seen
            if any(m.startswith(p) for p in _FORBIDDEN_PREFIXES)
        ]
        assert not bad, py_name + " imports forbidden: " + str(bad)


# ---------------------------------------------------------------------------
# Auxiliary: append-only store invariant
# ---------------------------------------------------------------------------

class TestProposalStoreAppendOnly:

    def test_store_records_three_events(self) -> None:
        store = ProposalStore()
        for to_status in (
            ProposalStatus.CREATED.value,
            ProposalStatus.PENDING_REVIEW.value,
            ProposalStatus.APPROVED.value,
        ):
            store.append(ProposalEvent(
                proposal_id="p-1",
                feedback_id="fb-1",
                target_identity="KO-1",
                from_status=None,
                to_status=to_status,
                timestamp="2026-01-01T00:00:00Z",
            ))
        assert store.count() == 3
        assert len(store.list()) == 3

    def test_store_rejects_non_event_payload(self) -> None:
        store = ProposalStore()
        with pytest.raises(TypeError):
            store.append("not an event")  # type: ignore[arg-type]

    def test_list_by_target_filters(self) -> None:
        store = ProposalStore()
        for tgt in ("KO-A", "KO-B"):
            store.append(ProposalEvent(
                proposal_id="p-" + tgt,
                feedback_id="fb-" + tgt,
                target_identity=tgt,
                from_status=None,
                to_status=ProposalStatus.CREATED.value,
                timestamp="2026-01-01T00:00:00Z",
            ))
        assert len(store.list_by_target("KO-A")) == 1
        assert len(store.list_by_target("KO-B")) == 1
        assert len(store.list_by_target("KO-C")) == 0
