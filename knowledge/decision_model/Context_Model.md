# Context Model

- **Layer:** Knowledge (Decision Model sub-model)
- **Companion document:** `Decision_Model_V1.md`

## 0. Purpose

This document defines the **shape of `DecisionContext`** -- the
shared, mutable state object that is passed between every agent
in the Decision Engine "s pipeline.

`DecisionContext` is the single source of truth for "what the
engine knows so far". Each agent reads the fields it needs,
mutates the fields it owns, and leaves the others alone.

## 1. Why a Context Model

Three reasons.

1. **One state, many agents.** Without a shared context object,
   each agent would maintain its own state, and the pipeline
   would spend more time passing arguments than reasoning.
2. **Reproducibility.** A recommendation is reproducible when
   the `DecisionContext` at each agent invocation is recorded.
   With one shared context, the recording is automatic.
3. **Traceable unknowns.** `unknown` is a first-class value in
   the context. Every agent can see exactly which inputs are
   missing, and the engine can refuse to run when too many are.

## 2. The Five Context Sub-models

`DecisionContext` is composed of five sub-models. Each
sub-model is owned by one or two agents and is read by several.

| Sub-model | Owner (writes) | Consumers (read) |
| --- | --- | --- |
| `space` | Space Agent | Project Fit, Strategy, Object Selector, Explain |
| `goal` | Decision Maker Agent | Project Fit, Strategy, Object Selector, Explain |
| `project_fit` | Project Fit Agent | Strategy, Explain |
| `knowledge_context` | Knowledge Retriever | Strategy, Object Selector, Explain |
| `strategies` | Strategy Agent | Object Selector, Explain |
| `recommendations` | Object Selector Agent | Explain |
| `explanation` | Explain Agent | (terminal output) |

The sub-models are filled **strictly in order**. The Space
Agent may not write `space` before the Vision Engine has
written the Vision JSON. The Strategy Agent may not write
`strategies` before all five upstream sub-models are filled
(or explicitly marked `unknown`).

## 3. The Space Sub-model

The Space sub-model records what the engine knows about the
physical site. It has five axes, each with an `observed` /
`inferred` / `unknown` provenance flag.

```text
space = {
    dimensions: { observed: bool, value: dict, notes: str },
    light_climate: { observed: bool, value: dict, notes: str },
    surroundings: { observed: bool, value: dict, notes: str },
    existing_features: { observed: bool, value: dict, notes: str },
    atmosphere: { observed: bool, value: str, notes: str },
    unknowns: [str]
}
```

- `observed`: the field was directly seen (e.g. the Vision
  Engine reported it).
- `inferred`: the field was inferred from related observations.
- `unknown`: the field was not observed and not inferred.

A field with `observed = false` is not necessarily empty; it
may be `inferred` with a confidence value, or `unknown` with a
human-readable note.

The Space Agent owns this sub-model. No other agent writes to
it. Object Selector and Strategy may read it.

## 4. The Goal Sub-model

The Goal sub-model records what the user wants. It has a
primary function, optional secondary goals, and explicit
constraints.

```text
goal = {
    primary_function: { stated: bool, value: str, source: str },
    secondary_goals: [ { value: str, source: str } ],
    constraints: [ { kind: str, value: str, source: str } ],
    unknowns: [str]
}
```

- `primary_function`: the single most important thing the
  space is for (per DP-001).
- `secondary_goals`: up to 3 additional goals.
- `constraints`: hard constraints the user has stated
  (budget band, timeline, jurisdictional limits).

The Decision Maker Agent owns this sub-model. Project Fit and
Strategy consume it.

## 5. The Project Fit Sub-model

The Project Fit sub-model records the engine "s verdict on
whether the project is worth doing and in which direction. It
has six fields (per ADR-006).

```text
project_fit = {
    strength: [str],
    risk: [str],
    capability_match: { value: str, confidence: float },
    recommended_direction: [str],
    avoid_direction: [str],
    confidence: float,
    unknowns: [str]
}
```

- `strength` and `risk` are observational lists, not opinions.
- `capability_match` judges the investor / stakeholder "s fit
  to the project.
- `recommended_direction` and `avoid_direction` are directional
  hints for the Strategy stage.
- `confidence` is the engine "s overall confidence in the
  Project Fit Report.

The Project Fit Agent owns this sub-model. Strategy and Explain
consume it.

## 6. The Knowledge Context Sub-model

The Knowledge Context sub-model records what relevant knowledge
the engine has retrieved. It has four slices (per Sprint 9
Knowledge Retriever).

```text
knowledge_context = {
    cases: [KnowledgeSnippet],
    themes: [KnowledgeSnippet],
    objects: [KnowledgeSnippet],
    rules: [KnowledgeSnippet],
    handbook: [KnowledgeSnippet]
}
```

Each `KnowledgeSnippet` has:

```text
{
    kind: str,             # case | theme | object | rule | handbook
    id: str,               # stable ID from the library
    title: str,
    excerpt: str,
    relevance_score: float,
    source_path: str
}
```

The Knowledge Retriever owns this sub-model. Strategy, Object
Selector, and Explain consume it.

## 7. The Strategies Sub-model

The Strategies sub-model records the strategies the engine has
considered. Each strategy is a candidate direction; the Object
Selector uses them as ranking axes.

```text
strategies = [
    {
        id: str,
        space_positioning: str,
        core_problem: str,
        design_direction: str,
        investment_logic: str,
        served_goals: [str],         # references to goal sub-model
        knowledge_refs: [str],      # references to knowledge_context
        status: enum,                # kept | dropped
        drop_reason: Optional[str]
    },
    ...
]
```

A strategy is `kept` if it survived the Strategy Agent "s
internal ranking, or `dropped` if it was filtered out (with a
`drop_reason` recording why).

The Strategy Agent owns this sub-model. Object Selector and
Explain consume it.

## 8. The Recommendations Sub-model

The Recommendations sub-model records the final candidate set
emitted by the Object Selector. It is a ranked list, not a
single item.

```text
recommendations = [
    {
        id: str,
        object_id: str,           # stable ID from knowledge/objects/
        title: str,
        rank: int,                # 1 = top recommendation
        match_scores: {           # the 5 dimensions from DP-003
            space: float,
            user: float,
            budget: float,
            operation: float,
            context: float
        },
        strength_alignment: float,
        tradeoffs: [str],         # FB-05 enforcement
        served_strategies: [str],
        served_goals: [str],
        confidence: float
    },
    ...
]
```

The Object Selector Agent owns this sub-model. Explain consumes
it.

## 9. The Explanation Sub-model

The Explanation sub-model records the customer-facing prose
the engine will emit. It is structured so the Markdown
generator can render it deterministically.

```text
explanation = {
    space_summary: str,
    decision_maker_summary: str,
    project_fit_summary: str,
    strategy_summary: [str],
    recommendation_summary: [str],
    per_recommendation: [
        {
            recommendation_id: str,
            prose: str,            # the customer-facing paragraph
            reasoning_chain: [str] # the decision trail
        }
    ],
    unknowns: [str]
}
```

The Explain Agent owns this sub-model. It is terminal; the
Markdown generator consumes it.

## 10. Invariants

Every sub-model carries the following invariants:

1. **No silent invention.** A value with `observed = true` or
   `stated = true` must be traceable to an input (Vision JSON,
   user-stated, retrieved knowledge, computed from inputs).
2. **`unknown` is explicit.** A field that has no value must
   carry `unknowns: [...]` with a human-readable reason.
3. **Append-only revision history.** When an agent updates a
   sub-model, the previous value is preserved in a side
   log, not overwritten. The `DecisionContext` log is the
   engine "s reproducible artifact.
4. **One writer per sub-model.** Two agents do not write to the
   same sub-model. When two agents need to add data, the
   owning agent composes the inputs.

## 11. Persistence

The `DecisionContext` is recorded as a JSON artifact at the
end of every pipeline run. The artifact is versioned with the
pipeline version that produced it. The same `DecisionContext`
fed into the same pipeline version must produce the same
recommendation (reproducibility).

## 12. Relationship to Other Sub-models

- **Project_Fit_Model.md** describes the Project Fit sub-model
  in more detail, especially the input dimensions and the
  output fields.
- **Strategy_Model.md** describes the Strategies sub-model
  in more detail, especially the strategy-candidate generation
  and ranking algorithm.

## 13. Maintenance

- A change to a sub-model "s **shape** (adding, removing, or
  renaming a field) is a breaking change and requires ADR.
- A change to a sub-model "s **invariants** requires ADR.
- A change to a sub-model "s **owner** (which agent writes to
  it) is a breaking change and requires ADR.
- Adding a new sub-model is allowed without ADR if it does not
  affect existing sub-models.

## References

- ADR-005, Section 6 (pipeline stages).
- ADR-006 (Project Fit Intelligence).
- ADR-008 (Vision Output Schema -- Canonical V3).
- `../Constitution/P002_Value_To_Decision_Maker.md` (served_goals
  contract).
- `../Constitution/P003_Understand_Before_Recommending.md` (ordering
  constraint).
