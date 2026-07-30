
> **DEPRECATED 2026-07-30 (Sprint 17 / ADR-009).** This folder is the
> experimental Sprint 16 structure. The canonical Space Cognition
> knowledge lives at knowledge/brain/space_cognition/README.md.
> This file is preserved for history reference only; do not edit.
# CaseOS Brain -- Level 1: Space Cognition

- **Layer:** Brain -- Level 1
- **Status:** Accepted
- **Date:** 2026-07-30
- **Audience:** future readers, future agents, future maintainers.
- **Output consumer:** Brain Level 2 (Space Diagnosis, future).

## Purpose

This folder is the first cognitive level of the CaseOS Brain.
It captures **how CaseOS understands a space** -- before any
judgment, diagnosis, recommendation, or implementation.

The discipline of Level 1 is **capture what is, not what should
be**. A violation of this discipline propagates downstream and
produces recommendation prose that reads confidently but
cannot be defended.

## The Brain as a layered architecture

The CaseOS Brain is layered. Each level builds on the previous.
Level 1 is the first layer; further levels will follow as
separate folders under `knowledge/brain/`.

```text
Level 1 -- Space Cognition     <-- THIS FOLDER
   |
   v
Level 2 -- Space Diagnosis     (future; reads Level 1 output)
   |
   v
Level 3 -- Decision            (future; reads Level 2 output)
   |
   v
Level 4 -- Recommendation      (future; reads Level 3 output)
```

Each level has one input and one output. Level 1 "s input is
the Vision Engine "s V3 JSON; Level 1 "s output is the
`SpaceCognition` record consumed by Level 2.

## What Level 1 contains

| File | Role |
| --- | --- |
| `Role.md` | What Space Cognition does in CaseOS, and what it must never do. |
| `Position.md` | Where Space Cognition sits in the architecture, and what it is adjacent to but separated from. |
| `Characteristics.md` | The nine observable characteristics, grouped into four families, with controlled vocabulary and provenance flags. |
| `Emotion.md` | The emotional character of a space, separate from atmosphere, with provenance and (future) population qualifier. |
| `README.md` | This file. |

## What Level 1 produces

A `SpaceCognition` record with three parts:

1. **Characteristics** -- 9 dimensions in 4 families, each with
   a state, a provenance flag, a source link, and an optional
   note. See `Characteristics.md`.
2. **Emotion** -- 1-3 emotion tags, each with a provenance flag
   and (future) a population qualifier. See `Emotion.md`.
3. **Provenance summary** -- the count of `observed` /
   `inferred` / `unknown` fields, used by Level 2 to decide
   whether to ask the user for missing inputs.

## What Level 1 does NOT contain

Three prohibitions, all constitutional:

- **NOT products.** No object, no equipment, no material is
  named at Level 1. The cognition describes a space as it is.
- **NOT recommendations.** No strategy, no intervention, no
  "this space should have a X". Recommendation lives at
  Level 4.
- **NOT implementation.** No construction detail, no material
  specification, no code path. Implementation lives in the
  runtime pipeline; Level 1 is cognitive knowledge, not
  implementation.

These prohibitions mirror the four NOTs in `Role.md` and the
four NOTs in `Characteristics.md`. They are consistent with
Constitution Principles 002 (objects serve goals) and 003
(understand before recommending).

## Reading order

For a new contributor:

1. `Role.md` -- the discipline.
2. `Position.md` -- the place.
3. `Characteristics.md` -- the vocabulary.
4. `Emotion.md` -- the felt sense.
5. The runtime pipeline ("knowledge/decision_model/") -- how
   Level 1 "s output is consumed by the Decision Engine.

For a future Level 2 author (Diagnosis):

1. This README.
2. The `SpaceCognition` record shape (Characteristics + Emotion
   + Provenance summary).
3. Constitution Principles 001-004 and the Forbidden Behaviors
   (per "docs/standards/CaseOS_Constitution_V1.md") -- the
   judgment rules Level 2 must obey.

## Cross-references

- `docs/standards/CaseOS_Constitution_V1.md` -- the philosophy
  Level 1 obeys (principles + forbidden behaviors).
- `docs/standards/CaseOS_Decision_Principles_V1.md` -- the
  implementation guide.
- `knowledge/principles/DP-002` -- the operational rule that
  the space record comes first.
- `knowledge/decision_model/Context_Model.md` Section 3 -- the
  runtime shape of Level 1 "s output as the `space` sub-model.
- `knowledge/decision_model/Decision_Model_V1.md` -- the
  larger Decision Model architecture.
- `knowledge/expert_handbook/06_Space_Psychology.md` -- the
  psychology research behind the vocabulary.

## Future extensions

When Level 2 (Diagnosis) is built, it will live at
`knowledge/brain/Level_2_Space_Diagnosis/` and will read this
folder "s output. The Diagnosis Layer "s job is to ask
"is this space suitable for the user "s stated goal?" -- which
requires the cognition recorded here, but adds judgment.

The Brain Levels are a **forward-only architecture**. A later
level may not silently redefine an earlier level "s output.
If a later level needs a different shape, the earlier level
is updated through ADR, not bypassed.

## Maintenance

- This folder is **cognitive knowledge**, not implementation.
  A change to the runtime Space Agent does not require a change
  here, as long as the cognitive output remains equivalent.
- Adding a new **vocabulary term** to an existing
  characteristic or emotion tag is a non-breaking change
  (allowed without ADR).
- Adding a new **characteristic** or **emotion tag family** is
  a breaking change (the Diagnosis Layer "s input contract
  grows) and requires ADR.
- Renaming or removing a vocabulary term or characteristic is
  a breaking change and requires ADR.
- Adding a new Brain level (`Level_3`, `Level_4`, ...) requires
  ADR (it changes the architecture).

