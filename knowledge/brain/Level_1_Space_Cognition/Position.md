# Position -- Space Cognition

- **Layer:** Brain -- Level 1
- **Status:** Accepted
- **Date:** 2026-07-30
- **Companion documents:** `Role.md`, `Characteristics.md`,
  `Emotion.md`, `README.md`.

## Statement

> Space Cognition sits **upstream of every judgment** and
> **downstream of raw perception**. It is the layer that
> translates what the Vision Engine sees into a structured
> cognitive description that the Diagnosis Layer (Level 2)
> can reason about.

## Where it sits in the architecture

The Brain is layered. Level 1 is the first layer; further
levels will follow. The current known pipeline is:

```text
User input
   |
   v
Vision Engine (V3 JSON, raw perception)
   |
   v
Level 1 -- Space Cognition      <-- THIS FOLDER
   |
   v
Level 2 -- Space Diagnosis      (future, not yet built)
   |
   v
Level 3 -- Decision             (future, not yet built)
   |
   v
Level 4 -- Recommendation       (future, not yet built)
```

Within CaseOS as a whole:

```text
User / Site Photo
   |
   v
Vision Engine
   |
   v
+--------------------------+
| Brain: Level 1           |  <-- THIS FOLDER
| Space Cognition           |
+--------------------------+
   |
   v
Decision Engine (uses Space Cognition as input)
   |  (per ADR-005 and the Decision Model V1)
   v
Recommendation / Output
```

## Position characteristics

Four properties of this layer "s position:

1. **Upstream of Diagnosis.** Space Cognition is the input to
   the Diagnosis Layer (Level 2). Without perception, judgment
   is guesswork. The Diagnosis Layer cannot invent what Level 1
   has not observed.

2. **Downstream of Vision Engine.** Space Cognition receives
   what the Vision Engine has already extracted (themes,
   materials, colors, age groups, free-form description) and
   adds the **cognitive layer**: not what is in the image, but
   what it means, how it feels, what its character is.

3. **Independent of user goal.** Space Cognition describes the
   space as it is, not as the user wants it to be. A playground
   described as "compact, sunny, urban, lively" remains so
   even if the user "s stated goal is "a calm retreat". The
   mismatch between description and goal is **surfaced** by
   Diagnosis, not hidden by Cognition.

4. **Independent of recommendation.** Space Cognition must be
   reusable across multiple downstream uses. The same cognitive
   description can feed a "treehouse" recommendation, a "reading
   corner" recommendation, or a "do nothing" decision. Cognition
   serves all of them equally; it serves none of them
   preferentially.

## What Level 1 is NOT adjacent to

Level 1 is **deliberately separated** from:

- **Constitution.** The Constitution is philosophy; Level 1 is
  perception. Level 1 must obey the Constitution (per the four
  NOTs in `Role.md`) but does not redefine it.
- **Decision Principles.** The Decision Principles are how the
  engine must act; Level 1 is what the engine has observed.
  Level 1 follows the principles (P003: observe before
  recommending) but is not the principle itself.
- **Design Principles (DPs).** DPs are rules the engine must
  not skip. Level 1 follows DP-002 (space first, object second)
  by **being** the space record that comes first.
- **Expert Handbook.** The Handbook is operational depth; Level
  1 is the structured description that the Handbook "s methods
  reason from.

## Boundaries with the runtime pipeline

The runtime pipeline (ADR-005 / Decision Model V1) has a
**Space Agent** whose job is to produce the `space` sub-model
of `DecisionContext`. The Space Agent is the **runtime
implementation** of this layer "s knowledge. The two are
related but not identical:

| | Space Cognition (this folder) | Space Agent (runtime) |
| --- | --- | --- |
| **What it is** | Cognitive knowledge. | Implementation. |
| **Form** | Markdown prose. | Python code. |
| **Audience** | Future readers, future agents, future maintainers. | The engine "s pipeline. |
| **Stability** | Stable across pipeline rewrites. | Can change without invalidating this folder. |

A change to this folder does NOT require a code change. A code
change to the Space Agent does NOT require a change to this
folder, as long as the cognitive output remains equivalent.

## Cross-references

- `Role.md` -- what Level 1 does.
- `Characteristics.md` -- the eight cognitive dimensions Level 1
  produces.
- `Emotion.md` -- the emotional tag Level 1 produces.
- `knowledge/decision_model/Decision_Model_V1.md` -- the larger
  Decision Model architecture.
- `knowledge/decision_model/Context_Model.md` Section 3 -- the
  `space` sub-model is the runtime shape of Level 1 "s output.
- ADR-005 -- the Decision Intelligence pipeline that consumes
  Level 1 "s output.
- `knowledge/expert_handbook/06_Space_Psychology.md` -- the
  handbook chapter that grounds Level 1 "s vocabulary in
  psychology research.

## Maintenance

- A change to the **level order** (inserting a new layer
  between Level 1 and Level 2, or reordering) is a breaking
  architectural change and requires ADR.
- A change to the **input source** (replacing the Vision
  Engine "s V3 JSON with a different schema) requires ADR
  (V3 is the canonical schema per ADR-008).
- A change to the **output consumer** (Level 2 receiving a
  different record shape) requires ADR (the Diagnosis Layer "s
  input contract changes).
