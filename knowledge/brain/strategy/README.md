# Strategy

- **Module:** Strategy
- **Layer:** Brain
- **Pipeline Position:** 6 (after Diagnosis, before Theme
  Strategy)
- **Status:** Accepted
- **Date:** 2026-07-30

## Purpose

Determine **the transformation direction**. Strategy reads
the Diagnosis report and decides what kind of move the
project is: remove, add, reorganise, anchor, sequence,
quiet, intensify. Strategy chooses the **direction**, never
the equipment.

Strategy is the Brain "s "first how". After Diagnosis names
the problem, Strategy proposes the move.

## Core Principles

1. **Strategy before object.** A strategy may be realized
   with many objects; it must not name objects.
2. **Remove before add.** Subtraction is a strategy.
3. **Space before object.** The space is moved first;
   objects fill in second (DP-002).
4. **Match before beauty.** The strategy must first fit
   Space, User, Budget, Operation, Context; beauty is a
   tie-breaker only (DP-003).
5. **Restraint creates quality.** A strategy that says
   "less" is often the right one.
6. **Concentrate value.** Resources should protect the
   single most important move.
7. **Find the spatial eye.** Every strong project has a
   point the eye locks onto; Strategy may need to find it
   or protect it.

## Decision Rules

Strategy proposes a **StrategySet** -- up to five
strategies, drawn from the five strategic families below.
Strategy does not pick one for the user; it offers the
ordered set with rationale.

### Family 1. Landmark

A single dominant feature that organises the whole site.
Use when the space lacks an anchor (diagnosis focal =
absent or competing).

### Family 2. Journey

A sequenced experience from arrival to departure. Use when
diagnosis vitality = dormant and the user wants narrative.

### Family 3. Field

A diffuse, varied landscape where many small moves
together make the place. Use when the space is already
strong and the move is gentle.

### Family 4. Layered

Multiple horizontal layers (ground, mid, upper) with
different programs at each level. Use when the space has
vertical potential.

### Family 5. Anchor

One existing element (tree, slope, view, wall) is the
centre of gravity; the strategy protects and amplifies it.
Use when diagnosis focal = clear and the project is
amplification, not new build.

### Tie-breakers

If more than one family fits, rank by:

1. **Diagnosis priority** -- the synthesis "s priority.
2. **Project Fit confidence** -- if fit is low, pick the
   lowest-cost family.
3. **Budget sensitivity** -- Anchor and Field are cheaper
   than Landmark and Journey; Layered is the most
   expensive.
4. **Constitution principle 004** -- amplify strengths
   before adding new.

## Inputs

- `diagnosis/` -- DiagnosisReport.
- `space_cognition/` -- SpaceCognition record.
- `experience_perception/` -- ExperienceProfile record.
- `client_understanding/` -- ClientUnderstanding record.
- `project_fit/` -- ProjectFitReport.

## Outputs

A `StrategySet`:

```text
StrategySet = {
    strategies: [
        {
            id: str,                          // "STR-001"
            family: "landmark" | "journey"
                    | "field" | "layered"
                    | "anchor",
            rank: int,                        // 1..5
            statement: str,                   // one sentence
            rationale: [str],                 // cited evidence
            expected_effect: {
                on_fit: str,
                on_vitality: str,
                on_focal: str,
                on_risk: str
            },
            budget_class: "low" | "mid" | "high",
            risk_notes: [str],
            confidence: float
        }
    ],
    recommended_primary: str,                  // id
    rationale_summary: str                     // 1-2 sentences
}
```

Each strategy carries its provenance (the diagnosis and
cognition facts it cites). Strategy never names objects.

## Examples

### Example 1: Kindergarten in a wrong-scale plaza

**Diagnosis:** fit = mismatched (scale), focal = absent,
risk = soft (heat).

**StrategySet:**
- STR-001 (rank 1): "Shrinking the place." Family = Anchor
  (existing tree row on north edge becomes the child
  refuge). Budget class = low.
- STR-002 (rank 2): "Layered canopy." Family = Layered
  (shade structure at child height + activity zone at
  ground). Budget class = mid.
- STR-003 (rank 3): "Story walk." Family = Journey
  (arrival gate, hedge tunnel, tree-house, sandpit,
  departure). Budget class = mid.
- recommended_primary = "STR-001" because Diagnosis
  priority is "scale and shade" and Project Fit
  confidence is low.

### Example 2: Forest clearing -- ready

**Diagnosis:** fit = aligned, focal = clear (trees), risk
= soft only.

**StrategySet:**
- STR-001 (rank 1): "Protect the clearing." Family =
  Anchor. Budget class = low.
- STR-002 (rank 2): "Add a single small facility." Family
  = Landmark. Budget class = mid. (Only if the user "s
  goal requires it.)

### Example 3: Mixed commercial plaza

**Diagnosis:** focal = competing, vitality = strained.

**StrategySet:** three strategies from Landmark, Field,
Anchor in rank order.

## Cross-references

- `constitution/` -- Principle 002 (Design serves
  decisions), Principle 004 (Amplify strengths).
- `principles/DP-002` -- *Space First, Object Second.* The
  five families are pure space moves.
- `principles/DP-003` -- *Match Before Beauty.* The
  tie-breakers operationalise it.
- `diagnosis/` -- upstream producer.
- `theme_strategy/` -- downstream consumer (theme
  selection follows strategy selection).
- `recommendation/` -- downstream consumer (objects are
  scoped to the chosen strategy).
- `knowledge/decision_model/Strategy_Model.md` -- the
  runtime shape used by the Decision Engine "s Strategy
  Agent. The five families here are the canonical labels;
  the runtime may add sub-strategies.

## Maintenance

- Adding a new strategic family is a breaking change to
  the Brain "s strategy vocabulary and requires ADR.
- Renaming a family is a breaking change and requires
  ADR.
- Reordering the tie-breakers is a non-breaking change
  (allowed without ADR), but should still be documented
  in the Release Notes.
- Promoting a sub-strategy to a family is a breaking
  change and requires ADR.
