# Recommendation

- **Module:** Recommendation
- **Layer:** Brain
- **Pipeline Position:** 8 (final; after Strategy + Theme)
- **Status:** Accepted
- **Date:** 2026-07-30

## Purpose

Convert **the chosen strategy and theme** into a structured
set of **solution directions**. Recommendation is the only
Brain module allowed to name specific categories of
objects, sequences, or moves. It is **not** a catalogue
dump: every recommendation is tied to a strategy and a
theme, and every recommendation carries its rationale and
its trade-offs.

Recommendation is the **last mile of the Brain**. After
this module, the human explanation layer takes over
(Explain Agent, customer-facing prose).

## Core Principles

1. **Strategy first, objects second.** Every
   recommendation cites a strategy id; an orphan object
   is rejected (DP-002).
2. **Theme first, surface second.** Every recommendation
   cites the primary theme; an object that does not
   extend the theme is rejected.
3. **Spatial anchor only when needed.** A large theme
   facility is recommended **only when diagnosis shows
   the space lacks a core** (diagnosis.focal = absent
   or competing).
4. **One core, not many.** A RecommendationSet must not
   contain two competing anchors. Multiple small moves
   that amplify a single core are allowed.
5. **Match before beauty.** Each recommendation passes
   the five-match test: Space, User, Budget, Operation,
   Context. Beauty is a tie-breaker only (DP-003).
6. **Protect core value first.** When budget is tight,
   the core recommendation is preserved; satellite moves
   are trimmed.
7. **Customer language only.** The Explain Agent portion
   of the output avoids technical AI language and
   marketing jargon.

## Decision Rules

Recommendation applies **seven rules** in order:

### Rule 1. Anchor-or-not gate

If diagnosis.focal is `clear` or `misdirected`, do **not**
add a large theme facility. Protect / amplify the
existing anchor instead.

If diagnosis.focal is `absent` or `competing`, **one**
RecommendationSet may include a large theme facility.

### Rule 2. One core rule

A RecommendationSet contains **exactly one** core
recommendation. Up to four satellite recommendations
amplify the core. Zero satellite is allowed; two cores
is forbidden.

### Rule 3. Five-match test

Each recommendation passes the five-match test:

- **Space** -- fits the Space Cognition record.
- **User** -- fits the Client Understanding + Experience
  Perception profiles.
- **Budget** -- fits the Project Fit Report "s budget
  band.
- **Operation** -- fits the operation capability.
- **Context** -- fits the site and the market.

A recommendation that fails any axis is rejected, not
down-weighted.

### Rule 4. Theme binding

Each recommendation must cite the primary theme (or the
secondary theme, with rationale). A recommendation
unrelated to the theme is rejected.

### Rule 5. Budget preservation

If the recommendation total exceeds the budget band,
the satellites are trimmed first; the core may only be
trimmed after all satellites are removed.

### Rule 6. Trade-off disclosure

Each recommendation carries its trade-offs explicitly:
- cost band (low / mid / high)
- risk notes (which decision principles it strains)
- time horizon (immediate / seasonal / multi-year)
- reversibility (easy / medium / hard to undo)

### Rule 7. Language discipline

The Explain Agent portion follows the language rules:

- **Forbidden words**: striking, beautiful, amazing,
  impressive, iconic, world-class, ultimate, perfect.
- **Required style**: objective descriptors (large-
  scale, circular canopy, stainless steel spiral slide,
  rope net, open park setting).
- **No marketing adjectives**: comparison "we"re the
  best" is forbidden; the value is expressed in
  concrete terms (stay time +X%, photo share +Y).

## Inputs

- `strategy/` -- StrategySet (chosen strategy).
- `theme_strategy/` -- ThemeSelection (primary + optional
  secondary).
- `diagnosis/` -- DiagnosisReport.
- `space_cognition/` -- SpaceCognition record.
- `experience_perception/` -- ExperienceProfile record.
- `client_understanding/` -- ClientUnderstanding record.
- `project_fit/` -- ProjectFitReport.
- `knowledge/objects/` -- the Object Library (categories,
  not products).
- `knowledge/taxonomy/theme/` -- the Theme Library.

## Outputs

A `RecommendationSet`:

```text
RecommendationSet = {
    core: {
        id: str,                              // "REC-001"
        strategy_ref: str,                    // "STR-002"
        theme_ref: str,                       // "FOREST"
        name: str,                            // short label
        category: str,                        // "treehouse",
                                               // "spiral_slide",
                                               // "reading_corner"
        description: str,                     // concrete, no
                                               // marketing jargon
        five_match: {
            space: { pass: bool, note: str },
            user: { pass: bool, note: str },
            budget: { pass: bool, note: str },
            operation: { pass: bool, note: str },
            context: { pass: bool, note: str }
        },
        trade_offs: {
            cost_band: "low" | "mid" | "high",
            risk_notes: [str],
            time_horizon: "immediate"
                          | "seasonal"
                          | "multi_year",
            reversibility: "easy" | "medium" | "hard"
        },
        rationale: [str]                      // cited brain
                                               // inputs
    },
    satellites: [                              // up to 4
        // same shape as core, with role =
        // "amplifier" | "connector"
        // | "annotation" | "seasonal"
    ],
    trade_off_summary: str,                    // 1 sentence
    budget_total_band: "low" | "mid" | "high",
    language_check: {
        forbidden_words_found: [str],
        pass: bool
    },
    provenance_summary: {
        observed: int,
        inferred: int,
        unknown: int
    },
    unknowns: [str]
}
```

A `language_check.pass = false` blocks the output until
the prose is rewritten.

## Examples

### Example 1: Forest clearing

**Inputs (abbreviated):**
- Strategy = STR-001 (Anchor).
- Theme = FOREST, confidence 0.92.
- Diagnosis focal = clear (trees as natural anchor).

**Outputs:**
- core = { id: REC-001, strategy_ref: STR-001,
  theme_ref: FOREST, category: treehouse, description:
  "single small treehouse on existing mature tree, rope
  bridge to existing second tree, bark-step access" }
- satellites = [REC-002 (den-build kit), REC-003
  (seasonal leaf-crown station)]
- Rule 1 says: do not add a large theme facility; the
  treehouse is small (under 30 sqm).
- Rule 2: one core.
- Rule 3: passes all five axes.
- language_check passes.

### Example 2: Urban wrong-scale plaza

**Inputs (abbreviated):**
- Strategy = STR-002 (Layered).
- Theme = OCEAN.CORAL, confidence 0.65, candidates
  offered.
- Diagnosis focal = absent.

**Outputs:**
- core = { id: REC-001, strategy_ref: STR-002,
  theme_ref: OCEAN.CORAL, category: shade_canopy +
  sand_zone + tide_table, description: "shade canopy at
  child height, sand play zone below, water-tide table
  for observation" }
- satellites = [REC-002 (seat step around tree pit),
  REC-003 (wayfinding sculpture set, three pieces)]
- Rule 1 allows the large facility (diagnosis focal =
  absent).
- Rule 4: every recommendation cites OCEAN.CORAL.
- trade_offs.cost_band = mid

### Example 3: Forbidden words detected

**Input:** a draft explanation says "striking landmark".

**Output:** `language_check = { forbidden_words_found:
["striking"], pass: false }`. The Explain Agent must
rewrite to "9m timber tower with rope net and stainless
steel slide" before the report can ship.

## Cross-references

- `constitution/` -- Principle 001 (most suitable), P002
  (design serves decisions), P004 (amplify strengths).
- `principles/DP-002` -- *Space First, Object Second.* The
  anchoring rule is the strict form of DP-002.
- `principles/DP-003` -- *Match Before Beauty.* The five-
  match test is the strict form of DP-003.
- `strategy/` -- upstream producer.
- `theme_strategy/` -- upstream producer.
- `knowledge/decision_model/Strategy_Model.md` -- the
  runtime Strategy Agent consumes the same five families.
- `knowledge/objects/` -- the source of category names
  (no manufacturer, no price).
- `knowledge/expert_handbook/04_Positioning_Method.md`
  -- anchoring + positioning method.
- `knowledge/expert_handbook/05_Negative_Rules.md` -- the
  negative rules ("do not pile on equipment", "no
  decoration without story") that the seven rules
  enforce.

## Maintenance

- Adding a new rule (e.g., a sustainability rule) is a
  breaking change to the Brain "s output contract and
  requires ADR.
- Renaming a rule is a breaking change and requires ADR.
- Adding to the `forbidden_words` list is a non-breaking
  change (allowed without ADR), but every addition must
  be revisited by Explain Agent "s regression suite.
- Changing the satellite cap (default 4) is a breaking
  change and requires ADR.
