# DP-001: Primary Function First

- **ID:** DP-001
- **Status:** Accepted
- **Date:** 2026-07-30
- **Layer:** Knowledge (Design Principle)
- **Pipeline Stage:** Goal Agent + Decision Maker Agent
- **Companion documents:**
  - `knowledge/decision_rules/Space_Decision_Principles.md` -- top-level principles
  - `docs/standards/CaseOS_Constitution_V1.md` -- philosophy
  - `docs/standards/CaseOS_Decision_Principles_V1.md` -- implementation guide

---

## Principle

Every space should first fulfill its primary function.

## Explanation

Before discussing aesthetics, style or decoration,
the primary purpose of the space must be satisfied.

If the primary function is unknown, CaseOS asks. CaseOS does
NOT infer a primary function from the site's prior use, the
supplier "s catalogue, or visual cues alone.

If a recommendation does not serve the primary function, it is
decoration -- and decoration is allowed only after the primary
function is served and the user has signalled budget for the
extra.

A primary function is not the same as a theme. A "Forest theme"
is a form, not a function. A "high-climb challenge course" may be
a function in one space and a distraction in another. Form
follows function, not the other way around.

### Examples

- **Children "s play space** -> Children must have meaningful play.
- **Commercial plaza** -> Customers must have reasons to stay.
- **Community space** -> Residents must have reasons to gather.

### Negative Examples

- A kindergarten rooftop receives a colourful plastic play set
  before outdoor class storage is solved. The play set is a
  decoration; the storage is the function.
- A heritage courtyard receives a stainless steel signature
  sculpture before visitor shading and seating are solved. The
  sculpture is the decoration; the shading is the function.
- A hospital healing garden receives a busy splash fountain
  before patient quiet and accessible paths are solved. The
  fountain is the decoration; the quiet is the function.

## Design Implication

Never recommend visual upgrades before the core function is established.

## Cross-references

- Constitution Principle 002 -- *Objects serve goals.*
- Constitution Principle 004 -- *Amplify the strengths of a space.*
- Decision Principle 003 -- *Content serves Purpose.*
- Space_Decision_Principles.md principle 8 -- *User "s stated goals win, within constraints.*
- ADR-005 Decision Intelligence (Goal Agent + Decision Maker Agent
  are the runtime home of this DP).
- ADR-006 Project Fit Intelligence (Project Fit confirms or
  surfaces the primary function before DP-001 fires).

## Maintenance

- A change to DP-001 is a breaking change to the Goal Agent and
  Decision Maker Agent. It must be reviewed and versioned.
- DP-001 does not enumerate what counts as a valid primary
  function. The vocabulary of primary functions belongs to the
  Goal Library (`knowledge/goals/`) and to the Domain Packs.
