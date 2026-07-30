# Role -- Space Cognition

- **Layer:** Brain -- Level 1
- **Status:** Accepted
- **Date:** 2026-07-30
- **Companion documents:**
  - `Position.md` -- where this layer sits in the architecture.
  - `Characteristics.md` -- the eight cognitive dimensions.
  - `Emotion.md` -- the emotional character of a space.
  - `README.md` -- the index.

## Statement

> Space Cognition is the **perceptual foundation** of CaseOS.
> It captures how the system sees, hears, feels, and remembers a space
> before any judgment, diagnosis, or recommendation is made.

## What Space Cognition does

Three roles, in order:

1. **Perception.** Space Cognition receives the raw signals emitted
   by the Vision Engine (a V3 JSON describing themes, materials,
   colors, age groups, and a free-form description of the scene)
   and translates them into a **structured cognitive description**
   of the space. The translation is the cognitive layer; the V3
   JSON is the raw layer.

2. **Memory.** Space Cognition stores perceived spaces in a form
   that can be compared, retrieved, and reasoned about. Two cases
   seen six months apart must be **comparable**: same shape,
   same vocabulary, same provenance.

3. **Translation.** Space Cognition translates the user's mental
   image of a space ("a quiet garden", "a chaotic corner") into
   the structured form that downstream layers can reason about.
   The translation is loss-aware: round-trips between user language
   and cognitive vocabulary are recorded, not assumed.

## What Space Cognition is NOT

Four prohibitions, all of which are constitutional:

1. **NOT judgment.** It does not say "this space is good" or
   "this space is bad". It records the space as it is observed.
2. **NOT diagnosis.** It does not identify problems. Diagnosis is
   the next layer (Level 2).
3. **NOT recommendation.** It does not suggest objects,
   strategies, or interventions. Recommendation lives further
   downstream.
4. **NOT implementation.** It does not describe how a space was
   built or should be built. It describes how a space **is**.

The discipline of Level 1 is **capture what is, not what should
be**. A violation of this discipline at Level 1 propagates to all
downstream layers and produces recommendation prose that reads
confidently but cannot be defended.

## Why this role matters

Two reasons.

1. **Better perception = better judgment.** A Diagnosis layer
   that receives a vague cognitive description will produce vague
   diagnoses. The user will receive vague recommendations. The
   discipline of capturing the space sharply at Level 1 is the
   prerequisite for sharp judgment downstream.
2. **Reusability.** A single cognitive description of a space can
   feed many downstream uses. The same description can support a
   "treehouse" recommendation, a "reading corner" recommendation,
   a "do nothing" diagnosis, or a market research query. The
   description is independent of the use.

## Inputs and outputs

### Inputs

- The Vision Engine "s V3 JSON (per ADR-008).
- Optional user-stated context: site name, history, intended use,
  known constraints.

### Outputs

- A `SpaceCognition` record containing:
  - **Characteristics** (8 dimensions, per `Characteristics.md`).
  - **Emotion** (1-3 emotional tags, per `Emotion.md`).
  - **Provenance** for every claim: observed / inferred / unknown.
  - **Source links** back to the Vision JSON.

The `SpaceCognition` record is the input to the Diagnosis Layer
(Level 2). It is not the input to anything else.

## Cross-references

- Constitution Principle 003 -- *Understand before recommending.*
  Level 1 is the **observe** step.
- Decision Principle 002 -- *Space before Object.* Level 1 is the
  space record.
- DP-002 -- *Space First, Object Second.* Level 1 is the space
  record; DP-002 is the rule that the record must come first.
- `knowledge/decision_model/Context_Model.md` Section 3 -- the
  `space` sub-model is the **runtime shape** of what this layer
  produces.
- `knowledge/decision_model/Decision_Model_V1.md` Section 3 --
  the Space Agent in the pipeline is the **runtime implementation**
  of this layer.
- `knowledge/expert_handbook/06_Space_Psychology.md` -- how
  people perceive spaces (this layer "s academic cousin).

## Maintenance

- A change to the **inputs** (a new field in V3 JSON) requires
  ADR (V3 is the canonical schema).
- A change to the **outputs** (a new characteristic, a new
  emotion tag) requires ADR (the Diagnosis Layer "s input
  contract changes).
- A change to the **provenance flags** (adding `inferred_high`
  between `inferred` and `unknown`) requires ADR.
- A change to the **prohibitions** (lifting any of the four
  NOTs above) is a Constitution amendment and requires ADR.
