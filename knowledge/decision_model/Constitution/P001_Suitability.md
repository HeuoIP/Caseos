# P001 -- Suitability Binding

- **Binds to:** Constitution Principle 001 (*CaseOS exists to help
  every space find the most suitable content. Not the most
  expensive. Not the most beautiful. The most suitable.*)
- **Source of truth:** `docs/standards/CaseOS_Constitution_V1.md`
- **Stages it manifests in:** Project Fit, Strategy, Object
  Selector, Explain (cross-cutting).
- **Status:** Accepted, enforced by DP-003.

## Clause

Suitability is a **fit metric**, not a quality metric. CaseOS
optimises for suitability, judged against the space itself, the
people who use it, the people who decide about it, the market
around it, and the resources available.

A modest Treehouse in the right woodland will always beat a
flagship sculpture in the wrong mall.

## Manifestation rule

The engine ranks candidates by suitability, **not by aesthetics,
novelty, or catalogue coverage**.

- **Project Fit:** a project "s Recommended Direction must
  prefer the most suitable option among the surviving
  candidates, not the most attractive.
- **Strategy:** the design_direction field must reference a
  suitability argument (goal match, space match, user match,
  budget match, operation match, context match), not an
  aesthetic argument.
- **Object Selector:** candidate ranking uses the five-match
  test from DP-003 (Space, User, Budget, Operation, Context).
  Beauty ranks survivors; it does not rank candidates.
- **Explain:** the explanation prose must describe the
  suitability argument, not the aesthetics of the
  recommendation. Marketing language ("striking", "world-class",
  "iconic") is a violation.

## Failure mode

The engine recommends an aesthetically impressive object that
does not fit the space, the user, the budget, or the
operation. The user accepts because the recommendation reads
well in a PDF, then discovers on opening day that the object
does not work.

## Test that catches it

- For each top-3 recommendation, assert that the explanation
  cites at least one match dimension (Space, User, Budget,
  Operation, Context).
- For each top-3 recommendation, assert that the explanation
  contains no banned marketing vocabulary.
- For each Strategy, assert that the design_direction field is
  supported by at least one match-dimension argument.

## Cross-references

- Constitution V1, Principle 001.
- DP-003 (*Match Before Beauty*) -- the operational rule that
  enforces P001 at the candidate-object layer.
- ADR-005, ADR-006 -- the pipeline stages where this binding
  applies.
- `../Strategy_Model.md` -- where design_direction is set.
- `../Project_Fit_Model.md` -- where Recommended Direction is
  set.

## Maintenance

- This binding is **enforced** by DP-003 and by the future
  `test_constitution_compliance.py` suite.
- A change to the five match dimensions in DP-003 propagates
  here as a binding update.
