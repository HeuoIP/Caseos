# ADR-015: CaseOS Knowledge Object Model V1

- **Status:** Proposed
- **Date:** 2026-07-31
- **Layer:** Knowledge (the spine beneath all four intelligences)
- **Affects:** CKO, Decision Rules, Decision Patterns, Expert Principles, Failure Patterns, User Preferences; eventually retrieval (Rank 2 in AR-001)
- **Related ADRs:** ADR-011 (CKO Learning Source), ADR-012 (Evaluation), ADR-013 (Human Understanding), ADR-014 (Decision Intelligence Model); informed by `CaseOS_Intelligence_Architecture_V2.md`
- **Supersedes:** none
- **Source of truth:** `docs/architecture/ADR-015-knowledge-object-model.md`

> **Reading note.** Like ADR-014, this document is **a model**, not a software design. It deliberately avoids the vocabulary of `class`, `table`, `schema`, `API`, `vector`, `index`. Where a "Knowledge Object" is described, it is described as the **smallest reusable unit of expert intelligence** that CaseOS will accumulate over time -- the shape a piece of professional insight takes when it is written down so that it can later be reused, retrieved, contested, or refined.

---

## Context

CaseOS has established, in sequence:

- **ADR-013** -- Human Understanding Engine Foundation
- **ADR-014** -- Decision Intelligence Model V1 (the judgment model)
- **CaseOS Intelligence Architecture V2** -- the four-engine blueprint

The system now requires a **unified knowledge representation model**.

The purpose of ADR-015 is to answer one question:

> What is the **smallest reusable unit of CaseOS intelligence**?

CaseOS should **not** accumulate:

- image collections (unstructured),
- isolated tags (over-fragmented),
- disconnected documents (unretrievable).

CaseOS should accumulate:

```
Reusable Knowledge Objects.
```

A Knowledge Object is the **unit of memory** that the four intelligence
engines will share. Without it, every engine invents its own vocabulary and
the Brain fragments. With it, every piece of professional insight becomes
a citizen of the CaseOS memory.

---

## Decision

Create **CaseOS Knowledge Object Model V1**.

A **Knowledge Object** represents a structured piece of spatial intelligence
that contains:

```
Context
Observation
Reasoning (Diagnosis + Decision + Principle)
Applicability
Boundary
Feedback
```

It is what an experienced designer's insight looks like when it is
**lifted out of a single project** and **set down in language so that
others -- including future AI engines -- can use it**.

---

## Knowledge Object Core Structure

Every Knowledge Object carries **nine fields**:

### 1. Identity

**Question:** What *kind* of knowledge is this?

Allowed identities (V1):

- **Golden Case Object** -- a successful real-world example.
- **Decision Pattern Object** -- a reusable judgment logic.
- **Expert Principle Object** -- generalized design wisdom.
- **Failure Pattern Object** -- a known mistake or risk.
- **User Preference Object** -- a pattern learned from behaviour.

No other identities in V1. A new identity type is a new ADR.

### 2. Situation Context

**Question:** What situation does this knowledge apply to?

Includes:

- project type
- environment
- user type
- constraints
- business goal

### 3. Observation

**Question:** What was actually observed?

Examples:

> *Space:* empty boundary area; disconnected architecture relationship; lack of activity center.
> *User:* prefers natural education; values parent experience.

### 4. Diagnosis

**Question:** Why does this situation exist?

The **hidden problem** behind the observation. This field is what
distinguishes expert knowledge from tagging.

Example:

> *Observation:* large empty space between buildings.
> *Diagnosis:* no emotional anchor connecting children, architecture and activity.

### 5. Decision

**Question:** What decision was made?

Cross-reference: **ADR-014 Decision Intelligence Model**. The Decision
field of a Knowledge Object is a **summary**, not the full Decision
Object -- the full reasoning lives in ADR-014's seven-step template.

Example:

> Create a themed experience anchor instead of adding multiple small facilities.

### 6. Principle

**Question:** What is the reusable expert lesson?

The principle is the **lifted-out rule** that survives being moved from
this project to another.

Example:

> A kindergarten outdoor space should create a memorable experience center before adding secondary play functions.

The principle must be **verb-able** -- it must phrase as something a
designer can act on. A principle that can only be described, not acted
on, is a slogan, not knowledge.

### 7. Applicability

**Question:** Where can this knowledge be reused?

Includes:

- **Suitable:** project types, user goals, space conditions.
- **Not Suitable:** conflicting conditions (mirrored from Boundary below).

Applicability and Boundary are two sides of the same coin: Applicability
says "yes when"; Boundary says "no when". Both must be filled.

### 8. Boundary

**Question:** What should NOT be done?

Purpose: prevent **wrong recommendations**.

Example:

> Do not apply this pattern when:
> - budget cannot support a meaningful experience node,
> - the existing space already lacks basic safety functions.

A Knowledge Object with no Boundary field is **incomplete**, not
"neutral". Default-no-boundary makes a knowledge object dangerous in
production.

### 9. Feedback

**Question:** What happened after this knowledge was applied?

Includes:

- result
- user satisfaction
- unexpected outcome
- future adjustment

The Feedback field is what makes a Knowledge Object **a living unit**
rather than a static document. Knowledge Objects without feedback stay
in the library; knowledge objects with feedback graduate into the
**Trusted** tier.

---

## Knowledge Object Types V1

V1 recognises five types. Each type is a **configuration** of the nine
fields above -- not a separate structure.

### 1. Golden Case Object

A successful real-world example.

Typical emphasis: Identity, Situation Context, Observation, Decision,
Feedback.

### 2. Decision Pattern Object

Reusable judgment logic.

Typical emphasis: Situation, Diagnosis, Decision, Principle, Applicability,
Boundary.

### 3. Expert Principle Object

Generalised design wisdom.

Typical emphasis: Principle, Applicability, Boundary. Often minimal
on Observation / Feedback.

### 4. Failure Pattern Object

A known mistake or risk.

Typical emphasis: Diagnosis (what went wrong), Boundary (what must not
repeat), Feedback (the cost paid).

### 5. User Preference Object

Patterns learned from human behaviour.

Typical emphasis: Situation (which user), Observation (which behaviour),
Principle (what it implies for design), Feedback (whether acting on it
worked).

---

## Relationship Among Types

The five types are **peers**, not a hierarchy. A Golden Case can hold a
Decision Pattern; a Decision Pattern can rest on an Expert Principle.
The relationship is **composition**, not inheritance.

```
Golden Case    =  Image  +  Context  +  Decision  +  Principle
Decision Pattern =  Situation  +  Diagnosis  +  Decision
Expert Principle =  Generalised wisdom
Failure Pattern =  Anti-Decision (used as a guard)
User Preference =  Behaviour signal -> design implication
```

Failure Patterns are the only type that is **adversarial** to recommendation:
they exist explicitly to veto otherwise-good decisions. The Decision
Engine must consult them **before** the Recommendation Engine runs.

---

## Knowledge Flow (lifecycle)

```
Experience
   ↓
Observation, Diagnosis, Decision          (captured by human / AI review)
   ↓
Knowledge Object
   ↓
Retrieval                              (consumed by Decision Intelligence)
   ↓
Recommendation
   ↓
Feedback                               (outcome of the recommendation)
   ↓
Knowledge Update                       (this same object, refined)
```

A Knowledge Object therefore has a **seven-stage life**: born from
experience, formalised, retrievable, recommended against, fed back,
refined, and (eventually) retired.

Retirement is part of the lifecycle. When feedback consistently contradicts
a Principle, the object moves to **Deprecating** rather than disappearing
silently.

---

## Relationship with Existing ADRs

| Existing ADR | Role with respect to Knowledge Objects |
| --- | --- |
| ADR-011 CKO Learning Source | Defines **where** knowledge comes from (external excellent cases first). |
| ADR-012 Case Evaluation Score | Provides **evaluation signals** that determine intake / promotion of Golden Case Objects. |
| ADR-013 Human Understanding | Provides **user-related signals** used to enrich the Situation Context of every Object. |
| ADR-014 Decision Intelligence Model | **Consumes** Knowledge Objects. The Decision Engine retrieves them, not produces them. |
| (future) ADR-016 Recommendation Engine | **Consumes** the Decision Object that the Decision Engine synthesises from the retrieved Knowledge Objects. |
| (future) ADR-017 Feedback Loop Contract | **Records** the Feedback field of every Knowledge Object that participated in a recommendation. |

ADR-011 through ADR-014 are **producing** ADRs. ADR-015 is the
**representational** ADR that those producers write into and that the
Decision Engine reads from. ADR-016 / ADR-017 are the **downstream
consumers**.

---

## Architectural Style Rules (inherited)

These rules from the V2 blueprint and from ADR-014 apply:

1. Every Knowledge Object declares Identity / Situation / Observation /
   Diagnosis / Decision / Principle / Applicability / Boundary / Feedback.
2. A Knowledge Object without Boundary field is incomplete and must not be
   recommended.
3. Failure Patterns are consumed **before** Recommendation, not after.
4. Every identity type is a peer of the others -- no `extends`.
5. Knowledge Objects are stored in **knowledge/** alongside Brain modules,
   not inside `app/`. They are content, not code.

---

## Why this is the solution to "image collections, isolated tags, disconnected documents"

The three anti-patterns ADR-015 calls out each fail a specific test:

| Anti-pattern | Test it fails |
| --- | --- |
| Image collections | Cannot answer "why this works?" (no Diagnosis). |
| Isolated tags | Cannot answer "when to use?" (no Applicability). |
| Disconnected documents | Cannot be retrieved by the Decision Engine (no Decision Identity). |

The Knowledge Object Model passes all three tests by construction. It is
the **minimal structure** that makes a piece of content consumable by
the CaseOS brain.

---

## Non-Goals (explicit)

ADR-015 does **NOT** define:

- database schema,
- vector database,
- API,
- retrieval algorithm,
- UI.

The Knowledge Object Model is a **text model**. Software that stores,
retrieves, or ranks these objects comes later (AR-001 Rank 2). This ADR
decides only **what** a Knowledge Object looks like.

---

## Future Extensions

Natural follow-ups, kept out of this ADR:

- **ADR-015b** -- Knowledge Object Software Contract V1 (typed fields, allowed values, event names). Requires ADR-015 to exist.
- **ADR-015c** -- Retrieval Engine V1 (search / rank / score Knowledge Objects at runtime). AR-001 Rank 2.
- **ADR-015d** -- Trust Tiering V1 (Inspired / Candidate / Trusted / Deprecated / Retired), driven by the Feedback field.
- (after) **ADR-016** Recommendation Engine V1 -- consumer.
- (after) **ADR-017** Feedback Loop Contract V1 -- writer of the Feedback field.

015b / 015c / 015d slots exist so that future implementation ADRs do
not crowd into the 014 range or the 016/017 ranges.

---

## Acceptance Criteria

This ADR is complete when:

1. CaseOS has a unified written definition of *knowledge* -- **DONE** by the nine-field model.
2. Golden Cases can evolve from images into intelligence objects -- **UNLOCKED** by the Identity type "Golden Case Object" and the relationship table.
3. Decision Patterns can be stored and reused -- **UNLOCKED** by the "Decision Pattern Object" type and the Applicability field.
4. Future learning systems have a stable memory foundation -- **DONE** by the seven-stage lifecycle and the Feedback field.

A future engineer reading Sections "Core Structure" and "Knowledge Flow"
should be able to take any existing piece of design content in CaseOS and
say which of the nine fields it already has, and which it is missing. If
they can do this, ADR-015 has done its job.

---

*End of ADR-015. The next ADR slot is ADR-016 (Recommendation Engine V1), with ADR-015b / 015c / 015d reserved for storage, retrieval, and trust tiering.*