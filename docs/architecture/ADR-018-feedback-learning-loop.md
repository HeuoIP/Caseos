# ADR-018: CaseOS Feedback Learning Loop Contract V1

- **Status:** Proposed
- **Date:** 2026-07-31
- **Layer:** Learning (the closing of the CaseOS intelligence loop)
- **Affects:** Knowledge Object lifecycle, Trust labels, Decision Pattern quality, future agent role
- **Related ADRs:** ADR-013 (Human), ADR-014 (Decision), ADR-015 (Knowledge Object), ADR-016 (Trust), ADR-017 (Recommendation)
- **Implements:** the **Feedback Learning Engine** declared in the V2 Blueprint Section 2.4 (was an "ADR slot pending" reference; now concretely numbered).
- **Supersedes:** none
- **Source of truth:** `docs/architecture/ADR-018-feedback-learning-loop.md`
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