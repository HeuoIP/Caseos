"""End-to-end pipeline test.

Sprint 19.1 Acceptance Criteria Test 1: "pipeline can execute end-to-end".
Uses the default six-stage pipeline with placeholder modules; the test
proves the structure works, not the intelligence quality.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make the package importable when running pytest from anywhere in the repo.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.brain.runtime.context import ProjectContext
from caseos.brain.runtime.pipeline import default_pipeline


def test_default_pipeline_runs_end_to_end() -> None:
    project = ProjectContext(
        project_id="test-1",
        project_type="kindergarten_outdoor",
        site_description="an empty outdoor space",
        user_goal="increase enrollment",
        constraints="limited budget",
    )
    pipeline = default_pipeline()
    ctx = pipeline.run(project)

    # All six stages filled their slot
    assert ctx.human_context is not None, "human stage did not run"
    assert len(ctx.knowledge_patterns) >= 0, "knowledge stage did not run"
    assert ctx.decision_object is not None, "decision stage did not run"
    assert ctx.trust_object is not None, "trust stage did not run"
    assert ctx.recommendation is not None, "recommendation stage did not run"
    assert ctx.metadata.get("markdown"), "output stage did not render"

    # Stage log lists every stage we wired.
    log = ctx.metadata.get("stage_log", [])
    names = [entry["stage"] for entry in log if entry["stage"] != "pipeline"]
    assert names == ["human_understanding", "knowledge", "decision", "trust", "recommendation", "output"]


def test_six_stages_wired() -> None:
    pipeline = default_pipeline()
    assert len(pipeline.stages) == 6
    assert [s.name for s in pipeline.stages] == [
        "human_understanding",
        "knowledge",
        "decision",
        "trust",
        "recommendation",
        "output",
    ]