"""Tests for the Decision Intelligence rule engine (Sprint 19.2).

Acceptance Criteria from spec section "Testing":
    Test 1 -- empty kindergarten space: decision = experience anchor;
              boundary = no equipment stacking.
    Test 2 -- overloaded playground: diagnosis = visual disorder;
              decision = remove before adding.
    Test 3 -- budget conflict: no luxury recommendation; mentions
              constraint validation.

Implementation notes:
    - Tests construct a ProjectContext directly (bypassing the JSON
      loader) so they are independent of the file system.
    - The DecisionEngine is called directly; the pipeline context is
      not built because the rule engine signature does not depend on
      PipelineContext.
    - Each test asserts (a) the expected 7 Decision-Object fields are
      present, (b) the expected rule id / boundary / decision wording
      surfaces, and (c) the trace block carries the rule id (i.e.
      reasoning is traceable).
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from caseos.brain.runtime.context import PipelineContext, ProjectContext
from caseos.intelligence.decision.module import (
    DecisionEngine,
    DecisionModule,
)


# ------------- fixtures -------------

def _project(**overrides) -> ProjectContext:
    """Build a ProjectContext. `extras` is set on construction (frozen)."""
    base = dict(
        project_id="t",
        project_type="kindergarten_outdoor",
        site_description="",
        user_goal="",
        constraints="",
        extras={},
    )
    base.update(overrides)
    return ProjectContext(**base)


def _ctx(project: ProjectContext) -> PipelineContext:
    """A pipeline context with empty human / knowledge / trust slots."""
    return PipelineContext(project=project)


# ------------- helpers -------------

REQUIRED_FIELDS = (
    "situation",
    "observation",
    "diagnosis",
    "decision",
    "reasoning",
    "boundary",
    "applicability",
)


def _assert_seven_fields(obj: dict) -> None:
    for field_name in REQUIRED_FIELDS:
        assert field_name in obj, f"missing Decision Object field: {field_name}"
        assert isinstance(obj[field_name], str) and obj[field_name].strip(), \
            f"Decision Object field '{field_name}' is empty"


def _run_stage(project: ProjectContext) -> dict:
    DecisionModule().run(_ctx(project))
    return _ctx(project).decision_object if False else _ctx(project).__dict__["decision_object"]


def _decide(project: ProjectContext) -> dict:
    ctx = _ctx(project)
    DecisionModule().run(ctx)
    return ctx.decision_object


# ------------- Test 1 -------------

def test_rule_r1_empty_kindergarten_experience_anchor() -> None:
    """Empty kindergarten space -> experience anchor; no equipment stacking."""

    project = _project(
        site_description=(
            "empty outdoor area; some existing equipment, but the "
            "site lacks a memorable identity"
        ),
        user_goal="create a memorable experience for children",
        constraints="limited budget",
    )
    obj = _decide(project)

    _assert_seven_fields(obj)

    # Traceability: rule id must be R-01
    assert obj["_trace"]["rule_id"] == "R-01"
    assert "Rule R-01 fired" in obj["reasoning"]
    # Decision content
    assert "anchor" in obj["decision"].lower()
    # Boundary content
    assert "scattered" in obj["boundary"].lower() or \
        "equipment" in obj["boundary"].lower()
    # No equipment stacking language slipped into the decision itself
    assert "stacking" not in obj["decision"].lower()


# ------------- Test 2 -------------

def test_rule_r3_overloaded_playground_remove_before_adding() -> None:
    """Overloaded playground -> remove before adding; visual hierarchy."""

    project = _project(
        site_description=(
            "the playground is overloaded; scattered equipment "
            "everywhere and a clear lack of hierarchy"
        ),
        user_goal="improve enrolment",
        constraints="",
    )
    obj = _decide(project)

    _assert_seven_fields(obj)

    assert obj["_trace"]["rule_id"] == "R-03"
    assert "Rule R-03 fired" in obj["reasoning"]
    assert "remove before adding" in obj["decision"].lower() \
        or "remove" in obj["decision"].lower()
    assert "visual" in obj["diagnosis"].lower() or \
        "hierarchy" in obj["diagnosis"].lower()
    # Boundary should not be empty and should not contradict the decision
    assert obj["boundary"]


# ------------- Test 3 -------------

def test_rule_r2_budget_conflict_no_luxury_recommendation() -> None:
    """Budget conflict -> refuse luxury recommendation; mention validation."""

    project = _project(
        site_description="",
        user_goal=(
            "deliver a landmark high-end facility as the centre of "
            "the new development"
        ),
        constraints="limited budget",
        extras={"budget": "tight"},
    )
    obj = _decide(project)

    _assert_seven_fields(obj)

    assert obj["_trace"]["rule_id"] == "R-02"
    assert "Rule R-02 fired" in obj["reasoning"]
    # Must not silently pick the landmark option
    assert "landmark" not in obj["decision"].lower()
    # Must mention validation / strategy / constraint
    blob = (obj["decision"] + " " + obj["reasoning"] + " " + obj["boundary"]).lower()
    assert any(
        kw in blob
        for kw in ("validation", "constraint", "budget", "strategy", "validation of fit")
    ), "Decision / Reasoning / Boundary must call out the budget conflict"


# ------------- Auxiliary: rule-by-rule engine direct tests -------------

def test_engine_rule_r1_only_fires_when_both_signals() -> None:
    eng = DecisionEngine()
    p_only_lack = _project(site_description="lacks identity", user_goal="")
    out = eng.decide(p_only_lack, {}, [])
    assert out["_trace"]["rule_id"] != "R-01", \
        "R-01 must not fire on lack-of-identity alone"

    p_only_equip = _project(
        site_description="has existing equipment but is otherwise fine",
        user_goal="",
    )
    out = eng.decide(p_only_equip, {}, [])
    assert out["_trace"]["rule_id"] != "R-01", \
        "R-01 must not fire on equipment-only signal"


def test_engine_more_information_required_when_no_rule_matches() -> None:
    eng = DecisionEngine()
    p = _project(
        site_description="",
        user_goal="",
        constraints="",
    )
    out = eng.decide(p, {}, [])
    assert out["_trace"]["rule_id"] is None
    assert "more information required" in out["decision"].lower()


def test_engine_first_rule_in_order_wins_when_multiple_match() -> None:
    """If R-01 and R-03 both match, R-01 is primary (more specific)."""
    eng = DecisionEngine()
    p = _project(
        site_description=(
            "space lacks identity; existing equipment scattered; "
            "overloaded playground"
        ),
        user_goal="",
        constraints="limited budget",
    )
    out = eng.decide(p, {}, [])
    assert out["_trace"]["rule_id"] == "R-01"
    # But other rule ids are still listed in the trace:
    assert "R-03" in out["_trace"]["all_matched_rules"]