# Sprint 22.3.3 — ADR-018 Architecture Stabilization V1

- **Date:** 2026-08-03
- **Sprint:** 22.3.3 (doc-only freeze)
- **Status:** COMPLETED
- **Owner:** ADR-018 Architecture Stabilization V1
- **Source of truth:** `docs/reviews/Sprint_22_3_3_Architecture_Stabilization_Report.md`
- **Related ADRs:** ADR-018 (Feedback Learning Loop Contract V1,
  Implemented (Runtime) / Waiting for Knowledge Evolution),
  ADR-020 (Knowledge Evolution Safety Principle V1, Proposed,
  created by this Sprint)
- **Sprint stack:** builds on 22.1, 22.2-A, 22.2-B, 22.3, 22.3.1,
  22.3.2

---

## 1. Summary

Sprint 22.3.3 is a **doc-only Architecture Freeze Sprint**.
It does **not** ship new runtime capability. It does **not**
ship Knowledge Evolution. It exists to:

1. Freeze the architecture that the Sprint 22.1 → 22.3.2
   runtime delivered.
2. Lock the four hard rules that the Feedback Learning Loop
   must obey from this point forward.
3. Publish ADR-020 (Knowledge Evolution Safety Principle V1)
   so that the future Sprint 22.4 has a written contract to
   implement against.

The sprint is the **safety bridge** between the runtime-completed
Feedback Learning Loop and the not-yet-implemented Knowledge
Evolution step. It does not narrow that bridge; it documents
exactly how wide the bridge is, and what is forbidden from
crossing it.

### 1.1 What was done

| Deliverable | File | Status |
| --- | --- | --- |
| ADR-018 updated (front-matter + Sections 14-17) | `docs/architecture/ADR-018-feedback-learning-loop.md` | DONE |
| ADR-020 created | `docs/architecture/ADR-020_Knowledge_Evolution_Safety_Principle_V1.md` | DONE |
| Traceability Matrix updated (ADR-018 status, ADR-020 row, Sprint 22.3.3 row) | `docs/architecture/ADR_Traceability_Matrix_V1.md` | DONE |
| V2 Blueprint updated (Section 8 ADR-018 status, ADR-020 row, historical placeholder note) | `docs/architecture/CaseOS_Intelligence_Architecture_V2.md` | DONE |
| Review Report (this file) | `docs/reviews/Sprint_22_3_3_Architecture_Stabilization_Report.md` | DONE |

### 1.2 What was NOT done

The following are explicitly out of scope and **must not** be
attempted in this Sprint or its direct follow-ups without a new
ADR:

- Knowledge Evolution runtime (deferred to Sprint 22.4)
- Knowledge Object field writes
- Retrieval ranking changes
- Decision / Trust / Recommendation rule changes
- Pipeline wiring changes
- Any new `backend/caseos/**` module
- Any new test code (the runtime is already covered by Sprint
  22.3.2 tests)
- LLM, embedding, vector DB, database, external API

---

## 2. ADR-018 Current Boundary (frozen by Sprint 22.3.3)

ADR-018 is now **Implemented (Runtime) / Waiting for Knowledge
Evolution**. The runtime is **frozen** pending Sprint 22.4.

### 2.1 Runtime shape

```
Feedback
   |
   v
Feedback Runtime              (Sprint 22.1, shipped)
   |
   v
Evaluation Layer              (Sprint 22.2-A, shipped)
   |
   v
Contradiction Detection       (Sprint 22.2-B, shipped)
   |
   v
Learning Proposal             (Sprint 22.3, shipped)
   |
   v
Human Review Gate             (Sprint 22.3.1, shipped)
   |
   v
Interpretation Policy         (Sprint 22.3.2, shipped)
   |
   v
ChangeIntent                  (Sprint 22.3.2, shipped)
   |
   v
(Future Sprint 22.4) Knowledge Evolution   -- NOT IN V1
```

### 2.2 Side-channel posture

The Feedback Learning Loop is a **side-channel**. It is not
inserted into:

```
Human -> Knowledge -> Retrieval -> Decision -> Trust
       -> Recommendation -> Output
```

The main pipeline is unaware of the loop. The loop is invoked
by an operator (or a future feedback tool) and writes only
to its own append-only stores. The runtime cannot call back
into the main pipeline; the only consumer of `ChangeIntent` in
V1 is the Markdown report and the future Evolution Transaction.

### 2.3 Hard rules (full text in ADR-018 Sections 14-17)

The four hard rules that the freeze locks are:

1. **Feedback is Side Channel.** No path
   `Feedback -> Decision` or `Feedback -> Recommendation`.
2. **Human Approval Boundary.** Every Knowledge change must
   pass through
   `Feedback -> Proposal -> Human Review -> ChangeIntent -> Evolution`.
3. **ChangeIntent is Last Safe Layer.** `ChangeIntent` is the
   single input to a future Evolution Transaction. It does
   not mutate any runtime state.
4. **Intelligence Authority Protection.** The loop never
   writes to `caseos.intelligence.decision`,
   `caseos.intelligence.trust`,
   `caseos.intelligence.recommendation`, or
   `caseos.knowledge.retrieval`. Knowledge Evolution may
   write only to the KO field that `ChangeIntent` named.

These four rules are non-negotiable. A future ADR is required
to relax any of them.

---

## 3. Future Knowledge Evolution Boundary (ADR-020)

ADR-020 (Knowledge Evolution Safety Principle V1) is the
**principle** that the future Sprint 22.4 must obey. It is
**Proposed** in V1; it becomes **Accepted** only when Sprint
22.4 ships a runtime that satisfies all five Mandatory Rules.

### 3.1 Core principle (one sentence)

> **Approved learning proposal may suggest knowledge evolution,
> but never directly mutate knowledge.**

### 3.2 Evolution Pipeline (target shape)

```
ChangeIntent
   |
   v
Evolution Transaction
   |
   v
Governance Validation
   |
   v
Knowledge Version Update
   |
   v
Audit Record
```

### 3.3 Mandatory Rules (full text in ADR-020 Section 3)

| Rule | Name | Summary |
| --- | --- | --- |
| 1 | No Direct Mutation | `Proposal -> Transaction -> Validated update`. Never `Proposal -> KO update`. |
| 2 | Version Required | KO has a `version` field; updates are `v1 -> v2`, never overwrite. |
| 3 | Audit Required | Every evolution records `before`, `after`, `reason`, `proposal_id`, `reviewer`, `timestamp`. Append-only. |
| 4 | Rollback Required | Any evolution is rollback-able by a new evolution that obeys the same rules. |
| 5 | No Intelligence Rewrite | Evolution does not modify Decision, Trust, Recommendation, or Retrieval. |

### 3.4 Inherited boundary

ADR-020 Rule 5 inherits and re-states ADR-018 Rule 4. The
combined boundary is the **single allowed write target** of
the entire Feedback Learning Loop. Any future ADR that proposes
a second write target is a hardening violation.

### 3.5 Status

| ADR | Status | Reason |
| --- | --- | --- |
| ADR-020 | **Proposed** | The principle is locked; the runtime (Sprint 22.4) is not yet implemented. Per spec: "不要标记 Implemented" |

---

## 4. Forbidden Paths

The following paths are **forbidden** by the architecture
freeze. They are listed verbatim from the spec and the
applicable ADR rule.

### 4.1 Path A — Feedback bypasses the loop

```
Feedback -> Decision
```

Forbidden by: **ADR-018 Rule 1** (Feedback is Side Channel).

The runtime has no listener that takes `Feedback` and feeds
it directly to the Decision Engine. Any future code that
wires this is a hardening violation.

### 4.2 Path B — Feedback bypasses the loop

```
Feedback -> Recommendation
```

Forbidden by: **ADR-018 Rule 1** (Feedback is Side Channel).

Symmetric to Path A. The Recommendation Engine has no
`Feedback` listener.

### 4.3 Path C — Approved proposal writes directly to KO

```
Approved Proposal -> Direct KO Mutation
```

Forbidden by: **ADR-020 Rule 1** (No Direct Mutation).

The required path is `Approved Proposal -> Transaction ->
Validated update`. A future implementation that does
`proposal.kO_field = new_value` directly is a hardening
violation.

### 4.4 Path D — Knowledge Evolution rewrites intelligence

```
Knowledge Evolution -> Decision Rule Rewrite
```

Forbidden by: **ADR-020 Rule 5** (No Intelligence Rewrite)
and **ADR-018 Rule 4** (Intelligence Authority Protection).

The future Evolution Transaction is allowed to write only to
the KO field that `ChangeIntent` named. It is not allowed to
mutate Decision, Trust, Recommendation, or Retrieval.

### 4.5 Path E — ChangeIntent mutates runtime

```
ChangeIntent -> KO write
ChangeIntent -> Decision write
ChangeIntent -> Trust write
ChangeIntent -> Recommendation write
ChangeIntent -> Retrieval write
```

Forbidden by: **ADR-018 Rule 3** (ChangeIntent is Last Safe
Layer).

`ChangeIntent` is a frozen dataclass. It cannot mutate anything
by construction. A future implementation that imports
`ChangeIntent` and calls a writer on it is a hardening
violation.

---

## 5. Sprint 22.4 Entry Conditions

Sprint 22.4 (Knowledge Evolution V1) is **NOT** part of this
Sprint 22.3.3. The current sprint's job is to publish the
principle; Sprint 22.4's job is to implement the runtime.

### 5.1 Pre-conditions (must be true before Sprint 22.4 begins)

1. ADR-018 is **Implemented (Runtime) / Waiting for Knowledge
   Evolution** — i.e. the runtime is shipped and frozen by
   Sprint 22.3.3. ✅
2. ADR-020 is **Proposed** — i.e. the principle is locked by
   Sprint 22.3.3. ✅
3. The `ChangeIntent` dataclass is frozen and AST-tested for
   forbidden prefixes — i.e. no runtime can mutate from a
   `ChangeIntent`. ✅
4. The Interpretation Policy supports only `boundary_update` and
   `principle_update` as `change_type` values. ✅ (Any other
   `change_type` returns `None`.)
5. All 112 Sprint 22.3.2 tests are green. ✅
6. No Sprint 22.x has modified `caseos.intelligence.*`,
   `caseos.knowledge.retrieval`, `caseos.knowledge.governance`,
   or `caseos.knowledge.intake`. ✅

### 5.2 Sprint 22.4 in-scope (the future)

When Sprint 22.4 begins, it must:

- Implement the **Evolution Pipeline**
  (`ChangeIntent -> Transaction -> Validation -> Version Update
  -> Audit Record`).
- Enforce the five ADR-020 Mandatory Rules by code, not by
  documentation alone.
- Add AST tests mirroring the Sprint 22.3.2
  `TestArchitectureBoundary` discipline.
- Promote ADR-020 from **Proposed** to **Accepted** when
  the Acceptance Criteria in ADR-020 Section 5 are all green.

### 5.3 Sprint 22.4 out-of-scope (the future)

The following are explicitly **out** of Sprint 22.4 scope:

- Automatic learning of any kind.
- LLM, embedding, vector DB, or database choices.
- Modifying the Feedback Runtime, Evaluation Layer,
  Contradiction Analyzer, Learning Proposal, Human Review
  Gate, or Interpretation Policy beyond what ADR-020 Rule 5
  allows.
- A second human approval step beyond what ADR-018 Rule 2
  already requires.
- A 22.4 sub-sprint to "skip" the Human Review Gate. ADR-018
  Rule 2 forbids it.

If Sprint 22.4 discovers a need to violate any of the above,
the sprint must **stop**, file a new ADR, and wait for ADR
approval before continuing.

---

## 6. Verification

This Sprint is doc-only. There are no new code modules and
no new test cases. The verification commands from the spec
section "Verification" are:

```bash
git diff --stat
git status
```

### 6.1 Scope check (this commit)

- **Files changed:** only files under `docs/`.
- **No backend code change.**
- **No new runtime module.**
- **No pipeline change.**
- **No test logic change.**
- **No Knowledge Object, Retrieval, Decision, Trust, or
  Recommendation change.**

### 6.2 ADR number consistency check

- ADR-018 sections 14-17 added without renumbering.
- ADR-018 status changed from `Proposed` to
  `Implemented (Runtime) / Waiting for Knowledge Evolution`
  in three places (ADR-018 front-matter, Traceability Matrix
  Section 3, V2 Blueprint Section 8).
- ADR-020 is the **next** slot after ADR-019. No slot is
  skipped.

### 6.3 Architecture boundary check

- The Interpretation Policy module
  (`backend/caseos/knowledge/feedback/interpretation/`) is
  unchanged by this sprint.
- The AST boundary tests in
  `backend/caseos/tests/test_feedback_interpretation.py`
  continue to pass (no source modified; no test modified).

---

## 7. Completion Report (per spec format)

```
Sprint 22.3.3 completed
Commit: <hash>

Files:
  M  docs/architecture/ADR-018-feedback-learning-loop.md
  +  docs/architecture/ADR-020_Knowledge_Evolution_Safety_Principle_V1.md
  M  docs/architecture/ADR_Traceability_Matrix_V1.md
  M  docs/architecture/CaseOS_Intelligence_Architecture_V2.md
  +  docs/reviews/Sprint_22_3_3_Architecture_Stabilization_Report.md

Code modified:      NO
Backend modified:   NO
Pipeline modified:  NO
ADR-018 updated:    YES
ADR-020 created:    YES
Tests:              N/A
Architecture freeze: PASS
```

---

## 8. Current ADR-018 Status

| ADR | Status (as of Sprint 22.3.3) | Reason |
| --- | --- | --- |
| ADR-018 Feedback Learning Loop Contract V1 | **Implemented (Runtime) / Waiting for Knowledge Evolution** | Runtime frozen by Sprint 22.3.3. The runtime layers (22.1 → 22.3.2) are shipped; Knowledge Evolution is the next step. |
| ADR-020 Knowledge Evolution Safety Principle V1 | **Proposed** | Principle locked by Sprint 22.3.3. Runtime implementation is gated on the future Sprint 22.4. |
| ADR-019 Evidence Retrieval Intelligence Principle V1 | **Proposed** | Pre-Sprint 20. Unchanged by this sprint. |

The Feedback Learning Loop is **runtime-complete but
evolution-incomplete**. The bridge between the two is
ADR-020. The bridge's safety rails are ADR-018 Sections
14-17 and ADR-020 Section 3.
