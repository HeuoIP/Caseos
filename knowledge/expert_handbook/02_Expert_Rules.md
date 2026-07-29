# 02 Expert Rules

> Codified rules that experienced playground and space designers apply
> without thinking. These rules are domain knowledge, not engine logic.
> The Decision Engine consults them like a junior designer consults a
> senior partner.

## 1. Purpose

Capture the implicit rules that experienced designers use to make
good space decisions, so the Decision Engine can apply them consistently
instead of rediscovering them case by case.

## 2. Scope

**In scope**
- Rules of thumb that survive across climate, budget, and culture.
- Rules that are testable against real cases.
- Rules that an experienced designer would say "obviously" to.

**Out of scope**
- Personal aesthetic preferences.
- Code or jurisdictional regulations (those live in `docs/standards/`).
- Marketing or sales language.

## 3. Core Concepts

Expert designers reason along five axes at once.

- **Who is the user.** Not "children" but a specific age band, group size,
  caregiver pattern, and accessibility need.
- **What is the journey.** Not a single photo but the sequence of moments
  the user will experience.
- **What is the constraint.** Footprint, climate, budget, regulation, sight
  lines, soil, drainage, sun path, wind.
- **What is the atmosphere.** The emotional register a space should carry
  (calm, thrilling, communal, contemplative, playful).
- **What is the cost over time.** Not the capex, but the 5-year and
  10-year cost including maintenance, replacement, and supervision.

## 4. Heuristics

A non-exhaustive list. Each heuristic is one line; the worked example in
01_Space_Decision_Method.md shows several in combination.

1. **The photo lies.** A photo cannot show dimensions, soil, drainage,
   jurisdiction, or budget. Treat images as evidence about atmosphere
   only.
2. **Children are not small adults.** A 4-year-old and a 9-year-old want
   different things. A 4-year-old and a 4-year-old in a wheelchair want
   the same affordance through different means.
3. **The slowest user defines the accessibility of the space.** If a
   grandparent cannot sit, watch, and reach a toilet, the space is not
   family-friendly.
4. **A space without a place to sit is not a public space.** Seating is
   not optional; it is the precondition for a public.
5. **Shade is not a feature, it is infrastructure.** Plan shade first,
   then place objects under it.
6. **Maintenance is a design parameter, not an afterthought.** A beautiful
   space that cannot be maintained becomes a liability in year three.
7. **Theme is a wrapper, not a driver.** The atmosphere comes from
   materials, scale, and behaviour, not from the character on the wall.
8. **The most important object is the one that creates the first moment
   of arrival.** Without a strong arrival, the rest does not register.
9. **Sound matters as much as sight.** A space that looks beautiful but
   echoes or bangs is uncomfortable.
10. **A great space is one you can describe in one sentence.** If you
    cannot, neither can the user.

## 5. Vocabulary

- **Arrival** — the first moment a user registers the space.
- **Loop** — a circulation path that returns to its start.
- **Edge** — the boundary between activity and rest.
- **Backdrop** — the visual context (sky, planting, architecture) that
  frames the activity.
- **Sensory load** — the combined intensity of sight, sound, touch, and
  motion a user experiences.
- **Dwell time** — how long a typical user stays.
- **Capex vs opex** — capital cost vs operating cost.

## 6. Common Pitfalls

- **Designing for the brochure.** Marketing the space well is not the same
  as designing it well.
- **Treating accessibility as a checklist.** Real inclusion changes
  geometry, not just adds a ramp.
- **Confusing theme richness with design quality.** A forest theme with
  three elements can be richer than a pirate theme with twenty.
- **Specifying equipment before atmosphere.** Equipment lists are an
  outcome of a journey, not a starting point.
- **Optimising for the photo.** A great photo is not always a great
  space; many great spaces photograph poorly.
- **Borrowing a foreign context wholesale.** What works in a Nordic
  forest does not necessarily work in a Shenzhen plaza.

## 7. Cross-References

- 01_Space_Decision_Method.md — the method that applies these rules.
- 06_Space_Psychology.md — the psychological basis for several rules.
- 07_Lifestyle_Model.md — how lifestyle shapes which rules apply.
- 04_Positioning_Method.md — why a rule might be relaxed when positioning
  is the goal.
- 05_Negative_Rules.md — the things these rules forbid.

## 8. Worked Example

**Scenario.** A 300 m² schoolyard in a hot climate, used by 6 to 9 year
olds, 90 minutes per day, supervised.

**Apply heuristics 5, 6, 9.**
- Heuristic 5 (shade first) → the design must provide shade for 70% of the
  active area before any object is specified.
- Heuristic 6 (maintenance) → the school has a single caretaker; equipment
  with rope nets, wood, or electronics must be limited.
- Heuristic 9 (sound) → nearby classrooms require a sound cap; metal
  slides and loud interactive walls should be reconsidered.

**Result.** The method proposes a shade structure first, then a small
climbing tower in Robinia wood, a low-height stainless slide (heat-managed
shade over the runout), a reading nook on the shaded edge, and no IP
sculpture (maintenance cost too high for this setting). The pirate theme
suggested by the client is recorded as a future consideration but is not
the driver of the V1 design.

## 9. Open Questions

- [ ] How are these heuristics encoded for the engine: as rules, as
  scoring weights, or as guardrails on the recommendation?
- [ ] Which heuristics are universal, and which are culture-specific?
- [ ] How does the engine explain to the user *which* heuristic it
  applied when it rejected a candidate?

## 10. Maintenance

- New heuristics are added only with a worked example and at least one
  counter-example.
- A heuristic may be deprecated when a counter-example shows the rule
  fails more often than it helps.
- Cross-references must be updated whenever a related document changes
  its vocabulary or scope.
