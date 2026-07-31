# ADR-016: CaseOS Intelligence Trust Model V1

- **Status:** Proposed
- **Date:** 2026-07-31
- **Layer:** Trust (orthogonal to Decision; cuts across all four intelligences)
- **Affects:** Every Decision Object, every Recommendation, every Knowledge Object promotion
- **Related ADRs:** ADR-013 (Human), ADR-014 (Decision), ADR-015 (Knowledge Object), ADR-012 (Evaluation -- source of many trust signals)
- **Supersedes:** none
- **Source of truth:** `docs/architecture/ADR-016-intelligence-trust-model.md`

> **Numbering note (must read).** The earlier `CaseOS_Intelligence_Architecture_V2.md` (Section 8) tentatively labeled:
>
> - ADR-016 = Recommendation Engine V1
> - ADR-017 = Feedback Loop Contract V1
>
> This ADR takes slot ADR-016 for the **Trust Model** instead. Subsequent ADRs therefore shift:
>
> - **ADR-017 = Recommendation Engine V1** (was ADR-016 in the placeholder)
> - **ADR-018 = Feedback Learning Loop Contract V1** (was ADR-017)
>
> The V2 Blueprint placeholder table does **not** match the published slot allocation. That update is documented as a follow-up task and is **not** part of this ADR commit. Reading this ADR is unaffected.
>
> **Reading note (model, not software).** This ADR inherits the discipline set by ADR-014 and ADR-015: it describes **how professional reasoning is qualified and made explainable**, not how a software system computes a number. Where "Confidence Level" is mentioned, it is a *qualitative judgment label* an expert would write down, not an enum or a numeric column. Where "Source Reliability" is mentioned, it is a *qualitative property* of a source, not a database field.

---

## Context

CaseOS has established:

- **ADR-013** -- Human Understanding Engine
- **ADR-014** -- Decision Intelligence Model
- **ADR-015** -- Knowledge Object Model

The system can now:

- understand users,
- analyse spaces,
- generate decisions,
- store knowledge.

However, a professional decision system requires **one more capability**:

> Trust.

CaseOS must not only answer:

> "What should we do?"

It must also answer:

> "Why should we trust this decision?"

---

## Decision

Create **CaseOS Intelligence Trust Model V1**.

The Trust Model defines how CaseOS evaluates:

- evidence,
- confidence,
- reliability,
- applicability,

**behind every Decision Object**.

The Trust Model is **orthogonal** to the Decision Intelligence Engine. The
Decision Engine answers "what should we do"; the Trust Model answers "how
much should we believe the answer". Both are required for a professional
decision to leave the system.

---

## 1. Trust Model Purpose

The purpose is **not**:

> to create mathematical certainty.

The purpose **is**:

> to make AI reasoning **transparent, explainable, and professionally credible**.

This is the difference between a system an expert will sign their name on,
and a system an expert will not. ADR-016 exists to make the system the
former kind.

---

## 2. Trust Object (a qualification template, not a class)

Every **Decision** that leaves the Decision Engine must carry a
**Trust Object** -- a small block of qualitative qualification that
describes the reasoning behind the reasoning.

A Trust Object has **five fields**. Each field is a question a senior
designer asks when checking their own work.

### 1. Evidence

**Question:** What supports this decision?

Sources:

- Golden Cases
- Knowledge Objects (any Identity type from ADR-015)
- Expert Principles
- Spatial Analysis
- User Signals

A Trust Object must list **which kinds** of evidence were used and
**how many independent sources** agreed.

### 2. Source Reliability

**Question:** How trustworthy is this knowledge source?

Source reliability is a **qualitative label** written on a source at
intake time -- not a score computed at retrieval time. The five labels
below are the V1 vocabulary:

- **expert-verified** -- signed off by a domain expert.
- **real-project-completed** -- came from a delivered, used space.
- **user-feedback** -- validated by users in the wild.
- **repeated-success** -- recurrence across multiple projects.
- **theoretical-assumption** -- hypothesized, not yet validated.

A source with multiple labels (e.g. "expert-verified + real-project-completed")
is more trusted than one with none. Mixing `theoretical-assumption` alone is a
yellow flag; it is allowed but the Trust Object must say so.

### 3. Applicability Match

**Question:** How similar is this situation to the previous knowledge it leans on?

Consider:

- project type
- spatial condition
- user goal
- constraints

A Trust Object declares Applicability Match as **a narrative judgement**
("high", "medium", "low") explaining how the matches and mismatches
weighted out. It is **not** a similarity score. The decision is taken by
the expert who writes the Trust Object, not by a metric.

### 4. Confidence Level

**Question:** How confident should CaseOS be in this decision?

Three qualitative levels:

- **High Confidence** -- strong evidence + high applicability.
- **Medium Confidence** -- partial evidence + expert reasoning.
- **Low Confidence** -- insufficient evidence; the Decision Engine should
  still issue the decision but **only as a draft**.

A Trust Object **never** rounds "Low" up to "Medium". A Low remains Low
because the consequence of mislabelling Low as Medium is the consequence
of shipping an over-confident decision.

### 5. Uncertainty Handling

**Question:** What is missing or unresolved?

The Trust Object must explicitly state:

- what information is incomplete,
- what requirements conflict,
- what similar cases are absent.

CaseOS must be able to say, plainly:

> "I need more information."

Examples of legitimate uncertainty:

- budget unclear,
- business goal unclear,
- conflicting requirements,
- insufficient similar cases.

A Trust Object that hides uncertainty is a **breach of the Anti-Hallucination
Principle** (Section 6).

---

## 3. Trust Evaluation Flow

```
Decision Candidate
   ↓
Evidence Collection
   ↓
Knowledge Matching
   ↓
Applicability Check
   ↓
Boundary Check
   ↓
Confidence Assessment
   ↓
Decision Output (+ Trust Object)
```

This flow runs **inside** the Decision Intelligence Engine, before the
Decision Object is handed to the Recommendation Engine. The Trust Object
is attached as a footer; it travels with the Decision throughout the
rest of the pipeline.

Three rules about the flow:

1. The **Boundary Check** step uses the Boundary field of every
   Knowledge Object retrieved (per ADR-015 Section 8). A Decision
   candidate that violates a Boundary is dropped silently only with a
   written reason. Silent rejection without written reason is itself a
   breach of Trust.
2. The **Evidence Collection** step must include **at least one piece
   of evidence whose source label is not `theoretical-assumption`**, or
   Confidence must be downgraded to Low.
3. The **Confidence Assessment** step writes exactly one of High /
   Medium / Low. There is no fourth level. "Don't know" is encoded as
   **Low + an Uncertainty Handling description**, not as a fourth label.

---

## 4. Relationship with Existing Models

| Existing model | What it does | Trust Model's role |
| --- | --- | --- |
| Knowledge Object (ADR-015) | Provides memory | Knowledge Objects supply **Source Reliability labels** and **Boundary conditions** to the Trust Object. |
| Decision Intelligence (ADR-014) | Creates judgment | The Trust Object is attached to the Decision Object at the moment of judgement. |
| Trust Model (ADR-016, this) | Evaluates reliability | Decides whether the Decision is **shippable**, **ship-with-caveats**, or **withheld**. |
| Recommendation Engine (future ADR-017) | Communicates judgement | Reads the Trust Object and decides whether the customer-facing message includes the caveats or not. |

Trust is therefore a **post-judgement step**, not a pre-judgement filter.
We do not refuse to think because we are unsure; we think, and then we
**label the certainty of what we thought**.

---

## 5. Trust Explanation Format

Every **major** recommendation -- the ones the customer will read in a
proposal -- must be explainable in this format:

```
Decision:
   <the decision>

Why:
   1. <reason 1>
   2. <reason 2>
   3. <reason 3>
   4. <reason 4>

Confidence:
   <High | Medium | Low>

Caveats:
   <if any, listed here, taken from the Uncertainty Handling field>
```

### Worked example

```
Decision:
   Create a themed experience centre.

Why:
   1. The space lacks a visual anchor.
   2. Similar successful kindergarten cases show this pattern.
   3. The user goal prioritises enrolment attraction.
   4. The selected strategy fits the budget constraint.

Confidence:
   High

Caveats:
   None.
```

If the same decision had been reached with thin evidence, the format
would become:

```
Decision:
   Create a themed experience centre.

Why:
   1. Similar successful kindergarten cases suggest a single anchor.

Confidence:
   Low

Caveats:
   - Budget specificity pending.
   - Only two prior cases of similar user goal; transferability is narrow.
   - Site environmental relationship not yet analysed.
```

Same Decision. Different Trust Object. Different downstream behaviour.

This is exactly the property that distinguishes a Trust Model from a
confident-sounding output: **the same answer can be High, Medium, or
Low depending on what backs it**.

---

## 6. Anti-Hallucination Principle

CaseOS prefers:

> "I don't know yet."

over:

> "An unsupported recommendation."

A wrong confident answer is **strictly worse** than an incomplete answer.

In concrete terms:

- **No** padding a Trust Object with evidence the Decision did not actually use.
- **No** inferring Source Reliability labels that are not present on the source at intake time.
- **No** raising Confidence Level to compensate for Uncertainty Handling boilerplate.
- **Yes** attaching the `Low + Caveats` form when the decision is uncertain.
- **Yes** attaching `I need more information.` as the **entire** Decision if
  the four contexts (per ADR-014 Section 1) contradict each other and a
  decision cannot be synthesised at all.

This principle is the operational form of ADR-014 Principle 5 (a Decision
is allowed to refuse) and of Constitution Principle 003 (Understand
before recommending).

---

## 7. Relationship with Golden Cases

Golden Cases are also Knowledge Objects; their Source Reliability labels
already exist. ADR-016 adds two **trust rules** specific to Golden Cases:

1. A visually attractive case **without** evidence labels should **not**
   automatically become a strong recommendation source.
2. A Golden Case that has been used in past Recommendations **without**
   producing good real-world outcomes should be **demoted** -- not
   deleted, but moved out of the candidate pool. Demotion is an act of
   trust maintenance, not of disgracing the case.

These rules are written here because Golden Cases occupy the largest
share of the CaseOS knowledge library in V1; their trust treatment is a
public policy of the system.

---

## 8. Architectural Style Rules (inherited + new)

Inherited from the V2 blueprint and from ADR-014 / ADR-015:

1. Every Decision leaves the Decision Engine **with a Trust Object attached**.
2. The Trust Object is **not** optional. A Decision Object without one
   is treated as Low-confidence by default.
3. Failure Patterns (ADR-015) are **still consulted first**; if a
   Boundary vetoes the Decision, the Trust Object never has to be written.
4. Trust Level labels (High / Medium / Low) are **never** mixed with
   numeric scores. No "score 87". Just labels, with the caveats that justify them.
5. A Trust Object cannot be edited silently. Editorial changes to a
   Trust Object are themselves logged as feedback events (future ADR-018).

New rule added by this ADR:

6. **Trust is monotonic in time**, only with a written reason. A Knowledge
   Object may move from Inspired to Candidate to Trusted; it may not
   move backwards silently. Demotion requires a Feedback log entry.

---

## 9. Non-Goals (explicit)

ADR-016 does **NOT** define:

- scoring algorithm,
- machine learning model,
- database fields,
- retrieval implementation,
- "AI hallucination detection" mechanism.

It defines **reasoning trust principles only**.

Future implementation ADRs (numbered 017b / 017c -- separate from the
slot-shift mentioned in the front-matter) will translate the principles
into software when the time comes.

---

## 10. Future Extensions

Slot allocation, after the front-matter correction:

| Slot | Topic | Note |
| --- | --- | --- |
| **ADR-017** | Recommendation Engine V1 | Was ADR-016 in the V2 Blueprint placeholder; promoted one slot forward. |
| **ADR-018** | Feedback Learning Loop Contract V1 | Was ADR-017 in the placeholder; promoted one slot forward. |
| **ADR-016b** | Trust Levels Software Contract V1 | Typed fields for High / Medium / Low + allowed source-reliability labels. |
| **ADR-016c** | Trust Explanation Rendering | The customer-facing template (`Why / Confidence / Caveats`) as a Markdown / PDF renderer. |
| **ADR-016d** | Trust Demotion Policy | The formal rules under which a Knowledge Object is moved to a lower tier; ties into ADR-018. |

---

## 11. Acceptance Criteria

This ADR is complete when:

1. CaseOS can explain why a decision is trustworthy -- **DONE** by
   Sections 2, 5, and 6.
2. Every recommendation can trace back to evidence -- **DONE** by
   Section 3's Evidence Collection step and Section 5's Why-block format.
3. Uncertainty can be expressed -- **DONE** by Section 2 field 5 and by
   Section 6's Anti-Hallucination Principle.
4. Future commercial usage has a professional credibility foundation
   -- **DONE** by the combination of Confidence labels, Caveats
   mechanism, and Golden Case demotion policy.

A future reviewer can take the worked example in Section 5 and produce
both a High-confidence and a Low-confidence version of the same Decision
without changing the Decision field. If they can do this, ADR-016 has
done its job.

---

## 12. Follow-Up (not part of this commit)

- The V2 Blueprint's Section 8 placeholder table (ADR-014 -> Decision,
  ADR-015 -> Preference Signals, ADR-016 -> Recommendation Engine,
  ADR-017 -> Feedback Loop) does not match the actual slot allocation
  after ADR-015 was repurposed for the Knowledge Object Model and
  ADR-016 (this document) is allocated to the Trust Model. The
  placeholder table should be updated in a separate ADR or doc-only
  commit.

---

*End of ADR-016. The next ADR slot is ADR-017 (Recommendation Engine V1, slot-shifted from ADR-016 in the V2 placeholder table).*