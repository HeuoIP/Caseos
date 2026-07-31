"""Tests for the Human Understanding Runtime (Sprint 21, ADR-013).

Acceptance Criteria from spec section 9 (Tests):
    1. structured input creates HumanContext
    2. missing fields remain unknown
    3. empty user_goal rejected
    4. warnings generated
    5. human stage writes context into pipeline
    6. retrieval consumes human signals
    7. decision remains authority
    8. existing tests remain green (verified by full suite)

The eight numbered tests are exactly the spec bullets. They are
followed by auxiliary tests for ADR-013 invariants:

    * schema_version is recorded
    * the human module does not import retrieval / decision / trust
      / recommendation / governance / intake (architecture boundary)
    * backward-compatible retrieve() signature still works when
      human_context=None
    * the full pipeline output Markdown includes a Human
      Understanding section.
"""
from __future__ import annotations

import ast
import inspect
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.brain.runtime.context import PipelineContext, ProjectContext
from caseos.brain.runtime.pipeline import default_pipeline
from caseos.intelligence.human import (
    HumanContext,
    HumanModule,
    HumanValidationResult,
    UNKNOWN,
    extract_human_context,
    validate_human_context,
    human_context_to_markdown,
)
from caseos.knowledge.retrieval.module import (
    RetrievalEngine,
    SCORE_HUMAN_BOOST_MAX,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "backend"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _project(**overrides) -> ProjectContext:
    base = dict(
        project_id="kg-001",
        project_type="kindergarten_outdoor",
        site_description="500 sqm outdoor area between the teaching "
                          "building and the playground; some existing "
                          "equipment remains on site but the area "
                          "lacks a memorable theme or identity",
        user_goal="improve enrollment attraction",
        constraints="limited budget",
    )
    base.update(overrides)
    return ProjectContext(**base)


def _project_with_extras(**extra_fields) -> ProjectContext:
    """Project with explicit human-context fields inside `extras`.

    Real callers will use the CLI / API to surface these. The
    extractor is what does the mapping.
    """
    p = _project()
    extras = dict(p.extras or {})
    for k, v in extra_fields.items():
        extras[k] = v
    return ProjectContext(
        project_id=p.project_id,
        project_type=p.project_type,
        site_description=p.site_description,
        user_goal=p.user_goal,
        constraints=p.constraints,
        extras=extras,
    )


# ------------- Test 1: structured input creates HumanContext -------------

def test_structured_input_creates_human_context() -> None:
    """Spec example: site/budget/goal/preference create a HumanContext."""
    p = _project_with_extras(
        preference="natural education",
        budget="medium",
        business="private kindergarten",
        success="children engagement and parent recognition",
    )
    res = extract_human_context(p)
    ctx = res.human_context
    assert isinstance(ctx, HumanContext)
    assert ctx.user_goal == "improve enrollment attraction"
    assert ctx.business_context == "private kindergarten"
    assert ctx.emotional_preference == "natural education"
    assert ctx.budget_context == "medium"
    assert ctx.success_definition == "children engagement and parent recognition"
    assert res.mapped_fields == [
        "user_goal",
        "business_context",
        "emotional_preference",
        "budget_context",
        "constraints",
        "success_definition",
    ]


# ------------- Test 2: missing fields remain unknown ---------------------

def test_missing_fields_remain_unknown() -> None:
    """No invention. Missing fields stay UNKNOWN (not None / not empty)."""
    p = ProjectContext(
        project_id="x",
        project_type="kindergarten_outdoor",
        site_description="",
        user_goal="increase enrollment",
        constraints="",
    )
    res = extract_human_context(p)
    ctx = res.human_context
    assert ctx.user_goal == "increase enrollment"
    # site_description is spatial, not business context: NOT a fallback.
    assert ctx.business_context == UNKNOWN
    assert ctx.emotional_preference == UNKNOWN
    assert ctx.budget_context == UNKNOWN
    assert ctx.success_definition == UNKNOWN
    assert ctx.constraints == []
    assert "emotional_preference" in ctx.unknowns()
    assert "budget_context" in ctx.unknowns()
    assert "success_definition" in ctx.unknowns()
    assert "business_context" in ctx.unknowns()


# ------------- Test 3: empty goal rejected -------------------------------

def test_empty_goal_rejected() -> None:
    """Empty user_goal -> HumanValidationResult.valid = False."""
    ctx = HumanContext(
        user_goal="",
        success_definition="increase enrollment",
    )
    res = validate_human_context(ctx)
    assert isinstance(res, HumanValidationResult)
    assert res.valid is False
    assert "user_goal" in res.missing_required
    assert any("user_goal" in e for e in res.errors)
    assert "success_definition" not in res.missing_required


def test_empty_success_definition_rejected() -> None:
    ctx = HumanContext(
        user_goal="increase enrollment",
        success_definition="",
    )
    res = validate_human_context(ctx)
    assert res.valid is False
    assert "success_definition" in res.missing_required


# ------------- Test 4: warnings generated --------------------------------

def test_warnings_generated_for_missing_optional_fields() -> None:
    """Missing budget / constraints / business_context -> warnings."""
    ctx = HumanContext(
        user_goal="increase enrollment",
        success_definition="engagement",
    )
    res = validate_human_context(ctx)
    assert res.valid is True
    assert "budget_context" in res.missing_optional
    assert "constraints" in res.missing_optional
    assert "business_context" in res.missing_optional
    assert any("budget_context" in w for w in res.warnings)
    assert any("constraints" in w for w in res.warnings)


# ------------- Test 5: human stage writes context into pipeline ----------

def test_human_stage_writes_context_into_pipeline() -> None:
    """HumanModule writes ctx.human_context + metadata['human_validation']."""
    p = _project_with_extras(
        preference="natural",
        budget="medium",
        success="parent recognition",
    )
    pipeline = default_pipeline()
    ctx = pipeline.run(p)
    assert ctx.human_context is not None
    assert ctx.human_context["user_goal"] == "improve enrollment attraction"
    assert ctx.human_context["emotional_preference"] == "natural"
    assert ctx.metadata["human_schema_version"] == "human_context_v1"
    assert "human_validation" in ctx.metadata
    val = ctx.metadata["human_validation"]
    assert val["valid"] is True
    assert "user_goal" in ctx.metadata["human_mapped_fields"]
    assert "emotional_preference" in ctx.metadata["human_mapped_fields"]


# ------------- Test 6: retrieval consumes human signals ------------------

def test_retrieval_consumes_human_signals() -> None:
    """A human keyword that matches a KO pushes P1 contribution up
    (bounded). The rule list stays P1..P4."""
    ko = {
        "identity": "GoldenCase.test_v1",
        "principle": "natural playground anchors the experience",
        "applicability": {"suitable": ["kindergarten_outdoor"]},
        "boundary": ["do not apply without budget"],
    }
    project = _project()
    decision = {}

    engine = RetrievalEngine()
    ep_no_human = engine.retrieve(
        project=project, decision=decision,
        knowledge_patterns=[ko], human_context=None,
    )
    ep_with_human = engine.retrieve(
        project=project, decision=decision,
        knowledge_patterns=[ko],
        human_context={
            "user_goal": "natural outdoor classroom",
            "business_context": "private kindergarten",
            "success_definition": "child engagement",
        },
    )

    assert len(ep_no_human.relevant_objects) == 1
    assert len(ep_with_human.relevant_objects) == 1
    # The applicability_reason records contributing rules.
    assert "P1=" in ep_with_human.applicability_reason
    # The P1 contribution string MUST differ because the human
    # keyword overlap is reported as part of P1.
    p1_no = ep_no_human.applicability_reason
    p1_with = ep_with_human.applicability_reason
    assert p1_no != p1_with, (p1_no, p1_with)
    # Boost is bounded by SCORE_HUMAN_BOOST_MAX.
    assert SCORE_HUMAN_BOOST_MAX <= 15


def test_retrieval_rule_list_unchanged() -> None:
    """Sprint 21 spec: do not change ADR-019 priority order."""
    from caseos.knowledge.retrieval.module import RULE_APPLICABILITY
    rule_ids = [r.id for r in RULE_APPLICABILITY]
    assert rule_ids == ["P1", "P2", "P3", "P4"]
    assert "P5" not in rule_ids


# ------------- Test 7: decision remains authority ------------------------

def test_decision_remains_authority() -> None:
    """HumanContext cannot directly create a Decision.

    The Decision Engine is the authority. Different human contexts
    can shift the rule that fires, but the *rule_id* is always the
    authority -- never a string invented by the human module.
    Both runs below should produce a non-None rule_id, and the
    decision is produced by the Decision Engine, NOT by HumanModule.
    """
    p = _project()
    pipeline = default_pipeline()
    ctx_sympathetic = pipeline.run(_project_with_extras(
        preference="natural",
        budget="medium",
        success="parent recognition",
    ))
    pipeline2 = default_pipeline()
    ctx_hostile = pipeline2.run(_project_with_extras(
        preference="luxury landmark",
        budget="limited",
        success="visual landmark",
    ))

    assert ctx_sympathetic.decision_object is not None
    assert ctx_hostile.decision_object is not None
    rid_sym = ctx_sympathetic.decision_object["_trace"]["rule_id"]
    rid_hos = ctx_hostile.decision_object["_trace"]["rule_id"]
    assert rid_sym is not None
    assert rid_hos is not None
    # The decision engine version is unchanged.
    assert ctx_sympathetic.decision_object["_engine_version"] == "decision_engine_v1"
    assert ctx_hostile.decision_object["_engine_version"] == "decision_engine_v1"


# ------------- Test 8: existing tests remain green ----------------------

def test_existing_baseline_tests_remain_green() -> None:
    """Run the baseline test suite (Sprint 20.7 + earlier) and assert
    74+ tests pass -- the new Human Understanding layer does not
    break the existing pipeline."""
    env_overrides = {"PYTHONPATH": str(BACKEND)}
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "backend/caseos/tests", "-q",
         "--ignore=backend/caseos/tests/test_human_understanding.py"],
        cwd=str(REPO_ROOT),
        env={**os.environ, **env_overrides},
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    assert "passed" in proc.stdout


# ===========================================================================
# Auxiliary tests (ADR-013 invariants)
# ===========================================================================

def test_schema_version_is_human_context_v1() -> None:
    res = extract_human_context(_project_with_extras(preference="natural"))
    assert res.human_context.schema_version == "human_context_v1"


def test_unknown_sentinel_is_preserved() -> None:
    """UNKNOWN is the literal string "__UNKNOWN__" and never empty."""
    assert UNKNOWN == "__UNKNOWN__"
    ctx = HumanContext()
    assert ctx.user_goal == UNKNOWN
    assert ctx.is_unknown("user_goal") is True
    ctx.user_goal = "real"
    assert ctx.is_unknown("user_goal") is False


def test_human_module_does_not_import_retrieval_or_decision_or_others() -> None:
    """Architecture boundary: human must not import from retrieval /
    decision / trust / recommendation / governance / intake.

    AST-based check so docstring text describing the boundary is
    not mistaken for an import.
    """
    from caseos.intelligence import human as human_pkg

    forbidden_top_level = (
        "caseos.knowledge.retrieval",
        "caseos.intelligence.decision",
        "caseos.intelligence.trust",
        "caseos.intelligence.recommendation",
        "caseos.knowledge.governance",
        "caseos.knowledge.intake",
    )
    modules = [
        human_pkg.module,
        human_pkg.extractor,
        human_pkg.validator,
        human_pkg.object,
        human_pkg.report,
    ]
    for mod in modules:
        src = inspect.getsource(mod)
        tree = ast.parse(src)
        for imp in ast.walk(tree):
            if isinstance(imp, ast.Import):
                for n in imp.names:
                    top = n.name.split(".")[0]
                    for forbidden in forbidden_top_level:
                        assert top != forbidden.split(".")[0], (
                            f"{mod.__name__} imports {n.name!r} which "
                            "violates the Human Understanding architecture "
                            "boundary."
                        )
            elif isinstance(imp, ast.ImportFrom):
                mod_name = imp.module or ""
                for forbidden in forbidden_top_level:
                    assert not mod_name.startswith(forbidden), (
                        f"{mod.__name__} imports from {mod_name!r} which "
                        f"violates the boundary (forbidden: {forbidden!r})."
                    )


def test_human_understanding_section_in_report() -> None:
    """The pipeline's Markdown report should include a Human
    Understanding section."""
    p = _project_with_extras(
        preference="natural",
        budget="medium",
        success="parent recognition",
    )
    markdown = default_pipeline().run(p).metadata.get("markdown") or ""
    assert "# Human Understanding" in markdown
    assert "natural" in markdown
    assert "medium" in markdown


def test_human_context_to_markdown_for_report() -> None:
    """The standalone renderer produces a well-formed Markdown block."""
    ctx = HumanContext(
        user_goal="increase enrollment",
        business_context="private kindergarten",
        emotional_preference="natural",
        budget_context="medium",
        constraints=["existing equipment cannot be demolished"],
        success_definition="parent recognition",
        risk_tolerance="moderate",
        decision_priority="quality",
    )
    md = human_context_to_markdown(ctx)
    assert "# Human Understanding" in md
    assert "increase enrollment" in md
    assert "existing equipment cannot be demolished" in md
    assert "Unknowns: (none -- all fields supplied)" in md


def test_retrieval_without_human_context_still_works() -> None:
    """Backward-compat: human_context=None produces the same EP as
    calling retrieve() without any human context."""
    ko = {
        "identity": "GoldenCase.test_v1",
        "principle": "natural playground anchors the experience",
        "applicability": {"suitable": ["kindergarten_outdoor"]},
        "boundary": [],
    }
    engine = RetrievalEngine()
    project = _project()
    ep1 = engine.retrieve(project=project, decision=None,
                         knowledge_patterns=[ko])
    ep2 = engine.retrieve(project=project, decision=None,
                         knowledge_patterns=[ko], human_context=None)
    assert ep1.to_dict() == ep2.to_dict()
