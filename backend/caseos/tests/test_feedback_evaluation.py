"""Tests for the Feedback Evaluation Core Foundation V1 (Sprint 22.2-A)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.knowledge.feedback import (
    FeedbackEvent, FeedbackStatus, new_event, new_feedback,
    FeedbackSource, FeedbackType,
)
from caseos.knowledge.feedback.evaluation import (
    FeedbackEvaluation, FeedbackEvaluator, FeedbackWeight,
    SOURCE_WEIGHTS, SOURCE_PRIORITIES, SOURCE_PRIORITY_LABEL,
    WeightAssessment, generate_report, generate_summary, source_weight,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"


# ------------- Foundation object ---------------------------------------

def test_feedback_evaluation_fields_present() -> None:
    e = FeedbackEvaluation(
        feedback_id="fb-1", source="EXPERT",
        feedback_type="POSITIVE_CONFIRMATION",
        weight=100, priority="highest", requires_human_review=True,
    )
    d = e.to_dict()
    for k in ("feedback_id","source","feedback_type","weight",
             "priority","requires_human_review","created_at"):
        assert k in d
    assert d["requires_human_review"] is True


# ------------- Weight engine ------------------------------------------

def test_source_weight_ladder() -> None:
    assert source_weight(FeedbackSource.EXPERT) == 100
    assert source_weight(FeedbackSource.OUTCOME) == 75
    assert source_weight(FeedbackSource.REASON) == 50
    assert source_weight(FeedbackSource.PREFERENCE) == 25
    assert SOURCE_WEIGHTS[FeedbackSource.EXPERT.value] == 100
    assert SOURCE_PRIORITIES[FeedbackSource.EXPERT] == "highest"
    assert SOURCE_PRIORITY_LABEL == SOURCE_PRIORITIES


def test_weight_assessment_unknown_source() -> None:
    r = FeedbackWeight().assess("ROBOT")
    assert r.is_valid is False
    assert r.weight == 0
    assert r.priority == "unknown"


# ------------- Evaluator ----------------------------------------------

def test_evaluator_reads_feedback_object() -> None:
    fb = new_feedback(FeedbackSource.EXPERT, FeedbackType.NEGATIVE_CORRECTION,
                      "KO-1", "boundary too strict")
    r = FeedbackEvaluator().evaluate(fb)
    assert isinstance(r, FeedbackEvaluation)
    assert r.source == "EXPERT"
    assert r.feedback_type == "NEGATIVE_CORRECTION"
    assert r.weight == 100
    assert r.priority == "highest"
    assert r.requires_human_review is True


def test_evaluator_reads_feedback_event() -> None:
    fb = new_feedback(FeedbackSource.PREFERENCE, FeedbackType.PREFERENCE_SIGNAL,
                      "KO-2", "nicer", feedback_id="fb-2")
    ev = new_event("fb-2", None, FeedbackStatus.RECEIVED,
                   snapshot=fb.to_dict())
    r = FeedbackEvaluator().evaluate(ev)
    assert r.feedback_id == "fb-2"
    assert r.source == "PREFERENCE"
    assert r.weight == 25
    assert r.requires_human_review is True


def test_evaluator_accepts_plain_dict() -> None:
    r = FeedbackEvaluator().evaluate({
        "feedback_id": "fb-3", "source": "OUTCOME",
        "feedback_type": "POSITIVE_CONFIRMATION",
    })
    assert r.feedback_id == "fb-3"
    assert r.weight == 75


# ------------- Report --------------------------------------------------

def test_report_renders_markdown() -> None:
    fb = new_feedback(FeedbackSource.EXPERT, FeedbackType.POSITIVE_CONFIRMATION,
                      "KO-1", "works", feedback_id="fb-1")
    r = FeedbackEvaluator().evaluate(fb)
    md = generate_report(r)
    assert "# Feedback Evaluation Report" in md
    assert "Total evaluations" in md
    assert "Per-evaluation detail" in md


def test_summary_is_json_safe() -> None:
    fb = new_feedback(FeedbackSource.REASON, FeedbackType.NEGATIVE_CORRECTION,
                      "KO-1", "too expensive", feedback_id="fb-4")
    r = FeedbackEvaluator().evaluate(fb)
    s = generate_summary(r)
    for k in ("total_evaluations","weight_distribution",
              "priority_distribution","reviews_required"):
        assert k in s
    assert s["total_evaluations"] == 1
    assert s["reviews_required"] == 1


# ------------- Architecture boundary ----------------------------------

def test_evaluation_does_not_import_intelligence_engines() -> None:
    """The evaluation module must not import the existing engines."""
    forbidden = ("caseos.intelligence.decision",
                 "caseos.intelligence.trust",
                 "caseos.intelligence.recommendation",
                 "caseos.knowledge.retrieval")
    import ast
    from pathlib import Path
    mod_dir = Path(BACKEND) / "caseos" / "knowledge" / "feedback" / "evaluation"
    for py in mod_dir.glob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if any(node.module.startswith(f) for f in forbidden):
                    pytest.fail(f"{py.name} imports {node.module}")


# ------------- Baseline regression -----------------------------------

def test_existing_baseline_tests_remain_green() -> None:
    env = {**os.environ, "PYTHONPATH": str(BACKEND) + os.pathsep + str(REPO_ROOT)}
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "backend/caseos/tests", "-q",
         "--ignore=backend/caseos/tests/test_feedback_evaluation.py",
         "--ignore=backend/caseos/tests/test_human_understanding.py",
         "--ignore=backend/caseos/tests/test_feedback_runtime.py"],
        cwd=str(REPO_ROOT), env=env, capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    assert "passed" in proc.stdout
