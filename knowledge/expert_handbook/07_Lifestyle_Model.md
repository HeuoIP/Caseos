# 07 Lifestyle Model

> How the lifestyle of the target user shapes the design of a space.
> Lifestyle is a soft constraint that influences the score vector and
> the weight vector. The Decision Engine uses lifestyle to make
> recommendations that fit a user's real life, not an abstract user.

## 1. Purpose

Capture the lifestyle dimensions that materially affect a space
decision, so the engine can match a candidate to a user without
asking intrusive personal questions. Lifestyle is not identity;
it is the routine, the resources, the culture, and the rhythm of
daily life.

## 2. Scope

**In scope**
- Lifestyle dimensions that an end user, a designer, or a planner
  can observe or describe.
- Dimensions that affect how a space is used, not how it is built.
- Cross-cultural lifestyle patterns that the engine must recognise.

**Out of scope**
- Demographic data that does not affect space use (e.g. annual
  household income bracket as a target variable).
- Personal preferences that are not part of a lifestyle pattern.
- Marketing segmentation.

## 3. Core Concepts

The model has five lifestyle dimensions. Each is scored on a small
scale so the engine can compare candidates against the user's
lifestyle quickly.

1. **Urbanity** — the density and rhythm of daily life. From rural
   to high-density urban.
2. **Family structure** — who lives together and how they spend
   time outside. From single adult to multi-generational household.
3. **Activity pattern** — the weekly rhythm of activity. From home-
   centric to high-mobility.
4. **Cultural context** — the local norms of public space, gender
   use, intergenerational mixing, and so on.
5. **Resource tier** — the time, attention, and money available
   for a space visit. Not income, but resource-for-this-activity.

These dimensions are not a survey; they are an inference from what
the user tells the engine or from what the engine observes about
the site.

## 4. Heuristics

- **Lifestyle is an inference, not a question.** The engine
  observes the site context (urban / suburban / rural), the
  declared user (family with children, elderly resident,
  commuter), and the declared rhythm (weekend family, weekday
  lunch, evening walk), and infers the rest.
- **Lifestyle changes the weight vector, not the score vector.**
  A Reading_Corner scores the same on emotional value regardless
  of lifestyle; an urban user weights emotional value higher
  than a rural user.
- **Cultural context is local.** Lifestyle dimensions do not have
  universal thresholds; the engine must localise.
- **Lifestyle is the user, not the demographic.** Two families
  with the same income can have very different lifestyles; the
  engine must respect the difference.

## 5. Vocabulary

- **Urbanity** — density and rhythm of daily life.
- **Family structure** — composition and time-sharing pattern.
- **Activity pattern** — weekly rhythm of activity.
- **Cultural context** — local norms of public space.
- **Resource tier** — time, attention, money available for this
  activity.
- **Inference** — the engine's reading of lifestyle from
  observable signals, not from a survey.

## 6. Common Pitfalls

- **Treating lifestyle as a fixed demographic.** Lifestyle changes
  with life stage, season, and circumstance.
- **Letting resource tier drive recommendation.** Resource tier
  constrains, but should not exclude, a candidate.
- **Assuming urban lifestyle = modern lifestyle.** Many urban
  contexts in the CaseOS market are traditional and family-led.
- **Reading cultural context from a country label.** The engine
  must localise within a country, not just by country.

## 7. Cross-References

- 03_Value_Taxonomy.md — lifestyle changes the weight vector.
- 04_Positioning_Method.md — positioning is partly a statement
  of intended lifestyle.
- 02_Expert_Rules.md heuristics 5 (shade first), 6 (maintenance),
  9 (sound) — these are lifestyle-sensitive.
- 06_Space_Psychology.md — lifestyle affects which psychological
  register applies.

## 8. Worked Example

**User profile.**
- Urbanity: medium-density urban, ground-floor retail, no private
  outdoor space.
- Family structure: two working parents, one child aged 4, one
  grandparent nearby.
- Activity pattern: weekend family outings, weekday lunch in the
  neighbourhood.
- Cultural context: mixed traditional-modern, multi-generational
  mixing is normal.
- Resource tier: moderate, time-poor, money-moderate.

**Lifestyle inferences.**
- Time-poor → low-maintenance design is preferred.
- Multi-generational → seating for the grandparent, play for the
  child, both visible to each other.
- No private outdoor → the public space substitutes for the
  backyard on weekends.
- Traditional-modern → a sense of place that is neither
  aggressively modern nor overtly themed.

**Effect on the recommendation.** A small Treehouse, a Reading_Corner
near the entrance, a low-height slide, and a planting-rich landscape
with shade. No IP_Sculpture (cultural register mismatch), no
Interactive_Wall (maintenance mismatch with time-poor lifestyle),
no tall climbing structure (grandparent visibility fails).

## 9. Open Questions

- [ ] Should the engine ask for lifestyle signals, or always infer?
- [ ] How is "resource tier" measured without a personal question?
- [ ] How does the engine handle a space that serves multiple
  lifestyles at once (e.g. a schoolyard used by families on
  weekends)?
- [ ] When lifestyle and stated goal conflict, which wins?

## 10. Maintenance

- The five dimensions are stable. Sub-dimensions may be added.
- Cultural-context rules must be reviewed with a local expert
  before release in a new market.
- Worked examples should accumulate per market.
