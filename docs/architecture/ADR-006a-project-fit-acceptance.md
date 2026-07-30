# ADR-006a: Project Fit Architecture -- Acceptance

- **Status:** Accepted
- **Date:** 2026-07-30
- **Supersedes:** -- (records the acceptance of ADR-006)
- **Superseded by:** --
- **Accepts:** ADR-006 (Project Fit Intelligence Architecture,
  originally Proposed 2026-07-30, generalisation landed same day)

---

## 1. Context

ADR-006 was Proposed on 2026-07-30. On the same day, after a
user-driven review, the doc was generalised: the original
investor-centric framing was replaced by a generic Project Fit
Architecture with five judgment dimensions (Space / Stakeholder /
Goal / Market / Resource) and a generic Non Goals sub-section
that does not bind the Project Fit Agent to a specific project
type, industry, or project entity.

The System Review on 2026-07-30 found (P0-2) that the ADR had
been left in the Proposed state for two days with no formal
acceptance decision. This amendment records the acceptance of
ADR-006 in line with the Constitution "s amendment procedure.

---

## 2. Decision

ADR-006 is **Accepted** with the following clarifications:

1. The Project Fit Agent described in ADR-006 is the **entry
   agent** of a future "Project Intelligence Layer" that sits between the
   Decision Maker Agent and the Knowledge Retriever Agent.
2. Other future agents of that layer (Commercial Evaluation,
   Budget, Safety, Education, Psychology, Fengshui) are explicitly
   out of scope for ADR-006. Each one gets its own ADR when it is
   proposed. ADR-006 "s Future Extension list is a wishlist,
   not a roadmap.
3. ADR-006 "s two-version history (v1, v2) is preserved in git
   history. The current text is the v2 generalised version.

---

## 3. Acceptance criteria

ADR-006 "s original 6 acceptance criteria (defined in the ADR "s section 11)
are restated and confirmed:

1. [x] Project Fit Agent "s input, output, and pipeline position are defined
   without ambiguity.
2. [x] ADR-006 does not conflict with ADR-005; the two are
   complementary (ADR-005 = how, ADR-006 = whether).
3. [x] Non Goals are explicit: no financial prediction, no market
   scraping, no project-entity binding.
4. [x] Future Extension is a wishlist, not a roadmap; each future
   agent gets its own ADR.
5. [x] The Project Fit Agent can be inserted into the existing
   pipeline without changing any existing agent interface.
6. [x] The framework is generic -- the same Project Fit Agent
   serves investor, owner, operator, government, and community
   projects.

---

## 4. Implementation plan

The Project Fit Agent is not yet implemented (no Sprint task has
addressed it). The first Sprint that touches it will:

- Add ackend/app/core/agents/project_fit_agent.py with a
  ProjectFitAgent class registered in AgentRegistry.
- Insert "project_fit" into the default pipeline at the position defined
  by ADR-006 (after decision_maker, before knowledge_retriever).
- Define the ProjectFitReport data class in
  ackend/app/core/decision/models.py.
- Add a Project Fit section to the Markdown report.
- Add a project_fit slice to DecisionContext.

This is on the roadmap but is NOT part of the 8-step System
Review follow-up plan. It will be addressed by a future
Sprint task.

---

## 5. References

- ADR-006 -- Project Fit Intelligence Architecture (the accepted
  doc, now Accepted).
- ADR-005 -- Decision Intelligence Architecture (the sibling
  layer; also amended by ADR-005a today).
- ADR-007 -- CaseOS Constitution V1 (the highest-level
  philosophy that ADR-006 inherits).
- System Review 2026-07-30 -- P0-2, the finding that motivated
  this acceptance amendment.
