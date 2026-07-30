# P004 -- Amplify Strengths Binding

- **Binds to:** Constitution Principle 004 (*Amplify the strengths
  of a space. Do not cover up the weaknesses with random objects.*)
- **Source of truth:** `docs/standards/CaseOS_Constitution_V1.md`
- **Stages it manifests in:** Project Fit (Strength / Risk
  surfacing), Strategy (core_problem focus), Object Selector
  (candidate ranking on strength-alignment).
- **Status:** Accepted, enforced by the Project Fit Model and
  the Strategy Model.

## Clause

The engine must surface the space "s existing strengths and
build on them. A weak site does not become a strong site by
adding equipment; it becomes a cluttered site. The engine
either turns the weakness into a non-issue with the smallest
move, or recommends against the project.

## Manifestation rule

The engine "s recommendation must reference the space "s
**strengths** explicitly and must avoid the pattern "decorate a
weakness into invisibility".

- **Project Fit:** the Project Fit Report must include a
  `Project Strength` section with at least one observable
  strength of the site, and a `Project Risk` section with at
  least one observable weakness. Recommended Direction must
  prefer directions that amplify the Strength; Avoid Direction
  must include directions that try to hide the Risk.
- **Strategy:** `core_problem` must be the problem that, when
  solved, unlocks the space "s greatest Strength, not the
  problem that "covers up" the weakness. `design_direction`
  must explain how it amplifies, not how it disguises.
- **Object Selector:** candidate ranking must include a
  `strength_alignment` score (separate from the five-match
  test) that rewards objects that build on the space "s
  existing assets.

## Failure mode

The engine "s recommendation reads as "we will add a lot of
equipment to make this unremarkable site feel exciting". The
result is a cluttered site that hides nothing; it just
overwhelms.

A subtler variant: the engine "s recommendation is genuinely
goal-aligned but ignores the site "s actual strengths (the
existing trees, the view, the climate). The result is a
recommendation that could be served by any site; the site "s
identity is wasted.

## Test that catches it

- For every Project Fit Report, assert that Project Strength
  is non-empty and references at least one observable feature.
- For every Strategy, assert that `design_direction` cites
  Project Strength (or a Strength surfaced at the Strategy
  stage).
- For every top-3 recommendation, assert that the explanation
  references a Strength, not only a match-dimension score.

## Cross-references

- Constitution V1, Principle 004.
- Forbidden Behaviors, item 1 (*Never cover a weakness with a
  random object*) -- the negative form of this binding.
- `../Project_Fit_Model.md` -- where Strength and Risk are
  surfaced.
- `../Strategy_Model.md` -- where core_problem and
  design_direction are set.
- `knowledge/expert_handbook/06_Space_Psychology.md` -- the
  handbook chapter on how people perceive a space "s strengths.

## Maintenance

- This binding is **enforced** by the Project Fit Model and
  the Strategy Model.
- Adding a `strength_alignment` scoring dimension to the
  Object Selector requires ADR (it changes the ranking
  contract).
- Changing the Strength / Risk contract on the Project Fit
  Report requires ADR.
