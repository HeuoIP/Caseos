# ADR-011: CKO Learning Source & Value Model V1

- **Status:** Accepted
- **Date:** 2026-07-30
- **Sprint:** 19
- **Layer:** Knowledge / Retrieval (Case Knowledge)
- **Affects:** `knowledge/cases/`
- **Schema impact:** schema v1 -> schema v1.1 (non-breaking
  additive extension)

---

## Context

CKO V1 (knowledge/cases/) is designed to transform
external excellent design cases into professional
reasoning assets.

A CKO is not an image record. A CKO captures the
**reasoning that made a project work**, the
**conditions under which it applies**, and the
**design logic that can be learned**.

Two questions were left open in ADR-009 / Sprint 17 CKO:

1. **Where do CKOs come from?** Internal projects vs.
   external excellent cases vs. AI-generated cases vs.
   crowdsourced contributions.
2. **How do we measure whether a CKO is worth
   keeping?** The Section 7 four-axis evaluation scores
   **how good the project is**; they do **not** measure
   **how much the project can teach us**.

This ADR closes both questions at V1.

---

## Decision 1. Knowledge Source

CKO V1 only ingests one knowledge source:

```
knowledge_source: external_excellent_case
```

Internal company projects, client deliverables, AI-
generated cases, and crowdsourced contributions are
**explicitly excluded** from V1. The first objective is
building **industry-level spatial intelligence**, not
company-style imitation, not vendor imitation, not user-
generated imitation.

A CKO whose origin is anything other than
`external_excellent_case` is rejected at V1.

### Future sources (each requires ADR to enable)

| Value | When it may be enabled |
| --- | --- |
| `design_firm_award_shortlist` | When CaseOS ingests an industry awards feed (e.g., WLA, IPA). |
| `academic_case_study` | When a peer-reviewed case is added with citation. |
| `internal_company_case` | When CaseOS has its own delivery history worth canonicalising. **At least V3.** |
| `partner_contributed` | When a partner firm donates anonymised case material. |
| `ai_synthetic_case` | When the AI can synthetically design a case that meets all gates. **At least V3, with strong rationale.** |

### Why external first

- Industry intelligence is the highest-value asset the
  system needs to develop fast.
- Internal cases are biased by the firm "s house
  style; using them as the first source would lock in
  the firm "s aesthetic as "industry".
- External cases force CaseOS to reason across
  vocabularies, materials, climate, culture -- which
  is the very reasoning V1 needs to learn.

---

## Decision 2. Learning Value Model

CKO V1 carries a **`learning_value`** record that scores
**how much a case can teach** along five axes. Each axis
is an independent `0..1` float. The five axes are
distinct and not redundant with Section 7 "s evaluation
scores; they answer a different question.

```
learning_value:
  space_logic:        0..1
  experience_logic:   0..1
  theme_logic:        0..1
  user_logic:         0..1
  commercial_logic:   0..1
```

### Axis 1. Space Logic

**Question:** Why does this space work spatially?

**Evaluates:**
- spatial organization
- relationship between architecture and site
- scale
- circulation
- spatial hierarchy

### Axis 2. Experience Logic

**Question:** Why do users want to stay?

**Evaluates:**
- child behavior
- interaction
- exploration
- challenge
- repeatability

### Axis 3. Theme Logic

**Question:** Why is this space memorable?

**Evaluates:**
- story
- identity
- visual language
- emotional connection

### Axis 4. User Logic

**Question:** Why do different users accept this space?

**Evaluates:**
- child suitability
- parent perception
- teacher / operator experience

### Axis 5. Commercial Logic

**Question:** Why does this project create value?

**Evaluates:**
- attraction value
- communication value
- operational potential

### Distinction from Section 7 Evaluation

| | Section 7 Evaluation | Section 8 Learning Value |
| --- | --- | --- |
| Question | How good is this project? | How much can it teach us? |
| Scale | 0..10 integer per axis | 0..1 float per axis |
| Cardinal axes | design, experience, innovation, commercial | space, experience, theme, user, commercial |
| A case can score | High on experience, low on commercial | High on space_logic, low on commercial_logic |
| Reject condition | Score 0 on any axis | All axes 0 = dropped at index time |

A case that scores **10** on `commercial_value_score` but
**0.2** on `theme_logic` is **excellent but not very
teachable for theme**.

A case that scores **0.4** on `experience_score` (i.e.,
modest) but **0.9** on `experience_logic` is **modest but
extremely teachable for experience**.

These are different filters and both matter.

---

## Decision 3. CKO Quality Principle

> **A beautiful image does not equal a valuable case.**

A CKO Library must apply a quality gate at intake:

### Low-value cases (rejected at V1)

- **only an attractive rendering** (no reasoning visible).
- **only a colour inspiration** (no space, no behaviour,
  no theme logic).
- **only an equipment display** (no spatial
  organisation).

### High-value cases (welcomed at V1)

- **clear space logic** (the spatial argument is
  readable from the CKO evidence).
- **clear experience logic** (the behaviour argument is
  readable).
- **reusable design principles** (the CKO cites
  Constitution principles, DPs, Brain module sections,
  or Expert Handbook rules).

### Threshold policy

A CKO whose average `learning_value` is below **0.4** is
flagged for manual review at V1 and dropped at V2.

This threshold is itself a tuning parameter and can be
revised by ADR.

---

## Schema Impact

`knowledge/cases/schema/cko_schema_v1.md` becomes
**cko_schema_v1.1** (non-breaking additive extension).
The changes:

1. **Section 0 Case Identity** gains a new
   `knowledge_source` field.
   - Type: enum, currently the single value
     `external_excellent_case`. The enum is forward-
     declared so future values can be added by ADR.

2. **New Section 8 Learning Value** added.
   - `learning_value` object with five float fields
     each `0..1`.

Required-vs-optional policy:

- `knowledge_source` is **required** (Section 0
  required-field list grows).
- `learning_value` is **required** (a CKO without
  learning value is not a case, it is a picture).

This is non-breaking for **Schema V1 consumers** only if
those consumers ignore unknown fields. The CKO example
file is updated atomically with this ADR.

---

## Field Definitions (full)

### knowledge_source

| Field | Type | Required | Allowed values |
| --- | --- | --- | --- |
| `knowledge_source` | enum | yes | `external_excellent_case` (V1; future values require ADR) |

### learning_value

| Field | Type | Required | Range |
| --- | --- | --- | --- |
| `learning_value.space_logic` | float | yes | `0..1` |
| `learning_value.experience_logic` | float | yes | `0..1` |
| `learning_value.theme_logic` | float | yes | `0..1` |
| `learning_value.user_logic` | float | yes | `0..1` |
| `learning_value.commercial_logic` | float | yes | `0..1` |

---

## Maintenance

- Adding a new value to `knowledge_source`: requires ADR.
- Removing a `knowledge_source` value still in use:
  requires ADR.
- Renaming any `learning_value` axis: requires ADR.
- Adding a new `learning_value` axis: requires ADR.
- Lowering the **average** threshold from `0.4` to
  another value: requires ADR.
- Changing any single-field range (`0..1` -> something
  else): requires ADR.

---

## Out of Scope (V1)

- Internal case ingestion.
- AI-generated cases.
- Crowdsourced cases.
- Auto-scoring of `learning_value` by LLM (the scores
  are filled by the CKO Librarian, not by AI).
- Database schema, vector store, AI extraction pipeline.

---

## Non Goals

This ADR does not deliver any new capability. It locks
the **source** and the **value model** of CKO at V1.

