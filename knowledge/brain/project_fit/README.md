# Project Fit

- **Module:** Project Fit
- **Layer:** Brain
- **Pipeline Position:** 2 (after Client Understanding, before Space Cognition)
- **Status:** Accepted
- **Date:** 2026-07-30
- **Companion ADR:** ADR-006 (Project Fit Intelligence Architecture).

## Purpose

Evaluate whether project goals match reality. A project with
ambitious goals and limited resources is not a good project;
a project with modest goals and abundant resources may be a
great one. Project Fit surfaces the match (or the mismatch)
before any design work begins.

Project Fit is the **first judgment** in the Brain. It runs
**after** the Constitution (philosophy) and **after** Client
Understanding (client profile), and **before** any space-
specific reasoning.

## Core Principles

> **A successful project is not the best condition, but the
> best match.**

Other principles:

1. **Judgment before taste.** Project Fit assesses whether the
   project should be done, not whether the project is
   attractive.
2. **Project feasibility precedes design ambition.** A design
   that exceeds the project "s resource envelope is not a
   good design; it is an unbuildable design.
3. **Recommend against when warranted.** A negative Project Fit
   verdict is a valid outcome and is propagated to downstream
   modules.
4. **Observation, not opinion.** Every Project Fit field is
   traceable to an input fact, not to a guess.
5. **Confidence is explicit.** A Project Fit verdict with low
   confidence is partial; the Brain asks the user for missing
   inputs before proceeding.

## Decision Rules

Project Fit reads **four** input dimensions (per the ADR-009
spec, with a refinement from ADR-006 "s five dimensions -- the
Space dimension is moved to `space_cognition/` for separation
of concerns):

1. **Client capability.** Experience + budget + operational
   capacity. Read from the `ClientProfile`.
2. **Space condition.** Read from `space_cognition/` "s output
   (downstream of this module; Project Fit runs a **partial**
   assessment using only the photo and any user-stated site
   facts at this stage, then re-evaluates after Space
   Cognition).
3. **Budget / resource.** The user "s stated budget band and
   the realistic cost band for the project "s category.
4. **Market / environment.** The surrounding market "s support
   for the project "s ambition.

Project Fit produces **six** output fields (per ADR-006):

1. **Strength** -- at least 3 observable strengths (per P004).
2. **Risk** -- at least 3 observable risks.
3. **Capability Match** -- the client "s fit to the project.
4. **Recommended Direction** -- the direction that amplifies
   strength.
5. **Avoid Direction** -- the direction that hides risk.
6. **Confidence** -- the engine "s overall confidence in the
   Project Fit Report.

A Project Fit Report with `confidence < 0.4` triggers the
**recommend-against mode**: the pipeline terminates at
Project Fit, and the Brain "s output is a single sentence
plus the Project Fit Report "s Strength / Risk rationale.

## Inputs

- The Vision Engine "s V3 JSON.
- The `ClientProfile` from `client_understanding/`.
- Optional user-stated site facts (budget, timeline, market).
- Optional retrieved market cases (via the Knowledge
  Retriever).

## Outputs

A `ProjectFitReport`:

```text
ProjectFitReport = {
    strength: [str],            // at least 3 observational items
    risk: [str],                // at least 3 observational items
    capability_match: { value: str, confidence: float },
    recommended_direction: [str],
    avoid_direction: [str],
    confidence: float,          // overall
    unknowns: [str]
}
```

Downstream consumers: `diagnosis/`, `strategy/`.

## Examples

### Example 1: Strong fit

**Input:** Experienced client, generous budget, strong site
with mature trees, well-defined market.

**Output:**
- strength = [existing trees, experienced client, stable market]
- risk = [minor: maintenance access, no major risk]
- capability_match = { value: "strong", confidence: 0.9 }
- recommended_direction = [amplify existing tree cover,
  create a forest-themed play journey]
- avoid_direction = [remove trees, generic catalogue play set]
- confidence = 0.85

### Example 2: Weak fit (recommend-against candidate)

**Input:** Novice client, tight budget, exposed rooftop,
ambitious scope ("build a flagship playground on a 50 m2
rooftop").

**Output:**
- strength = [good view]
- risk = [tight budget, novice client, exposed site,
  scope exceeds envelope]
- capability_match = { value: "weak", confidence: 0.8 }
- recommended_direction = [reduce scope; choose a small
  signature element, not a full playground]
- avoid_direction = [proceed with original scope; install
  large equipment]
- confidence = 0.6

If the user insists on the original scope, the next Project
Fit re-evaluation may drop confidence below 0.4 and trigger
recommend-against.

### Example 3: Recommend-against

**Input:** Project "s stated goal is internally contradictory
("a quiet celebration space") and the user refuses to
resolve the contradiction.

**Output:**
- strength = [user has budget]
- risk = [contradictory goal, unresolved, blocks all directions]
- capability_match = { value: "blocked", confidence: 0.3 }
- recommended_direction = [resolve the contradiction first]
- avoid_direction = [proceed without resolution]
- confidence = 0.3 -- **below 0.4 threshold**

The pipeline terminates. The Brain "s output is a single
sentence: "This project is not recommended." plus the
Strength / Risk rationale.

## Cross-references

- `constitution/` -- Principle 004 (Amplify Strengths) and
  Forbidden Behavior 01 (no padding a weak site).
- `client_understanding/` -- the upstream source of the
  ClientProfile.
- `space_cognition/` -- the downstream source of the Space
  description.
- `knowledge/decision_model/Project_Fit_Model.md` -- the
  runtime reasoning model for this module.
- ADR-006 -- the original Project Fit ADR (this Brain module
  is a refinement of ADR-006 with the Space dimension moved
  to `space_cognition/`).

## Maintenance

- A change to the four input dimensions is a breaking change
  and requires ADR.
- A change to the six output fields is a breaking change and
  requires ADR.
- A change to the `confidence` threshold (currently 0.4 for
  recommend-against) is a breaking change and requires ADR.
- A change to the Strength / Risk minimum count (currently
  at least 3 each) is a non-breaking change if the minimum
  is increased, breaking if decreased.
