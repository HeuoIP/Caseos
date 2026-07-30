
> **DEPRECATED 2026-07-30 (Sprint 17 / ADR-009).** This folder is the
> experimental Sprint 16 structure. The canonical Space Cognition
> knowledge lives at knowledge/brain/space_cognition/README.md.
> This file is preserved for history reference only; do not edit.
# Emotion -- Space Cognition

- **Layer:** Brain -- Level 1
- **Status:** Accepted
- **Date:** 2026-07-30
- **Companion documents:** `Role.md`, `Position.md`,
  `Characteristics.md`, `README.md`.

## Statement

> A space is not only geometry; it is also a **felt sense**.
> Space Cognition captures the **emotional character** of a
> space, separate from its geometry and atmosphere.
> Emotion is the **predicted human response** to the space;
> atmosphere is the **observable condition** of the space.

## Why emotion is separate from atmosphere

The two are related but distinct:

- **Atmosphere** (per `Characteristics.md` Section 5) is the
  **observable** condition: density of activity, visible users,
  time signature. A photo can show atmosphere.
- **Emotion** is the **predicted human response** to the
  observable. A forest clearing can be observed as
  "sparsely populated, late afternoon, surrounded by mature
  trees" (atmosphere) and **predicted** to feel "serene" or
  "mysterious" or both (emotion).

The two are recorded separately because the same atmosphere can
produce different emotions in different populations. A
"sparsely populated, late afternoon" space can feel:
- serene to a retiree,
- lonely to a child,
- romantic to a couple,
- foreboding to a nervous adult.

The atmosphere is **objective** (or near-objective). The
emotion is **predicted, with a population qualifier**. The
prediction is recorded with provenance.

## Emotional categories (non-exhaustive)

The vocabulary is intentionally a short list of strong,
distinct emotions. Each tag should be **defensible**: a
Diagnosis Layer (Level 2) reading "serene" must be able to
trace it to a visible feature.

| Tag | Defensible trigger |
| --- | --- |
| **Serene** | Quiet, sheltered, soft light, slow movement, neutral sound. |
| **Vibrant** | Active, mixed users, bright light, varied surfaces. |
| **Mysterious** | Enclosed, low light, hidden sightlines, unusual vegetation. |
| **Welcoming** | Open access, soft edges, varied users, comfortable seating. |
| **Awe-inspiring** | Large scale, dramatic vertical, exceptional view, unexpected feature. |
| **Intimate** | Small scale, enclosed, soft light, comfortable temperature. |
| **Exposed** | Open sky, no shelter, visible from distance, hard edges. |
| **Sheltered** | Overhead cover, walls, hedges, enclosed feeling. |
| **Joyful** | Visible play, mixed ages, bright colors, soft surfaces. |
| **Contemplative** | Quiet, single focal point, slow movement, neutral sound. |
| **Adventurous** | Varied terrain, surprise elements, exploratory affordances. |
| **Restful** | Soft surfaces, comfortable seating, slow movement, low noise. |
| **Solemn** | Formal, symmetrical, single focal point, quiet. |
| **Playful** | Varied shapes, surprise elements, interactive affordances, bright colors. |

This list is a starter set. Additions are allowed by future
Sprints; renames require ADR.

## Multi-tag records

A space can carry **more than one** emotion tag. The Cognition
records all that apply, with their provenance.

Examples:

- A forest clearing: `serene + awe-inspiring`.
- A rooftop playground: `vibrant + exposed`.
- A walled garden: `sheltered + intimate + contemplative`.
- A public plaza at noon: `vibrant + welcoming`.
- A forest path at dusk: `mysterious + adventurous + slightly
  exposed`.

The tags are not mutually exclusive. The number of tags is
typically 1-3; more than 4 is a sign the vocabulary is being
overloaded and the Diagnosis Layer should be used instead.

## Provenance

Emotion tags carry the same three flags as Characteristics:

| Flag | Meaning | Example |
| --- | --- | --- |
| `observed` | Directly visible (e.g. visible users, visible activity, visible light). | "Vibrant: observed (mixed users and visible activity in the photo)." |
| `inferred` | Deduced from atmospheric and characteristic observations. | "Serene: inferred (sparse activity + soft light + slow-movement affordances)." |
| `unknown` | Cannot be inferred from current input. | "Emotion: unknown (the photo is taken from above; the felt sense cannot be inferred)." |

A tag without provenance is **fabrication** and must not be
recorded.

## Population qualifier (future)

The same atmosphere can produce different emotions in different
populations. A future version of this layer may add a
`population` field to each tag:

```text
emotion = [
    { tag: "serene", population: "retiree", provenance: "inferred", note: "..." },
    { tag: "lonely", population: "child",    provenance: "inferred", note: "..." },
    { tag: "romantic", population: "couple", provenance: "inferred", note: "..." }
]
```

This is **not** in V1 (this document), but it is the design
intent. When Level 2 (Diagnosis) needs to compare the space "s
emotional character to the **user** "s emotional goal, the
population qualifier becomes essential.

## What Emotion is NOT

- **NOT prescribed.** The Cognition says "this space is likely
  to feel X", not "this space SHOULD feel X". The latter is
  the user "s goal and lives in Level 2 / Decision.
- **NOT a single tag.** Spaces carry multiple emotions. A
  Cognition that records a single emotion is reductive.
- **NOT aesthetic.** "Beautiful" is not an emotion tag; it is
  an aesthetic judgment. Beautiful spaces can feel serene,
  joyful, awe-inspiring, OR unsettling. Cognition captures the
  feeling, not the aesthetic.
- **NOT therapy.** Emotion tags are descriptive, not
  prescriptive of how users should feel. The Diagnosis Layer
  asks whether the predicted emotion matches the user "s goal;
  it does not prescribe emotional outcomes.

## Cross-references

- `Role.md` -- the discipline of observation over judgment.
- `Position.md` -- where this output feeds in the pipeline.
- `Characteristics.md` Section 5 -- the related-but-separate
  Atmosphere dimension.
- `knowledge/expert_handbook/06_Space_Psychology.md` -- how
  people perceive and feel in spaces; the psychology basis
  for this vocabulary.

## Maintenance

- Adding a new **emotion tag** is a non-breaking change
  (allowed without ADR).
- Renaming or removing an **emotion tag** is a breaking change
  (the Diagnosis Layer "s vocabulary contract changes) and
  requires ADR.
- Adding the **population qualifier** (V2) is a breaking
  change to the Emotion record shape and requires ADR.

