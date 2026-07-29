"""Smoke test for the CaseOS Agent Framework V1.

This test does NOT exercise AI intelligence. It verifies that:

  * the engine can be constructed with the default pipeline,
  * all five default agents register and run in order,
  * the DecisionContext is correctly populated stage by stage,
  * a real V2 Vision JSON (adapted to V3) flows through the pipeline,
  * the Markdown report generator renders without error.

Run:
    cd backend && python -m pytest tests/test_agent_framework.py -v
or:
    cd backend && python tests/test_agent_framework.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make `app` importable when running this file directly.
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.core.agents import AgentRegistry  # noqa: E402
from app.core.decision import DecisionEngine, KnowledgeBase  # noqa: E402
from app.core.recommendation import ReportGenerator, render_markdown  # noqa: E402

_REPO_ROOT = _BACKEND.parent
_KB = KnowledgeBase(_REPO_ROOT / "knowledge")


def _adapt_v2_to_v3(v2: dict) -> dict:
    """Minimal V2 -> V3 adapter so we can reuse real analysis JSON."""
    return {
        "basic_info": {
            "project_name": v2.get("project_name", ""),
            "case_id": "",
            "site_type": v2.get("site_type", ""),
            "country": "",
            "city": "",
        },
        "design": {
            "theme": v2.get("theme", []) or [],
            "style": v2.get("style", []) or [],
            "design_language": v2.get("design_keywords", []) or [],
            "design_story": "",
            "design_highlights": [],
        },
        "target_users": {
            "age_group": v2.get("age_group", []) or [],
            "user_type": [],
            "estimated_capacity": "",
        },
        "play_experience": {
            "play_behaviors": v2.get("play_behaviors", []) or [],
            "play_value": [],
            "challenge_level": "",
            "interaction_type": [],
        },
        "space": {"space_structure": "", "functional_zones": [], "circulation": "", "viewpoints": []},
        "equipment": {
            "functional_units": v2.get("functional_units", []) or [],
            "core_equipment": [],
            "interactive_devices": [],
        },
        "landscape": {"planting": [], "terrain": "", "water_features": [], "shade": ""},
        "materials": {"main_materials": v2.get("materials", []) or [], "ground_materials": [], "safety_surface": []},
        "color": {"colors": v2.get("colors", []) or [], "main_color": "", "color_strategy": ""},
        "safety": {"estimated_age_range": "", "risk_level": "", "inclusive_design": False},
        "commercial": {"applicable_scene": [], "commercial_value": [], "operation_features": []},
        "ai_analysis": {
            "keywords": v2.get("design_keywords", []) or [],
            "vision_summary": v2.get("vision_summary", ""),
            "design_interpretation": v2.get("design_interpretation", ""),
            "confidence": 0.0,
        },
        "metadata": v2.get("metadata", {}),
    }


def _synthetic_v3() -> dict:
    """A hand-crafted V3 Vision JSON for an indoor commercial playground."""
    return {
        "basic_info": {"project_name": "Sky Mall Kids Zone", "site_type": "SITE.SHOPPING_MALL"},
        "design": {
            "theme": [{"id": "FANTASY.FAIRY_TALE", "role": "primary", "confidence": 0.8}],
            "style": ["STYLE.MODERN"],
            "design_language": ["curved", "soft palette"],
            "design_highlights": ["Anchor treehouse with rope net bridge"],
        },
        "target_users": {"age_group": ["AGE.PRESCHOOL", "AGE.EARLY_CHILDHOOD"]},
        "play_experience": {"play_behaviors": ["PLAY.CLIMB", "PLAY.SLIDE"]},
        "equipment": {"functional_units": ["UNIT.SLIDE", "UNIT.CLIMBING"]},
        "materials": {"main_materials": ["MATERIAL.HDPE", "MATERIAL.ROPE"]},
        "color": {"colors": ["COLOR.WARM"]},
        "safety": {"inclusive_design": True, "risk_level": "medium"},
        "ai_analysis": {
            "vision_summary": "indoor family entertainment zone with curved structures and soft surfaces",
            "design_interpretation": "Uses fairy tale narrative to organize circulation",
            "confidence": 0.85,
        },
        "metadata": {},
    }


# ----- tests --------------------------------------------------------

def test_registry_has_all_default_agents() -> None:
    expected = {"space", "decision_maker", "strategy", "object_selector", "explain"}
    assert expected.issubset(set(AgentRegistry.names())), (
        f"missing agents: {expected - set(AgentRegistry.names())}"
    )
    print(f"  [ok] registry has: {sorted(AgentRegistry.names())}")


def test_engine_runs_synthetic_v3() -> None:
    engine = DecisionEngine(knowledge=_KB)
    ctx = engine.run(_synthetic_v3())
    assert ctx.space_summary is not None
    assert ctx.decision_maker is not None
    assert ctx.goals, "DecisionMakerAgent should populate goals"
    assert ctx.strategies, "StrategyAgent should populate strategies"
    assert ctx.top_recommendations, "ObjectSelectorAgent should produce recommendations"
    assert ctx.explanations, "ExplainAgent should produce explanations"

    print(f"  [ok] site={ctx.space_summary.site_type} domain={ctx.space_summary.domain}")
    print(f"  [ok] profile={ctx.decision_maker.profile}")
    print(f"  [ok] goals={[g.goal_id for g in ctx.goals]}")
    print(f"  [ok] strategies={[s.strategy_id for s in ctx.strategies]}")
    print(f"  [ok] top={[r.object_id for r in ctx.top_recommendations]}")


def test_engine_runs_real_v2_adapted() -> None:
    src = _REPO_ROOT / "data" / "analysis" / "cases" / "0001.json"
    if not src.exists():
        print(f"  [skip] {src} not found")
        return
    v2 = json.loads(src.read_text(encoding="utf-8"))
    v3 = _adapt_v2_to_v3(v2)
    engine = DecisionEngine(knowledge=_KB)
    ctx = engine.run(v3)
    assert ctx.space_summary is not None
    assert ctx.top_recommendations
    md = render_markdown(ctx)
    assert "CaseOS Recommendation" in md
    assert ctx.space_summary.site_type or "N/A" in md
    print(f"  [ok] site={ctx.space_summary.site_type} theme={ctx.space_summary.primary_theme}")
    print(f"  [ok] profile={ctx.decision_maker.profile}")
    print(f"  [ok] markdown length = {len(md)} chars")


def test_report_generator_writes_file(tmp_path: Path | None = None) -> None:
    import tempfile
    if tmp_path is None:
        tmp_path = Path(tempfile.mkdtemp())
    rg = ReportGenerator(DecisionEngine(knowledge=_KB))
    out = tmp_path / "report.md"
    res = rg.generate(_synthetic_v3(), output_path=out)
    assert out.exists()
    assert out.read_text(encoding="utf-8") == res.markdown
    print(f"  [ok] wrote {out} ({out.stat().st_size} bytes)")


def test_extensibility_register_custom_agent() -> None:
    """Verify a new agent can be added without modifying the engine."""
    from app.core.agents.base import Agent, AgentRegistry
    from app.core.decision.pipeline import Pipeline

    @AgentRegistry.register
    class _PingAgent(Agent):
        name = "ping"
        display_name = "Ping"

        def run(self, context) -> None:
            context.add_metadata("pinged", True)

    try:
        engine = DecisionEngine(
            knowledge=_KB,
            pipeline=Pipeline(agent_names=["space", "ping"]),
        )
        ctx = engine.run(_synthetic_v3())
        assert ctx.metadata.get("pinged") is True
        print("  [ok] custom agent 'ping' added and ran without engine change")
    finally:
        # Clean up so we don't pollute the global registry for other tests.
        AgentRegistry._agents.pop("ping", None)


def main() -> int:
    print("== CaseOS Agent Framework V1 smoke test ==\n")
    for fn in [
        test_registry_has_all_default_agents,
        test_engine_runs_synthetic_v3,
        test_engine_runs_real_v2_adapted,
        test_report_generator_writes_file,
        test_extensibility_register_custom_agent,
    ]:
        print(f"[run] {fn.__name__}")
        fn()
        print()
    print("== ALL TESTS PASSED ==")
    return 0


if __name__ == "__main__":
    import tempfile
    # Patch test_report_generator_writes_file to use a real tmp dir.
    tmp = Path(tempfile.mkdtemp())
    test_report_generator_writes_file(tmp)
    sys.exit(main())