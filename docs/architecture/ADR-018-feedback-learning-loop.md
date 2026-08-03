# ADR-018: CaseOS Feedback Learning Loop Contract V1

- **Status:** Implemented (Runtime) / Waiting for Knowledge Evolution
- **Date:** 2026-07-31 (updated 2026-08-03 by Sprint 22.3.3)
- **Layer:** Learning (the closing of the CaseOS intelligence loop)
- **Affects:** Knowledge Object lifecycle, Trust labels, Decision Pattern quality, future agent role
- **Related ADRs:** ADR-013 (Human), ADR-014 (Decision), ADR-015 (Knowledge Object), ADR-016 (Trust), ADR-017 (Recommendation), ADR-020 (Knowledge Evolution Safety Principle V1, Proposed)
- **Implements:** the **Feedback Learning Engine** declared in the V2 Blueprint Section 2.4 (was an "ADR slot pending" reference; now concretely numbered).
- **Supersedes:** none
- **Source of truth:** `docs/architecture/ADR-018-feedback-learning-loop.md`
- **Implementation frozen by:** Sprint 22.3.3 (ADR-018 Architecture Stabilization V1)
- **Triggers doc-only follow-up commit:** V2 Blueprint Section 8 placeholder table update + ADR-016/017 front-matter corrections to point at this slot allocation.

> **Reading note (model, not implementation).** Inherited from ADR-014 through ADR-017: this ADR defines **the shape of a feedback story and the rules of how feedback updates knowledge**. It does not define machine learning algorithms, analytics systems, queues, or UI tracking. Where an "event" appears below, it is a **kind of thing that happened** -- not a JSON event schema. Where "append-only" appears, it is a **trust-monotonicity rule** (mirroring ADR-016 rule 6), not a database write characteristic.

---

## Context

CaseOS Intelligence Architecture now includes:

- **ADR-013** -- Human Understanding Engine
- **ADR-014** -- Decision Intelligence Model
- **ADR-015** -- Knowledge Object Model
- **ADR-016** -- Intelligence Trust Model
- **ADR-017** -- Recommendation Engine

The system can:

- understand users,
- analyse spaces,
- create decisions,
- store knowledge,
- explain recommendations.

However, an intelligent system must **improve through real-world interaction**.

The purpose of ADR-018 is to define:

> How feedback from users, projects, and outcomes flows back into CaseOS intelligence.

This is the **closing loop** of the V2 Blueprint's four-engine model:
without it, the engines degrade into one-shot advisors; with it, they
become a **continuously-evolving brain**.

---

## Decision

Create **CaseOS Feedback Learning Loop V1**.

The Feedback Learning Loop transforms:

```
Human Response
   +
Project Outcome
   +
Expert Evaluation
              =
Knowledge Evolution
```

The three inputs above are the **three voices** of feedback. They are
not equal: Human Response and Project Outcome are observed; Expert
Evaluation is curated. The Loop treats them differently.

---

## 1. Feedback Principle

Feedback is **not only** satisfaction.

Feedback in CaseOS is **four-fold**:

### 1. Preference Feedback

**Question:** "What did the user prefer?"

Examples:

- selected option A
- rejected option B
- requested different style

### 2. Reason Feedback

**Question:** "Why did the user choose this?"

Examples:

- too expensive
- not suitable
- too ordinary
- beautiful but impractical

### 3. Outcome Feedback

**Question:** "What happened after implementation?"

Examples:

- children engagement increased
- parent response improved
- operation difficulty appeared

### 4. Expert Feedback

**Question:** "What does the professional think?"

Examples:

- good decision
- wrong diagnosis
- missed constraint

V1 recognises all four. The Loop **prioritises them in this order** when
updating Knowledge Objects:

1. Expert Feedback first (curated, slow, lowest volume, highest signal).
2. Outcome Feedback second (observed, slow, real-world).
3. Reason Feedback third (high-volume, requires interpretation).
4. Preference Feedback fourth (high-volume, often surface; can be
   misleading without Reason Feedback).

The ordering is the first place where naive "click-counting" disappears:
volume is not a proxy for value.

---

## 2. Feedback Loop Flow

```
Recommendation (ADR-017)
   ↓
User Interaction             (in the wild, OR in the product)
   ↓
Feedback Capture             (the Loop's intake)
   ↓
Feedback Interpretation      (which Knowledge / Trust field does this update)
   ↓
Knowledge Object Update      (ADR-015 fields: applicability, boundary, principle)
   ↓
Trust Adjustment             (ADR-016: source reliability, confidence)
   ↓
Future Decision Improvement  (closes back into ADR-014 Decision Engine)
```

This flow is **the closing arrow** of the V2 Blueprint's diagram. Until
this ADR, the diagram's closing arrow was labelled but had no contract.
ADR-018 is that contract.

---

## 3. Feedback Object Relationships

The Loop updates **three upper-layer ADRs** in turn.

### A. Knowledge Object (ADR-015)

The Loop may update three fields:

- **applicability** -- "we now know this applies to project types X, Y, Z"
- **boundary**    -- "we now know this does NOT apply when condition W"
- **principle**   -- "we now know this principle is more nuanced: ..."

Example:

> A successful case reveals: "This pattern works better for small kindergartens than large commercial parks."

The Loop adds the new applicability condition; the Boundary field is
written so the Decision Engine refuses to apply the pattern to large
commercial parks without re-evaluation.

### B. Trust Model (ADR-016)

The Loop may update:

- **source reliability** (the qualitative label set on the source at intake)
- **confidence** of any future Decision in which this Knowledge Object participates

Example:

> Repeated successful application of a Knowledge Object promotes the
> source's `real-project-completed` label from a singular count to a
> recurring count, and the Decision Engine's Confidence Level rises
> accordingly.

### C. Decision Intelligence (ADR-014)

The Loop may update:

- **decision pattern** -- if the same Situation-Diagnosis-Decision triplet
  recurs and is consistently endorsed by expert feedback, the triplet is
  promoted to a **trusted Decision Pattern**.
- **reasoning quality** -- if a Reasoning field is repeatedly understood
  by customers and never contradicted by outcome feedback, the Reasoning
  field's quality score increases.

The Loop **does not** revise a Decision Object's **Strategy** or
**Boundaries** field directly. Those fields are updated through the
Knowledge Object boundary mechanism (A above), which is the only path
allowed to reach a Decision's Boundary field.

---

## 4. Feedback Types

Five Feedback Types are recognised in V1. Each maps to a way the Loop
interprets an incoming event.

### 1. Positive Confirmation

> The decision worked.

Effect: prefer this Knowledge / Decision / Trust in future retrievals.

### 2. Negative Correction

> The decision failed or was unsuitable.

Effect: trigger **review**, **do not** immediately demote. (See
Section 5 Principle 2.)

### 3. Preference Signal

> User preference changed understanding.

Effect: enrich Human Context (per ADR-013) **and** mark which existing
Knowledge Objects benefit from this preference shift.

### 4. Unexpected Discovery

> New knowledge appeared.

Effect: requires **expert feedback** before promotion to a new
Knowledge Object. Discovery alone does not enter the library.

### 5. Contradiction Signal

> Existing knowledge conflicts with reality.

Effect: highest priority for Expert Feedback. A contradiction is the
**only** signal type that can veto an existing Boundary field.

The five types together replace the temptation to treat all feedback
as a single "rating" signal. V1 does not have ratings.

---

## 5. Learning Rules

### Principle 1

> Feedback updates knowledge, not just records activity.

A counter on a Knowledge Object that has no Knowledge consequence is
not a Feedback event; it is dead data. The Loop **only** records what
it intends to change.

### Principle 2

> One negative outcome does not delete knowledge.

It triggers **review**. The Boundary mechanism of ADR-015 Section 8
is invoked, and the field is rewritten to capture the new constraint
that prevented the negative outcome. Knowledge disappears only by
**Deprecation** (per ADR-015 lifecycle), never by deletion.

### Principle 3

> Repeated evidence changes confidence gradually.

Confidence is **not** a single flipped bit. It rises and falls with the
**trailing evidence count** over time. Single events change nothing;
trend changes everything. This is consistent with ADR-016 rule 6
("Trust is monotonic in time, only with a written reason").

### Principle 4

> Feedback can challenge existing assumptions.

When feedback contradicts a long-standing Principle, the Loop surfaces
the contradiction to **Expert Feedback** first; it does **not** route
straight into a Knowledge update. Expert Feedback is the firewall
between noisy real-world signals and the curated library.

---

## 6. Feedback and Trust Evolution (worked example)

### Initial state

```
Knowledge Object:
    Principle : "Natural exploration spaces improve parent perception."
    Evidence  : 3 cases.
    Confidence: Medium.
```

### After 20 successful projects + positive feedback

```
Knowledge Object:
    Principle : unchanged.
    Evidence  : 23 cases (3 + 20).
    Confidence: High.
```

The Principle was **not edited**; the supporting evidence count rose;
Confidence moved up.

### After multiple failures

```
Knowledge Object:
    Principle : unchanged.
    Evidence  : 23 cases; 4 contradictions.
    Boundary  : REVISED. New clause: do not apply when the site's
                daylight exposure is constrained (most failures
                had this in common).
```

The Principle is **unchanged**. The Boundary mechanism absorbed the
new constraint. The next time the Decision Engine consults this
Knowledge Object, the Boundary veto will fire before the Decision is
formed.

This is the entire feedback story in two graphs: **Confidence and
Boundary are independent levers**. Positive feedback moves Confidence;
negative feedback moves Boundary. Neither erases the underlying
principle.

---

## 7. Human-in-the-Loop Principle

CaseOS does **not** blindly self-modify.

> Important knowledge changes require **expert review** or **strong repeated evidence**.

### V1 thresholds

| Change | Required signal |
| --- | --- |
| Move Confidence from Medium to High | >= 20 successful outcomes OR >= 3 expert confirmations |
| Move Confidence from High to Medium | a single contradiction triggers **review only**; demotion waits for >= 3 expert-approved contradictions |
| Edit a Principle field | always requires **expert feedback**, regardless of evidence volume |
| Edit a Boundary field | a Contradiction Signal + **expert feedback** |
| Create a new Knowledge Object | expert feedback required (per Section 4 type 4) |
| Deprecate a Knowledge Object | expert feedback required |

These thresholds are **explicit** so that no engineer in the future
wonders what "strong evidence" means. The numbers are V1 starting
points; revisions to them are themselves an ADR.

---

## 8. Anti-Patterns

The Loop must avoid, explicitly:

### 1. Counting clicks as intelligence.

A "clicked-thrice" Knowledge Object is not necessarily a better one.
Volume does not justify promotion.

### 2. Optimising only for popularity.

Popular decisions are not always correct decisions. The Loop preserves
the Expert Feedback channel as a firewall against popularity bias.

### 3. Deleting unpopular but valuable knowledge.

Deprecation requires Expert Feedback (per Section 7). The Loop
**never** removes a Knowledge Object on popularity grounds alone.

### 4. Learning from low-quality feedback.

Reason Feedback ("too ordinary", "not suitable") needs interpretation
before it updates anything. The Loop runs Reason Feedback through
**Feedback Interpretation** (Section 2) before letting it touch a
Knowledge field. Raw Reason Feedback never writes to fields directly.

These four anti-patterns are the V1 floor. New anti-patterns found in
production will be added by future ADR, not silently merged in.

---

## 9. Complete Intelligence Loop

The closed loop that CaseOS V2 has been pointing at:

```
Human Understanding       (ADR-013)
   ↓
Spatial Intelligence     (V2 Blueprint / ADR-008)
   ↓
Decision Intelligence    (ADR-014)
   ↓
Trust Evaluation         (ADR-016)
   ↓
Recommendation           (ADR-017)
   ↓
Human Response           (the world)
   ↓
Feedback Learning Loop   (this ADR-018)
   ↓
Knowledge Evolution      (writes back into ADR-015 + ADR-016 + ADR-014)
```

This loop is the **diagrammatic answer** to AR-001's complaint that
five engine sections were "isolated". After ADR-018 lands, every
engine has at least one writing arrow that lands somewhere; nothing
is a dead end.

---

## 10. Architectural Style Rules (inherited + new)

Inherited from V2 Blueprint + ADR-014..ADR-017:

1. The Loop **only writes** into fields explicitly named in Section 3.
   It is forbidden from inventing new Knowledge fields.
2. The Loop **never deletes** a Knowledge Object; only deprecation is
   permitted (per Section 7).
3. The Loop honours Confidence of every Decision it modifies.

New rule added by this ADR:

4. **The Loop is append-only.** Every feedback event is logged before
   it takes effect. A feedback event is never overwritten; corrections
   arrive as a *new* event (a Contradiction Signal), not by editing
   history. This mirrors ADR-016 rule 6 and ADR-015 rule 6 (Feedback
   field is append-only).

---

## 11. Non-Goals (explicit)

ADR-018 does **NOT** define:

- machine learning algorithms,
- database implementation,
- analytics systems,
- UI tracking,
- persona modelling,
- LLM-based feedback interpretation,
- automatic Knowledge Object creation.

The Loop is a **contract**, not an implementation. The contract names
**what changes, when, and why** -- not which database table it writes
to. Future ADR slots 018b / 018c (declared in Section 12) will turn
the contract into event types, store, and interpretation policy.

---

## 12. Future Extensions (in declared order)

| Slot | Topic | Note |
| --- | --- | --- |
| **ADR-018b** | Feedback Event Types V1 | Concrete taxonomy of event names the Loop recognises; locked to Section 4's five types. |
| **ADR-018c** | Feedback Store V1 | Append-only storage shape for events. |
| **ADR-018d** | Feedback Interpretation Policy V1 | The rules that turn Reason Feedback text into field updates. |
| **ADR-019** | CaseOS Memory Architecture V1 | Cross-cutting: aggregates the four engines' state into a per-user, per-project **memory model** that the four engines all read. |
| **doc-only** | **Architecture Consistency Patch** | V2 Blueprint Section 8 placeholder table update to reflect actual ADR allocation; ADR-016 / ADR-017 front-matter corrections. Triggers after this commit. |
| (after patch) | **Sprint 19** | Brain Runtime V1. Wires the four engines + Trust + Recommendation + Feedback into one runnable pipeline (per AR-001 Rank 1 + Rank 3 + Rank 5). |

The Architecture Consistency Patch **belongs in the same change set**
as this ADR per the spec's "Future Extensions" instruction. The patch
is implemented as a separate doc-only commit immediately after this
ADR lands, so this ADR's own diff is single-purpose.

---

## 13. Acceptance Criteria

This ADR is complete when:

1. CaseOS has a closed intelligence loop -- **DONE** by Section 9.
2. Feedback can improve Knowledge Objects -- **DONE** by Section 3.A
   and Principle 1.
3. Trust can evolve from evidence -- **DONE** by Section 6 worked
   example and the Confidence / Boundary independent-lever model.
4. Future decisions can become better than previous decisions
   -- **DONE** by the principle that **Confidence and Boundary are
   independent levers**, neither of which erases the underlying
   principle.

A future reviewer can read Sections 5 (Principles), 6 (worked
example), and 7 (thresholds) and reproduce how a single negative
outcome **does not** delete knowledge but **does** lead to a Boundary
revision. If they can do that, ADR-018 has done its job.

---

*End of ADR-018. After this lands, the next commit is the doc-only Architecture Consistency Patch (V2 Blueprint Section 8 + ADR-016/017 front-matter references). Then Sprint 19 (Brain Runtime V1).*
﻿
---

## 14. Feedback Learning Loop Architecture V1 (Sprint 22.3.3 update)

This section freezes the architecture that the Sprint 22.1 → 22.3.2
runtime delivered. It is the **post-implementation mirror** of
Section 9's abstract loop, and is the source of truth for the
Sprint 22.3.3 Architecture Freeze.

The runtime sequence is:

```
Feedback
   |
   v
Feedback Runtime              (Sprint 22.1)
   |
   v
Evaluation Layer              (Sprint 22.2-A)
   |
   v
Contradiction Detection       (Sprint 22.2-B)
   |
   v
Learning Proposal             (Sprint 22.3)
   |
   v
Human Review Gate             (Sprint 22.3.1)
   |
   v
Interpretation Policy         (Sprint 22.3.2)
   |
   v
ChangeIntent
   |
   v
(Future Sprint 22.4) Knowledge Evolution
```

### 14.1 Module Map

| Stage | Module path | Sprint |
| --- | --- | --- |
| Feedback Runtime | `backend/caseos/knowledge/feedback/` | 22.1 |
| Evaluation Layer | `backend/caseos/knowledge/feedback/evaluation/` | 22.2-A |
| Contradiction Detection | `backend/caseos/knowledge/feedback/evaluation/analyzer.py` | 22.2-B |
| Learning Proposal | `backend/caseos/knowledge/feedback/proposal.py` | 22.3 |
| Human Review Gate | `backend/caseos/knowledge/feedback/review/` | 22.3.1 |
| Interpretation Policy | `backend/caseos/knowledge/feedback/interpretation/` | 22.3.2 |
| `ChangeIntent` (object) | `backend/caseos/knowledge/feedback/interpretation/object.py` | 22.3.2 |
| Knowledge Evolution | (not yet implemented) | (Sprint 22.4) |

### 14.2 Implementation Status

The runtime is **Implemented** from `Feedback` through `ChangeIntent`.
Knowledge Evolution is the **next** Sprint and is **NOT** in this
ADR's scope. The runtime is **frozen** pending Sprint 22.4.

The freeze means:

- The runtime layer accepts no new features between Sprint 22.3.3
  and Sprint 22.4 (Knowledge Evolution).
- Bug fixes are allowed; architecture changes require a new ADR.
- The boundary is held by AST tests in every interpretation
  module (see Sprint 22.3.2 `TestArchitectureBoundary`).

### 14.3 Pipeline Position

The Feedback Learning Loop is a **side-channel**. It is not
inserted into the main pipeline:

```
Human -> Knowledge -> Retrieval -> Decision -> Trust
       -> Recommendation -> Output
```

The loop is invoked by an operator (or a future feedback tool)
and writes only to its own append-only stores. The main
pipeline is unaware of the loop's existence.

---

## 15. Architecture Hard Rules (Sprint 22.3.3 freeze)

These four rules are the **architectural floor** of the Feedback
Learning Loop. They are non-negotiable and apply to every
implementation Sprint that touches the loop. Each rule is
enforced by either an AST test, a frozen dataclass contract,
or a code-review discipline. A future ADR is required to relax
any of them.

### Rule 1 — Feedback is Side Channel

Feedback is **NOT** part of the Intelligence Runtime. The
runtime pipeline is:

```
Human -> Knowledge -> Retrieval -> Decision -> Trust
       -> Recommendation -> Output
```

The forbidden connections are:

```
Feedback -> Decision        (FORBIDDEN)
Feedback -> Recommendation  (FORBIDDEN)
```

The only path from Feedback to the runtime is:

```
Feedback -> Learning Loop -> ChangeIntent -> (Future) Knowledge Evolution
```

`ChangeIntent` is a *proposal* to a future Knowledge Evolution
sprint. It is **not** an authority in the runtime. It carries
no write capability to Decision, Trust, or Recommendation.

### Rule 2 — Human Approval Boundary

There is no path:

```
AI feedback -> Automatic learning
```

Any Knowledge Object change must pass through:

```
Feedback -> Proposal -> Human Review -> ChangeIntent -> Evolution
```

`requires_human_review=True` is enforced in V1 at three
independent layers:

- the proposal layer (`LearningProposal.requires_human_review`),
- the review layer (`ReviewManager.approve` requires a
  `reviewer` argument),
- the interpretation layer
  (`InterpretationPolicy.interpret` returns `None` when the
  proposal has `requires_human_review=False`).

It cannot be turned off in V1. A future ADR may relax this rule
only after the V1 architecture has produced a measurable
track record of human-approved evolutions.

### Rule 3 — ChangeIntent is Last Safe Layer

`ChangeIntent` is the **only** input that a future Knowledge
Evolution sprint is allowed to consume.

`ChangeIntent` itself is **read-only** with respect to:

- Knowledge Object fields,
- Corpus,
- Retrieval ranking,
- Decision Engine state,
- Trust Engine state,
- Recommendation Engine state.

A `ChangeIntent` may be:

- validated (`validate_change_intent`),
- queued for future consumption,
- rendered as a Markdown report,
- persisted in an append-only audit store (future sprint),
- (in a future sprint) consumed by an Evolution transaction.

A `ChangeIntent` may **not** be applied directly to the runtime
in V1. The frozen `ChangeIntent` dataclass is the audit anchor.

### Rule 4 — Intelligence Authority Protection

The Feedback Learning Loop **never** writes to:

- `caseos.intelligence.decision`,
- `caseos.intelligence.trust`,
- `caseos.intelligence.recommendation`,
- `caseos.knowledge.retrieval`.

The only thing Knowledge Evolution may write to (in a future
Sprint 22.4) is the **Knowledge Object field** that the
`ChangeIntent` named. The future Retrieval Engine may then
read the updated Knowledge Object on its next pass. No
intelligence engine state is mutated.

This is the **single allowed write target** of the entire
Feedback Learning Loop. Any future ADR that proposes a second
write target is a hardening violation and must be re-numbered
as a separate ADR for architecture-review-level visibility.

---

## 16. Sprint 22.x Implementation Status (Sprint 22.3.3 freeze)

| Stage | Status | Sprint | Commit (post-Sprint 22.3.2) |
| --- | --- | --- | --- |
| Feedback Runtime | **Shipped** | 22.1 | (pre-tracked) |
| Evaluation Layer | **Shipped** | 22.2-A | (pre-tracked) |
| Contradiction Detection | **Shipped** | 22.2-B | (pre-tracked) |
| Learning Proposal | **Shipped** | 22.3 | dbfe6dd |
| Human Review Gate | **Shipped** | 22.3.1 | 7f23ffb |
| Interpretation Policy | **Shipped** | 22.3.2 | 6824b1f |
| `ChangeIntent` (object) | **Shipped** | 22.3.2 | 6824b1f |
| Architecture Freeze | **Shipped** | 22.3.3 | (this commit) |
| Knowledge Evolution | **Not Started** | (Sprint 22.4) | -- |

The complete loop is **runtime-complete** but **evolution-incomplete**.
The `ChangeIntent` is the last shipped artifact; everything past it
is governed by ADR-020 (Proposed) and is **NOT** in scope of any
shipped Sprint as of 22.3.3.

---

## 17. ChangeIntent Contract Reference (frozen by Sprint 22.3.2)

The `ChangeIntent` is defined in
`backend/caseos/knowledge/feedback/interpretation/object.py` as a
**frozen** dataclass with 11 fields:

- `intent_id`
- `proposal_id`
- `target_identity`
- `change_type`
- `target_field`
- `current_value`
- `proposed_value` (always `None` in V1)
- `reason`
- `risk_level`
- `requires_human_review` (always `True` in V1)
- `created_at`

The V1 mapping in
`backend/caseos/knowledge/feedback/interpretation/policy.py` only
supports two `change_type` values:

- `boundary_update` (target_field: `boundary`)
- `principle_update` (target_field: `principle`)

Any other `change_type` returns `None` from the policy. The V1
mapping is **locked**. Future Sprints may extend the mapping
table in `policy.py` **only** via a new ADR; in-place extension
is a hard-rule violation.

The `proposed_value` is intentionally `None` in V1: the policy
**never invents the future Knowledge Object value**. Sprint 22.4
(future) is the first sprint that may fill `proposed_value`,
and only after a second human approval step.

---

*End of ADR-018 additions for Sprint 22.3.3. The ADR remains the
single source of truth for the Feedback Learning Loop contract.
The next architectural change is gated by ADR-020 (Knowledge
Evolution Safety Principle V1, Proposed) and Sprint 22.4.*
