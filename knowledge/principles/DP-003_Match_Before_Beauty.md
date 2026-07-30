# DP-003: Match Before Beauty

- **ID:** DP-003
- **Status:** Accepted
- **Date:** 2026-07-30
- **Layer:** Knowledge (Design Principle)
- **Pipeline Stage:** Object Selector Agent
- **Companion documents:**
  - `knowledge/decision_rules/Space_Decision_Principles.md` -- top-level principles
  - `docs/standards/CaseOS_Constitution_V1.md` -- philosophy
  - `docs/standards/CaseOS_Decision_Principles_V1.md` -- implementation guide

---

## Principle

Suitability precedes aesthetics.

## Explanation

A beautiful but mismatched object is worse than a plain but
matched one. "Match" means the object serves the goal, suits
the space, fits the user, respects the climate, and fits the
budget -- all at the same time.

Beauty is a secondary filter. It is applied only to candidates
that have already passed the five-match test. Beauty cannot
rescue a failed match: a beautiful object that fails any of the
five tests is dropped, not down-weighted.

A plain object that passes all five tests is a valid
recommendation. Plainness is not a flaw.

Beauty is judged along the dimensions the user has signalled
(style, theme, atmosphere, brand) -- never on the engine "s own
aesthetic preferences. The engine does not promote an
intervention to "universally beautiful".

### Examples

- **An ornate gilded sculpture in a quiet meditation garden** -> mismatch (style clashes with the atmosphere).
- **A cheap plastic slide in a luxury resort** -> mismatch (user-tier and brand-tier mismatch).
- **An industrial steel pergola in a derelict urban park** -> match (amplifies the existing industrial strength).
- **A natural wood bench on a shaded rainforest path** -> match (climate and atmosphere aligned).

### Negative Examples

- A striking stainless steel mirror-finish sculpture is proposed
  for a coastal public park. Salt air etches the mirror finish
  within weeks; the climate test fails.
- A premium signature play set is proposed for a low-budget
  neighbourhood park. The budget test fails.
- A bold red slide is proposed for a quiet hospice garden.
  The atmosphere test fails.
- A 4-metre climbing frame is proposed for a 40 m² courtyard.
  The dimension test fails.

## Design Implication

Never let beauty override fit. Beauty ranks survivors, not candidates.

## Cross-references

- Constitution Principle 001 -- *The most suitable, not the most
  beautiful.* This DP is the operational expression of that
  principle at the candidate-object layer.
- Constitution Principle 003 -- *Understand before recommending.*
- Decision Principle 004 -- *Recommend from the Decision Maker "s
  Perspective.* Marketing language in prose is the failure mode.
- Space_Decision_Principles.md principle 2 -- *Hard constraints
  are not negotiable.*
- Space_Decision_Principles.md principle 6 -- *Trade-offs must be
  visible.*
- DP-001 -- match cannot be evaluated before the primary
  function is identified.
- DP-002 -- match cannot be evaluated before the space is
  examined.
- Expert Handbook 03 Value Taxonomy -- the seven value dimensions
  are how match is measured.
- Expert Handbook 08 Object Value Map -- the bridge between
  candidate objects and the value dimensions.
- ADR-005 Decision Intelligence (Object Selector Agent is the
  runtime home of this DP).
- ADR-006 Project Fit Intelligence (Project Fit is a pre-match
  filter, not a substitute for it).

## Maintenance

- A change to the five-match tests (a new test, a re-ordering)
  is a breaking change to the Object Selector Agent and to
  every ranked recommendation that has cited a match score.
  Versioned.
- DP-003 does not prescribe how "beauty" is scored; the Visual
  Style Taxonomy (`knowledge/taxonomy/style/`) and the user "s
  stated style preference are the inputs. The engine does not
  invent a beauty score of its own.
