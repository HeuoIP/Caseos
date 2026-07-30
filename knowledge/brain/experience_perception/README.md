# Experience Perception

- **Module:** Experience Perception
- **Layer:** Brain
- **Pipeline Position:** 4 (after Space Cognition, before Diagnosis)
- **Status:** Accepted
- **Date:** 2026-07-30

## Purpose

Understand **how a space is experienced by the people in it**.
Experience Perception reads the space record produced by
Space Cognition and projects it through the lens of human
senses, emotion, and imagination. It produces a structured
description of what the space *feels like* and *invites*, free
of judgment or recommendation.

Experience Perception is the **bridge from the physical space
to the human experience**. It is the only Brain module that
explicitly models the person inside the space.

## Core Principles

> "Space is not an object to observe.
> Space is a relationship between people and environment."

1. **People-first.** Every statement is about a person "s
   sensory or emotional experience, not about the bricks.
2. **Multi-population.** The same space is experienced
   differently by a child, a parent, a senior, a passerby.
3. **Time-aware.** Atmosphere changes by time of day, season,
   crowd density. Record the dominant variant and the
   variance.
4. **Perception, not preference.** "Calm" is a perception;
   "I like calm" is a preference. This module records
   perceptions only.
5. **Independent from the user "s goal.** A space "s
   experience is what it is; whether it matches the user "s
   goal is the next module "s job.

## Decision Rules

Experience Perception analyses the space along **seven
perceptual axes**:

### 1. Scale proportion

How the body relates to the room. Examples: intimate /
human / monumental / vast. Children feel a 3 m height as
adults do not.

### 2. Spatial relationship

Enclosure, exposure, threshold, prospect, refuge. Where the
eye can travel and where it cannot.

### 3. Atmosphere

The dominant mood word. Quiet / lively / ceremonial /
playful / tense / neutral / warm / cold. Atmosphere is a
holistic impression, not a single variable.

### 4. Story feeling

Whether the space suggests a narrative. "This feels like a
forest hideout." "This feels like a stage." Story feeling is
the implicit invitation the space offers.

### 5. Imagination

What the space makes a child (or adult) imagine. "A pirate
ship." "A garden." "A workshop." A space with low
imagination is not necessarily bad; it is a constraint.

### 6. Stay desire

The pull to remain, observe, sit, touch, explore. A bench
under a tree has stay desire; a busy corridor does not.

### 7. Vitality

The presence or absence of life -- people, animals, plants,
moving water, sound, light. Vitality may be observed or
potential ("the bones are quiet, but the bones can host life").

## Inputs

- `space_cognition/` output (the four-axes SpaceCognition
  record).
- Optional user-stated context (intended users, capacity,
  hours of use).
- Optional contextual data (time of day, season, weather,
  crowd density).

## Outputs

An `ExperienceProfile` record, structured per population
segment:

```text
ExperienceProfile = {
    segments: [
        {
            population: str,             // "child_3_6",
                                          // "parent",
                                          // "senior",
                                          // "passerby"
            scale_proportion: str,
            spatial_relationship: str,
            atmosphere: str,
            story_feeling: str,
            imagination: [str],
            stay_desire: { observed: bool, value: str },
            vitality: { observed: bool, value: str },
            time_variants: [
                {
                    time: str,         // "morning", "dusk"
                    atmosphere: str,
                    notes: str
                }
            ]
        }
    ],
    sensory_map: {
        sight: [str],     // dominant visual cues
        sound: [str],     // quiet, traffic, birds, water
        touch: [str],     // textures within reach
        smell: [str]      // grass, food, engine, none
    },
    dominant_atmosphere: str,
    provenance_summary: {
        observed: int,
        inferred: int,
        unknown: int
    },
    unknowns: [str]
}
```

The output is reusable across multiple downstream uses
(Diagnosis, Explain Agent, customer-facing prose).

## Examples

### Example 1: Forest clearing with a child

**Input:** A 200 m2 clearing with mature trees, soft ground,
dappled light; same as Space Cognition Example 2.

**Output (ExperienceProfile, segment "child_3_6"):**
- scale_proportion = "human, sheltered" (inferred)
- spatial_relationship = "refuge + prospect" (inferred)
- atmosphere = "quiet, magical" (inferred)
- story_feeling = "forest adventure, fairy hollow" (inferred)
- imagination = ["hideout", "dragon nest", "fairy ring"]
  (inferred)
- stay_desire = high (observed)
- vitality = "mature, ambient" (observed)
- time_variants = [{ morning: "dewy, soft light" }]

The same clearing through a senior "s eyes:
- atmosphere = "peaceful, retreat" (inferred)
- story_feeling = "memory of countryside" (inferred)
- imagination = [] (inferred)
- stay_desire = high (inferred)
- vitality = "low movement, sensory-rich" (observed)

Same space, two experiences. The Brain keeps both.

### Example 2: Urban commercial plaza at noon

**Input:** Open plaza, hard paving, fountains off mid-day,
no shade, food trucks.

**Output (segment "passerby"):**
- scale_proportion = "monumental, exposed" (observed)
- spatial_relationship = "prospect, no refuge" (observed)
- atmosphere = "lively, transactional" (observed)
- story_feeling = "stage" (inferred)
- stay_desire = low (observed)
- vitality = high (observed)
- sensory_map.sound = ["traffic", "voices", "fountain off"]

### Example 3: Ambiguous (single photo, no people)

**Output:**
- segments = one generic segment, most fields unknown
- dominant_atmosphere = inferred with low confidence
- unknowns flagged

The Brain asks for more signal before proceeding to
Diagnosis.

## Cross-references

- `constitution/` -- Principle 003 (Understand before
  recommending). Experience Perception is the second
  half of the "understand" step.
- `space_cognition/` -- upstream producer.
- `diagnosis/` -- downstream consumer (compares
  Experience Perception against the user "s goal).
- `recommendation/` -- downstream consumer (Explain Agent
  uses perception language in customer-facing prose).
- `knowledge/expert_handbook/06_Space_Psychology.md` --
  the psychology research behind the seven axes.

## Maintenance

- Adding a new perceptual axis (e.g., thermal comfort) is a
  breaking change to the ExperienceProfile contract and
  requires ADR.
- Adding a new population segment (e.g., "tourist") is a
  non-breaking change (allowed without ADR).
- Changing the controlled vocabulary under any axis is a
  non-breaking change (allowed without ADR).
- Renaming an axis is a breaking change and requires ADR.
