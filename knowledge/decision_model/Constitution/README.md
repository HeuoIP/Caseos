# Constitution Bindings

> The Constitution "s bridge into the Decision Engine.
> Each binding records how one Constitution clause (or forbidden
> behavior) manifests in the Decision Engine "s reasoning.

## Purpose

The Constitution is **philosophy**. The Decision Engine is
**implementation**. Bindings are the **bridge**: each binding
records how one clause constrains, requires, or forbids a
specific part of the engine "s reasoning.

Without bindings, the Constitution "s clauses live in one
document and the engine "s behaviour lives in another, with no
trace between them. A future contributor who asks "where does
Constitution P001 (the most suitable) actually manifest in the
engine?" can find the answer in `P001_Suitability.md`, not in
a code-dive.

## What is a binding

A binding is a small file that documents, for one Constitution
clause:

1. **The clause** -- a one-paragraph statement of what the
   Constitution says.
2. **The stages it manifests in** -- which Decision Engine
   stage(s) the clause constrains.
3. **The manifestation rule** -- the specific rule the engine
   applies at those stages.
4. **The failure mode** -- the behaviour the engine must NOT
   exhibit if the clause is violated.
5. **The test that catches it** -- the future test that will
   fail when the manifestation rule is broken.

A binding is **declarative**. It does not say how to implement
the rule; it says what the rule means and where it applies.

## What lives here

| File | Binds to | One-line summary |
| --- | --- | --- |
| `P001_Suitability.md` | Constitution Principle 001 | The engine optimises for suitability, not beauty. |
| `P002_Value_To_Decision_Maker.md` | Constitution Principle 002 | The engine serves the decision maker "s goal, not the catalogue "s. |
| `P003_Understand_Before_Recommending.md` | Constitution Principle 003 | The engine observes before judging. |
| `P004_Amplify_Strengths.md` | Constitution Principle 004 | The engine amplifies, it does not cover up. |
| `Forbidden_Behaviors.md` | Constitution Section 4 | The seven hard constraints the engine must never break. |

## Source of truth

The Constitution itself lives at
`docs/standards/CaseOS_Constitution_V1.md`. The bindings here
do **not** redefine the Constitution; they only describe how
the engine implements it. When the Constitution is amended
(through ADR), the bindings must be reviewed and updated.

## Cross-cutting vs per-stage

Bindings are evaluated in two modes:

- **Per-stage.** The clause constrains one specific stage of
  the pipeline. The binding "s manifest rule applies only at
  that stage.
- **Cross-cutting.** The clause constrains the pipeline as a
  whole, regardless of stage. The binding "s manifest rule is
  checked continuously.

P002 (objects serve goals) is cross-cutting: it is checked at
Strategy, Object Selector, and Explain.

P003 (understand before recommending) is **ordering**: it
imposes the pipeline "s sequential structure.

The Forbidden Behaviors are **hard constraints**: a violation
is a pipeline-level abort, not a per-stage down-weight.

## Versioning

A binding is versioned with the Constitution. A change to a
binding follows the Constitution "s amendment procedure (ADR
+ version bump). A change to a binding "s **manifestation rule**
without a change to the underlying clause is a non-breaking
change to the engine; it should be versioned but does not
require ADR.

## Maintenance

- This folder is the **Constitution side** of the Decision
  Model. The pipeline side lives in `../Decision_Model_V1.md`.
- A new Constitution principle automatically requires a new
  binding file under this folder.
- A new Forbidden Behavior automatically requires an entry in
  `Forbidden_Behaviors.md`.
- A binding that has no test catching it is **unenforced** and
  must be marked as such in its Maintenance section.

## References

- `docs/standards/CaseOS_Constitution_V1.md` -- the source of
  truth for the principles being bound.
- `../Decision_Model_V1.md` -- the pipeline these bindings
  constrain.
