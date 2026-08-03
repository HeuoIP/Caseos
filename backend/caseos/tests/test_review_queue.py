"""Tests for the Human Review Queue Surface (Sprint 22.3.1).

Coverage per Sprint 22.3.1 spec section 测试要求:

    Test 1  Proposal can be enqueued in Review Queue
    Test 2  ReviewItem fields are complete
    Test 3  Queue is append-only
    Test 4  approve() performs the PENDING -> APPROVED transition
    Test 5  reject() performs the PENDING -> REJECTED transition
    Test 6  Illegal transitions are rejected
    Test 7  The original LearningProposal is never modified
    Test 8  AST architecture boundary (no forbidden imports)

Plus auxiliary invariants for the report, frozen dataclass,
and JSON safety.
"""
from __future__ import annotations

import ast
import copy
import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest

from caseos.knowledge.feedback import (
    LearningProposal, PROPOSAL_TYPE_BOUNDARY,
    PROPOSAL_TYPE_PRINCIPLE, ProposalStore,
)
from caseos.knowledge.feedback.review import (
    ReviewAction, ReviewError, ReviewItem, ReviewManager, ReviewQueue,
    ReviewStatus, generate_report,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
REVIEW_DIR = BACKEND / "caseos" / "knowledge" / "feedback" / "review"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_proposal(
    *,
    proposal_id: str = "p-1",
    feedback_id: str = "fb-1",
    target_identity: str = "KO-1",
    proposal_type: str = PROPOSAL_TYPE_BOUNDARY,
    reason: str = "boundary violated",
    suggested_change: str = "refine boundary",
    status: str = "CREATED",
) -> LearningProposal:
    return LearningProposal(
        proposal_id=proposal_id,
        feedback_id=feedback_id,
        target_identity=target_identity,
        proposal_type=proposal_type,
        current_state={"boundary": ["Do not add scattered equipment"]},
        suggested_change=suggested_change,
        reason=reason,
        requires_human_review=True,
        status=status,
    )


@pytest.fixture
def queue() -> ReviewQueue:
    return ReviewQueue()


@pytest.fixture
def proposal_store() -> ProposalStore:
    return ProposalStore()


@pytest.fixture
def manager(queue: ReviewQueue, proposal_store: ProposalStore) -> ReviewManager:
    return ReviewManager(queue=queue, proposal_store=proposal_store)


@pytest.fixture
def pending_item(manager: ReviewManager) -> ReviewItem:
    return manager.queue.enqueue(_make_proposal())


# ---------------------------------------------------------------------------
# Test 1 -- Proposal can be enqueued
# ---------------------------------------------------------------------------

class TestEnqueue:

    def test_proposal_is_enqueued_with_pending_status(
        self, manager: ReviewManager,
    ) -> None:
        proposal = _make_proposal(proposal_id="p-X")
        item = manager.queue.enqueue(proposal)
        assert isinstance(item, ReviewItem)
        assert item.proposal_id == "p-X"
        assert item.target_identity == "KO-1"
        assert item.proposal_type == PROPOSAL_TYPE_BOUNDARY
        assert item.status == ReviewStatus.PENDING.value
        assert manager.queue.list_pending() == [item]

    def test_summary_captures_proposal_reason(self, manager) -> None:
        proposal = _make_proposal(reason="specific reason text")
        item = manager.queue.enqueue(proposal)
        assert "specific reason text" in item.summary


# ---------------------------------------------------------------------------
# Test 2 -- ReviewItem fields are complete
# ---------------------------------------------------------------------------

class TestReviewItemFields:

    EXPECTED_FIELDS = {
        "review_id", "proposal_id", "target_identity",
        "proposal_type", "summary", "status", "created_at",
    }

    def test_all_seven_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(ReviewItem)}
        assert self.EXPECTED_FIELDS.issubset(actual), (
            "missing fields: " + str(self.EXPECTED_FIELDS - actual)
        )

    def test_dataclass_is_frozen(self) -> None:
        item = ReviewItem(
            review_id="r-1", proposal_id="p-1",
            target_identity="KO-1", proposal_type="boundary_update_candidate",
            summary="x", status=ReviewStatus.PENDING.value,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            item.status = ReviewStatus.APPROVED.value  # type: ignore[misc]

    def test_to_dict_is_json_safe(self) -> None:
        item = ReviewItem(
            review_id="r-1", proposal_id="p-1",
            target_identity="KO-1", proposal_type="boundary_update_candidate",
            summary="x", status=ReviewStatus.PENDING.value,
        )
        encoded = json.dumps(item.to_dict())
        assert json.loads(encoded) == item.to_dict()


# ---------------------------------------------------------------------------
# Test 3 -- Queue is append-only
# ---------------------------------------------------------------------------

class TestAppendOnly:

    def test_enqueue_grows_the_queue(self, manager) -> None:
        assert manager.queue.count() == 0
        manager.queue.enqueue(_make_proposal(proposal_id="p-1"))
        manager.queue.enqueue(_make_proposal(proposal_id="p-2"))
        assert manager.queue.count() == 2
        assert manager.queue.distinct_review_count() == 2

    def test_status_change_appends_a_new_entry(self, manager) -> None:
        proposal = _make_proposal(proposal_id="p-1")
        item = manager.queue.enqueue(proposal)
        manager.approve(item.review_id, reviewer="alice")
        # 1 PENDING + 1 APPROVED = 2 records, 1 distinct review.
        assert manager.queue.count() == 2
        assert manager.queue.distinct_review_count() == 1
        history = manager.queue.history_for(item.review_id)
        assert [h.status for h in history] == ["PENDING", "APPROVED"]

    def test_forbidden_methods_raise_type_error(self, manager) -> None:
        with pytest.raises(TypeError):
            manager.queue.update()
        with pytest.raises(TypeError):
            manager.queue.delete()
        with pytest.raises(TypeError):
            manager.queue.overwrite()
        with pytest.raises(TypeError):
            manager.queue.clear()

    def test_forbidden_methods_reject_positional_and_keyword(
        self, manager,
    ) -> None:
        with pytest.raises(TypeError):
            manager.queue.update("any", "args", key="value")
        with pytest.raises(TypeError):
            manager.queue.delete(item_id="x")


# ---------------------------------------------------------------------------
# Test 4 -- approve performs PENDING -> APPROVED
# ---------------------------------------------------------------------------

class TestApprove:

    def test_approve_transitions_to_approved(
        self, manager, pending_item: ReviewItem,
    ) -> None:
        event = manager.approve(pending_item.review_id,
                                reviewer="alice", note="good")
        assert manager.queue.get(pending_item.review_id).status == (
            ReviewStatus.APPROVED.value
        )
        assert manager.queue.list_pending() == []
        assert len(manager.queue.list_approved()) == 1
        assert event.to_status == "APPROVED"
        assert event.from_status == "PENDING_REVIEW"

    def test_approve_records_proposal_event(
        self, manager, pending_item, proposal_store: ProposalStore,
    ) -> None:
        assert proposal_store.count() == 0
        manager.approve(pending_item.review_id)
        assert proposal_store.count() == 1
        ev = proposal_store.latest_for(pending_item.proposal_id)
        assert ev is not None
        assert ev.to_status == "APPROVED"


# ---------------------------------------------------------------------------
# Test 5 -- reject performs PENDING -> REJECTED
# ---------------------------------------------------------------------------

class TestReject:

    def test_reject_transitions_to_rejected(
        self, manager, pending_item: ReviewItem,
    ) -> None:
        event = manager.reject(pending_item.review_id,
                               reviewer="bob", note="not now")
        assert manager.queue.get(pending_item.review_id).status == (
            ReviewStatus.REJECTED.value
        )
        assert manager.queue.list_pending() == []
        assert len(manager.queue.list_rejected()) == 1
        assert event.to_status == "REJECTED"
        assert event.from_status == "PENDING_REVIEW"

    def test_reject_records_proposal_event(
        self, manager, pending_item, proposal_store: ProposalStore,
    ) -> None:
        manager.reject(pending_item.review_id)
        assert proposal_store.count() == 1
        ev = proposal_store.latest_for(pending_item.proposal_id)
        assert ev is not None
        assert ev.to_status == "REJECTED"


# ---------------------------------------------------------------------------
# Test 6 -- Illegal transitions are rejected
# ---------------------------------------------------------------------------

class TestIllegalTransitions:

    def test_cannot_approve_already_approved(
        self, manager, pending_item: ReviewItem,
    ) -> None:
        manager.approve(pending_item.review_id)
        with pytest.raises(ReviewError):
            manager.approve(pending_item.review_id)

    def test_cannot_reject_already_approved(
        self, manager, pending_item: ReviewItem,
    ) -> None:
        manager.approve(pending_item.review_id)
        with pytest.raises(ReviewError):
            manager.reject(pending_item.review_id)

    def test_cannot_approve_already_rejected(
        self, manager, pending_item: ReviewItem,
    ) -> None:
        manager.reject(pending_item.review_id)
        with pytest.raises(ReviewError):
            manager.approve(pending_item.review_id)

    def test_cannot_reject_already_rejected(
        self, manager, pending_item: ReviewItem,
    ) -> None:
        manager.reject(pending_item.review_id)
        with pytest.raises(ReviewError):
            manager.reject(pending_item.review_id)

    def test_unknown_review_id_raises(self, manager) -> None:
        with pytest.raises(ReviewError):
            manager.approve("does-not-exist")
        with pytest.raises(ReviewError):
            manager.reject("does-not-exist")


# ---------------------------------------------------------------------------
# Test 7 -- The original LearningProposal is never modified
# ---------------------------------------------------------------------------

class TestProposalImmutable:

    def test_enqueue_does_not_mutate_proposal(self, manager) -> None:
        proposal = _make_proposal(proposal_id="p-1")
        before = copy.deepcopy(proposal.to_dict())
        manager.queue.enqueue(proposal)
        assert proposal.to_dict() == before

    def test_approve_does_not_mutate_proposal(
        self, manager, pending_item,
    ) -> None:
        proposal = _make_proposal(proposal_id="p-1")
        before_status = proposal.status
        before_suggested = proposal.suggested_change
        manager.approve(pending_item.review_id)
        assert proposal.status == before_status
        assert proposal.suggested_change == before_suggested

    def test_reject_does_not_mutate_proposal(
        self, manager, pending_item,
    ) -> None:
        proposal = _make_proposal(proposal_id="p-1")
        before_status = proposal.status
        manager.reject(pending_item.review_id)
        assert proposal.status == before_status


# ---------------------------------------------------------------------------
# Test 8 -- AST architecture boundary
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
        "__init__.py", "object.py", "queue.py", "action.py", "report.py",
    ])
    def test_no_forbidden_imports(self, py_name: str) -> None:
        py = REVIEW_DIR / py_name
        if not py.exists():
            pytest.skip("missing module: " + py_name)
        seen = _imports(py)
        bad = [
            m for m in seen
            if any(m.startswith(p) for p in _FORBIDDEN_PREFIXES)
        ]
        assert not bad, py_name + " imports forbidden: " + str(bad)


# ---------------------------------------------------------------------------
# Auxiliary: report rendering
# ---------------------------------------------------------------------------

class TestReport:

    def test_report_includes_all_sections(
        self, manager, pending_item,
    ) -> None:
        manager.approve(pending_item.review_id, reviewer="alice")
        # add a second proposal and reject it
        item2 = manager.queue.enqueue(
            _make_proposal(proposal_id="p-2", reason="another boundary"),
        )
        manager.reject(item2.review_id, reviewer="bob")
        md = generate_report(manager.queue)
        assert "# Human Review Queue Report" in md
        assert "## Pending Reviews" in md
        assert "## History" in md
        assert "### Approved" in md
        assert "### Rejected" in md
        assert "p-1" in md
        assert "p-2" in md

    def test_report_empty_queue_renders_cleanly(self, queue) -> None:
        md = generate_report(queue)
        assert "(none)" in md
        assert "## Pending Reviews" in md


# ---------------------------------------------------------------------------
# Auxiliary: lifecycle helpers
# ---------------------------------------------------------------------------

class TestLifecycleHelpers:

    def test_review_action_to_proposal_status(self) -> None:
        from caseos.knowledge.feedback.review.action import (
            _to_proposal_status, _to_review_status,
        )
        from caseos.knowledge.feedback import ProposalStatus
        assert _to_proposal_status(ReviewAction.APPROVE) == (
            ProposalStatus.APPROVED
        )
        assert _to_proposal_status(ReviewAction.REJECT) == (
            ProposalStatus.REJECTED
        )
        assert _to_review_status(ReviewAction.APPROVE) == (
            ReviewStatus.APPROVED
        )
        assert _to_review_status(ReviewAction.REJECT) == (
            ReviewStatus.REJECTED
        )
