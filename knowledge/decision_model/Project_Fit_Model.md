# Project Fit Model

- **Layer:** Knowledge (Decision Model sub-model)
- **Companion document:** `Decision_Model_V1.md`
- **Companion ADR:** ADR-006 (Project Fit Intelligence Architecture).

## 0. Purpose

Project Fit is the **first reasoning stage after the Vision
Engine**. It answers the question: **is this project worth
doing, and in which direction?**

Project Fit runs **before** Strategy. Its job is to filter out
projects that look attractive but are not feasible, and to
surface projects that look unremarkable but are feasible. The
Strategy stage then builds on Project Fit "s verdict.

Project Fit is **judgment before taste**. It exists so that
the Strategy stage does not have to second-guess feasibility
on every cycle.

## 1. Why Project Fit exists

Many real-world projects fail not because of bad design but
because of bad **project** decisions:

- Investment capability does not match project ambition.
- The market does not support the project "s positioning.
- The site "s conditions do not support the project "s goals.
- The stakeholder "s decision style does not fit the project "s
  timeline.

Project Fit surfaces these mismatches early, before the
Strategy stage has committed to a direction.

## 2. The Five Input Dimensions

Project Fit reads five dimensions (per ADR-006, generalised
from the original investor-centric framing):

| Dimension | Reads from | What it asks |
| --- | --- | --- |
| **Space** | Vision JSON + user-stated site facts | Does the site support the project "s ambition? |
| **Stakeholder** | user-stated profile + inferred profile | Does the decision maker fit the project "s demands? |
| **Goal** | Decision Maker Agent (Goal sub-model) | Is the goal clear, achievable, and aligned with the space? |
| **Market** | user-stated market context + retrieved market cases | Does the surrounding market support the project? |
| **Resource** | user-stated budget + timeline + operational capability | Are the resources sufficient for the project "s ambition? |

Each dimension produces **observational facts**, not opinions.
A fact with low confidence is recorded as `unknown`, not as a
guess.

## 3. The Five Output Dimensions

Project Fit writes six fields to `DecisionContext.project_fit`
(see Context_Model.md Section 5). The **six** outputs are
grouped into the five input dimensions as follows:

| Output | Source dimension | What it means |
| --- | --- | --- |
| `strength` | Space + Goal + Market | At least 3 observable strengths. |
| `risk` | Space + Stakeholder + Resource | At least 3 observable risks. |
| `capability_match` | Stakeholder + Resource | Does the decision maker fit the project? |
| `recommended_direction` | Space + Goal + Market | The direction that amplifies strength. |
| `avoid_direction` | Risk + Capability Match | The direction that hides risk. |
| `confidence` | (overall) | The engine "s confidence in the Report. |

Each output is recorded with provenance: where the
observation came from, and what confidence the engine has in
it.

## 4. Reasoning Process

The Project Fit Agent runs a 4-step process.

### Step 1 -- Collect facts.

Read each of the five input dimensions and collect the
observable facts. Facts with `confidence < 0.5` are recorded
as `unknown`, not as data points.

### Step 2 -- Pair facts.

For each pair of dimensions, identify alignments and
mismatches. Example: a stakeholder "s stated budget aligns
with the space "s scale (alignment), but the goal "s ambition
exceeds the resource "s timeline (mismatch).

### Step 3 -- Surface Strength and Risk.

`strength` is the union of aligned pairs. `risk` is the union
of mismatched pairs. Both are observation lists, not
opinions; each item must be traceable to an input fact.

### Step 4 -- Synthesise Direction.

`recommended_direction` is the direction that, if pursued,
would amplify the most aligned pair. `avoid_direction` is the
direction that would hide the most mismatched pair. Both are
1-3 short phrases, not paragraphs.

If the engine cannot identify a recommended_direction (no
aligned pair survives), the Project Fit Report is **negative**:
the recommendation is to **recommend against** the project.

## 5. Edge cases

### 5.1 Missing data

When one or more input dimensions have all-`unknown` data,
the Project Fit Report is **partial**. A partial report
includes whatever Strength and Risk can be observed, marks
the unobserved dimensions as `unknown`, and the engine must
ask the user for the missing inputs before issuing a
recommendation.

### 5.2 Conflicting signals

When two input dimensions conflict (e.g. Space says the site
supports an intimate scale, Goal says the user wants a
flagship landmark), the Project Fit Agent surfaces the
conflict as a `risk` item and asks the user to resolve it.
The agent does NOT pick a side.

### 5.3 Insufficient confidence

When `confidence < 0.4`, the Project Fit Agent returns an
empty Report (no Recommendation is issued downstream). The
agent asks the user for the missing inputs.

### 5.4 Recommend-against

When the engine concludes that the project should not be
done, the Project Fit Report "s `recommended_direction` is
the single phrase "**recommend against**". The Strategy
stage treats this as a hard pipeline abort.

## 6. Output contract

The Project Fit Report is part of `DecisionContext.project_fit`.
See `Context_Model.md` Section 5 for the exact JSON shape.

In prose, the Project Fit Report renders as:

```text
## Project Fit

### Strength
- [strength 1]
- [strength 2]
- [strength 3]

### Risk
- [risk 1]
- [risk 2]
- [risk 3]

### Capability Match
[capability_match.value] (confidence: [capability_match.confidence])

### Recommended Direction
- [direction 1]
- [direction 2]

### Avoid Direction
- [direction 1]
- [direction 2]

### Confidence
[confidence]
```

## 7. Relationship to Strategy

Project Fit is **upstream** of Strategy. The Strategy Agent
reads `DecisionContext.project_fit` and uses:

- `strength` and `recommended_direction` as positive inputs
  to the Strategy "s design_direction.
- `risk` and `avoid_direction` as negative inputs (what
  Strategy must not propose).
- `confidence` as a prior on Strategy "s own confidence
  estimate.

When Project Fit returns `recommend against`, Strategy is
skipped. The pipeline terminates at Project Fit.

## 8. Cross-references

- ADR-006 (Project Fit Intelligence Architecture).
- `Context_Model.md` Section 5 (project_fit sub-model shape).
- `Constitution/P004_Amplify_Strengths.md` (binding that
  requires Strength and Risk to be observational, not
  opinionated).
- `Constitution/Forbidden_Behaviors.md`, FB-01 (no padding a
  weak site), FB-03 (no fabricated confidence).
- `Constitution/Forbidden_Behaviors.md`, FB-04 (hard
  constraints: jurisdiction, climate, footprint are not
  negotiable).

## 9. Maintenance

- A change to the five input dimensions is a breaking change
  and requires ADR.
- A change to the six output fields is a breaking change and
  requires ADR.
- A change to the `confidence` threshold (currently 0.4 for
  abort) is a breaking change and requires ADR.
- Adding a new reasoning step (Step 5, Step 6, ...) is
  allowed without ADR as long as the inputs and outputs are
  unchanged.
