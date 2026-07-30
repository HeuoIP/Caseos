# DP-002: Space First, Object Second

- **ID:** DP-002
- **Status:** Accepted
- **Date:** 2026-07-30
- **Layer:** Knowledge (Design Principle)
- **Pipeline Stage:** Space Agent
- **Companion documents:**
  - `knowledge/decision_rules/Space_Decision_Principles.md` -- top-level principles
  - `docs/standards/CaseOS_Constitution_V1.md` -- philosophy
  - `docs/standards/CaseOS_Decision_Principles_V1.md` -- implementation guide

---

## Principle

Examine the space before proposing any object.

## Explanation

The same object produces different outcomes in different spaces.
Dimensions, light, climate, surroundings, and existing features
determine whether an object fits or fails.

A space can be enhanced, neutral, or ruined by an object.
Only the first outcome is acceptable.

A space record across five axes -- dimensions, light / climate,
surroundings, existing features, atmosphere -- is required before
any object candidate is admitted. If the user proposes an object
before describing the space, CaseOS answers the space questions
first.

The space record is part of the recommendation output. A
recommendation without a Space Summary is not reproducible and
must not be issued.

### Examples

- **A treehouse in a woodland** -> fits the canopy and the
  atmosphere. The same "treehouse" object on a rooftop is a
  contradiction.
- **A reading corner in a quiet alcove** -> fits. The same
  reading corner on a windy rooftop, near a busy road, is hostile.
- **A natural wood bench in a shaded rainforest path** -> fits.
  The same bench in equatorial full sun fails in two seasons.

### Negative Examples

- A 1.5 m slide is proposed for a 30 m² urban courtyard. The
  dimensions axis was skipped.
- A wooden bench is proposed for a salt-coast public terrace
  without a maintenance plan. The climate axis was skipped.
- A signature sculpture is proposed for a busy intersection
  with no seating. The surroundings and atmosphere axes were
  skipped.

## Design Implication

Never propose an object before recording the five space axes
(dimensions, light / climate, surroundings, existing features,
atmosphere).

## Cross-references

- Constitution Principle 003 -- *Understand before recommending.*
- Constitution Principle 004 -- *Amplify the strengths of a space.*
- Decision Principle 002 -- *Space before Object.*
- Space_Decision_Principles.md principle 1 -- *Evidence before
  invention.*
- Space_Decision_Principles.md principle 2 -- *Hard constraints
  are not negotiable.*
- Expert Handbook 01 Method, step 1 (Five-axis space observation)
  -- DP-002 is the knowledge that step 1 operationalises.
- Expert Handbook 06 Space Psychology -- atmosphere is a space
  attribute, not a decoration attribute.
- ADR-005 Decision Intelligence (Space Agent is the runtime home
  of this DP).

## Maintenance

- A change to the five axes (a new axis, or a re-ordering) is a
  breaking change to the Space Agent and to every recommendation
  that has cited a Space Summary. Versioned.
- DP-002 does not prescribe how to record a space; the Schema
  layer (`schemas/`) owns the recording shape.
