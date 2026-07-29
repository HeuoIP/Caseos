# 01 Space Decision Method

> The operating procedure the future CaseOS Space Decision Engine will follow.
> A companion to `knowledge/decision_rules/Space_Decision_Principles.md`, this
> document turns the ten principles into a step-by-step method.

## 1. Purpose

Define one deterministic, replayable procedure that takes a target space, a
user goal, and a set of constraints, and produces a defensible recommendation
of what to place in that space. The method is the *how*; the principles are
the *what*.

## 2. Scope

**In scope**
- A single end-to-end method for one space, one goal, one set of constraints.
- A method that always returns a recommendation, an alternative, a "why not",
  a list of unknowns, and a reproducibility record.
- A method that survives missing information by asking, not by guessing.

**Out of scope**
- Implementation details of any specific model, vector index, or database.
- Multi-space portfolio planning.
- Procurement, contract management, or construction supervision.

## 3. Core Concepts

The method is built on six concepts, in order.

1. **Evidence** — facts about the space (from images, drawings, prior cases,
   or user statement) and the explicit list of facts the method does NOT have.
2. **Constraints** — hard rules that cannot be broken. A candidate that
   fails a hard constraint is filtered out, not down-weighted.
3. **Goals** — the user's stated objective. The method does not invent goals;
   it asks when goals are missing.
4. **Candidates** — the set of interventions or reference cases the engine
   retrieves from knowledge.
5. **Trade-offs** — the explicit costs of choosing one candidate over another.
6. **Action** — recommend, ask a question, or refuse. The method never
   silently guesses.

## 4. Heuristics

The method follows these heuristics at every step.

- **Start with constraints, end with trade-offs.** A recommendation that
  ignores either is incomplete.
- **Show your unknowns before your recommendations.** The user can correct
  the unknowns; the user cannot correct a confident guess.
- **Return a set, not an oracle.** A ranked set with a recommended option,
  alternatives, and a "why not" is more useful and more honest.
- **Every score is decomposable.** A user should be able to see *why* one
  candidate outranks another. Single-number scores without components are
  refused.
- **Reproducibility is non-negotiable.** The same inputs (snapshot) MUST
  return the same outputs.
- **Refuse is a valid action.** When the inputs are too thin to defend a
  recommendation, the method returns a structured request for more
  information instead of inventing.

## 5. Vocabulary

- **TargetSpace** — the physical place being advised.
- **ReferenceCase** — a documented precedent used as evidence.
- **Intervention** — a candidate thing to place (an Object from
  `knowledge/objects/`).
- **Suitability** — the scored, constraint-aware fit of one intervention for
  one target space.
- **Hard constraint** — a rule whose violation excludes a candidate.
- **Soft preference** — a goal, weight, or ranking signal.
- **Unknown** — a fact the method does not have and is requesting.
- **Trade-off** — the cost paid for choosing one candidate over another.

## 6. Common Pitfalls

- **Skipping the constraint filter** and scoring invalid candidates.
- **Treating the highest embedding similarity as the best candidate.**
- **Hiding unknowns to look confident.**
- **Recommending one option when the user has not stated a clear goal.**
- **Generating concept imagery before the user has selected an intervention.**
- **Refusing to refuse.** A defensible "I need more information" is better
  than a guess.
- **Letting the theme override the constraint filter.** Theme is a soft
  preference; safety and footprint are hard constraints.

## 7. Cross-References

- `knowledge/decision_rules/Space_Decision_Principles.md` — the principles
  this method operationalises.
- `knowledge/objects/README.md` — the object library.
- `knowledge/taxonomy/theme/` — theme leaves with Recommended / Unsuitable /
  Alternative Objects.
- `docs/review/Architecture_Review_2026_07.md` — the architecture review
  that introduced the method's place in the system.
- 02_Expert_Rules.md — domain rules the method must respect.
- 09_Decision_Tree.md — concrete decision flows that implement the method.

## 8. Worked Example

**Input (compressed).**
- Target: a 600 m² corner of a public park, urban context, mixed-use, used by
  families and elderly neighbours.
- Stated goal: a place that gives children a reason to play and gives
  grandparents a place to sit and watch.
- Known constraints: flat ground, no power supply, partial shade, nearby
  residential, budget modest.
- Known unknowns: exact budget, soil condition, whether the local authority
  requires EN 1176, daily user counts.

**Step 1 — Evidence.** The method records observations (flat, partial shade,
urban) and unknowns (budget, soil, jurisdiction).

**Step 2 — Constraints.** Hard constraints are applied: footprint <= 600 m²,
no electrical equipment, fall-height safety surface where climbing exists,
no permanent noise or lighting disturbance for nearby residents.

**Step 3 — Goals.** The user has stated two goals: play value for children,
rest value for grandparents. The method treats both as soft preferences
and weights them by user statement.

**Step 4 — Candidates.** From the object library, the method retrieves
Treehouse, Slide, Reading_Corner, Interactive_Wall, IP_Sculpture. Slide and
Interactive_Wall are filtered out for hard-constraint reasons (Slide needs a
climbable structure that the flat site does not naturally provide;
Interactive_Wall needs power). Treehouse needs a structure the site does not
support either. Reading_Corner and IP_Sculpture pass the hard filter.

**Step 5 — Trade-offs.** The method computes:
- Reading_Corner: high rest value, high inclusion, low cost, low thrill.
- IP_Sculpture: high landmark, high brand, low rest, moderate cost.
- Neither alone satisfies both goals; the method proposes the combination.

**Step 6 — Action.** Recommendation = Reading_Corner (primary) +
IP_Sculpture (secondary, modest scale). Alternatives: a small wooden
climbing tower. Why-not: Slide rejected by hard constraint;
Interactive_Wall rejected by hard constraint; Treehouse rejected by
footprint. Unknowns returned as a structured request.

**Output.** Reproducible recommendation artifact with the input snapshot,
filter, weights, model versions, and candidate set recorded.

## 9. Open Questions

- [ ] How many recommendation candidates is the right number to return? 3
  to 5 is a working hypothesis.
- [ ] How does the method score "inclusivity" when the user does not
  specify? A default weight is needed.
- [ ] How does the method handle a target space that crosses two domain
  packs (e.g. a park that also wants art)?
- [ ] When the user changes a constraint mid-flow, does the method restart,
  or does it incrementally re-evaluate?

## 10. Maintenance

- A change to the method is a **breaking change** to the future engine.
  It must be reviewed and versioned.
- Worked examples must be added for every new failure mode observed in
  user tests or in the benchmark suite.
- The vocabulary section is the source of truth for engine-facing terms.
  If a term changes here, all related schemas and prompts must change
  together.
