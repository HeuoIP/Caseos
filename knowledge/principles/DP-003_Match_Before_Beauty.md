# DP-003: Match Before Beauty

- **ID:** DP-003
- **Status:** Accepted
- **Date:** 2026-07-30
- **Layer:** Knowledge (Design Principle)
- **Pipeline Stage:** Object Selector Agent
- **Format:** minimal (Principle only; the five match dimensions
  are operationalised by the Object Selector spec, not by the DP).
- **Match Dimensions:** Space, User, Budget, Operation, Context.
  See "Maintenance" below for the dimension-set history.
- **Companion documents:**
  - `knowledge/decision_rules/Space_Decision_Principles.md` -- top-level principles
  - `docs/standards/CaseOS_Constitution_V1.md` -- philosophy
  - `docs/standards/CaseOS_Decision_Principles_V1.md` -- implementation guide

---

## Principle

A beautiful solution is not necessarily the right solution.

The first responsibility of design
is matching.

Matching:

- Space
- User
- Budget
- Operation
- Context

Beauty comes after fit.

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
- DP-001 -- the primary function (a.k.a. the user "s goal) is one
  input to the **Context** match dimension and must be identified
  before match scoring.
- DP-002 -- the **Space** match dimension needs the five space
  axes recorded by the Space Agent.
- ADR-005 Decision Intelligence (Object Selector Agent is the
  runtime home of this DP).
- ADR-006 Project Fit Intelligence (Project Fit is a pre-match
  filter, not a substitute for match scoring).

## Maintenance

### Match-dimension set (history)

The five match dimensions were tightened on 2026-07-30 from an
earlier draft:

| Earlier draft | Current | Why it changed |
| --- | --- | --- |
| Goal match | **Context** match | Goal identification is owned by DP-001. Folding "goal" into Context avoids duplicate pipelines and keeps the primary function as the upstream input, not a scoring axis. |
| Space match | **Space** match | Unchanged. |
| User match | **User** match | Unchanged. |
| Climate match | **Operation** match | Climate is one operational consideration (maintenance, replacement cycle, service life). Bundling climate with operation, cleaning, and safety checks is more teachable than splitting it out. |
| Budget match | **Budget** match | Unchanged. |

The new dimensions are: **Space, User, Budget, Operation, Context**.
The new shape is a five-test filter, not a five-axis score. A
candidate passes only when all five tests succeed at once.

### Amendment rules

- A change to the principle wording is editorial and does not
  require ADR.
- A change to the principle "s pipeline stage, or to the match
  dimension set (Space, User, Budget, Operation, Context), is
  breaking and requires ADR.
- Match scoring (weights, thresholds, tie-breakers, evidence
  requirements) lives in the Object Selector spec, not in this
  DP.
- Worked examples of match scoring in action live in the Expert
  Handbook (`knowledge/expert_handbook/08_Object_Value_Map.md`),
  not in this DP.
- The failure-mode vocabulary (beautiful-but-wrong, catalogue
  default, style monoculture, marketing-prose contamination)
  belongs in the Expert Handbook "s Negative Rules chapter, not
  in this DP.
