# 03 Value Taxonomy

> What "value" means when we say a space is good.
> A taxonomy of value dimensions that the Decision Engine can score against,
> and that designers can use to talk about trade-offs.

## 1. Purpose

Provide a shared vocabulary for the dimensions of value that a space can
deliver. The taxonomy makes trade-offs explicit, makes scoring defensible,
and makes the user-facing explanation of a recommendation consistent.

## 2. Scope

**In scope**
- Value dimensions that an end user, a designer, or an operator can
  perceive and describe.
- Dimensions that are independent enough to be scored separately.
- Dimensions that survive across playground, urban, cultural, and
  commercial settings.

**Out of scope**
- Pure cost accounting (capex / opex) — see Expert Rules heuristic 6.
- Marketing value (brand awareness, social-media reach) — that is a
  separate analysis.
- Jurisdictional compliance (EN 1176 etc.) — that is a hard constraint,
  not a value dimension.

## 3. Core Concepts

The taxonomy has seven primary value dimensions. Each is independent
and can be high or low for the same space. The Decision Engine should
score each candidate on each dimension and then let the user state which
dimensions they weight.

1. **Functional value** — does the space do what the user needs it to do?
2. **Emotional value** — does the space make the user feel something?
3. **Social value** — does the space support the relationships the user
   cares about?
4. **Educational value** — does the space teach or develop the user?
5. **Aesthetic value** — is the space beautiful in a way the user values?
6. **Ecological value** — does the space contribute to a living system?
7. **Economic value** — does the space pay back over time?

Each dimension has three to five sub-dimensions. The sub-dimensions are
what the Decision Engine actually scores.

## 4. Heuristics

When scoring or discussing value, use these heuristics.

- **Score sub-dimensions, then aggregate.** A single "social value: 0.7"
  number is uninformative. A decomposition into three sub-scores is.
- **Score against the user, not against the designer.** The user is the
  judge of value. The designer is the judge of feasibility.
- **Trade-off visibility beats aggregate optimisation.** "A scores 0.8 on
  emotional, 0.4 on ecological" is more useful than "A scores 0.6 overall."
- **Value is contextual.** A value score is only meaningful against a
  stated user, goal, and site.
- **Zero is a valid score.** A space can be intentionally low on a
  dimension; that is a design choice, not a failure.

## 5. Vocabulary

- **Primary dimension** — one of the seven top-level values.
- **Sub-dimension** — a measurable facet of a primary dimension.
- **Score vector** — the tuple of (sub-dimension, score) pairs that
  describe a candidate's value.
- **Weight vector** — the tuple of (sub-dimension, weight) the user
  applies to the score vector.
- **Trade-off** — a difference in the score vector that the user must
  accept to choose one candidate over another.

## 6. Common Pitfalls

- **Confusing "good for the designer" with "good for the user."** A
  designer may value aesthetic and ecological highly; a parent may
  value functional and social.
- **Treating the taxonomy as a checklist.** A space does not have to
  score high on every dimension.
- **Letting one dimension dominate.** A space that scores 1.0 on
  emotional and 0.1 on safety is not a 0.5 space; it is a hazard.
- **Using the taxonomy as a marketing tool.** "We deliver all seven
  values" is a slogan, not a score.

## 7. Cross-References

- 01_Space_Decision_Method.md — the method that aggregates the score
  vector into a recommendation.
- 08_Object_Value_Map.md — the mapping from objects to value dimensions,
  which makes the taxonomy operational.
- 04_Positioning_Method.md — how positioning changes the weight vector.
- 06_Space_Psychology.md — the basis for the emotional and social
  dimensions.

## 8. Worked Example

**Candidate A: a small wooden climbing tower.**
- Functional: 0.6 (climbing, low group capacity)
- Emotional: 0.7 (adventure, accomplishment)
- Social: 0.4 (parallel play, low co-play)
- Educational: 0.5 (motor skills, problem-solving)
- Aesthetic: 0.6 (natural material)
- Ecological: 0.5 (wood, low embodied carbon)
- Economic: 0.7 (low cost, low maintenance)

**Candidate B: an interactive wall.**
- Functional: 0.5 (engagement, not movement)
- Emotional: 0.6 (curiosity)
- Social: 0.8 (parallel and cooperative)
- Educational: 0.9 (cause-and-effect, language)
- Aesthetic: 0.4 (modern, less natural)
- Ecological: 0.3 (electronics, replacement cycle)
- Economic: 0.4 (medium cost, higher maintenance)

**Trade-off.** Candidate A is cheaper and more natural; Candidate B
teaches more and supports more social play. A user who weights
educational + social over ecological + cost would prefer B. A user who
weights ecological + cost over educational would prefer A. The
recommendation is a defensible position, not a single truth.

## 9. Open Questions

- [ ] Should ecological value be split into "embodied" and "operational"
  (e.g. the carbon of building vs. the carbon of running)?
- [ ] Should economic value include option value (the value of being
  able to change the space later)?
- [ ] Is aesthetic value user-defined, or does the engine need a
  default aesthetic register per domain pack?
- [ ] How is value scored for accessibility? Is it a sub-dimension of
  functional, or its own dimension?

## 10. Maintenance

- Sub-dimensions may be added or removed, but a change to the seven
  primary dimensions is a breaking change.
- Worked examples should accumulate in this file over time.
- Scoring rubrics for each sub-dimension belong in a separate
  `value_rubrics/` directory (not yet created).
