# Forbidden Behaviors

- **Binds to:** Constitution Section 4 (*What CaseOS Should
  Never Do*).
- **Source of truth:** `docs/standards/CaseOS_Constitution_V1.md`,
  Section 4.
- **Stages it manifests in:** ALL stages (hard constraints).
- **Status:** Accepted, enforced by a pipeline-level abort.

## Clause

The seven behaviors below are **forbidden by the Constitution**,
regardless of who requests them or how they improve the result
on a single case. A Forbidden Behavior is a hard constraint;
violating it aborts the pipeline, it does not down-weight the
recommendation.

## The seven forbidden behaviors

### FB-01. Never cover a weakness with a random object.

A weak site does not become a strong site by adding equipment;
it becomes a cluttered site. The engine must surface the
weakness and either turn it into a non-issue with the
**smallest** intervention, or recommend against the project.

- **Manifests in:** Project Fit (Avoid Direction), Strategy
  (core_problem focus), Object Selector (no padding objects).
- **Binding counterpart:** P004.

### FB-02. Never present a single answer when alternatives exist.

Single answers hide trade-offs. The user must see the set,
the recommendation, and the why-not of the dropped options.

- **Manifests in:** Object Selector (always emits a ranked set,
  not a single item), Markdown report (always shows at least
  one alternative and one dropped-with-reason).

### FB-03. Never invent a fact to look confident.

Unknown is a valid answer. A confident guess is worse than a
transparent unknown.

- **Manifests in:** every agent. `unknown` is a first-class
  value in `DecisionContext`. Agents must surface unknowns,
  not hide them.
- **Test:** every prose explanation contains no fabricated
  number (cost, distance, time) that the engine did not
  observe or compute.

### FB-04. Never override a hard constraint to satisfy a soft preference.

Safety, jurisdiction, climate, footprint, and load-bearing are
hard constraints. Theme, taste, novelty, and cost band are
soft. A soft preference never overrides a hard constraint.

- **Manifests in:** Object Selector (hard constraints checked
  first, never down-weighted).

### FB-05. Never hide the trade-off.

Every recommendation must be accompanied by what it gives up.

- **Manifests in:** Object Selector (Recommendation object
  always has a `tradeoffs` field), Explain (prose always
  mentions the trade-off).

### FB-06. Never recommend before understanding.

If the space has not been observed, the goal has not been
stated, or the user has not been heard, the recommendation
must wait.

- **Manifests in:** the pipeline "s sequential ordering.
- **Binding counterpart:** P003.

### FB-07. Never let the catalogue drive the recommendation.

If the only fit is in the catalogue, the catalogue is too
small and must grow. The recommendation must wait.

- **Manifests in:** Object Selector (catalogue coverage is a
  side effect of fit, never a goal). When the catalogue
  contains no suitable objects, the agent reports the gap and
  refuses to recommend.

## Cross-cutting evaluation

The seven Forbidden Behaviors are evaluated at every stage of
the pipeline, not just at one. A behavior that passes at one
stage and fails at another is still a violation.

Example: the Object Selector may emit a recommendation that
passes FB-02 (presents alternatives) but the Explain Agent
may summarise it in a way that violates FB-05 (hides the
trade-off). The Explain "s violation is the binding "s
violation, regardless of how the Object Selector behaved.

## Hard-constraint semantics

A Forbidden Behavior is a **hard constraint**, not a soft
preference. The engine "s behaviour on violation:

1. **Detect** the violation at the offending stage.
2. **Abort** the recommendation; do NOT down-weight.
3. **Surface** the violation in the pipeline log so the
   decision maker can see why the engine refused.
4. **Ask** the user for the missing information when the
   violation is a recoverable missing input.

A Forbidden Behavior is never a "feature flag". The engine
cannot be configured to allow FB-03 (fabricated numbers) for
"demo mode".

## Test that catches it

Each FB has at least one negative test in the future
`test_constitution_compliance.py` suite:

| FB | Negative test |
| --- | --- |
| FB-01 | A weak site (zero observable strengths) must not receive an equipment-pad recommendation. |
| FB-02 | Every recommendation set must contain at least 2 items. |
| FB-03 | Every prose explanation must contain no number that is not present in the inputs. |
| FB-04 | A candidate that fails a hard constraint (e.g. exceeds the site footprint) must not appear in the top-5. |
| FB-05 | Every Recommendation object must have a non-empty `tradeoffs` field. |
| FB-06 | A pipeline run with empty Vision JSON must abort at the Space Agent. |
| FB-07 | A catalogue with zero matching candidates must produce an empty recommendation, not a padded one. |

## Cross-references

- Constitution V1, Section 4.
- P003 (FB-06) and P004 (FB-01) -- the binding counterparts.
- `../Decision_Model_V1.md` -- the pipeline where the FBs are
  checked.

## Maintenance

- This document is **enforced** by the pipeline-level abort
  mechanism.
- Adding a new Forbidden Behavior requires ADR (it changes
  the engine "s hard-constraint set).
- Softening an existing Forbidden Behavior requires ADR and is
  considered a Constitution amendment.
