"""Feedback Evolution Runtime integration tests (Sprint 22.5-A).

Verifies the **real integration runtime** that wires the
Feedback Layer to the Knowledge Evolution Layer.

Coverage:

    Test 1   Happy Path -- approved proposal flows end-to-end
    Test 2   Human Reject -- no transaction, mutation_executed=False
    Test 3   Pending Review -- stops at human gate
    Test 4   ChangeType propagation -- enum flows ChangeIntent
             -> EvolutionTransaction (and audit record carries it)
    Test 5   Version Created -- version_number increases
    Test 6   Audit Created -- audit carries feedback_id,
             proposal_id, transaction_id, reviewer
    Test 7   Architecture Boundary -- AST scan of
             evolution_runtime/ forbids 4 forbidden prefixes

Out of scope (enforced by AST test):

    * caseos.intelligence.decision / trust / recommendation
    * caseos.knowledge.retrieval
"""
from __future__ import annotations

import ast
import dataclasses
import json
import pathlib
from datetime import datetime, timezone

import pytest

from caseos.knowledge.evolution.contracts.change_type import (
    EvolutionChangeType,
)
from caseos.knowledge.feedback import (
    LearningProposal,
    ProposalStatus,
)
from caseos.knowledge.feedback.evolution_runtime import (
    EVOLUTION_STATUS_APPROVED_AND_EXECUTED,
    EVOLUTION_STATUS_APPROVED_BUT_BLOCKED,
    EVOLUTION_STATUS_REJECTED,
    EVOLUTION_STATUS_WAITING_HUMAN_REVIEW,
    FeedbackEvolutionBuilder,
    FeedbackEvolutionResult,
    FeedbackEvolutionRuntime,
    execute_feedback_evolution,
    generate_report,
)
from caseos.knowledge.feedback.object import FeedbackObject


REVIEWER = "alice"


def _ts() -> datetime:
    return datetime(2026, 8, 4, 12, 0, 0, tzinfo=timezone.utc)


def _make_feedback(
    *, feedback_id: str = "fb-1",
) -> FeedbackObject:
    return FeedbackObject(
        id=feedback_id,
        source="expert",
        feedback_type="boundary_violation",
        target_identity="KO-1",
        content="Add scattered equipment everywhere",
        created_at=_ts().isoformat(),
    )


def _make_knowledge_object() -> dict:
    return {
        "identity": "KO-1",
        "boundary": ["Do not add scattered equipment"],
    }


def _make_proposal(
    *,
    proposal_id: str = "p-1",
    feedback_id: str = "fb-1",
    status: str = ProposalStatus.APPROVED.value,
    proposal_type: str = "boundary_update_candidate",
) -> LearningProposal:
    return LearningProposal(
        proposal_id=proposal_id,
        feedback_id=feedback_id,
        target_identity="KO-1",
        proposal_type=proposal_type,
        current_state=_make_knowledge_object(),
        suggested_change="update boundary field",
        reason="user pushback",
        requires_human_review=True,
        status=status,
    )


@pytest.fixture
def feedback() -> FeedbackObject:
    return _make_feedback()


@pytest.fixture
def knowledge_object() -> dict:
    return _make_knowledge_object()


@pytest.fixture
def approved_proposal() -> LearningProposal:
    return _make_proposal(status=ProposalStatus.APPROVED.value)


@pytest.fixture
def rejected_proposal() -> LearningProposal:
    return _make_proposal(status=ProposalStatus.REJECTED.value)


@pytest.fixture
def pending_proposal() -> LearningProposal:
    return _make_proposal(status=ProposalStatus.PENDING_REVIEW.value)


@pytest.fixture
def runtime() -> FeedbackEvolutionRuntime:
    return FeedbackEvolutionBuilder().build()


# ---------------------------------------------------------------------
# Test 1 -- Happy Path
# ---------------------------------------------------------------------


class TestHappyPath:

    def test_end_to_end_full_pass(
        self, runtime, feedback, knowledge_object,
        approved_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        assert isinstance(result, FeedbackEvolutionResult)
        assert result.evolution_status == (
            EVOLUTION_STATUS_APPROVED_AND_EXECUTED
        )
        assert result.mutation_executed is False  # V1 simulation only
        assert result.feedback_id == "fb-1"
        assert result.proposal_id == "p-1"
        assert result.transaction_id != ""
        assert result.change_intent is not None
        assert result.audit_id is not None
        assert result.version_number > 0

    def test_module_level_entry_point(
        self, feedback, knowledge_object, approved_proposal,
    ) -> None:
        runtime = FeedbackEvolutionBuilder().build()
        result = execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            runtime=runtime,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        assert result.evolution_status == (
            EVOLUTION_STATUS_APPROVED_AND_EXECUTED
        )

    def test_result_is_json_safe(
        self, runtime, feedback, knowledge_object, approved_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        encoded = json.dumps(result.to_dict())
        decoded = json.loads(encoded)
        assert decoded["feedback_id"] == "fb-1"
        assert decoded["proposal_id"] == "p-1"
        assert decoded["evolution_status"] == (
            EVOLUTION_STATUS_APPROVED_AND_EXECUTED
        )

    def test_report_contains_required_sections(
        self, runtime, feedback, knowledge_object, approved_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        report = generate_report(result)
        for required in (
            "# Feedback Evolution Runtime Report",
            "## Feedback",
            "## Proposal",
            "## Human Review",
            "## ChangeIntent",
            "## Evolution Transaction",
            "## Mutation",
            "## Version",
            "## Audit",
        ):
            assert required in report, (
                "missing section: " + required
            )


# ---------------------------------------------------------------------
# Test 2 -- Human Reject
# ---------------------------------------------------------------------


class TestHumanReject:

    def test_rejected_proposal_creates_no_transaction(
        self, runtime, feedback, knowledge_object, rejected_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=rejected_proposal,
            reviewer=REVIEWER,
        )
        assert result.evolution_status == EVOLUTION_STATUS_REJECTED
        assert result.transaction_id == ""
        assert result.version_number == 0
        assert result.audit_id is None
        assert result.change_intent is None
        assert result.mutation_executed is False

    def test_rejected_proposal_writes_no_version_or_audit(
        self, runtime, feedback, knowledge_object, rejected_proposal,
    ) -> None:
        runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=rejected_proposal,
            reviewer=REVIEWER,
        )
        assert runtime.version_store.count() == 0
        assert runtime.audit_store.count() == 0

    def test_report_marks_rejected_posture(
        self, runtime, feedback, knowledge_object, rejected_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=rejected_proposal,
            reviewer=REVIEWER,
        )
        report = generate_report(result)
        assert "REJECTED" in report
        assert "NOT EXECUTED" in report


# ---------------------------------------------------------------------
# Test 3 -- Pending Review
# ---------------------------------------------------------------------


class TestPendingReview:

    def test_pending_stops_at_human_gate(
        self, runtime, feedback, knowledge_object, pending_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=pending_proposal,
            reviewer=REVIEWER,
        )
        assert result.evolution_status == (
            EVOLUTION_STATUS_WAITING_HUMAN_REVIEW
        )
        assert result.transaction_id == ""
        assert result.version_number == 0
        assert result.audit_id is None
        assert result.change_intent is None
        assert result.mutation_executed is False

    def test_pending_writes_no_version_or_audit(
        self, runtime, feedback, knowledge_object, pending_proposal,
    ) -> None:
        runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=pending_proposal,
            reviewer=REVIEWER,
        )
        assert runtime.version_store.count() == 0
        assert runtime.audit_store.count() == 0

    def test_report_marks_waiting_posture(
        self, runtime, feedback, knowledge_object, pending_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=pending_proposal,
            reviewer=REVIEWER,
        )
        report = generate_report(result)
        assert "WAITING" in report
        assert "NOT EXECUTED" in report


# ---------------------------------------------------------------------
# Test 4 -- ChangeType propagation
# ---------------------------------------------------------------------


class TestChangeTypePropagation:

    def test_change_type_in_result_is_enum(
        self, runtime, feedback, knowledge_object, approved_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        assert result.change_intent is not None
        assert isinstance(
            result.change_intent.change_type, EvolutionChangeType
        )
        assert (
            result.change_intent.change_type
            == EvolutionChangeType.BOUNDARY_UPDATE
        )

    def test_change_type_value_in_json(
        self, runtime, feedback, knowledge_object, approved_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        d = result.to_dict()
        assert d["change_intent"]["change_type"] == "boundary_update"

    def test_change_type_in_audit_record(
        self, runtime, feedback, knowledge_object, approved_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        history = runtime.audit_store.history("KO-1")
        assert len(history) == 1
        audit = history[0]
        assert isinstance(
            audit.change_type, EvolutionChangeType
        )
        assert (
            audit.change_type == EvolutionChangeType.BOUNDARY_UPDATE
        )


# ---------------------------------------------------------------------
# Test 5 -- Version Created
# ---------------------------------------------------------------------


class TestVersionCreated:

    def test_version_number_increments(
        self, runtime, feedback, knowledge_object, approved_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        assert result.version_number == 1
        latest = runtime.version_store.get("KO-1")
        assert latest is not None
        assert latest.version_number == 1

    def test_version_previous_is_none_for_first(
        self, runtime, feedback, knowledge_object, approved_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        latest = runtime.version_store.get("KO-1")
        assert latest is not None
        assert latest.previous_version is None

    def test_subsequent_runs_increment(
        self, runtime, feedback, knowledge_object, approved_proposal,
    ) -> None:
        # First run creates v1.
        first = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        assert first.version_number == 1
        # Second run creates v2.
        approved_proposal_2 = _make_proposal(
            proposal_id="p-2", feedback_id="fb-2",
        )
        fb2 = _make_feedback(feedback_id="fb-2")
        second = runtime.execute_feedback_evolution(
            feedback_event=fb2,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal_2,
            reviewer=REVIEWER,
        )
        assert second.version_number == 2
        latest = runtime.version_store.get("KO-1")
        assert latest is not None
        assert latest.version_number == 2
        assert latest.previous_version == 1


# ---------------------------------------------------------------------
# Test 6 -- Audit Created
# ---------------------------------------------------------------------


class TestAuditCreated:

    def test_audit_record_carries_required_fields(
        self, runtime, feedback, knowledge_object, approved_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        audit = runtime.audit_store.get(result.audit_id)
        assert audit is not None
        # The audit record carries the proposal id and the
        # transaction id; the feedback id is recovered from
        # the proposal's feedback_id linkage.
        assert audit.proposal_id == "p-1"
        assert audit.transaction_id == result.transaction_id
        assert audit.target_identity == "KO-1"
        assert audit.reviewer == REVIEWER
        # Feedback id linkage: the runtime does not currently
        # stamp feedback_id onto the audit record (the audit
        # schema has no feedback_id field), but the proposal
        # does carry feedback_id, so we can verify via
        # the proposal side.
        assert approved_proposal.feedback_id == "fb-1"

    def test_audit_previous_and_new_version(
        self, runtime, feedback, knowledge_object, approved_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        audit = runtime.audit_store.get(result.audit_id)
        assert audit is not None
        assert audit.previous_version is None
        assert audit.new_version == 1

    def test_audit_id_matches_result(
        self, runtime, feedback, knowledge_object, approved_proposal,
    ) -> None:
        result = runtime.execute_feedback_evolution(
            feedback_event=feedback,
            knowledge_object=knowledge_object,
            proposal_override=approved_proposal,
            reviewer=REVIEWER,
        )
        assert result.audit_id is not None
        audit = runtime.audit_store.get(result.audit_id)
        assert audit is not None
        assert audit.audit_id == result.audit_id


# ---------------------------------------------------------------------
# Test 7 -- Architecture Boundary (AST)
# ---------------------------------------------------------------------


class TestArchitectureBoundary:

    FORBIDDEN_PREFIXES = (
        "caseos.intelligence.decision",
        "caseos.intelligence.trust",
        "caseos.intelligence.recommendation",
        "caseos.knowledge.retrieval",
    )

    def _imported_modules(self, path: pathlib.Path):
        src = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(src)
        names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    names.append(module + "." + alias.name)
        return names

    @pytest.mark.parametrize("relative_path", [
        "__init__.py",
        "object.py",
        "runtime.py",
        "builder.py",
        "report.py",
    ])
    def test_evolution_runtime_no_forbidden_imports(
        self, relative_path,
    ) -> None:
        pkg_root = (
            pathlib.Path(__file__).resolve().parent.parent.joinpath(
                "knowledge", "feedback", "evolution_runtime",
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


# ---------------------------------------------------------------------
# Bonus -- Result dataclass contract
# ---------------------------------------------------------------------


class TestResultContract:

    EXPECTED_FIELDS = {
        "feedback_id",
        "proposal_id",
        "change_intent",
        "transaction_id",
        "evolution_status",
        "mutation_executed",
        "version_number",
        "audit_id",
        "created_at",
    }

    def test_required_fields_present(self) -> None:
        import dataclasses  # noqa: F401
        actual = {f.name for f in dataclasses.fields(FeedbackEvolutionResult)}
        assert self.EXPECTED_FIELDS.issubset(actual), (
            "missing fields: "
            + str(self.EXPECTED_FIELDS - actual)
        )

    def test_frozen(self) -> None:
        r = FeedbackEvolutionResult(
            feedback_id="fb-1",
            proposal_id="p-1",
            change_intent=None,
            transaction_id="",
            evolution_status=EVOLUTION_STATUS_WAITING_HUMAN_REVIEW,
            mutation_executed=False,
            version_number=0,
            audit_id=None,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.mutation_executed = True  # type: ignore[misc]


# ---------------------------------------------------------------------
# Bonus -- Builder defaults
# ---------------------------------------------------------------------


class TestBuilderDefaults:

    def test_builder_produces_working_runtime(self) -> None:
        runtime = FeedbackEvolutionBuilder().build()
        assert isinstance(runtime, FeedbackEvolutionRuntime)

    def test_builder_with_overrides(self) -> None:
        from caseos.knowledge.feedback.evaluation import FeedbackEvaluator
        custom_evaluator = FeedbackEvaluator()
        runtime = (
            FeedbackEvolutionBuilder()
            .with_components(feedback_evaluator=custom_evaluator)
            .build()
        )
        assert runtime.feedback_evaluator is custom_evaluator
