# DP-002: Space First, Object Second

- **ID:** DP-002
- **Status:** Accepted
- **Date:** 2026-07-30
- **Layer:** Knowledge (Design Principle)
- **Pipeline Stage:** Space Agent
- **Format:** minimal (Principle only; the principle is self-evident
  enough to stand on its own, the five space axes live in the
  Space Agent spec, and worked examples live in the Expert Handbook).
- **Companion documents:**
  - `knowledge/decision_rules/Space_Decision_Principles.md` -- top-level principles
  - `docs/standards/CaseOS_Constitution_V1.md` -- philosophy
  - `docs/standards/CaseOS_Decision_Principles_V1.md` -- implementation guide

---

## Principle

Understand the space before choosing objects.

Objects exist to solve spatial problems.

They are never the starting point.

Design begins with space,
not equipment.

## Cross-references

- Constitution Principle 003 -- *Understand before recommending.*
- Constitution Principle 004 -- *Amplify the strengths of a space.*
- Decision Principle 002 -- *Space before Object.*
- Space_Decision_Principles.md principle 1 -- *Evidence before
  invention.*
- Space_Decision_Principles.md principle 2 -- *Hard constraints
  are not negotiable.*
- ADR-005 Decision Intelligence (Space Agent is the runtime home
  of this DP).

## Maintenance

- A change to the principle wording is editorial and does not
  require ADR.
- A change to the principle "s pipeline stage, or to the five
  space axes (dimensions, light / climate, surroundings, existing
  features, atmosphere), is breaking and requires ADR.
- The five space axes are operationalised by the Space Agent
  spec, not by this DP. If a future Sprint needs to add an axis
  (e.g. *acoustics*, *smell*, *seasonal use pattern*), it does so
  in the Space Agent spec and references this DP from there.
- Worked examples of the principle in action live in the Expert
  Handbook (`knowledge/expert_handbook/01_Space_Decision_Method.md`),
  not in this DP.
