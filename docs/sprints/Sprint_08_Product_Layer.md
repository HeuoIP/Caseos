# Sprint 08 -- Product Layer

## Goal

Build the user-facing product pipeline of CaseOS. This sprint is NOT
about AI intelligence; it integrates the existing Vision Engine,
Decision Engine, and Knowledge Library into one runnable workflow
that a (future) Web UI can sit on top of.

## Existing Modules (reused as-is)

- Vision Engine: `backend/app/services/vision/`
- Decision Engine: `backend/app/core/decision/engine.py`
- Knowledge Library: `knowledge/{goals,strategies,reasoning,objects,taxonomy}/`
- Agent Framework: `backend/app/core/agents/`
- Markdown generator: `backend/app/core/recommendation/markdown_generator.py`

## New Architecture / Files

```
backend/app/core/product/
    __init__.py             public exports
    request.py              ProductRequest, ProjectType, PrimaryGoal
    response.py             ProductResponse, DecisionGoalView
    session.py              ProductSession, SessionStage, SessionStatus
    workflow.py             ProductWorkflow, WorkflowConfig
    product_flow.py         ProductFlow, ProductFlowError  (high-level facade)
```

Plus:

- `backend/tests/test_product_flow.py` -- 7 smoke tests, all green
- Small change to `backend/app/core/decision/engine.py` -- the engine
  now optionally accepts a pre-built `DecisionContext` so the product
  layer can pre-seed the user's primary goal before the agent pipeline
  runs.
- Small change to `backend/app/core/agents/decision_maker_agent.py`
  -- the agent now merges inferred goals with any pre-existing goals
  (e.g. user-supplied) instead of overwriting them.

## Product Flow (5 stages)

    1. vision         VisionAnalyzer.analyze(image_path) -> Vision JSON
    2. selections     Build DecisionContext; inject user primary_goal
    3. engine         DecisionEngine.run(vision_json, context=ctx)
    4. report         render_markdown(context) -> str
    5. images         skipped in V1 (future design-image generation)

The user-facing call surface is `ProductFlow.run(request)`. The async
surface (for the future Web UI) is `ProductFlow.run_session(session)`.

## User-facing types

### ProjectType (5)

- KINDERGARTEN       -> domain EDUCATION, profile EDUCATOR
- PUBLIC_PARK        -> domain PUBLIC_PARK, profile PUBLIC_ADMIN
- COMMERCIAL_SPACE   -> domain COMMERCIAL, profile COMMERCIAL_OPERATOR
- COMMUNITY          -> domain COMMUNITY, profile COMMUNITY_OPERATOR
- FAMILY             -> domain RESIDENTIAL, profile RESIDENTIAL_OPERATOR

### PrimaryGoal (5)

- INCREASE_VISITORS       -> BUSINESS.TRAFFIC
- IMPROVE_ENROLLMENT      -> EDU.ENROLLMENT
- IMPROVE_BRANDING        -> BUSINESS.BRAND
- BETTER_EXPERIENCE       -> CHILD.PLAY_VALUE
- SPACE_OPTIMIZATION      -> BUSINESS.REVENUE

## Acceptance Criteria

The workflow can be simulated with one image and one JSON payload,
producing a `ProductResponse` whose every required slice is populated:

- [x] Space Summary
- [x] Decision Goal
- [x] Strategy
- [x] Recommended Objects
- [x] Explanation
- [x] Markdown Report

Verified by `backend/tests/test_product_flow.py`.

## Out of Scope (deferred)

- No Web UI (deferred to Sprint 9+).
- No PDF (Markdown only in V1).
- No AI intelligence improvements.
- No image generation (stage 5 is reserved but skipped).
- No async/queueing (the flow is synchronous).

## Test Summary

```
== CaseOS Product Layer (Sprint 8) smoke test ==

[run] test_product_request_helpers
[run] test_run_returns_complete_response
[run] test_session_object_tracks_stages
[run] test_user_primary_goal_is_injected
[run] test_different_project_types_change_profile
[run] test_failure_does_not_crash_run
[run] test_describe_endpoint

== ALL TESTS PASSED ==
```

Plus regression: Sprint 7 `test_agent_framework.py` still all green
after the engine and decision_maker_agent tweaks.

## How a future Web UI calls this

```python
from app.core.product import (
    ProductFlow, ProductRequest, ProjectType, PrimaryGoal,
)

flow = ProductFlow()  # uses real Qwen vision analyzer by default
response = flow.run(ProductRequest(
    image_path="uploads/site_photo.jpg",
    project_type=ProjectType.KINDERGARTEN,
    primary_goal=PrimaryGoal.IMPROVE_ENROLLMENT,
    site_name="Maple Kindergarten",
))

return response.markdown_report
```

For test-time injection of a fake Vision analyzer:

```python
class FakeVision:
    def analyze(self, path): return {...}

flow = ProductFlow(vision_analyzer=FakeVision())
```