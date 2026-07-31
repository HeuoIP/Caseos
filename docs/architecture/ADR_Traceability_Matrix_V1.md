# ADR Traceability Matrix V1

- **Date:** 2026-07-31
- **Owner:** Architecture Consistency Patch V1
- **Source of truth:** `docs/architecture/ADR_Traceability_Matrix_V1.md`
- **Scope:** All Accepted + Proposed ADRs from ADR-005 to ADR-018.
- **Companion documents:**
  - `CaseOS_Intelligence_Architecture_V2.md` (the Blueprint now)
  - `CaseOS-Architecture-Baseline-V1.md` (the executing summary)
  - `AR-001_CaseOS_Architecture_Review_V1.md` (the review this matrix answers)

---

## 1. Purpose

CaseOS now has a non-trivial ADR corpus (16 documents, 17 including
ADR-007 which is encoded as the Constitution file rather than an
`ADR-007-*.md` filename). New readers cannot easily answer:

- What does each ADR decide?
- Who consumes the decision?
- What was the prior ADR it depended on?
- Which Sprint implemented it?

This matrix is the single page that answers those four questions for
all current ADRs. It exists so that:

- **a new engineer** can read this matrix, then jump straight to the
  ADRs they need (no need to read all 17),
- **a future Review** can diff this matrix against the current ADR
  corpus and instantly find orphans, dupes, and missing links.

---

## 2. Reading the Matrix

Columns:

- **ADR** -- file ID (zero-padded where applicable).
- **Title** -- short title (the filename minus the ADR-NNN prefix).
- **Status** -- `Accepted` | `Proposed` | `Merged-into`. ADR-005a and
  ADR-006a are amendments to ADR-005 and ADR-006 respectively; they
  are listed with their parent.
- **Purpose (one sentence)** -- the question this ADR answers.
- **Consumed by** -- who reads this ADR's output (decisions,
  products, agents, knowledge libraries).
- **Depends on** -- prior ADR(s) this ADR relies on.
- **Related Sprint** -- the Sprint that produced or extends this
  ADR. "Doc-only" means the ADR was its own delivery unit, not
  embedded in a Sprint.

---

## 3. The Matrix

| ADR | Title | Status | Purpose (one sentence) | Consumed by | Depends on | Related Sprint |
| --- | --- | --- | --- | --- | --- | --- |
| **ADR-007** | CaseOS Constitution V1 (encoded at `docs/standards/CaseOS_Constitution_V1.md`) | **Accepted (encoded)** | The highest-level philosophy of CaseOS (4 principles). | Every ADR that follows. Every Agent that ships. | -- | Constitution sprint (pre-ADR-numbered, pre-013) |
| **ADR-005** | Decision Intelligence Architecture | Accepted | The 6-stage Agent pipeline (Space -> Decision Maker -> Knowledge Retriever -> Strategy -> Object Selector -> Explain). | All 6 Agents in `backend/app/core/agents/`. Product Layer. | ADR-007 | Sprint 7 (Agent Framework) |
| **ADR-005a** | Decision Intelligence x Constitution Cross-Reference | Accepted | Binds 4 Constitution principles to specific Agent invocations. | ADR-005 | ADR-005, ADR-007 | Sprint 7 amendment |
| **ADR-006** | Project Fit Intelligence Architecture | Accepted | Adds a Project Fit Agent that decides whether to design at all. | ADR-005's pipeline. ADR-014's Decision Object. | ADR-007 | Sprint 8 (Product Layer overlap) |
| **ADR-006a** | Project Fit Architecture Acceptance | Accepted | Records user-driven generalisation from investor-centric to generic. | ADR-006 | ADR-006 | Sprint 8 amendment |
| **ADR-008** | Vision Output Schema -- Canonical V3 | Accepted | Single typed schema for Vision Analyzer output. | `backend/app/services/vision/`. ADR-015 (Knowledge Object Decision field). | ADR-007 | Schema-canonical sprint |
| **ADR-009** | Brain Knowledge Architecture | Accepted | Defines 9-module Brain layout (constitution, client, project_fit, cognition, experience, diagnosis, strategy, theme, recommendation). | All Brain modules in `knowledge/brain/`. Future agents that read Brain. | ADR-007 | Brain scaffolding sprint |
| **ADR-010** | Decision Rules Framework | **Proposed** | 8 categories of IF-THEN-BECAUSE reasoning rules. | Decision Engine (when wired). Currently **document-only, no engine consumes**. | ADR-007, ADR-009 | Decision Rules authoring sprint |
| **ADR-011** | CKO Learning Source & Value Model | Accepted | Where knowledge comes from (external excellent cases first) and the 5-axis learning value vector. | All Golden Cases. ADR-015 (Knowledge Object model). | ADR-007 | CKO V1 sprint |
| **ADR-012** | Case Evaluation Score V1 | Accepted | Adds Section 10 (intake + transferability) to CKO evaluation. | ADR-015 (Knowledge Object Identity). | ADR-011 | CKO V1 amendment |
| **ADR-013** | Human Understanding Engine Foundation V1 | **Proposed** | Foundational Engine: 3 signal sources, 4 model dimensions. | ADR-014 Decision Context; ADR-017 Recommendation variant selection. | ADR-007 | Doc-only (this patch) |
| **ADR-014** | Decision Intelligence Model V1 | **Proposed** | The judgment model: 7-step Expert Reasoning + Decision Object (7 fields). | ADR-017 (consumes Decision Object). ADR-018 (consumes Decision for promotion). | ADR-013, ADR-015 | Doc-only (this patch) |
| **ADR-015** | Knowledge Object Model V1 | **Proposed** | 9-field unified Knowledge Object with 5 Identity types; the spine of all knowledge. | ADR-014 (retrieval). ADR-018 (Feedback Loop writes here). | -- | Doc-only (this patch) |
| **ADR-016** | Intelligence Trust Model V1 | **Proposed** | Trust Object (5 fields) attached to every Decision; 3 confidence labels. | ADR-014 (Decision with Trust). ADR-017 (renders Trust). ADR-018 (Trust evolution). | ADR-014, ADR-015 | Doc-only (this patch) |
| **ADR-017** | Recommendation Engine V1 | **Proposed** | 7-section output template; 5 content types; 4 anti-patterns; audience variants. | Product Layer (renders). ADR-018 (consumes for feedback). | ADR-013, ADR-014, ADR-015, ADR-016 | Doc-only (this patch) |
| **ADR-018** | Feedback Learning Loop Contract V1 | **Proposed** | 4 feedback voices + 5 feedback types; Confidence / Boundary as independent levers; HITL thresholds. | ADR-015 (writes Feedback field). ADR-016 (writes Trust labels). ADR-014 (writes Decision Pattern). | ADR-014, ADR-015, ADR-016, ADR-017 | Doc-only (this patch) |

---

## 4. Orphan / Outlier Audit

Items found during this audit and their resolution:

1. **ADR-007 has no `docs/architecture/ADR-007-*.md` file** --
   resolved by reference. The Constitution is encoded at
   `docs/standards/CaseOS_Constitution_V1.md`. AR-001 review (5a0f6ad)
   flagged this. **Action:** this matrix and the Baseline Document both
   reference ADR-007 directly to the standards file. Future ADRs may
   still choose to publish a `ADR-007-constitution.md` pointer; that is
   a doc-only follow-up, not part of this patch.
2. **ADR-009 vs ADR-010 location conflict** -- AR-001 review flagged
   that ADR-010 was originally authored before the canonical Brain
   location was fixed. Both documents now reference each other;
   readers using the matrix above should treat **the file at
   `knowledge/brain/decision_rules/` as authoritative** for the
   Decision Rules contents and ADR-010 as the *contract* that names
   those rules. **No path change required** -- both are peers under
   the Brain layout.
3. **ADR-005 superseded by ADR-014?** -- No. ADR-005 is the **pipeline**
   (the agents and stages); ADR-014 is the **deep model** (the
   judgment shape). ADR-014 explicitly preserves ADR-005's pipeline
   (Section 8 Style Rules, Rule 1).
4. **ADR-013 vs ADR-011 overlap?** -- No. ADR-011 is about case-side
   knowledge (where the case's user logic lives); ADR-013 is about
   in-session user signals. The two together produce
   `situational_context`.
5. **ADR-016 "applicability" appears in ADR-015 too?** -- Yes; that is
   intentional. ADR-015's `applicability` is the *Knowledge Object's
   own* reusable-conditions field; ADR-016's `applicability` is the
   *Trust Object's* "match between current situation and prior
   knowledge" field. The fields share a name because they share a
   concept (applicability), but they are written on different objects
   by different processes. Future ADR-015b should disambiguate the
   schema names if confusion arises.

---

## 5. Sprint-to-ADR Coverage Map

For each Sprint that shipped, what ADR was either produced by or
extended by it:

| Sprint | ADRs produced or extended |
| --- | --- |
| 7 (Agent Framework) | ADR-005, ADR-005a |
| 8 (Product Layer) | ADR-006, ADR-006a |
| Brain scaffolding | ADR-009 |
| Decision Rules authoring | ADR-010 |
| CKO V1 | ADR-011, ADR-012 |
| Schema canonicalisation | ADR-008 |
| Constitution sprint | ADR-007 (encoded at `docs/standards/`) |
| Doc-only (this patch series) | ADR-013, ADR-014, ADR-015, ADR-016, ADR-017, ADR-018 |
| (proposed) Sprint 19 (Brain Runtime V1) | will consumer-wire ADR-009, ADR-010, ADR-013, ADR-014, ADR-015, ADR-016, ADR-017, ADR-018 |

---

## 6. Verification Checklist (run after this patch lands)

- [x] No ADR file is missing its purpose statement.
- [x] No ADR with status `Accepted` lacks a consumer.
- [x] No two ADRs cover the same decision field at conflict.
- [x] No ADR has a `depends on` reference to a non-existent ADR.
- [x] No orphan ADR reference remains except the known ADR-007
      (resolution entry above).
- [x] All Sprint references resolve to a Sprint doc under
      `docs/sprints/` (Sprint 19 does not yet exist; the matrix
      marks it as `(proposed)`).

---

*End of ADR Traceability Matrix V1. Next: V2 Blueprint Architectural
Update (Task 2 of this patch).*