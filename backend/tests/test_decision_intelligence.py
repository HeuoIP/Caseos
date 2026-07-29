"""Sprint 9 smoke test: Decision Intelligence V1 pipeline.

Acceptance criteria from the Sprint 9 task:

  * One image path + one V3 Vision JSON in.
  * Six sections in the Markdown report:
      1. Space Analysis
      2. Decision Maker Analysis
      3. Retrieved Knowledge
      4. Strategy
      5. Recommended Objects
      6. Explanation

No network. No LLM. No database. Pure local pipeline.
"""
from __future__ import annotations

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from app.core.agents import AgentRegistry
from app.core.decision import DecisionEngine, KnowledgeBase
from app.core.decision.pipeline import DEFAULT_PIPELINE
from app.core.recommendation import render_markdown

_REPO_ROOT = _BACKEND.parent
_KB = KnowledgeBase(_REPO_ROOT / "knowledge")


def _forest_v3():
    """A hand-crafted V3 Vision JSON for a Forest-themed public park."""
    return {
        "basic_info": {"project_name": "Forest Adventure Park", "site_type": "SITE.PUBLIC_PARK"},
        "design": {
            "theme": [{"id": "NATURE.FOREST", "role": "primary", "confidence": 0.92}],
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
            "keywords": ["forest", "treehouse", "nature", "rope"],
            "vision_summary": "Forest-themed public park with a treehouse, rope nets, and a long slide.",
            "design_interpretation": "Uses a forest narrative to organise a multi-level climbing path.",
            "confidence": 0.88,
        },
    }


def test_knowledge_retriever_agent_registered():
    """The new agent must show up in the registry."""
    assert "knowledge_retriever" in AgentRegistry.names()
    print("  [ok] knowledge_retriever registered: " + str(sorted(AgentRegistry.names())))


def test_default_pipeline_includes_retriever():
    """The default pipeline must place the retriever between DecisionMaker and Strategy."""
    assert "knowledge_retriever" in DEFAULT_PIPELINE
    i_dm = DEFAULT_PIPELINE.index("decision_maker")
    i_kr = DEFAULT_PIPELINE.index("knowledge_retriever")
    i_st = DEFAULT_PIPELINE.index("strategy")
    assert i_dm < i_kr < i_st, (
        "pipeline order wrong: dm=%d kr=%d st=%d" % (i_dm, i_kr, i_st))
    print("  [ok] pipeline order: " + str(DEFAULT_PIPELINE))


def test_full_pipeline_runs_cleanly():
    """All six agents should run without error on a realistic V3 input."""
    engine = DecisionEngine(knowledge=_KB)
    ctx = engine.run(_forest_v3())
    statuses = {s.agent: s.status for s in ctx.stages}
    assert all(statuses[a] == "ok" for a in DEFAULT_PIPELINE), statuses
    print("  [ok] all stages ok: " + str(statuses))


def test_knowledge_context_populated():
    engine = DecisionEngine(knowledge=_KB)
    ctx = engine.run(_forest_v3())
    kc = ctx.knowledge_context
    assert kc is not None, "knowledge_context not populated"
    assert kc.primary_theme == "NATURE.FOREST"
    assert kc.related_themes, "no themes retrieved"
    assert kc.related_objects, "no objects retrieved"
    theme_titles = [s.title for s in kc.related_themes]
    assert any("Forest" in t for t in theme_titles), theme_titles
    obj_titles = [s.title for s in kc.related_objects]
    assert any("Treehouse" in t for t in obj_titles), obj_titles
    print("  [ok] themes=" + str(theme_titles))
    print("  [ok] objects=" + str(obj_titles))


def test_strategy_analysis_fields():
    """The Strategy Analysis output must contain all four ADR fields."""
    engine = DecisionEngine(knowledge=_KB)
    ctx = engine.run(_forest_v3())
    sa = ctx.strategy_analysis
    assert sa is not None, "strategy_analysis missing"
    assert sa.space_positioning, "space_positioning empty"
    assert sa.core_problem, "core_problem empty"
    assert sa.design_direction, "design_direction empty"
    assert sa.investment_logic, "investment_logic empty"
    assert 0.0 < sa.confidence <= 1.0, "confidence out of range"
    print("  [ok] positioning: " + sa.space_positioning[:80])


def test_explanations_are_customer_facing():
    """Each explanation should read like a senior designer talking to a client."""
    engine = DecisionEngine(knowledge=_KB)
    ctx = engine.run(_forest_v3())
    assert ctx.explanations, "no explanations"
    for exp in ctx.explanations:
        assert exp.text, "empty text for " + exp.object_id
        bad_words = ["striking", "amazing", "iconic", "world-class"]
        for w in bad_words:
            assert w.lower() not in exp.text.lower(), (
                "forbidden word " + w + " in " + exp.object_id
            )
    print("  [ok] all " + str(len(ctx.explanations)) + " explanations clean")


def test_markdown_report_has_six_sections():
    """The acceptance criteria: a Markdown report with the six named sections."""
    engine = DecisionEngine(knowledge=_KB)
    ctx = engine.run(_forest_v3())
    md = render_markdown(ctx)
    assert "## Space" in md
    assert "## Decision Maker" in md
    assert "## Retrieved Knowledge" in md
    assert "## Strategy Analysis" in md
    assert "## Strategies" in md
    assert "## Top Recommendations" in md
    assert "## Explanations" in md
    print("  [ok] markdown report contains all 6 sections")
    print("  [ok] markdown length: " + str(len(md)))


def test_report_uses_real_v2_case():
    # If a real V2 file exists, run the pipeline against it too.
    import json
    src = _REPO_ROOT / "data" / "analysis" / "cases" / "0001.json"
    if not src.exists():
        print("  [skip] " + str(src) + " not found")
        return
    v2 = json.loads(src.read_text(encoding="utf-8"))
    v3 = {
        "basic_info": {"project_name": v2.get("project_name", ""), "site_type": v2.get("site_type", "")},
        "design": {
            "theme": v2.get("theme", []) or [],
            "design_language": v2.get("design_keywords", []) or [],
            "design_highlights": [],
        },
        "target_users": {"age_group": v2.get("age_group", []) or []},
        "play_experience": {"play_behaviors": v2.get("play_behaviors", []) or []},
        "equipment": {"functional_units": v2.get("functional_units", []) or []},
        "materials": {"main_materials": v2.get("materials", []) or []},
        "color": {"colors": v2.get("colors", []) or []},
        "ai_analysis": {
            "keywords": v2.get("design_keywords", []) or [],
            "vision_summary": v2.get("vision_summary", ""),
            "design_interpretation": v2.get("design_interpretation", ""),
            "confidence": 0.5,
        },
        "metadata": v2.get("metadata", {}),
    }
    engine = DecisionEngine(knowledge=_KB)
    ctx = engine.run(v3)
    md = render_markdown(ctx)
    assert "## Retrieved Knowledge" in md
    print("  [ok] V2-adapter pipeline ran")


def main():
    print("== CaseOS Sprint 9 smoke test ==")
    tests = [
        test_knowledge_retriever_agent_registered,
        test_default_pipeline_includes_retriever,
        test_full_pipeline_runs_cleanly,
        test_knowledge_context_populated,
        test_strategy_analysis_fields,
        test_explanations_are_customer_facing,
        test_markdown_report_has_six_sections,
        test_report_uses_real_v2_case,
    ]
    for fn in tests:
        print("[run] " + fn.__name__)
        fn()
        print()
    print("== ALL TESTS PASSED ==")
    return 0


if __name__ == '__main__':
    sys.exit(main())
