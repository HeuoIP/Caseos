# AR-001 Resolution Status V1

- **Date:** 2026-07-31
- **Owner:** Architecture Consistency Patch V1 / Task 4
- **Source of truth:** `docs/reviews/AR-001_Resolution_Status_V1.md`
- **Companion:** `docs/reviews/AR-001_CaseOS_Architecture_Review_V1.md` (5a0f6ad)

---

## 1. Purpose

AR-001 ranked six missing capabilities on 2026-07-30. This document
records, on 2026-07-31 (after ADR-013..018 and this patch), what
**status each finding now has**.

Three statuses are possible:

- **Resolved by architecture** -- a contract now exists; the runtime
  will consume it.
- **Requires implementation** -- a contract now exists; the runtime
  does not yet, and a Sprint is required.
- **Still missing** -- neither contract nor runtime exists; future
  ADR required.

---

## 2. The Six AR-001 Findings -- Resolution Status

### Finding 1 -- API / CLI surface (AR-001 Rank 1)

- **AR-001 verdict (30 Jul):** missing; the system has no entry point.
- **Today:** still missing at runtime.
- **Status:** **Requires implementation** (target Sprint 19 part 1).
- **Evidence:** AR-001 found `app/api/` empty, `app/main.py` serves only
  Swagger. ADR-005..ADR-018 are all contract-level; none of them
  introduce an API surface. Sprint 19 is the next planned Sprint to
  introduce a thin CLI and a routes file.

### Finding 2 -- Retrieval Engine (AR-001 Rank 2)

- **AR-001 verdict:** missing; cases library has schema but no retrieval.
- **Today:** contract-ready, runtime missing.
- **Status:** **Resolved by architecture, requires implementation.**
- **Evidence:**
  - ADR-015 Knowledge Object Model V1 introduces the unified memory
    unit (9-field object, 5 identity types).
  - ADR-016 Trust Model V1 introduces source-reliability labels that
    retrieval can rank against.
  - ADR-015c (reserved slot) is the explicit handoff to the Retrieval
    Engine.
  - Future Sprint 20 owns the runtime implementation.

### Finding 3 -- Theme Engine (AR-001 Rank 7a)

- **AR-001 verdict:** missing; `theme_strategy` Brain module has
  scaffolding but no engine reads it.
- **Today:** scaffolding only.
- **Status:** **Resolved by architecture, requires implementation.**
- **Evidence:**
  - ADR-009 Brain Knowledge Architecture includes `theme_strategy/`
    module with Place, Position, Characteristics, Emotion documents.
  - ADR-014 Decision Intelligence Model Section 6 ("Relationship with
    Golden Case") and ADR-015 Section 4 ("Knowledge Object Types V1")
    reference the Theme taxonomy in V2 Blueprint Section 6.
  - Theme Engine runtime = ADR-019+ (not yet allocated; reserved by
    ADR-018 Section 12 future-slot allocation).

### Finding 4 -- Experience Engine (AR-001 Rank 7b)

- **AR-001 verdict:** missing; `experience_perception` Brain module has
  scaffolding but no engine reads it.
- **Today:** scaffolding only.
- **Status:** **Resolved by architecture, requires implementation.**
- **Evidence:**
  - ADR-009 includes `experience_perception/` module.
  - ADR-014 Section 5 ("Expert Reasoning Pattern") references
    Experience Logic as a field of the Decision Object.
  - Experience Engine runtime = ADR-019+ (same slot allocation as
    Theme Engine; may share a Sprint).

### Finding 5 -- Constitution enforcement (AR-001 Rank 4)

- **AR-001 verdict:** missing; Constitution + Decision Principles
  have the rules but no executable check.
- **Today:** checklist exists; executable check does not yet.
- **Status:** **Resolved by architecture (Decision Principles +
  Constitution alignment note), requires implementation.**
- **Evidence:**
  - `CaseOS_Decision_Principles_V1.md` Section 4 has the operational
    checklist (6 YES items).
  - `docs/architecture/Constitution_Alignment_Note_V1.md` (this patch,
    Task 3) records the audit result.
  - ADR-016 rule 2 ("Trust Object is not optional") and ADR-014
    rule 5 ("A Decision is allowed to refuse") are **executable**
    assertions on Documents, expressed as writing rules rather than
    runtime checks.
  - Runtime enforcement = future Sprint ("Constitution Compliance
    Tests" was AR-001 Rank 4; renamed in the V2 Blueprint Section 8
    placeholder as a separate ADR slot, not yet allocated).

### Finding 6 -- Feedback system (AR-001 Rank 6)

- **AR-001 verdict:** missing; data flywheel declared but not wired.
- **Today:** contract-complete, runtime missing.
- **Status:** **Resolved by architecture, requires implementation.**
- **Evidence:**
  - ADR-018 Feedback Learning Loop Contract V1 introduces the full
    contract: 4 feedback voices, 5 feedback types, append-only rule,
    Human-in-the-Loop thresholds.
  - Sprint 19 part 2 is the targeted implementation Sprint (per ADR-018
    Section 12 "After this ADR, Sprint 19 Brain Runtime V1").

---

## 3. Status Summary Table

| Finding | AR-001 Rank | Status today | Owner |
| --- | --- | --- | --- |
| API / CLI surface | 1 | Requires implementation | Sprint 19 part 1 |
| Retrieval Engine | 2 | Resolved by architecture, requires implementation | Sprint 20 (ADR-015c) |
| Theme Engine | 7a | Resolved by architecture, requires implementation | ADR-019+ future sprint |
| Experience Engine | 7b | Resolved by architecture, requires implementation | ADR-019+ future sprint |
| Constitution enforcement | 4 | Partly resolved; runtime check still missing | ADR-N (not yet allocated) |
| Feedback system | 6 | Resolved by architecture, requires implementation | Sprint 19 part 2 |

---

## 4. Net Movement Since AR-001

AR-001 was a snapshot on commit `5a0f6ad`. This patch is on the
present head. Between them:

- 5 ADRs were filed (013..018, all Proposed).
- 1 V2 Blueprint was rewired (Section 2: 4-engine -> 6-component;
  Section 4: pipeline -> data flow; Section 7: Missing Capabilities
  -> Phase Definition).
- 1 traceability matrix was published (Task 1).
- 1 constitution alignment audit was recorded (Task 3).

Consequence for the six findings above:

- 0 findings went from "missing" to "still missing".
- 5 findings went from "missing" to "resolved by architecture,
  requires implementation".
- 0 findings were unaddressed.

The architecture phase (Phase 2 of Section 7 of V2 Blueprint) is
**documentation-complete**. The implementation phase (Phase 3) is
**starting at Sprint 19**.

---

## 5. What Would Re-Open AR-001 As An Open Finding

This status document is re-runnable. It will report the same
findings as long as no Sprint lands code that:

- exposes API / CLI (Finding 1)
- stores + retrieves Knowledge Objects at runtime (Finding 2)
- invokes Theme Engine on a request (Finding 3)
- invokes Experience Engine on a request (Finding 4)
- refuses a recommendation that violates Decision Principles (Finding 5)
- records a feedback event end-to-end (Finding 6)

Sprint 19 (planned) addresses Findings 1 + 6, not 2 / 3 / 4 / 5.
Sprint 20 (planned) addresses Finding 2. Findings 3 / 4 / 5 require
separate Sprints not yet scheduled.

This means: AR-001 is not yet **closed**; it is **progressing**.
A future review (AR-002) will close it when all six Findings reach
**Implementation Done**.

---

*End of AR-001 Resolution Status V1.*