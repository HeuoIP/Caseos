# CaseOS Agent Framework V1

> Sprint 7 deliverable. Architecture-first; no AI intelligence added.

## Goal

Build the first **runnable agent framework** that integrates the
existing modules (Vision Analyzer, Validator, Knowledge Library, Theme
Library, Object Library, Decision Rules) into one complete pipeline
without redesigning any of them.

## What it does

The framework takes a single Vision JSON dict as input and produces:

  1. A structured **SpaceSummary** of the physical site.
  2. An inferred **DecisionMaker** profile + ranked **Goals**.
  3. A set of **Strategies** that serve those goals (with conflict
     resolution).
  4. A ranked list of **Top Recommendations** (concrete Objects).
  5. **Explanations** in Chinese that justify each recommendation.
  6. A single **Markdown report** ready for the client.

All five stages are independent agents. The pipeline order is data, not
code: adding a Budget Agent, Fengshui Agent, Psychology Agent, Safety
Agent, or Commercial Agent requires zero changes to the engine.

## Architecture

```
backend/app/core/
    agents/
        __init__.py
        base.py              # Agent ABC + AgentRegistry
        space_agent.py       # Stage 1
        decision_maker_agent.py  # Stage 2
        strategy_agent.py    # Stage 3
        object_selector_agent.py # Stage 4
        explain_agent.py     # Stage 5
    decision/
        __init__.py
        models.py            # Dataclasses (no Pydantic dep)
        knowledge.py         # Lazy loader for Goal/Strategy/Reasoning/Object
        context.py           # DecisionContext (shared mutable state)
        pipeline.py          # DEFAULT_PIPELINE + Pipeline
        engine.py            # DecisionEngine
    recommendation/
        __init__.py
        markdown_generator.py    # Render DecisionContext -> MD
        report_generator.py     # High-level facade (engine + MD + file)
```

## Pipeline

```
Vision JSON (V3 schema)
    |
    v
[Space Agent]            reads Vision JSON -> SpaceSummary
    |
    v
[Decision Maker Agent]   infers profile + Goals from domain
    |
    v
[Strategy Agent]         picks Strategies, resolves conflicts
    |
    v
[Object Selector Agent]  ranks concrete Objects against Strategies
    |
    v
[Explain Agent]          fills Reasoning templates -> Chinese prose
    |
    v
[Markdown Generator]     renders everything into a single .md report
```

Each agent reads from and writes to a shared `DecisionContext`. The
engine never inspects agent internals -- it walks the pipeline list,
invokes `agent.run(context)`, and records timing/errors.

## Adding a new agent

Three lines of code:

```python
# 1. Create the file
# backend/app/core/agents/budget_agent.py
from app.core.agents.base import Agent, AgentRegistry

@AgentRegistry.register
class BudgetAgent(Agent):
    name = "budget"
    display_name = "Budget Agent"

    def run(self, context):
        # mutate context in place
        ...

# 2. Import it from the package __init__ (so registration runs)
# backend/app/core/agents/__init__.py
from app.core.agents.budget_agent import BudgetAgent

# 3. Insert into the pipeline
# backend/app/core/decision/pipeline.py
DEFAULT_PIPELINE = [
    "space",
    "decision_maker",
    "budget",          # <-- new
    "strategy",
    "object_selector",
    "explain",
]
```

No engine change. No other module change. The test
`test_extensibility_register_custom_agent` in
`backend/tests/test_agent_framework.py` proves this works.

## What is NOT in V1 (deferred to later sprints)

- LLM-backed reasoning inside ExplainAgent (V1 uses template-filling).
- Authentication, persistence, API surface.
- Budget / Fengshui / Psychology / Safety / Commercial agents (slots
  reserved in the pipeline).
- PDF generation (V1 outputs Markdown only).
- DAG-style pipelines (V1 is a linear list).

## Verification

Run the smoke test:

```
cd backend
python tests/test_agent_framework.py
```

Expected output includes:

```
[ok] registry has: ['decision_maker', 'explain', 'object_selector', 'space', 'strategy']
[ok] site=SITE.PUBLIC_PARK domain=PUBLIC_PARK
[ok] profile=PUBLIC_ADMIN
[ok] top=['OBJECT.INTERACTIVE_WALL', 'OBJECT.TREEHOUSE', 'OBJECT.IP_SCULPTURE']
[ok] custom agent 'ping' added and ran without engine change
== ALL TESTS PASSED ==
```

The test exercises:

  * The registry populates on import.
  * The engine runs end-to-end on a synthetic V3 Vision JSON.
  * The engine runs on a real V2 file (adapted to V3 by the test).
  * The Markdown report writes to disk.
  * A custom agent plugs in without touching the engine.

## Hand-off contract for callers

```python
from pathlib import Path
from app.core.decision import DecisionEngine, KnowledgeBase
from app.core.recommendation import ReportGenerator

kb = KnowledgeBase(Path("../knowledge"))
engine = DecisionEngine(knowledge=kb)
rg = ReportGenerator(engine)

result = rg.generate(vision_json_dict, output_path="out/report.md")
print(result.markdown)        # str
print(result.context.goals)   # list[GoalRef]
print(result.written_to)      # Path | None
```

The future FastAPI handler will be a one-liner that calls
`rg.generate(req.json(), output_path=None)`.

## Files touched

Created (no existing files were modified):

  * `backend/app/core/agents/base.py`
  * `backend/app/core/agents/space_agent.py`
  * `backend/app/core/agents/decision_maker_agent.py`
  * `backend/app/core/agents/strategy_agent.py`
  * `backend/app/core/agents/object_selector_agent.py`
  * `backend/app/core/agents/explain_agent.py`
  * `backend/app/core/agents/__init__.py`
  * `backend/app/core/decision/models.py`
  * `backend/app/core/decision/knowledge.py`
  * `backend/app/core/decision/context.py`
  * `backend/app/core/decision/pipeline.py`
  * `backend/app/core/decision/engine.py`
  * `backend/app/core/decision/__init__.py`
  * `backend/app/core/recommendation/markdown_generator.py`
  * `backend/app/core/recommendation/report_generator.py`
  * `backend/app/core/recommendation/__init__.py`
  * `backend/tests/test_agent_framework.py`

Pre-existing modules reused without modification:

  * `backend/app/services/vision/` (VisionAnalyzer)
  * `backend/app/services/validator/` (Validator)
  * `backend/prompts/`
  * `schemas/case_analysis_v3.json`
  * `knowledge/goals/`, `knowledge/strategies/`, `knowledge/reasoning/`,
    `knowledge/objects/`, `knowledge/taxonomy/`,
    `knowledge/decision_rules/`, `knowledge/expert_handbook/`.