# ADR-017: CaseOS Recommendation Engine V1

- **Status:** Proposed
- **Date:** 2026-07-31
- **Layer:** Communication (the "How to express" exit of the Decision Pipeline)
- **Affects:** Output template, audience-aware variants, proposal rendering, future agent role
- **Related ADRs:** ADR-005 (Decision Agent pipeline), ADR-013 (Human Understanding), ADR-014 (Decision Intelligence), ADR-015 (Knowledge Object), ADR-016 (Trust Model)
- **Supersedes:** none
- **Source of truth:** `docs/architecture/ADR-017-recommendation-engine.md`

> **Reading note (model, not implementation).** This ADR inherits the discipline set by ADR-014, ADR-015, ADR-016: it is a **model of how a recommendation reads**, not a software design for a class, an API, a UI, or a renderer. Where a "Recommendation Type" is mentioned, it is the **content shape** a recommendation takes for a given audience, not a UI surface or a class taxonomy.
>
> **Numbering note.** Slot allocation aligned with the front-matter correction in ADR-016: 017 = Recommendation Engine; 018 = Feedback Learning Loop.

---

## Context

CaseOS Intelligence Architecture now includes:

- **ADR-013** -- Human Understanding Engine
- **ADR-014** -- Decision Intelligence Model
- **ADR-015** -- Knowledge Object Model
- **ADR-016** -- Intelligence Trust Model

The system can now:

- understand users,
- understand spaces,
- create decisions,
- store knowledge,
- evaluate trust.

However, a professional advisor does more than make correct decisions.

> A professional advisor must **communicate** decisions effectively.

The purpose of ADR-017 is to define:

> How CaseOS transforms:
> ```
> Decision Objects
>    +
> Trust Objects
>    +
> Knowledge Evidence
> ```
> into:
> ```
> Human-readable recommendations.
> ```

Without this layer, CaseOS would be an expert that thinks correctly but
cannot be heard. ADR-017 exists so that the customer actually understands
why we recommended what we recommended.

---

## Decision

Create **CaseOS Recommendation Engine V1**.

The Recommendation Engine is responsible for:

> expressing decisions.

It is **not** responsible for:

> creating decisions.

```
Decision Intelligence     -- decides WHAT
Recommendation Engine     -- decides HOW TO COMMUNICATE
```

The two engines are sharply separated. Anything that smells like "should
the strategy be X instead of Y" is **Decision Intelligence's** territory;
this Engine may only **expose** that decision, not revise it.

---

## 1. Recommendation Input

The Recommendation Engine consumes **four inputs**. None of them is a
class. Each is a kind of structured statement the Engine has read.

### A. Decision Object

From **ADR-014**:

- problem
- diagnosis
- strategy
- experience logic
- reasoning
- boundaries

### B. Trust Object

From **ADR-016**:

- evidence
- source reliability
- applicability
- confidence
- uncertainty

### C. Human Context

From **ADR-013**:

- user goal
- concerns
- language preference
- decision style

### D. Knowledge Object

From **ADR-015**:

- supporting cases
- principles
- patterns

These four are read **together** to compose one recommendation. The Engine
does not re-derive any of them; it composes a single expression from
the existing articulation.

---

## 2. Recommendation Output Model (a composition shape, not a class)

A recommendation is **not** a database row, **not** a JSON schema, **not**
a UI panel. It is the **shape a recommendation takes when an advisor sits
down and tells a customer what they think**. That shape has seven
sections.

### 1. Situation Understanding

To the user:

> "We understand your situation."

The Recommendation Engine **mirrors back** the situation the user gave
us, in terms the user themselves would recognise. If the user said their
goal was improving enrolment, we say: "you are choosing to improve enrolment".
No jargon is introduced here.

### 2. Problem Diagnosis

What is really limiting the project.

If the Decision Object's Diagnosis field names "no emotional anchor", the
recommendation says "no emotional anchor". Diagnosis is **never softened,
never reworded**, never substituted with a more flattering description.
Honest diagnosis is part of the case the user agreed to hire us for.

### 3. Strategic Direction

What should be prioritised.

The strategy is **forward-looking**: where the space should go, what the
first move is, what to defer. The recommendation is allowed to be direct
("the first move is creating the central experience node") because the
Decision Object already carries Reasoning.

### 4. Experience Concept

What kind of experience should be created.

The recommendation translates the **Experience Logic** field of the
Decision Object into user-language. "Children enter, explore, interact,
stay, and repeat" becomes a sentence the customer can read aloud without
translating.

### 5. Implementation Direction

How this becomes a real solution.

This section **does not** prescribe equipment, finishes, or budgets. It
states the **order of operations**:

- first which decision,
- next which kind of design,
- then which kind of validation.

Equipment lists are an anti-pattern (see Section 7). Implementation
Direction is **structural**, not particulate.

### 6. Evidence

Why this recommendation is reliable.

This section is the rendered form of the **Trust Object's Evidence
field** (ADR-016 Section 2.1). The Engine does **not** add evidence. It
**narrates** what the Evidence field already contains. The list of
sources stays visible; nothing is summarised away.

### 7. Confidence and Caveats

What is certain and what needs validation.

The Engine renders the **Confidence Level** and the **Uncertainty
Handling** field of the Trust Object (ADR-016 Section 2.4 and 2.5).
Confidence is shown as the label it is (High / Medium / Low); no
transformation. Caveats are shown verbatim.

A confidence label is **always** written in a recommendation, including
when it is High. Hiding confidence when it is High is the start of the
**false-certainty** anti-pattern (Section 7.4).

---

## 3. Recommendation Principles

### Principle 1 -- Do not show conclusions without reasoning.

If the Reasoning field of the Decision Object is empty, the Strategic
Direction section cannot be issued. This mirrors ADR-014 Principle 1
("Do not recommend before diagnosis") in the communication layer.

### Principle 2 -- Do not overwhelm users with internal intelligence.

The reader is a customer, not a designer. The Engine drops the names of
agents, IDs of Knowledge Objects, taxonomy labels, and pipeline jargon.
The reader should be able to read every line without consulting CaseOS
documentation.

### Principle 3 -- Different users require different expressions.

The Human Context (`request.py` in the Product Layer carries it in
production) selects the **voice** and the **emphasis** of the same
Decision + Trust + Evidence. The Decision itself does not change.

---

### Examples of audience-aware emphasis

| Audience | Emphasis on each section |
| --- | --- |
| **Kindergarten owner** | Situation, Experience Concept, Confidence. Less Implementation Detail. |
| **Designer** | Diagnosis, Strategy, Reasoning trace. Implementation as design vocabulary. |
| **Manufacturer** | Boundaries, Implementation Direction as material/feasibility order. Experience Concept as production brief. |

The seven sections are **always present**; what changes is **how much
each section is expanded**, and **what vocabulary** is used. The shape
is constant; the surface is localisable per audience.

---

## 4. Recommendation Transformation (worked example)

This is the **transformation**, not the runtime. It shows what the
Recommendation Engine does to a Decision Object.

### Input

```
Decision (internal):
    "The space lacks an emotional anchor."

Reasoning trace:
    Observation : Large empty area between building and playground.
    Diagnosis   : No memorable experience centre.
    Strategy    : Create a themed exploration space.
```

### Output

```
Recommendation (user-facing):

  "The current site does not need more scattered equipment.
   The priority is creating one memorable children's experience centre
   that connects the teaching environment with outdoor activity."
```

### What changed

- "emotional anchor" -> "scattered equipment ... memorable experience centre"
  (translated to user vocabulary; meaning preserved).
- Diagnosis kept ("does not need ... scattered equipment" is the diagnosis phrase).
- Strategy preserved verbatim ("the priority is ... creating one ... experience centre").
- No equipment list. No style adjectives. No KPIs.

This is the **only** transformation the Recommendation Engine does:
**customer vocabulary** applied to a Decision whose content is unchanged.

---

## 5. Recommendation Types V1

The Recommendation Engine produces **content types**, not screen types.
A content type is a **shape a recommendation takes for a question**.
Five types defined in V1.

### 1. Diagnostic Recommendation

**Answers:** "What is wrong?"

Used when the Decision Object's Diagnosis is the main value. Suited to
first-contact customers who do not yet trust CaseOS.

### 2. Strategic Recommendation

**Answers:** "What should be done?"

Used when Strategy is the main value. The default type for kindergarten /
commercial / community first-engagement.

### 3. Design Direction Recommendation

**Answers:** "What experience direction?"

Used when Experience Logic is the main value. Suited to design studios
and manufacturers.

### 4. Implementation Recommendation

**Answers:** "How to move forward?"

Used when Implementation Direction is the main value. Suited to project
managers and procurement.

### 5. Commercial Recommendation

**Answers:** "Why does this create value?"

Used when the **Business Context** (per ADR-014 Section 1.D) is the
main value. Suited to investors, brand owners, and operators.

V1 allows a recommendation to be one of these five, **not** a mix. A
mixed recommendation degrades clarity. Future ADRs may allow mixed types
with explicit ordering rules; in V1, one type per recommendation.

---

## 6. Trust Integration

A recommendation **preserves** the Decision's confidence. The Engine
**does not** re-evaluate the Trust Object. It **renders** it.

Rules:

| Confidence | Engine behaviour |
| --- | --- |
| **High** | Provide a stronger, more direct recommendation. The Decision can be stated firmly; fewer caveats in the body, caveats still listed at the end. |
| **Medium** | Provide a recommendation **with options**, and explain the assumptions behind each. The reader should be able to see the seams in the reasoning. |
| **Low** | **Request more information** before issuing a strong direction. The recommendation can describe what is currently known and what is missing; it must not pretend to be a finished recommendation. |

A Medium-Confidence recommendation that reads as if it were High is a
breach of the Anti-Hallucination Principle of ADR-016.

---

## 7. Anti-Patterns

The Recommendation Engine must avoid, explicitly:

1. **Image-first recommendation.** Do not start with visual style before diagnosis. A picture of a beautiful playground that does not address the diagnosed problem is decoration, not advice.

2. **Equipment list recommendation.** Do not output:

   ```
   slide + swing + climbing frame
   ```

   Equipment lists are downstream decisions, not recommendations. The
   user has not yet earned the right to ask for equipment because the
   user has not yet been told what problem the equipment would solve.

3. **Generic inspiration.** Do not recommend without context. "Create a
   natural-themed space" is not a recommendation; it is a mood board. A
   recommendation must always name the **situation**, the **decision**,
   the **reason**, and the **evidence**.

4. **False certainty.** Do not hide uncertainty. A High-Confidence label
   may not be elided. A caveat listed in the Trust Object may not be
   dropped because the recommendation "felt cleaner" without it.

These four anti-patterns are the V1 floor. New anti-patterns found in
production will be added by future ADR, not silently merged in.

---

## 8. Relationship with Other Engines

| Engine | Question it answers | Passes to Recommendation Engine |
| --- | --- | --- |
| Human Understanding (ADR-013) | Who | user goal, concerns, language preference, decision style |
| Spatial Intelligence (informs Decision) | Where | (transitively) site diagnosis, environment relationship |
| Decision Intelligence (ADR-014) | What | problem, strategy, experience logic, reasoning, boundaries |
| Trust Model (ADR-016) | Why trust | confidence, source reliability, applicability, uncertainty |
| **Recommendation Engine (this ADR)** | **How to communicate** | the final user-facing artefact |

The Recommendation Engine is the **terminal engine** in the decision
pipeline. Nothing downstream exists in V1 except (future) Feedback
Logging (ADR-018). The Engine's **only** consumer in V1 is the **product
output** stage (proposal document, customer-facing message).

---

## 9. Architectural Style Rules (inherited + new)

Inherited from the V2 Blueprint and from ADR-014 / ADR-015 / ADR-016:

1. The Recommendation Engine reads; it does **not** write back to Decision / Trust / Knowledge.
2. The Engine honours the Decision Object's Reasoning field. Silence of
   reasoning is **not** a green light to over-explain.
3. The Engine never produces a fourth Confidence label and never rounds
   Low up.
4. The Engine names its content type ("Diagnostic Recommendation" etc.).

New rule added by this ADR:

5. **The same Decision + Trust + Evidence must produce N expressions,
   not N different decisions.** Differences between audience variants
   are limited to vocabulary, emphasis, and section depth. **Strategy,
   Diagnosis, Reasoning, and Boundary fields must be preserved across
   variants.** A kindergarten-owner variant that disagrees with the
   designer variant on Strategy is a bug.

---

## 10. Non-Goals (explicit)

ADR-017 does **NOT** define:

- image generation,
- CAD generation,
- UI surfaces,
- API contracts,
- workflow implementation,
- the rendering format (Markdown vs PDF vs voice).

It defines **the shape a recommendation takes in language**. Software
that renders it (Markdown report generator today, PDF tomorrow) is a
later ADR.

---

## 11. Future Extensions

Slot allocation, after the front-matter correction in ADR-016:

| Slot | Topic | Note |
| --- | --- | --- |
| **ADR-018** | Feedback Learning Loop Contract V1 | Was ADR-017 in the V2 Blueprint placeholder; promoted one slot. The Feedback Loop **consumes** the Recommendation Engine's output to update ADR-015 Knowledge Objects and ADR-016 Trust labels. |
| **ADR-017b** | Recommendation Renderer V1 (Markdown) | Concrete renderer producing the document the customer reads. |
| **ADR-017c** | Audience Variant Library | Reusable templates for the audience variants in Section 3. |
| **ADR-017d** | Mixed-Type Recommendation Rules | Allows two content types in one document with explicit ordering rules; deferred. |

---

## 12. Acceptance Criteria

This ADR is complete when:

1. CaseOS can convert expert decisions into user-facing recommendations
   -- **DONE** by Sections 1, 2, 4.
2. Recommendations preserve reasoning and trust -- **DONE** by Section 6
   rules and the worked example in Section 4.
3. Different audiences can receive different expressions of the same
   decision -- **DONE** by Section 3 audience table and rule 5 of
   Section 9.
4. The system does not become a simple image generation tool --
   **DONE** by Section 7 anti-patterns and the Boundary field of the
   Decision Object being a runtime guardrail.

A future reviewer can take the worked example in Section 4 and write
both a kindergarten-owner variant and a designer variant **without
editing the Decision / Trust fields**. If they can do that, ADR-017 has
done its job.

---

*End of ADR-017. The next ADR slot is ADR-018 (Feedback Learning Loop Contract V1, slot-shifted from ADR-017 in the V2 placeholder table).*