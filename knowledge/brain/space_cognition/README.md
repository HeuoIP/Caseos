# Space Cognition

- **Module:** Space Cognition
- **Layer:** Brain
- **Pipeline Position:** 3 (after Project Fit, before Experience Perception)
- **Status:** Accepted
- **Date:** 2026-07-30
- **Supersedes:** the experimental
  `Level_1_Space_Cognition_OBSOLETE/` (Sprint 16, 2026-07-30);
  see Maintenance for migration notes.

## Purpose

Understand **what kind of space exists**. Space Cognition
produces a structured description of the physical site, free
of judgment, recommendation, or implementation detail. The
description is the input to Experience Perception, Diagnosis,
Strategy, and the runtime Space Agent.

Space Cognition is **pure perception**. It captures what is,
not what should be.

## Core Principles

1. **Observe, don "t judge.** Space Cognition records the space
   as it is observed, not as it should be.
2. **Capture what is, not what should be.** A space described
   as "compact, sunny, urban, lively" remains so even if the
   user "s goal is "calm retreat". The mismatch is the next
   module "s job, not this one.
3. **Provenance is mandatory.** Every claim carries a
   provenance flag (`observed` / `inferred` / `unknown`).
4. **Independence from user goal.** Space Cognition "s output
   is reusable across multiple downstream uses.
5. **No product, no recommendation, no implementation.** This
   module describes a space; it does not name objects, suggest
   strategies, or describe construction.

## Decision Rules

Space Cognition analyses the space along **four axes**:

### 1. Spatial role

What is the space **for** in its current use? Examples:
- transit corridor (people pass through)
- gathering place (people stay)
- service point (people are served)
- contemplative space (people observe)
- play space (people engage actively)
- working space (people labour)
- mixed

The role is observed, not inferred from the user "s goal.

### 2. Spatial position

Where does the space sit in its **broader context**? Examples:
- ground-level open
- elevated (rooftop, terrace)
- enclosed (room, atrium, courtyard)
- edge (perimeter, threshold)
- island (surrounded by a different context)
- hidden (low visibility from outside)
- exposed (high visibility from outside)

### 3. Spatial characteristics

The space "s **physical and contextual** attributes, in four
sub-families:

- **Physical** -- Geometry, Light & Climate, Existing Features.
- **Contextual** -- Surroundings.
- **Experiential** -- Atmosphere, Sensory qualities.
- **Spatial Structure** -- Flow, Rhythm, Boundaries.

Each characteristic carries a controlled vocabulary (per
`knowledge/expert_handbook/06_Space_Psychology.md` and the
Vision Standard "s Site Type Taxonomy).

### 4. Spatial state

The space "s **current condition**: pristine / used / worn /
under construction / abandoned / disputed / transitioning.
The state is observed; transitions are recorded as `inferred`.

## Inputs

- The Vision Engine "s V3 JSON (per ADR-008).
- Optional user-stated site facts (history, known constraints,
  intended use).
- Optional ground-truth measurements (rare in V1; future).

## Outputs

A `SpaceCognition` record:

```text
SpaceCognition = {
    spatial_role: { observed: bool, value: str, source: str },
    spatial_position: { observed: bool, value: str, source: str },
    spatial_characteristics: {
        geometry: ...,
        light_climate: ...,
        existing_features: ...,
        surroundings: ...,
        atmosphere: ...,
        sensory: ...,
        flow: ...,
        rhythm: ...,
        boundaries: ...
    },
    spatial_state: { observed: bool, value: str, source: str },
    provenance_summary: {
        observed: int,
        inferred: int,
        unknown: int
    },
    unknowns: [str]
}
```

Every field carries its provenance. Downstream consumers:
Experience Perception, Diagnosis, Strategy.

## Examples

### Example 1: Compact urban kindergarten rooftop

**Input:** Photo of a 60 m2 rooftop terrace on a kindergarten,
3-6 year olds, urban setting, west-facing sun, low parapet.

**Output (SpaceCognition excerpt):**
- spatial_role = "play space + outdoor classroom" (observed)
- spatial_position = "elevated" (observed)
- spatial_characteristics.geometry = "rectangular 12m x 5m"
  (observed)
- spatial_characteristics.light_climate = "west sun 4-6h,
  wind-exposed" (inferred)
- spatial_state = "pristine" (observed)
- provenance_summary = { observed: 6, inferred: 2, unknown: 1 }

### Example 2: Forest clearing

**Input:** Photo of a 200 m2 clearing in a deciduous forest,
surrounded by mature trees, soft ground cover, no structures.

**Output (SpaceCognition excerpt):**
- spatial_role = "contemplative space + gathering" (observed)
- spatial_position = "ground-level open, edge of forest"
  (observed)
- spatial_characteristics.existing_features =
  "mature trees, soft ground" (observed)
- spatial_characteristics.atmosphere = "sheltered, dappled
  light" (observed)
- spatial_state = "pristine" (observed)
- provenance_summary = { observed: 8, inferred: 1, unknown: 0 }

### Example 3: Ambiguous (low signal)

**Input:** A single photo with limited context, low resolution.

**Output:**
- spatial_role = unknown
- spatial_position = unknown
- spatial_characteristics.geometry = unknown
- spatial_state = unknown
- provenance_summary = { observed: 0, inferred: 0, unknown: 9 }
- unknowns = [most fields]

The Brain asks the user for the missing inputs before
proceeding.

## Cross-references

- `constitution/` -- Principle 003 (Understand before
  recommending) -- Space Cognition is the **observe** step.
- `principles/DP-002` -- *Space First, Object Second.* Space
  Cognition is the space record.
- `experience_perception/` -- downstream consumer.
- `diagnosis/` -- downstream consumer (compares Space
  Cognition "s output against the user "s goal).
- `knowledge/decision_model/Context_Model.md` Section 3 --
  the runtime shape of the Space Cognition "s output as the
  `space` sub-model.
- `knowledge/expert_handbook/06_Space_Psychology.md` -- the
  psychology research behind the controlled vocabulary.
- `docs/standards/CaseOS_Vision_Standard_V1.md` -- the
  Vision Engine "s vocabulary that feeds Space Cognition.

## Maintenance

- A change to the **four axes** (adding a new axis) is a
  breaking change (the downstream modules " input contract
  grows) and requires ADR.
- A change to the **controlled vocabulary** under any axis
  is a non-breaking change (allowed without ADR).
- A change to the **provenance flags** (adding a new flag
  between `observed` and `inferred`) requires ADR.
- Renaming or removing an axis is a breaking change and
  requires ADR.
- **Migration from the old structure:** the experimental
  `Level_1_Space_Cognition_OBSOLETE/` folder (Sprint 16)
  is preserved for history reference. Its content (Role,
  Position, Characteristics, Emotion) is **not** a
  normative reference; the structure in this README is
  canonical. Future Sprints may migrate specific vocabulary
  terms from the OBSOLETE folder into the current
  characteristics sub-families.

