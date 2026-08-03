"""Sprint 22.2-B.4 -- Integration Verification for Sprint 22.2-B.1 ~ B.3.

This file is the **integration verification** layer for the
Contradiction Analyzer and its supporting data structures. It does
not implement any new intelligence; it pins the contract.

Groups:

    A. ContradictionResult contract       (Sprint 22.2-B.1)
    B. ContradictionAnalyzer contract    (Sprint 22.2-B.2 + B.2.1)
    C. Evaluation layer consumes analyzer (this sprint)
    D. Architecture-boundary AST scan    (this sprint)
    E. Feedback-runtime end-to-end       (this sprint)
    F. Stability / regression guards     (this sprint)
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
    FeedbackManager, FeedbackSource, FeedbackStatus, FeedbackStore,
    FeedbackType, FeedbackValidator, new_event, new_feedback,
)
from caseos.knowledge.feedback.evaluation import (
    FeedbackEvaluation, FeedbackEvaluator, SOURCE_WEIGHTS,
)
from caseos.knowledge.feedback.evaluation.contradiction import (
    ContradictionResult,
)
from caseos.knowledge.feedback.evaluation.analyzer import (
    ContradictionAnalyzer,
)
from caseos.knowledge.objects.loader import (
    DEFAULT_CORPUS_DIR, load_corpus,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"
EVAL_DIR = BACKEND / "caseos" / "knowledge" / "feedback" / "evaluation"


# ---------------------------------------------------------------------------
# Fixtures (integration-level, read-only)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real_ko() -> dict:
    """Load a real Knowledge Object from the on-disk corpus."""
    objects = load_corpus(DEFAULT_CORPUS_DIR)
    assert objects, "corpus must be non-empty for integration tests"
    ko = dict(objects[0])
    ko.setdefault("principle", "")
    ko.setdefault("boundary", [])
    return ko


@pytest.fixture(scope="module")
def analyzer() -> ContradictionAnalyzer:
    return ContradictionAnalyzer()


@pytest.fixture(scope="module")
def evaluator() -> FeedbackEvaluator:
    return FeedbackEvaluator()


# ---------------------------------------------------------------------------
# Group A -- ContradictionResult contract (Sprint 22.2-B.1)
# ---------------------------------------------------------------------------

class TestContradictionResultContract:
    """Pin every field of the B.1 data object."""

    EXPECTED_FIELDS = {
        "feedback_id": "str",
        "target_identity": "str",
        "has_conflict": "bool",
        "conflict_type": "str",
        "matched_field": "str",
        "explanation": "str",
        "requires_human_review": "bool",
        "created_at": "str",
    }

    def test_all_required_fields_present(self) -> None:
        actual = {f.name for f in dataclasses.fields(ContradictionResult)}
        for k in self.EXPECTED_FIELDS:
            assert k in actual, "missing required field: " + k

    def test_field_types_match(self) -> None:
        for f in dataclasses.fields(ContradictionResult):
            assert f.type == self.EXPECTED_FIELDS[f.name], (
                "field " + f.name + " type drift: "
                + str(f.type) + " vs contract "
                + str(self.EXPECTED_FIELDS[f.name])
            )

    def test_is_frozen(self) -> None:
        r = ContradictionResult(
            feedback_id="x", target_identity="y",
            has_conflict=True, conflict_type="boundary_conflict",
            matched_field="boundary", explanation="e",
            requires_human_review=True,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            r.has_conflict = False  # type: ignore[misc]

    def test_to_dict_is_json_safe(self) -> None:
        r = ContradictionResult(
            feedback_id="x", target_identity="y",
            has_conflict=False, conflict_type=None,
            matched_field="", explanation="e",
            requires_human_review=True,
        )
        d = r.to_dict()
        encoded = json.dumps(d)
        decoded = json.loads(encoded)
        assert decoded == d

    def test_created_at_auto_populated(self) -> None:
        r = ContradictionResult(
            feedback_id="x", target_identity="y",
            has_conflict=False, conflict_type=None,
            matched_field="", explanation="e",
            requires_human_review=True,
        )
        assert r.created_at
        assert r.created_at.endswith("Z")
        assert "T" in r.created_at


# ---------------------------------------------------------------------------
# Group B -- ContradictionAnalyzer contract (Sprint 22.2-B.2 + B.2.1)
# ---------------------------------------------------------------------------

class TestContradictionAnalyzerContract:

    def test_analyze_returns_contradiction_result(
        self, analyzer: ContradictionAnalyzer, real_ko: dict,
    ) -> None:
        out = analyzer.analyze({"content": "Add scattered equipment"}, real_ko)
        assert isinstance(out, ContradictionResult)

    def test_boundary_conflict_path(self, analyzer, real_ko) -> None:
        ko = {**real_ko, "boundary": ["Do not add scattered equipment"]}
        out = analyzer.analyze(
            {"content": "Add scattered equipment everywhere"}, ko,
        )
        assert out.has_conflict is True
        assert out.conflict_type == "boundary_conflict"
        assert out.matched_field == "boundary"
        assert out.requires_human_review is True

    def test_principle_conflict_path_without_hierarchy(self, analyzer, real_ko) -> None:
        ko = {**real_ko,
              "principle": "Create hierarchy before adding facilities"}
        out = analyzer.analyze(
            {"content": "Add facilities without hierarchy"}, ko,
        )
        assert out.has_conflict is True
        assert out.conflict_type == "principle_conflict"
        assert out.matched_field == "principle"

    def test_principle_conflict_path_with_instead_of(self, analyzer, real_ko) -> None:
        ko = {**real_ko,
              "principle": "Create hierarchy before adding facilities"}
        out = analyzer.analyze(
            {"content": "Add facilities instead of hierarchy"}, ko,
        )
        assert out.has_conflict is True
        assert out.conflict_type == "principle_conflict"

    def test_no_conflict_path_returns_none_type(
        self, analyzer: ContradictionAnalyzer, real_ko: dict,
    ) -> None:
        out = analyzer.analyze({"content": "This looks good"}, real_ko)
        assert out.has_conflict is False
        assert out.conflict_type is None
        assert out.matched_field == ""
        assert out.requires_human_review is True

    def test_safety_guard_creativity_after_safety(
        self, analyzer: ContradictionAnalyzer, real_ko: dict,
    ) -> None:
        ko = {**real_ko, "principle": "Safety before creativity"}
        out = analyzer.analyze(
            {"content": "Improve creativity after safety review"}, ko,
        )
        assert out.has_conflict is False
        assert out.conflict_type is None

    def test_safety_guard_descriptive_only(self, analyzer, real_ko) -> None:
        ko = {**real_ko, "boundary": ["Do not add scattered equipment"]}
        out = analyzer.analyze(
            {"content": "The site already has scattered equipment"}, ko,
        )
        assert out.has_conflict is False

    def test_is_stateless(self, analyzer, real_ko) -> None:
        ko = {**real_ko, "boundary": ["Do not add scattered equipment"]}
        r1 = analyzer.analyze(
            {"content": "Add scattered equipment everywhere"}, ko,
        )
        r2 = analyzer.analyze(
            {"content": "Add scattered equipment everywhere"}, ko,
        )
        assert r1.has_conflict == r2.has_conflict
        assert r1.matched_field == r2.matched_field
        assert r1.conflict_type == r2.conflict_type

    def test_does_not_mutate_knowledge_object(self, analyzer, real_ko) -> None:
        before = copy.deepcopy(real_ko)
        analyzer.analyze(
            {"content": "Add scattered equipment everywhere"}, real_ko,
        )
        assert real_ko == before


# ---------------------------------------------------------------------------
# Group C -- Evaluation layer can consume the analyzer output
# ---------------------------------------------------------------------------

class TestEvaluationLayerConsumesAnalyzer:

    def test_feedback_evaluation_passes_through_feedback_id(
        self, evaluator: FeedbackEvaluator,
    ) -> None:
        fb = new_feedback(
            FeedbackSource.EXPERT, FeedbackType.CONTRADICTION_SIGNAL,
            "KO-1", "Add scattered equipment everywhere",
        )
        ev = evaluator.evaluate(fb)
        assert isinstance(ev, FeedbackEvaluation)
        assert ev.feedback_id == fb.id
        assert ev.requires_human_review is True

    def test_evaluator_and_analyzer_share_feedback_id(
        self, evaluator: FeedbackEvaluator,
        analyzer: ContradictionAnalyzer, real_ko: dict,
    ) -> None:
        fb = new_feedback(
            FeedbackSource.EXPERT, FeedbackType.CONTRADICTION_SIGNAL,
            real_ko["identity"], "Add scattered equipment everywhere",
        )
        ev = evaluator.evaluate(fb)
        cr = analyzer.analyze(fb, real_ko)
        assert ev.feedback_id == cr.feedback_id == fb.id

    def test_evaluator_and_analyzer_share_target_identity(
        self, evaluator: FeedbackEvaluator,
        analyzer: ContradictionAnalyzer, real_ko: dict,
    ) -> None:
        fb = new_feedback(
            FeedbackSource.EXPERT, FeedbackType.CONTRADICTION_SIGNAL,
            real_ko["identity"], "Looks good overall",
        )
        ev = evaluator.evaluate(fb)
        cr = analyzer.analyze(fb, real_ko)
        assert cr.target_identity == real_ko["identity"]
        assert ev.feedback_id == fb.id

    def test_evaluator_works_on_dict(self, evaluator: FeedbackEvaluator) -> None:
        ev = evaluator.evaluate({
            "feedback_id": "fb-x", "source": "EXPERT",
            "feedback_type": "CONTRADICTION_SIGNAL",
            "target_identity": "KO-1", "content": "x",
        })
        assert ev.feedback_id == "fb-x"
        assert ev.weight == SOURCE_WEIGHTS["EXPERT"]
        assert ev.priority == "highest"

    def test_evaluator_works_on_feedback_event(
        self, evaluator: FeedbackEvaluator,
    ) -> None:
        fb = new_feedback(
            FeedbackSource.OUTCOME, FeedbackType.POSITIVE_CONFIRMATION,
            "KO-2", "works", feedback_id="fb-evt",
        )
        ev = new_event(
            "fb-evt", None, FeedbackStatus.RECEIVED,
            snapshot=fb.to_dict(),
        )
        out = evaluator.evaluate(ev)
        assert out.feedback_id == "fb-evt"
        assert out.source == "OUTCOME"
        assert out.weight == SOURCE_WEIGHTS["OUTCOME"]


# ---------------------------------------------------------------------------
# Group D -- Architecture boundary AST scan
# ---------------------------------------------------------------------------

_FORBIDDEN_PREFIXES = (
    "caseos.intelligence",
    "caseos.knowledge.retrieval",
)

_ALLOWED_PREFIXES = (
    "caseos.knowledge.feedback",
    "caseos.knowledge.governance",
    "caseos.knowledge.objects",
)


def _imports(py_path: Path) -> set:
    tree = ast.parse(py_path.read_text(encoding="utf-8"))
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module)
    return out


class TestArchitectureBoundary:

    def _check(self, py_name: str) -> None:
        py = EVAL_DIR / py_name
        assert py.exists(), py_name + " missing"
        seen = _imports(py)
        forbidden = [
            m for m in seen
            if any(m.startswith(p) for p in _FORBIDDEN_PREFIXES)
        ]
        assert not forbidden, (
            py_name + " imports forbidden modules: " + str(forbidden)
        )
        caseos_seen = [
            m for m in seen
            if m.startswith("caseos.") and m != "caseos"
        ]
        for m in caseos_seen:
            assert any(m.startswith(a) for a in _ALLOWED_PREFIXES), (
                py_name + " imports a non-allowlisted caseos module: " + m
            )

    def test_contradiction_py_boundary(self) -> None:
        self._check("contradiction.py")

    def test_analyzer_py_boundary(self) -> None:
        self._check("analyzer.py")

    def test_evaluator_py_boundary(self) -> None:
        self._check("evaluator.py")

    def test_weight_py_boundary(self) -> None:
        self._check("weight.py")

    def test_evaluation_object_py_boundary(self) -> None:
        self._check("object.py")

    def test_report_py_boundary(self) -> None:
        self._check("report.py")


# ---------------------------------------------------------------------------
# Group E -- Feedback-runtime end-to-end
# ---------------------------------------------------------------------------

class TestFeedbackRuntimeEndToEnd:

    def _manager(self) -> FeedbackManager:
        objects = load_corpus(DEFAULT_CORPUS_DIR)
        identities = {str(o.get("identity", "")) for o in objects
                      if o.get("identity")}
        return FeedbackManager(
            store=FeedbackStore(),
            validator=FeedbackValidator(),
            valid_targets=identities,
            require_target_check=True,
        )

    def test_full_pipeline_emits_evaluations(
        self,
        evaluator: FeedbackEvaluator,
        analyzer: ContradictionAnalyzer,
    ) -> None:
        m = self._manager()
        objects = load_corpus(DEFAULT_CORPUS_DIR)
        ko = objects[0]
        target = str(ko.get("identity", ""))
        fb = m.receive_feedback(
            FeedbackSource.EXPERT,
            FeedbackType.CONTRADICTION_SIGNAL,
            target,
            "Add scattered equipment everywhere",
        )
        m.validate(fb.id)
        m.generate_proposal(
            fb.id,
            current_state={"boundary": ko.get("boundary", [])},
        )
        ev = evaluator.evaluate(fb)
        cr = analyzer.analyze(fb, ko)
        assert ev.feedback_id == fb.id
        assert cr.feedback_id == fb.id
        assert m.store.count() > 0

    def test_pipeline_is_idempotent(
        self,
        evaluator: FeedbackEvaluator,
        analyzer: ContradictionAnalyzer,
    ) -> None:
        m = self._manager()
        objects = load_corpus(DEFAULT_CORPUS_DIR)
        ko = objects[0]
        target = str(ko.get("identity", ""))
        fb = m.receive_feedback(
            FeedbackSource.EXPERT,
            FeedbackType.CONTRADICTION_SIGNAL,
            target,
            "Add scattered equipment everywhere",
        )
        ev1 = evaluator.evaluate(fb)
        cr1 = analyzer.analyze(fb, ko)
        ev2 = evaluator.evaluate(fb)
        cr2 = analyzer.analyze(fb, ko)
        assert (ev1.feedback_id, ev1.weight) == (ev2.feedback_id, ev2.weight)
        assert (cr1.has_conflict, cr1.matched_field) == (
            cr2.has_conflict, cr2.matched_field,
        )


# ---------------------------------------------------------------------------
# Group F -- Stability / regression guards
# ---------------------------------------------------------------------------

class TestStabilityGuards:

    def test_contradiction_result_field_count_is_stable(self) -> None:
        assert len(dataclasses.fields(ContradictionResult)) == 8

    def test_analyzer_does_not_depend_on_intelligence_or_retrieval(
        self,
    ) -> None:
        import caseos.knowledge.feedback.evaluation.analyzer as mod
        forbidden = (
            "caseos.intelligence",
            "caseos.knowledge.retrieval",
        )
        for name in dir(mod):
            obj = getattr(mod, name)
            mod_name = getattr(obj, "__module__", "") or ""
            assert not any(mod_name.startswith(f) for f in forbidden), (
                "analyzer leaks dependency: " + name + " -> " + mod_name
            )

    def test_evaluator_returns_dataclass_with_correct_field_count(
        self,
    ) -> None:
        assert len(dataclasses.fields(FeedbackEvaluation)) == 7

    def test_evaluation_pipeline_does_not_modify_input(self) -> None:
        fb = new_feedback(
            FeedbackSource.EXPERT, FeedbackType.CONTRADICTION_SIGNAL,
            "KO-1", "Add scattered equipment everywhere",
        )
        before = copy.deepcopy(fb.to_dict())
        ContradictionAnalyzer().analyze(fb, {"boundary": ["Do not add"]})
        FeedbackEvaluator().evaluate(fb)
        assert fb.to_dict() == before
