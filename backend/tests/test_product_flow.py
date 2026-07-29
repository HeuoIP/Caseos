"""Smoke test for the CaseOS Product Layer (Sprint 8).

Acceptance criteria: the workflow can be simulated with one image path
and one JSON payload, and the output contains:

  * Space Summary
  * Decision Goal
  * Strategy
  * Recommended Objects
  * Explanation
  * Markdown Report

The Vision API is mocked so no network calls happen during the test.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.core.product import (  # noqa: E402
    PrimaryGoal,
    ProductFlow,
    ProductRequest,
    ProjectType,
    SessionStatus,
)
from app.core.product.session import ProductSession  # noqa: E402
from app.core.decision.knowledge import KnowledgeBase  # noqa: E402

_REPO_ROOT = _BACKEND.parent
_KB = KnowledgeBase(_REPO_ROOT / "knowledge")


# ---------------------------------------------------------------------
# Mock Vision Analyzer: returns canned V3 JSON. No network calls.
# ---------------------------------------------------------------------

class _MockVisionAnalyzer:
    """Stand-in for CaseVisionAnalyzer. Returns canned V3 JSON."""

    def __init__(self, payload: dict | None = None):
        self.payload = payload or self._default_payload()
        self.calls: list[str] = []

    def analyze(self, image_path: str) -> dict:
        self.calls.append(image_path)
        return self.payload

    @staticmethod
    def _default_payload() -> dict:
        return {
            "basic_info": {"project_name": "Sky Park", "site_type": "SITE.PUBLIC_PARK"},
            "design": {
                "theme": [
                    {"id": "NATURE.FOREST", "role": "primary", "confidence": 0.9},
                    {"id": "FANTASY.FAIRY_TALE", "role": "secondary", "confidence": 0.6},
                ],
                "style": ["STYLE.ORGANIC"],
                "design_highlights": ["Treehouse with rope bridge", "Sensory garden path"],
            },
            "target_users": {"age_group": ["AGE.3_6", "AGE.6_9"]},
            "play_experience": {"play_behaviors": ["PLAY.CLIMB", "PLAY.EXPLORE"]},
            "equipment": {"functional_units": ["UNIT.CLIMBING", "UNIT.SLIDE"]},
            "materials": {"main_materials": ["MATERIAL.WOOD", "MATERIAL.ROPE"]},
            "color": {"colors": ["COLOR.NATURAL"]},
            "safety": {"inclusive_design": True, "risk_level": "medium"},
            "ai_analysis": {
                "vision_summary": "Forest-themed public park playground with a treehouse, rope nets, and a long slide.",
                "design_interpretation": "Uses a forest narrative to organise a multi-level climbing path that supports exploration.",
                "confidence": 0.85,
            },
            "metadata": {},
        }


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _make_request(image_path: str = "data/images/cases/001.jpg") -> ProductRequest:
    return ProductRequest(
        image_path=image_path,
        project_type=ProjectType.PUBLIC_PARK,
        primary_goal=PrimaryGoal.INCREASE_VISITORS,
        site_name="Central Park Playscape",
    )


def _make_flow(payload: dict | None = None) -> ProductFlow:
    return ProductFlow(
        vision_analyzer=_MockVisionAnalyzer(payload),
        knowledge=_KB,
        repo_root=_REPO_ROOT,
    )


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_product_request_helpers() -> None:
    req = _make_request()
    assert req.domain == "PUBLIC_PARK"
    assert req.primary_goal_id == "BUSINESS.TRAFFIC"
    assert "\u516c\u5171" in req.project_description
    print(f"  [ok] domain={req.domain} goal={req.primary_goal_id}")


def test_run_returns_complete_response() -> None:
    """Acceptance criteria: every required slice is populated."""
    flow = _make_flow()
    req = _make_request()
    resp = flow.run(req)

    assert resp.space_summary is not None, "missing space_summary"
    assert resp.decision_goal is not None, "missing decision_goal"
    assert resp.strategies, "missing strategies"
    assert resp.recommended_objects, "missing recommended_objects"
    assert resp.explanations, "missing explanations"
    assert resp.markdown_report, "missing markdown_report"
    assert "CaseOS Recommendation" in resp.markdown_report

    print(f"  [ok] site={resp.space_summary.site_type}")
    print(f"  [ok] project={resp.decision_goal.project_type} goal={resp.decision_goal.primary_goal_label}")
    print(f"  [ok] profile={resp.decision_goal.inferred_profile}")
    print(f"  [ok] strategies={[s.strategy_id for s in resp.strategies]}")
    print(f"  [ok] top={[r.object_id for r in resp.recommended_objects]}")
    print(f"  [ok] explanations={len(resp.explanations)} paragraphs")
    print(f"  [ok] markdown length = {len(resp.markdown_report)} chars")


def test_session_object_tracks_stages() -> None:
    flow = _make_flow()
    session = ProductSession(request=_make_request())
    session = flow.run_session(session)

    assert session.status == SessionStatus.COMPLETED
    assert session.response is not None
    stage_names = [s.name for s in session.stages]
    assert stage_names == ["vision", "selections", "engine", "report", "images"]
    assert session.stages[0].status == "ok"
    assert session.stages[-1].status == "skipped"
    assert session.stages[-1].note.startswith("skipped")

    print(f"  [ok] stages={stage_names}")
    print(f"  [ok] session_id={session.session_id[:8]}...")


def test_user_primary_goal_is_injected() -> None:
    """The user-selected primary goal must appear at the top of the goals list."""
    flow = _make_flow()
    req = ProductRequest(
        image_path="x.jpg",
        project_type=ProjectType.KINDERGARTEN,
        primary_goal=PrimaryGoal.IMPROVE_ENROLLMENT,
    )
    resp = flow.run(req)

    # All goals should include EDU.ENROLLMENT (user choice) at index 0.
    assert resp.all_goals[0].goal_id == "EDU.ENROLLMENT"
    assert resp.all_goals[0].confidence == 1.0
    assert "User-selected" in resp.all_goals[0].rationale
    print(f"  [ok] primary goal injected: {resp.all_goals[0].goal_id}")


def test_different_project_types_change_profile() -> None:
    """Different project types should map to different inferred profiles.

    The mock Vision payload must be project-specific so that the
    engine's SpaceAgent picks the right site_type -> domain mapping.
    """
    park_payload = dict(_MockVisionAnalyzer._default_payload())
    park_payload["basic_info"] = {"site_type": "SITE.PUBLIC_PARK"}
    kg_payload = dict(_MockVisionAnalyzer._default_payload())
    kg_payload["basic_info"] = {"site_type": "SITE.KINDERGARTEN"}

    flow_park = _make_flow(park_payload)
    flow_kg = _make_flow(kg_payload)

    park = flow_park.run(ProductRequest(
        image_path="x.jpg", project_type=ProjectType.PUBLIC_PARK,
        primary_goal=PrimaryGoal.INCREASE_VISITORS,
    )).decision_goal.inferred_profile

    kg = flow_kg.run(ProductRequest(
        image_path="x.jpg", project_type=ProjectType.KINDERGARTEN,
        primary_goal=PrimaryGoal.IMPROVE_ENROLLMENT,
    )).decision_goal.inferred_profile

    assert park != kg, f"profile did not change: park={park} kg={kg}"
    print(f"  [ok] PUBLIC_PARK -> {park}")
    print(f"  [ok] KINDERGARTEN -> {kg}")


def test_failure_does_not_crash_run() -> None:
    """If Vision fails, the run raises ProductFlowError but session is recorded."""

    class _BrokenAnalyzer(_MockVisionAnalyzer):
        def analyze(self, image_path):
            raise RuntimeError("simulated network failure")

    flow = ProductFlow(
        vision_analyzer=_BrokenAnalyzer(),
        knowledge=_KB,
        repo_root=_REPO_ROOT,
    )
    session = ProductSession(request=_make_request())
    session = flow.run_session(session)

    assert session.status == SessionStatus.FAILED
    assert "simulated network failure" in (session.error or "")
    assert session.response is None
    assert session.stages[0].status == "error"

    # run() should raise.
    raised = False
    try:
        flow.run(_make_request())
    except Exception as exc:
        raised = True
        assert "simulated network failure" in str(exc)
    assert raised, "ProductFlow.run did not raise on FAILED session"
    print(f"  [ok] failure handled: status={session.status.value} error={session.error}")


def test_describe_endpoint() -> None:
    flow = _make_flow()
    desc = flow.describe()
    assert "workflow_stages" in desc
    assert "vision_analyzer" in desc
    assert desc["vision_analyzer"] == "_MockVisionAnalyzer"
    print(f"  [ok] describe={desc}")


def main() -> int:
    print("== CaseOS Product Layer (Sprint 8) smoke test ==\n")
    tests = [
        test_product_request_helpers,
        test_run_returns_complete_response,
        test_session_object_tracks_stages,
        test_user_primary_goal_is_injected,
        test_different_project_types_change_profile,
        test_failure_does_not_crash_run,
        test_describe_endpoint,
    ]
    for fn in tests:
        print(f"[run] {fn.__name__}")
        fn()
        print()
    print("== ALL TESTS PASSED ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())