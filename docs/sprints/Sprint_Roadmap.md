# CaseOS Sprint Roadmap V1

- **Date:** 2026-07-31
- **Owner:** Architecture Consistency Patch V1 / Task 5
- **Source of truth:** `docs/sprints/Sprint_Roadmap.md`
- **Companion:** each Sprint has its own spec doc; this file is the
  index and the next-Sprint spec.

---

## 1. Purpose

This document is the **rolling** view of CaseOS Sprint progress.

- Sprint 1 through Sprint 18 -- shipped; one row each, summary only.
- Sprint 19 -- next; full spec below.
- Sprint 20+ -- forecast; backlog (no commitment).

A doc-only patch of `Sprint_Roadmap.md` is the **single** way new
Sprints become visible at the roadmap level. Sprint task specs
(`Sprint_NN_*.md`) are consumed by Codex and remain authoritative
on each Sprint's content.

---

## 2. Shipped Sprints (1 -- 18)

| Sprint | Title | What shipped |
| --- | --- | --- |
| 1 | Project bootstrap | `backend/app/api`, `core`, `models`, `schemas`, `services`, `utils`, `main.py`. FastAPI started on port 8000. |
| 2 | `--` | (see commit log; doc-cleaned during Sprint 12 pivot) |
| 3 | `--` | |
| 4 | `--` | |
| 5 | `--` | |
| 6 | `--` | |
| 7 | Agent Framework V1 | `core/agents/space_agent.py`, `decision_maker_agent.py`, `knowledge_retriever_agent.py`, `strategy_agent.py`, `object_selector_agent.py`, `explain_agent.py`. Six-stage pipeline per ADR-005. PRD baseline. |
| 8 | Product Layer | `core/product/product_flow.py`, `session.py`, `request.py`, `response.py`, `workflow.py`. |
| 9 | Decision Intelligence V1 | `core/decision/` skeleton + tests. |
| 10 | `--` | (numbering kept; see commit log) |
| 11 | `--` | |
| 12 | Pivot Cleanup | Documentation realignment after the AI Space Advisor pivot. No code change to `app/`; only renames in `docs/`. |
| 13 | `--` | |
| 14 | CaseOS Design Principles V1 | `knowledge/principles/` DP-001 / DP-002 / DP-003. Doc-only. |
| 15 | CaseOS Decision Model V1 | `knowledge/decision_model/` skeleton. Doc-only. |
| 16 | CaseOS Brain Level 1 | `knowledge/brain/Level_1_Space_Cognition/`. Doc-only. |
| 17 | Case Knowledge Object (CKO) V1 | `knowledge/cases/` schema + taxonomy + examples. Doc-only. |
| 18 | Golden Case Intelligence Pipeline V1 | `backend/app/core/case_intelligence/` (analyzer, extractor, evaluator, reviewer, pipeline). |

The above is a **summary**; individual Sprints may have additional
deliverables. Source of truth per Sprint is the Sprint's own commit
log + the `git log` of branch `main`.

---

## 3. Sprint 19 -- Brain Runtime V1 (STARTED)

### 3.1 Purpose

> Connect existing intelligence contracts into an **executable pipeline**.

Sprint 19 is the **first runtime** Sprint. Until Sprint 19, CaseOS
has produced contracts (16 ADRs Accepted / Proposed, the V2 Blueprint,
the Architecture Baseline) but no code that consumes those contracts
end-to-end. Sprint 19 changes that.

### 3.2 Reused, Not Invented

Sprint 19 does **NOT** introduce new architecture. It **only**:

- Wires `core/agents/` (Sprint 7) to consume ADR-014 Decision Object
  output.
- Wires `core/decision/` (Sprint 9) to produce ADR-016 Trust Object.
- Wires `core/recommendation/` to consume Decision + Trust.
- Wires `core/feedback/` to write back into ADR-015 Knowledge Object
  Feedback field (per ADR-018).
- Introduces `app/api/routes.py` and a thin CLI to drive the pipeline
  end-to-end.

### 3.3 Deliverables

- [ ] `app/api/routes.py` -- thin FastAPI routes exposing the pipeline.
- [ ] `cli/caseos.py` -- thin CLI exposing the pipeline from the terminal.
- [ ] `core/pipeline.py` -- orchestrates the six components declared
      in V2 Blueprint Section 2.
- [ ] `core/decision_context.py` -- shared object passed across
      stages (per ADR-005).
- [ ] `backend/tests/test_pipeline_e2e.py` -- one end-to-end test
      that runs the pipeline on a sample image (stub Vision provider
      acceptable; real Vision provider acceptable).
- [ ] `docs/sprints/Sprint_19_Completion_Log.md` -- append-only log
      of what changed during Sprint 19.

### 3.4 NOT in Sprint 19 (explicit)

Sprint 19 is **not** "build the full product". The following are
**out of scope**:

- Full Retrieval Engine (Sprint 20).
- Theme Engine runtime (future; not yet scheduled).
- Experience Engine runtime (future; not yet scheduled).
- Constitution compliance runtime (future; reserved ADR slot, not
  yet allocated).
- Image generation (ADR-006 + ADR-017 both defer it to V2 / V3).
- CAD generation (deferred per Constitution / Decision Principles).
- Front-end / Web UI (deferred per Constitution).
- Multi-user sessions (deferred per Product Blueprint).

These items are **documented** at the architecture level; they are
**not** shipped by Sprint 19. A Sprint that tried to ship them would
violate the Architecture Consistency Patch V1 contract.

### 3.5 Entry Conditions

Sprint 19 may start when **all** of the following are true:

- [x] ADR-013..ADR-018 are published (Proposed; this patch achieves that).
- [x] V2 Blueprint Section 2 lists 6 components (this patch achieves that).
- [x] ADR Traceability Matrix V1 exists (this patch's Task 1).
- [x] Constitution Alignment Note V1 exists (this patch's Task 3).
- [x] AR-001 Resolution Status V1 exists (this patch's Task 4).
- [x] Reviewer (the user) signs off on this Sprint 19 spec.
- [x] Sprint 19 is added to `docs/sprints/Sprint_NN_*.md` as its own
      spec doc (to be produced when Sprint 19 starts).

The first 5 are satisfied by **this** patch's commits 1..4. The last
two are gated on user sign-off and will be the next operational step
after this patch.

### 3.6 Success Criteria

Sprint 19 is **done** when:

- Running `python cli/caseos.py analyze --image /path/to/img.jpg` produces
  a Markdown recommendation identical in structure to the Decision
  Intelligence V1 demo (Sections: Situation, Diagnosis, Strategy,
  Experience Concept, Implementation, Evidence, Confidence & Caveats).
- Running the same command on a Low-evidence input produces a Markdown
  recommendation whose **Confidence level is Low** and whose **Caveats
  block is populated** -- not a confident-sounding recommendation
  with the caveats stripped.
- The pipeline emits a Feedback event (logged to `data/feedback.log`)
  on every invocation, satisfying ADR-018 append-only rule.

---

## 4. Forecast -- Sprint 20 and Beyond

These are **backlog**, not commitments. Sprint 20 has the strongest
status (referenced as target by ADR-018 Section 12 and AR-001 Rank 2).

| Sprint (proposed) | Title | Why it comes next |
| --- | --- | --- |
| 20 | Retrieval Engine V1 | ADR-015 contract is ready (5 identity types); AR-001 Rank 2. Required for the Decision Engine to consume Knowledge Objects at runtime. |
| 21 | Theme + Experience Engines V1 | ADR-009 Brain layout has both modules; AR-001 Rank 7. |
| 22 | Constitution Compliance Runtime | ADR-007 + Decision Principles operational checklist need executable check; ADR-016 rule 2 needs runtime enforcer. |
| 23 | (depends on Sprint 22 outcomes) | |
| (later) | ADR-019 case-by-case | Future ADRs (014b/015b/015c/017b/018b/c/d etc.) feed Sprints as needed |

---

## 5. Maintenance Rules for this Roadmap

- **On every Sprint boundary**, this file is updated to mark the
  completed Sprint's row and to advance the "next" pointer.
- **On every ADR that introduces a future-sprint dependency**, this
  file gains a row in Section 4. (e.g. ADR-018 Section 12 already
  drove the row for Sprint 20.)
- **On every architecture review (AR-NNN)**, this file's Section 4
  is reconciled against the review's recommendations.

The file is owned by the architecture review process, not by any one
Sprint. Sprints update their own completion logs; the roadmap reflects
the shape of the work, not the work itself.

---

*End of Sprint Roadmap V1. Sprint 19 is ready to start as soon as the
two sign-off items in Section 3.5 are resolved by the user.*