# CaseOS Architecture Baseline V1

- **Date:** 2026-07-31
- **Status:** Baselines the architecture after the Architecture
  Consistency Patch V1 (commits `8b6600a`...`96565fa`).
- **Source of truth:** `docs/architecture/CaseOS-Architecture-Baseline-V1.md`
- **Purpose:** One document a new engineer can read end-to-end and
  understand CaseOS V2. Deeper documents (ADRs, Blueprint,
  Traceability Matrix, Constitution Alignment Note, AR-001
  Resolution Status, Sprint Roadmap) are referenced; not inlined.

---

## 1. Executive Summary

CaseOS is an **AI Space Advisor**. The user's question is **"what is
the best thing to place in this space?"**; CaseOS answers it as a
**consultative recommender**, not as an image generator.

The system is built around **six intelligence components**:

1. Human Understanding Engine
2. Spatial Intelligence Engine
3. Decision Intelligence Engine
4. Trust Model
5. Recommendation Engine
6. Feedback Learning Loop

Each component declares **Input / Processing / Output / Consumer**.
None of the six is "isolated" -- every component has at least one
named Consumer and at least one named Producer. The architecture
review AR-001 (commit 5a0f6ad) found five such isolated modules;
that count is now zero.

Documentation phase (Phase 1 + Phase 2): **complete**. Runtime
phase (Phase 3): **starting at Sprint 19**.

---

## 2. Current Architecture

The current architecture is **declarative**. It consists of:

- **16 ADR documents** (`docs/architecture/ADR-005` through
  `ADR-018`) + ADR-007 (Constitution) encoded at
  `docs/standards/CaseOS_Constitution_V1.md`.
- **1 V2 Blueprint** (`CaseOS_Intelligence_Architecture_V2.md`)
  showing the six components and the data flow between them.
- **1 Traceability Matrix** (`ADR_Traceability_Matrix_V1.md`)
  recording consumer / dependency / sprint-link for each ADR.
- **1 Constitution Alignment Note** documenting that no
  contradiction was found between ADR-013..018 and the Constitution
  / Decision Principles.
- **1 AR-001 Resolution Status** mapping the AR-001 Rank 1-6
  findings onto today's state.
- **1 Sprint Roadmap** indexing Sprints 1-19.
- **1 Architecture Baseline** (this file).

The architecture does **not** yet include a runtime consumer of the
six components. That is Phase 3.

---

## 3. Core Intelligence Engines

| # | Engine | Question | Authority | Status |
| --- | --- | --- | --- | --- |
| 3.1 | Human Understanding | What does this person really want? | ADR-013 | Proposed |
| 3.2 | Spatial Intelligence | What does this space need? | ADR-008/009/010/011/012 + V2 Blueprint | Mixed |
| 3.3 | Decision Intelligence | What should we do? | ADR-005 + ADR-014 | Accepted / Proposed |
| 3.4 | Trust Model | Why should we trust this decision? | ADR-016 | Proposed |
| 3.5 | Recommendation Engine | How should we express the solution? | ADR-017 | Proposed |
| 3.6 | Feedback Learning Loop | (closes the loop) | ADR-018 | Proposed |

Each engine accepts the four-engine declaration discipline from V2
Blueprint Section 5: Input / Processing / Output / Consumer. The
Consumer column is non-empty for every engine (this is the answer
to AR-001 Rank 4 in spirit, although the **runtime** enforcement
that uses this declaration is a separate future ADR).

---

## 4. ADR Map

The full per-ADR map is `ADR_Traceability_Matrix_V1.md`. The
spine-relevant relationships are:

```
ADR-005  Decision pipeline              (ACCEPTED)
    |
    +-- ADR-005a  Constitution cross-ref (ACCEPTED)
    |
ADR-006  Project Fit                    (ACCEPTED)
    +-- ADR-006a  Project Fit acceptance (ACCEPTED)
    |
ADR-007  Constitution                   (ACCEPTED; encoded at standards/)
    |
ADR-008  Vision Output Schema           (ACCEPTED)
    |
ADR-009  Brain Knowledge Architecture   (ACCEPTED)
    |
ADR-010  Decision Rules Framework       (PROPOSED)
    |
ADR-011  CKO Learning Source            (ACCEPTED)
    +-- ADR-012  Case Evaluation Score   (ACCEPTED)
    |
ADR-013  Human Understanding Engine     (PROPOSED; this patch)
    |
ADR-014  Decision Intelligence Model    (PROPOSED; this patch)
    |
ADR-015  Knowledge Object Model         (PROPOSED; this patch)
    |
ADR-016  Trust Model                    (PROPOSED; this patch)
    |
ADR-017  Recommendation Engine          (PROPOSED; this patch)
    |
ADR-018  Feedback Learning Loop         (PROPOSED; this patch)
```

ADR-013..ADR-018 are the **six contracts** Phase 2 produced in this
patch. ADR-005..ADR-012 are the **existing spine** they compose with.

---

## 5. Data Flow

The runtime data flow is a single forward path with one closing arrow.
Section 4 of V2 Blueprint spells it out in full; here is the summary.

```
User Signal       --v--      Spatial Observation
   |                          |
   v                          v
Human Understanding    Spatial Intelligence
   \                          /
    +------ Decision --------+
              |
              v
            Trust
              |
              v
       Recommendation
              |
              v
           Feedback
              |
              +-- writes back to: Human Context / Knowledge Library / Decision Rules
```

Two design rules govern this flow:

1. Trust is mandatory between Decision and Recommendation. A Decision
   without a Trust Object does not enter the Recommendation Engine.
2. Feedback is the **only** mechanism allowed to update another
   engine's output. Feedback writes are append-only.

---

## 6. Runtime Direction

Phase 3 starts at **Sprint 19 -- Brain Runtime V1**. The Sprint is
spec'd in `docs/sprints/Sprint_Roadmap.md` Section 3. In summary:

- Six of the engine contracts (ADR-013..ADR-018) are **consumed** by
  Sprint 19 code; the contracts themselves are not redesigned.
- The runtime is exposed as a **thin CLI** (`cli/caseos.py`) and
  **thin FastAPI routes** (`app/api/routes.py`).
- A single end-to-end test demonstrates the four behavior truths
  the runtime must guarantee: (a) Confidence matches evidence;
  (b) Caveats appear when evidence is thin; (c) every invocation
  logs a Feedback event; (d) repository's existing components
  (Vision Analyzer, Agent Framework, Product Layer) are reused,
  not rewritten.

---

## 7. Implementation Priorities (ranked by AR-002 candidate criteria)

These are the items AR-002 should track. They are the same items as
AR-001 Rank 1-6, refreshed by `AR-001_Resolution_Status_V1.md`.

| Priority | Item | Owner | Today | Sprint target |
| --- | --- | --- | --- | --- |
| 1 | API / CLI surface | Sprint 19 pt 1 | Requires implementation | Sprint 19 |
| 2 | Retrieval Engine runtime | Sprint 20 owner | Resolved by architecture | Sprint 20 |
| 3 | Feedback system runtime | Sprint 19 pt 2 | Resolved by architecture | Sprint 19 |
| 4 | Theme Engine runtime | future owner | Resolved by architecture | ADR-019+ future Sprint |
| 5 | Experience Engine runtime | future owner | Resolved by architecture | ADR-019+ future Sprint |
| 6 | Constitution compliance runtime | future owner | Partly resolved; runtime check missing | ADR-N future Sprint |

The first three of these are **Phase 3 entry backlog** (must ship
before Phase 3 is "done"). The last three are **Phase 3 acceleration
backlog**.

---

## 8. Known Risks

Risks recorded by the Architecture Consistency Patch V1 review.

### 8.1 ADR-007 has no file pointer

ADR-007 (Constitution) is encoded at
`docs/standards/CaseOS_Constitution_V1.md`, not at the conventional
`docs/architecture/ADR-007-*.md` location. AR-001 flagged this; the
Traceability Matrix (Task 1) records the resolution path. **Risk:**
new engineers may not realise ADR-007 is an ADR. **Mitigation:**
a future doc-only commit may publish a `ADR-007-constitution.md`
pointer file. Not part of this patch.

### 8.2 Decision Principles V1 does not yet cite ADR-018 explicitly

`CaseOS_Decision_Principles_V1.md` is older than ADR-018; its
operational checklist (Section 4) lists 6 YES items; ADR-018's
HITL threshold table is implicitly a 7th. **Risk:** a new agent might
ship without satisfying the HITL threshold. **Mitigation:** Decision
Principles V2 will absorb the HITL item (forward note in
`Constitution_Alignment_Note_V1.md`).

### 8.3 ADR-009 vs ADR-010 path coexistence

ADR-010 was authored before the canonical `knowledge/brain/`
location was fixed by ADR-009. Both files coexist; readers should
treat the file under `knowledge/brain/decision_rules/` as the
authoritative **content** and ADR-010 as the **contract**. **Risk:**
mis-citation. **Mitigation:** the Traceability Matrix records this
explicitly (Section 4 item 2).

### 8.4 ADR-015 vs ADR-016 applicability name collision

ADR-015 has an `applicability` field; ADR-016 has an `applicability
match` field. Both are intentional; both refer to applicability
in different contexts. **Risk:** schema names may collide when
ADR-015b (software contract) is filed. **Mitigation:** ADR-015b
will rename / namespace the fields.

### 8.5 Six ADRs are Proposed

ADR-013..018 are still **Proposed**, not Accepted. They are **the**
contracts Phase 3 will consume. **Risk:** an Accepted ADR has had
at least one Sprint review. The Proposed status is honest about
this; it is not a defect. **Mitigation:** Sprint 19's review should
move each ADR from Proposed to Accepted, with the patch documenting
the consumption evidence.

---

## 9. Sprint 19 Entry Conditions

Sprint 19 may begin when the following conditions are met:

- [x] ADR-013..ADR-018 are published (this patch achieves it).
- [x] V2 Blueprint Section 2 lists six components (this patch achieves it).
- [x] ADR Traceability Matrix V1 exists (Task 1 of this patch).
- [x] Constitution Alignment Note V1 exists (Task 3 of this patch).
- [x] AR-001 Resolution Status V1 exists (Task 4 of this patch).
- [x] Sprint Roadmap V1 exists (Task 5 of this patch).
- [x] Architecture Baseline V1 exists (Task 6 of this patch, i.e. this file).
- [ ] Reviewer (the user) signs off on the Sprint 19 spec.
- [ ] Sprint 19 is added as its own spec doc at
      `docs/sprints/Sprint_19_Brain_Runtime_V1.md` (when Sprint
      19 actually starts).

The first seven are **satisfied** by the commits `8b6600a`..`96565fa`
just pushed by this patch. The last two are operational next steps;
they require the user's explicit go.

**One sentence:** Phase 1 (knowledge) and Phase 2 (intelligence contracts) are both closed by this patch. Phase 3 (runtime) is unblocked and ready to start the moment the user authorises Sprint 19.

---

*End of CaseOS Architecture Baseline V1.*