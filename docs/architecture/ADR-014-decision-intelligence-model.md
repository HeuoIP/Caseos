# ADR-014: CaseOS Decision Intelligence Model V1

- **Status:** Proposed
- **Date:** 2026-07-31
- **Layer:** Intelligence (Decision Side)
- **Affects:** Reasoning pipeline, Golden Case extension, Recommendation Engine input contract, future ADR-016
- **Related ADRs:** ADR-005 (Decision pipeline), ADR-006 (Project Fit), ADR-009 (Brain), ADR-010 (Decision Rules), ADR-011 (CKO), ADR-012 (Evaluation), ADR-013 (Human Understanding)
- **Supersedes:** nothing
- **Source of truth:** `docs/architecture/ADR-014-decision-intelligence-model.md`

> **Reading note.** This document is a **judgment model**, not a software design document. It does not contain `class`, `service`, `function`, `database`, or schema definitions. Where the Decision Object is described, it is described as an **expert-judgment template** -- the shape an experienced designer's reasoning takes when it is articulated. Future ADRs (014b / 014c) will turn this template into a software contract. This ADR deliberately stops one layer above that line.

---

## Context

CaseOS V2 architecture defines four intelligence engines:

1. Human Understanding Engine
2. Spatial Intelligence Engine
3. **Decision Intelligence Engine** (this ADR)
4. Feedback Learning Engine

Human Understanding answers:

> "What does this person really want?"

Spatial Intelligence answers:

> "What does this space need?"

Decision Intelligence must answer:

> "What is the best decision for **this specific person** and **this specific space**?"

The purpose of ADR-014 is to define the **judgment model** behind CaseOS.

This is **not** an implementation document.
This is **not** an algorithm document.
This defines **how expert judgment is represented**.

A junior designer can describe what they see.
A senior designer can describe what should be done -- and why.
The Decision Intelligence Model is the spine of that seniority, captured once.

---

## Decision

Create **Decision Intelligence Model V1**.

Decision Intelligence is the core reasoning layer that transforms:

```
Human Context
   +
Spatial Context
   +
Knowledge Context
   +
Business Context
                 =   Design Decisions
```

The model is composed of seven layers of articulation, listed in
`Section 2`. Each layer is **a thinking step**, not a software step.

---

## 1. Decision Intelligence Input Model

The Decision Engine receives **four contexts**. None of them is "a class".
Each is a way of reading the situation.

### A. Human Context

From Human Understanding Engine:

- project goal
- emotional expectation
- style preference
- decision preference
- budget
- constraints

### B. Spatial Context

From Spatial Intelligence Engine:

- site diagnosis
- space problems
- opportunities
- environmental relationship
- existing conditions

### C. Knowledge Context

From the Brain:

- Golden Cases
- CKO
- Decision Rules
- Expert Principles
- Experience Library

### D. Business Context

Examples:

- commercial attraction
- enrollment improvement
- parent perception
- operation requirements

These four contexts are read **together**, not in sequence. The Decision
Engine's first act is to compose them, not to process them one by one.

---

## 2. Expert Judgment Model

The Decision follows seven **thinking steps**:

```
Observation
   ↓
Diagnosis
   ↓
Root Cause
   ↓
Priority
   ↓
Strategy
   ↓
Experience Logic
   ↓
Recommendation Direction
```

Each step is described below as the reasoning it represents -- the **kind
of question it asks**, not the operation it performs.

| Step | The question it asks |
| --- | --- |
| Observation | "What am I actually seeing here?" |
| Diagnosis | "Why does this feel right or wrong?" |
| Root Cause | "What is producing this state, underneath the surface?" |
| Priority | "Of all the things that could be fixed, which one matters first?" |
| Strategy | "If we can only act in one direction, which direction?" |
| Experience Logic | "What experience should the user have, end to end?" |
| Recommendation Direction | "Given all of the above, what should the next conversation be about?" |

A junior reasoning chain often stops at Observation or Diagnosis. A senior
reasoning chain goes all the way to Recommendation Direction with
**Reasoning** attached to every step.

---

## 3. Decision Object (a judgment template, not a class)

A **Decision Object** is the **shape an articulated decision takes** when
a senior designer writes it down for a colleague. It is **not** a database
table and **not** a software class. It is a **template of judgment** --
seven fields, each field a question.

```
A Decision Object contains:

  Problem       -- What problem are we solving?
  Evidence      -- Why do we believe this is the problem?
  Priority      -- Why solve this before other problems?
  Strategy      -- What is the strategic direction?
  Experience    -- What user experience should be created?
  Reasoning     -- Why is this the best choice?
  Boundaries    -- What are we explicitly not doing, and why?
```

The seventh field, **Boundaries**, is added by this ADR. It is missing from
typical design briefs, and it is exactly the field that prevents a good
strategy from being re-interpreted as "do everything".

A Decision Object is **complete** when:

- each of the seven fields is filled;
- each filled field is consistent with every other field;
- the Reasoning field carries enough trace that another expert could
  re-derive the decision without re-reading the source images.

---

## 4. Decision Principles

These principles are non-negotiable. They are stated once here and reused
by every future Agent that touches the Decision Engine.

### Principle 1 -- Do not recommend before diagnosis.

If the Diagnosis step is empty, the Recommendation Direction step is
forbidden. No exceptions.

### Principle 2 -- The same space may have different decisions for different users.

A Decision Object is not transferable between Human Contexts unless the
Strategy field is re-derived. Transferability is determined by the
`boundaries` field, not by visual similarity.

### Principle 3 -- The best solution is not the most beautiful solution.

The Decision Engine optimizes for **suitability**, not for visual
excellence. Visual excellence is a property of the Solution, not the
Decision. A beautiful decision that does not fit the user is **wrong**.

### Principle 4 -- Every recommendation must answer three questions.

1. Why **this**?
2. Why **now**?
3. Why not **others**?

If any of these three is missing, the Recommendation Direction is not yet
a recommendation; it is a draft.

### Principle 5 -- A Decision is allowed to refuse.

When the four contexts contradict each other -- e.g. the Human Context
asks for a luxury experience but the Business Context shows budget that
cannot support it -- the correct Decision Object is **"no decision yet,
escalate"**. Refusal is a valid Decision.

---

## 5. Expert Reasoning Pattern

The pattern below shows one Decision Object being formed step by step.
It is **exemplar reasoning**, not algorithm. The point is to show what
"good judgment" looks like when it is written down.

### 5.1 Input

**Kindergarten**

- Goal: Improve enrollment attraction
- Space: Large empty area between the teaching building and playground
- Human preference: Natural educational atmosphere
- Knowledge: Successful natural-exploration cases

### 5.2 Decision

**Problem**

The space lacks a visual and emotional anchor.

**Evidence**

- Distant from both the teaching building and the playground.
- No shade, no enclosure, no narrative.
- Children pass through but do not linger.

**Root Cause**

Children's activity and the building environment are disconnected; the
area is circulation, not destination.

**Priority**

Create one central experience node before adding secondary facilities.
Without a node, secondary facilities only spread the emptiness.

**Strategy**

Build a themed exploration space that connects the architecture and the
playground as a single narrative arc.

**Experience Logic**

Children enter, explore, interact, stay, and repeat.

**Boundaries**

- No large colourful equipment (over-stimulates and contradicts the
  natural atmosphere).
- No cliche "natural" props (artificial logs, plastic leaves).
- No second node elsewhere in the same space.

**Reasoning (the WHY)**

A central node concentrates narrative. When a single experience anchors
a space, children develop ownership of that anchor; ownership converts
passage into stay-time, and stay-time is the strongest predictor of
parent enrolment conversion in this segment.

---

## 6. Relationship with Golden Case

Golden Cases must do more than provide visual reference. They must
provide **Decision Patterns**.

Every Golden Case, after ADR-014, must be able to answer four
**pattern questions**:

```
Situation     -- What conditions existed?
Judgment      -- What decision was made?
Reason        -- Why was this decision correct?
Applicability -- When can this pattern be reused?
```

The pattern questions sit **beside** the Golden Case evaluation
introduced by ADR-012 (Section 1-10). Section 11 (currently proposed via
ADR-013) adds user affinity; ADR-014 adds **decision affinity**. The two
together let a future retrieval engine pick cases by:

- visual similarity (CKO image),
- evaluation strength (ADR-012),
- user affinity (ADR-013 / Section 11),
- **decision affinity (ADR-014 / Section 6)** -- the new dimension.

A case rich in visual information but poor in decision pattern is **not**
a useful Golden Case for this engine.

---

## 7. Relationship with Recommendation Engine

Decision Intelligence produces a **Decision Object**.

The Recommendation Engine (future ADR-016) transforms a **Decision Object**
into:

- proposal language (for a proposal document),
- visual direction (for an image generation brief),
- communication format (for a customer-facing explanation).

The boundary between the two engines is sharp:

| What | Decision Engine | Recommendation Engine |
| --- | --- | --- |
| Decides | **WHAT** should be done | **HOW** to express it |
| Reads | Four contexts | One Decision Object |
| Writes | Decision Object | Customer-facing artefacts |
| Touches user | Indirectly (via Decision Object) | Directly (via Solution output) |

Decision is allowed to be technical.
Recommendation must be customer-readable.
The handoff between them is the Decision Object's Reasoning field.

---

## 8. Architecture Style Rules (inherited from V2 blueprint)

The following rules from `CaseOS_Intelligence_Architecture_V2.md`
apply to the Decision Engine and are restated here for completeness:

1. Every engine declares **Input / Processing / Output / Consumer**.
2. No engine writes into another engine's output store.
3. No personas without behaviour.
4. No recommendation without decision.
5. Every knowledge base is a peer of the Brain.

The Decision Engine's Consumer is the Recommendation Engine. If ADR-016
has not yet been written, this Consumer is **declared, not yet wired**.

---

## 9. Non-Goals (explicit)

ADR-014 does **NOT** define:

- database schema,
- API contracts,
- UI surfaces,
- recommendation algorithms,
- user tracking,
- LLM prompt templates for decision synthesis,
- automatic decision generation (any automatic synthesis will be a
  separate ADR after a human review of V1).

ADR-014 is **judgment represented as text**. Software that consumes it
comes later.

---

## 10. Future Extensions

Future ADRs that this ADR enables (in declared order):

- **ADR-015** -- Preference Signal Schema V1 (turns ADR-013 scope into
  typed fields).
- **ADR-016** -- Recommendation Engine V1 (consumes Decision Object).
- **ADR-017** -- Feedback Learning Loop Contract V1 (closes the loop).
- (later) **ADR-014b** -- Decision Object Software Contract V1 (turns
  this judgment template into a typed contract; **not** part of this ADR).
- (later) **ADR-014c** -- Decision Pattern Library V1 (a peer of the
  CKO library; pattern-driven retrieval. Not part of this ADR).

ADR-014 deliberately stops at the judgment level. 014b / 014c exist as
named slots so that no future implementation ADR has to be shoe-horned
into ADR-014's number range.

---

## 11. Acceptance Criteria

This ADR is complete when:

1. CaseOS has a clear written definition of expert judgment -- **DONE** by
   Sections 2-5.
2. The Decision Intelligence Engine has its four declarations -- **DONE**
   in Section 8 of this ADR.
3. Future Golden Cases can be converted into reusable decision patterns --
   **UNLOCKED** by Section 6 (the pattern questions).
4. Future Sprint implementation has a stable reasoning target -- **DONE**
   by Sections 3-5 and the explicit Boundary to non-implementation in
   Section 9.

A future reviewer can read Sections 2-5 and reproduce the V2 example
(Kindergarten, empty area, natural preference) without any code or schema
in hand. If they can, this ADR has done its job.

---

*End of ADR-014. The next ADR slot is ADR-015 (Preference Signal Schema V1).*