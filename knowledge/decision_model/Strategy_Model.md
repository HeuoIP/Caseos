# Strategy Model

- **Layer:** Knowledge (Decision Model sub-model)
- **Companion document:** `Decision_Model_V1.md`

## 0. Purpose

Strategy is the reasoning stage that converts **Space + Goal +
Project Fit + Retrieved Knowledge** into a positioning and a
direction. It answers the question: **given that the project is
worth doing, what is the right way to approach it?**

Strategy is **direction before objects**. It exists so that
objects are chosen to serve a strategy, not to fill a
catalogue.

Strategy is **mandatory**. No Object Selector run may precede
a successful Strategy run. This is the binding manifestation of
Constitution P003 (understand before recommending) and DP-001
(primary function first).

## 1. Inputs

The Strategy Agent reads four sub-models from `DecisionContext`:

| Sub-model | What Strategy reads from it |
| --- | --- |
| `space` | The five space axes (per DP-002). |
| `goal` | Primary function + secondary goals + constraints. |
| `project_fit` | Strength, Risk, Recommended Direction, Avoid Direction, confidence. |
| `knowledge_context` | Themes, Objects, Rules, Handbook snippets. |

If any of these sub-models is `unknown` or missing, the
Strategy Agent refuses to run and asks the user for the
missing inputs. Strategy does NOT invent inputs.

## 2. Outputs

The Strategy Agent writes the `strategies` sub-model (see
`Context_Model.md` Section 7). Each strategy is a candidate
direction; the Object Selector ranks objects against the
strategies.

A strategy has seven fields:

```text
{
    id: str,
    space_positioning: str,
    core_problem: str,
    design_direction: str,
    investment_logic: str,
    served_goals: [str],
    knowledge_refs: [str],
    status: enum,
    drop_reason: Optional[str]
}
```

- `space_positioning` -- where the space sits in the user "s
  mental map. One sentence.
- `core_problem` -- the single most important problem to
  solve. One sentence.
- `design_direction` -- the design move that addresses the
  core problem. 1-3 sentences.
- `investment_logic` -- why this is the right place to spend
  money. 1-3 sentences.
- `served_goals` -- references to goals in `DecisionContext.goal`.
  Required, non-empty.
- `knowledge_refs` -- references to snippets in
  `knowledge_context`. Required, non-empty.
- `status` -- `kept` or `dropped`.
- `drop_reason` -- non-null only if `status = dropped`.

## 3. Reasoning Process

The Strategy Agent runs a 4-step process.

### Step 1 -- Generate strategy candidates.

From `project_fit.recommended_direction` and the retrieved
`knowledge_context`, generate 5-10 candidate strategies. Each
candidate is a plausible direction that:

- Serves at least one goal in `goal.primary_function` or
  `goal.secondary_goals`.
- Amplifies at least one item in `project_fit.strength`.
- Avoids every item in `project_fit.avoid_direction`.
- Cites at least one knowledge snippet.

If the agent cannot generate at least 3 candidates, the
strategy stage is too constrained; the agent surfaces the
constraint to the user.

### Step 2 -- Score candidates.

Each candidate is scored along four axes:

- **Goal match** -- does it serve at least one goal?
- **Space match** -- does it fit the five space axes?
- **Strength amplification** -- does it amplify a known strength?
- **Risk avoidance** -- does it avoid every Avoid Direction?

The score is a 4-tuple, not a single number. The agent does
NOT compute a weighted sum at this stage; weighting happens
later.

A candidate with `goal match = 0` is dropped (cannot serve any
goal = cannot be a strategy).

A candidate with `risk avoidance = 0` (it ignores an Avoid
Direction) is dropped.

### Step 3 -- Resolve conflicts and synergies.

When two surviving candidates conflict (compete for the same
budget or space), the agent picks the higher-scoring one and
records a `drop_reason` for the loser.

When two surviving candidates are synergistic (one amplifies
the other), the agent keeps both and notes the synergy.

### Step 4 -- Emit kept strategies.

The agent emits the kept strategies, ordered by their
4-tuple score (lexicographic). The Object Selector then ranks
objects against this ordered list.

## 4. The Five Strategy Categories

Strategies fall into five broad categories. The agent labels
each kept strategy with one of these, both for human reading
and for the Object Selector "s candidate retrieval:

| Category | One-line description |
| --- | --- |
| **Landmark** | One signature element that organises the space. |
| **Journey** | A sequenced path of elements that the user moves through. |
| **Field** | A single, homogeneous environment (e.g. a forest floor, a sand pit). |
| **Layered** | A vertical or zoned structure (e.g. rooftop levels, age bands). |
| **Anchor** | A small, distributed set of elements that serve the space "s rhythm. |

A strategy may belong to more than one category (e.g. a
"Journey through a Forest Field"). The agent records all that
apply.

## 5. Why strategy comes before objects

Three reasons.

1. **Catalogue neutrality.** The Object Selector ranks objects
   by match against strategies. Without strategies, the Object
   Selector ranks by catalogue fit, which is a catalogue
   default (Forbidden Behavior FB-07).
2. **Trade-off transparency.** A strategy has explicit
   `served_goals` and `knowledge_refs`. An object without a
   strategy has neither. Trade-offs are visible only when
   strategies are explicit.
3. **Reproducibility.** Two Object Selector runs with the same
   `strategies` produce the same ranking. Without strategies,
   two runs may produce different rankings depending on the
   retrieval algorithm.

## 6. Edge cases

### 6.1 Empty `project_fit`

If `project_fit.confidence < 0.4`, the Strategy Agent refuses
to run and surfaces the upstream issue to the user.

### 6.2 Conflicting primary functions

If the user "s stated `primary_function` is internally
contradictory ("a quiet celebration space"), the agent surfaces
the conflict as a `risk` and asks the user to resolve it.

### 6.3 No viable strategy

If every candidate is dropped, the agent emits a single
strategy with `design_direction = "no viable strategy"` and
`status = dropped`. The Object Selector is then skipped.

## 7. Output contract

The Strategies sub-model is part of `DecisionContext.strategies`.
See `Context_Model.md` Section 7 for the exact JSON shape.

In prose, the Strategies render as:

```text
## Strategy

### [Strategy 1 title]
- **Positioning:** [space_positioning]
- **Core Problem:** [core_problem]
- **Direction:** [design_direction]
- **Investment Logic:** [investment_logic]
- **Served Goals:** [goal 1], [goal 2]
- **Knowledge:** [ref 1], [ref 2]

### [Strategy 2 title]
...
```

## 8. Cross-references

- `Context_Model.md` Section 7 (strategies sub-model shape).
- `Project_Fit_Model.md` (upstream input).
- `Constitution/P001_Suitability.md` (binding: strategies must
  prefer suitability, not beauty).
- `Constitution/P002_Value_To_Decision_Maker.md` (binding:
  every strategy must declare `served_goals`).
- `Constitution/P004_Amplify_Strengths.md` (binding:
  design_direction must amplify a Strength, not hide a Risk).
- DP-001 (Primary Function First), DP-002 (Space First), DP-003
  (Match Before Beauty).
- `knowledge/strategies/` -- the Strategy Library that the
  Knowledge Retriever consults.

## 9. Maintenance

- A change to the four scoring axes (goal, space, strength,
  risk) is a breaking change and requires ADR.
- A change to the five strategy categories is a non-breaking
  change (additions allowed; renames require ADR).
- A change to the output shape (adding or removing a field)
  is a breaking change and requires ADR.
