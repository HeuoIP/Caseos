# Theme Strategy

- **Module:** Theme Strategy
- **Layer:** Brain
- **Pipeline Position:** 7 (after Strategy, before
  Recommendation)
- **Status:** Accepted
- **Date:** 2026-07-30

## Purpose

Determine **the thematic direction** of the project. Theme
Strategy takes the chosen Strategy and selects a primary
theme (and optional secondary theme) from the Theme
Library, with a Story, an Extension ability, and an
Experience path.

Theme Strategy is the layer where **the project acquires a
narrative**. The theme is the carrier of meaning; the
strategy is the carrier of form. Recommendation (next
module) maps theme + strategy into objects.

## Core Principles

1. **Theme comes from four roots.** A theme is legitimate
   only if it draws from at least one of:
   - **Client vision** -- the user "s stated wish.
   - **Environmental potential** -- what the site already
     carries (trees, slope, view, history).
   - **Space condition** -- what the space can hold.
   - **User needs** -- what the audience calls for.
2. **Theme must have three things.** A theme without a
   Story, an Extension ability, and an Experience path is
   a decoration, not a strategy. A decoration is
   rejected.
3. **Primary is mandatory, Secondary is allowed.** Every
   project gets one primary theme. A secondary theme is
   allowed only if it amplifies the primary, not
   competes with it (no two competing cores).
4. **Theme is reversible early, costly late.** Theme
   Strategy prefers conservative choices when confidence
   is low; the Decision Engine may request the user "s
   confirmation.
5. **Theme is independent of decoration.** Theme is the
   story; decoration is the surface. Theme Strategy
   chooses the story.

## Decision Rules

Theme Strategy applies **five gates** in order. If a gate
fails, Theme Strategy either returns candidates for the
user to choose, or returns empty.

### Gate 1. Source legitimacy

Every proposed theme must trace to at least one of the
four roots: Client vision / Environmental potential /
Space condition / User needs. Themes with no root are
rejected.

### Gate 2. Story presence

The theme must have a Story. A Story is one paragraph:
who is the child / user, what do they enter, what do they
discover, what do they leave with.

### Gate 3. Extension ability

The theme must extend into at least three concrete
extensions: a spatial move, a sensory cue, a behavioural
invitation. A theme that cannot extend is rejected.

### Gate 4. Experience path

The theme must produce a sequenced path: arrival, build,
peak, return. The path is a draft; Recommendation may
flesh it out.

### Gate 5. Composition

One primary theme (mandatory). Up to one secondary theme
(only if it amplifies the primary). The Decision Principle
"no two competing cores" applies.

## Inputs

- `strategy/` -- recommended_primary strategy.
- `space_cognition/` -- SpaceCognition record (source of
  environmental potential + space condition).
- `experience_perception/` -- ExperienceProfile record
  (source of story_feeling).
- `client_understanding/` -- ClientUnderstanding record
  (source of client vision + user needs).
- `knowledge/taxonomy/theme/` -- the Theme Library of 41
  leaves in 9 groups (Nature, Animal, Ocean, Space,
  Castle, Transportation, Fantasy, Science, Traditional
  Culture).

## Outputs

A `ThemeSelection`:

```text
ThemeSelection = {
    primary: {
        id: str,                              // "FOREST"
        name: str,                            // "Forest"
        confidence: float,                    // 0..1
        story: str,                           // one paragraph
        extensions: {
            spatial: str,
            sensory: str,
            behavioural: str
        },
        experience_path: [
            { stage: "arrival",  cue: str },
            { stage: "build",    cue: str },
            { stage: "peak",     cue: str },
            { stage: "return",   cue: str }
        ],
        sources: [
            "client_vision" | "environmental_potential"
            | "space_condition" | "user_needs"
        ]
    },
    secondary: null | {
        // same shape as primary
        role: "amplifier",
        // a secondary must never compete with primary
        rationale: str
    },
    candidates: [                              // optional,
        // shown to the user when confidence < 0.7
        // (same shape, list of 2-3 alternatives)
    ],
    rejected_themes: [
        {
            id: str,
            reason_gate: int                   // 1..5
        }
    ],
    rationale: str                             // 1-2 sentences
}
```

A `confidence < 0.7` triggers the `candidates` list and
flags the Decision Engine to ask the user for
confirmation.

## Examples

### Example 1: Forest clearing, "nature awareness" client

**Inputs:**
- Strategy = STR-001 (Anchor).
- Client vision = "children should love the woods".
- Environmental potential = mature trees, soft ground.
- User needs = explore, hide, climb.

**Outputs:**
- primary = { id: "FOREST", confidence: 0.92, story:
  "the clearing is a doorway into the woods; the child
  enters shy, climbs a tree-hide, returns braver."
  extensions: spatial = "tree-house path", sensory =
  "leaf-filtered light + bark texture", behavioural =
  "build a den."
  experience_path = [arrival at clearing, build the
  path, peak at tree-house, return with leaf crown].
  sources = ["client_vision", "environmental_potential",
  "user_needs"].
- secondary = null.
- candidates = none (confidence high).

### Example 2: Urban commercial, "brand anchor"

**Inputs:**
- Strategy = STR-002 (Landmark).
- Client vision = "we want to be the most Instagrammable
  spot in the district".
- Environmental potential = low (hard plaza).
- User needs = dwell time + shareable memory.

**Outputs:**
- primary = { id: "FANTASY.FAIRY_TALE", confidence:
  0.55, story: "the plaza becomes a stage..." }
- candidates = [{ id: "OCEAN.CORAL", rationale: "..." },
  { id: "SPACE.ROCKET", rationale: "..." }]
- Theme Strategy hands `candidates` to the product layer
  so the user can confirm.

### Example 3: Rejected -- decoration

A theme "neon retro" with no Story and no Extension
ability. Theme Strategy sets
`rejected_themes = [{ id: "NEON_RETRO", reason_gate:
2 }]` and forces the project to either pick a legitimate
theme from candidates or proceed without a theme.

## Cross-references

- `constitution/` -- Principle 001 (most suitable), P004
  (amplify strengths; "do not let the catalogue drive the
  recommendation").
- `strategy/` -- upstream producer (theme must serve the
  strategy, not the other way round).
- `recommendation/` -- downstream consumer (objects are
  chosen to realise the theme + strategy).
- `knowledge/taxonomy/theme/` -- the authoritative
  Theme Library (9 groups, 41 leaves).
- `knowledge/expert_handbook/02_Expert_Rules.md` --
  rule "do not pile on equipment; design the story first".

## Maintenance

- Adding a new theme group is a breaking change to the
  Theme Library and requires ADR.
- Adding a new theme leaf within an existing group is a
  non-breaking change (allowed without ADR), but must
  pass Gate 1-4 before publication.
- Renaming a theme is a breaking change and requires
  ADR (do not silently rename; downstream data uses the
  id).
- Changing the confidence threshold for user confirmation
  (default 0.7) is a non-breaking change (allowed without
  ADR).
