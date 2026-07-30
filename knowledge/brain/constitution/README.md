# Constitution

- **Module:** Constitution
- **Layer:** Brain (foundation)
- **Pipeline Position:** 0 (read by every downstream module)
- **Source of truth:** `docs/standards/CaseOS_Constitution_V1.md`
- **Status:** Accepted (Constitution V1, 2026-07-30)

## Purpose

Define the highest-level philosophy and constraints of CaseOS.
The Constitution is the permanent design philosophy every other
Brain module must obey. It is **not a how-to**. It is **not an
implementation guide**. It is the smallest set of beliefs that
defines what CaseOS is for, how it thinks, what it optimises
for, and what it must never do.

The Constitution is the **layer zero** of the Brain: it has no
inputs, and every other module reads from it.

## Core Principles

> **"方向对了，设计才有意义。**
> **设计应先解决正确的问题，再创造方案。"**
>
> (When the direction is right, the design has meaning.
> Design must solve the right problem before creating solutions.)

Four numbered principles, per the Constitution:

- **Principle 001** -- The most suitable, not the most beautiful.
- **Principle 002** -- Every recommendation must create value for
  the decision maker. Design serves decisions. Objects serve goals.
- **Principle 003** -- Understand before recommending.
- **Principle 004** -- Amplify the strengths of a space.

Plus **seven Forbidden Behaviors** (Constitution Section 4):

1. Never cover a weakness with a random object.
2. Never present a single answer when alternatives exist.
3. Never invent a fact to look confident.
4. Never override a hard constraint to satisfy a soft preference.
5. Never hide the trade-off.
6. Never recommend before understanding.
7. Never let the catalogue drive the recommendation.

## Decision Rules

1. **Constitution outranks everything.** A downstream module that
   contradicts a Principle is broken; the Principle must be
   enforced, not bypassed.
2. **Forbidden Behaviors are hard constraints.** A Behavior that
   is violated aborts the pipeline; it does not down-weight.
3. **Principles can only be amended by ADR.** A silent edit to a
   Principle is a Constitution violation.
4. **Principles apply across the pipeline.** A Principle checked
   only at one stage and not at another is unenforced.
5. **The Constitution can be referenced, not redefined.** This
   Brain module is a binding document; the source of truth is
   `docs/standards/CaseOS_Constitution_V1.md`.
6. **Layer ordering:** Constitution > Decision Principles > Top-
   Level Principles > Design Principles > Brain modules >
   Expert Handbook > Domain Packs.

## Inputs

None. The Constitution is the foundation. It has no inputs.

## Outputs

- The **four Principles** as decision constraints.
- The **seven Forbidden Behaviors** as hard constraints.
- The **layer ordering rules**.

Every downstream Brain module reads from this output. The
runtime pipeline enforces the outputs through
`knowledge/decision_model/Constitution/`.

## Examples

### Example 1: P003 binding -- sequencing

A future implementation wants the Object Selector (in
`recommendation/`) to run before the Space Agent (in
`space_cognition/`). This violates P003 (*understand before
recommending*). The Brain pipeline "s sequential ordering is a
binding manifestation of P003; the runtime must run Space
Cognition first.

### Example 2: FB-03 binding -- no invented facts

The Explain Agent (in `recommendation/`) wants to write a
cost number in its prose that is not in the inputs. This
violates FB-03 (*never invent a fact*). The Explain Agent must
either remove the number or mark it as `unknown`.

### Example 3: P001 binding -- suitability over beauty

The Object Selector ranks candidates by aesthetics (mirror-
finished stainless steel sculpture) over suitability (plain
wood bench in shade). This violates P001 (*the most suitable,
not the most beautiful*). The Object Selector must re-rank by
the five-match test (Space, User, Budget, Operation, Context),
with beauty as a tie-breaker only.

### Example 4: P004 binding -- amplify strengths

The Strategy module proposes adding a large climbing frame to
"liven up" a quiet memorial garden. This violates P004
(*amplify strengths, do not cover weaknesses*). The Strategy
must instead propose a smaller intervention that preserves the
garden "s quiet character.

## Cross-references

- `docs/standards/CaseOS_Constitution_V1.md` -- the source of
  truth for every Principle and Forbidden Behavior cited here.
- `docs/standards/CaseOS_Decision_Principles_V1.md` -- the
  four operational principles that operationalise the
  Constitution.
- `knowledge/principles/` -- the three must-not-skip DPs
  (DP-001, DP-002, DP-003).
- `knowledge/decision_model/Constitution/` -- per-Principle
  bindings for the Decision Engine.
- Every other module in `knowledge/brain/` -- the Constitution
  applies to all of them.

## Maintenance

- A change to a Principle is a Constitution amendment and
  requires ADR.
- A change to a Forbidden Behavior is a Constitution amendment
  and requires ADR.
- A change to the **layer ordering** is a Constitution
  amendment and requires ADR.
- A change to the **six-section template** (Purpose, Core
  Principles, Decision Rules, Inputs, Outputs, Examples) is a
  breaking change to the Brain "s interface and requires ADR.
- A change to this module "s Decision Rules (without changing
  the underlying Constitution) is allowed without ADR.
