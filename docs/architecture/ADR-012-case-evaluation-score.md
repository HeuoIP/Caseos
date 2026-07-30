# ADR-012: Case Evaluation Score V1

- **Status:** Accepted
- **Date:** 2026-07-30
- **Sprint:** 19 (continued)
- **Layer:** Knowledge / Retrieval (Case Knowledge)
- **Affects:** `knowledge/cases/`
- **Schema impact:** schema v1.1 -> schema v1.2 (non-breaking additive extension)
- **Source of truth:** `knowledge/cases/schema/cko_schema_v1.md` Section 9

---

## Context

CKO evaluation has been growing:

- **Section 7 (V1.0)** -- Project Quality, 4 axes, 0..10 int. Answers "how good is this project?".
- **Section 8 (V1.1, ADR-011)** -- Learning Value, 5 axes, 0..1 float. Answers "how much can this case teach us?".

A third question was still implicit:

- **Is this case worth keeping in the CKO library at all?**
- **Can this case be transferred to other project types?**

Section 7 and Section 8 measure **quality and teachability**; they do not measure **intake value** or **transferability**. A high-photogenic / low-logic case can score well on Section 7 yet fail as a CKO candidate. A high-logic case from a context that does not apply elsewhere can pass Section 7 yet need a guard.

This ADR closes the gap with Section 9.

---

## The Three Evaluation Layers (V1.2)

To prevent future confusion, V1.2 documents three orthogonal scoring layers.

| Layer | Section | Answer | Scale | Cardinal axes |
| --- | --- | --- | --- | --- |
| Project Quality | Section 7 | How good is this project? | 0..10 int | design, experience, innovation, commercial |
| Learning Value | Section 8 | How much can this case teach us? | 0..1 float | space_logic, experience_logic, theme_logic, user_logic, commercial_logic |
| **Case Evaluation** | **Section 9 (NEW)** | **Is this case worth keeping + is it transferable?** | **0..100 weighted, plus transferability object** | **space_logic, experience_logic, theme_meaning_logic, user_value, commercial_logic** |

The three layers are **orthogonal by design**: a case can score high on one and low on another. Section 9 is the **GATE** -- it decides whether the case becomes a Candidate Golden Case, a Priority Golden Case, or stays a Reference Case.

Different consumers read different layers:

- **Decision Engine** reads Section 7 (quality) and Section 9 (gate) to decide whether to **cite** a case.
- **Retrieval Engine** reads Section 8 (teachability) and Section 9 (transferability) to decide whether to **surface** a case.
- **CKO Librarian** reads Section 9 alone to decide whether to **admit** a case.

---

## Decision 1. Section 9 -- Case Evaluation Score

### Weights and ranges

| Dimension | Weight | Range | Question |
| --- | --- | --- | --- |
| Space Logic | 25 | 0..25 | Why does this space work spatially? |
| Experience Logic | 25 | 0..25 | Why do users want to stay? |
| Theme & Meaning Logic | 20 | 0..20 | Why is this space memorable? |
| User Value Logic | 15 | 0..15 | Why do different users accept this space? |
| Commercial Logic | 15 | 0..15 | Why does this project create value? |
| **Total** | **100** | **0..100** | Sum of above |

The five weights sum to **100**. The schema requires the writer to also record `total_score` explicitly; the future CKO Validator will check that `total_score == sum of the five weighted components`.

### Per-dimension evaluation criteria

#### Space Logic (weight 25)

Core question: *why does this space work spatially?*

Evaluate: relationship between architecture and site; spatial organization; scale and proportion; circulation; spatial hierarchy; visual focus.

Low: only object placement, no spatial logic. High: clear spatial structure, strong relationship between elements, good user movement experience.

#### Experience Logic (weight 25)

Core question: *why do users want to stay?*

Evaluate: child behavior; exploration; challenge; interaction; social play; emotional connection; repeatability; memory creation.

Low: single-function experience. High: complete experience journey (entry -> exploration -> challenge -> interaction -> memory).

#### Theme & Meaning Logic (weight 20)

Core question: *why is this space memorable?*

Theme does NOT only mean: IP character, artificial decoration, visual style. Theme can also be: natural exploration, ecological experience, cultural meaning, environmental relationship.

Evaluate: theme positioning; storytelling; emotional connection; consistency between environment and experience.

#### User Value Logic (weight 15)

Core question: *why do different users accept this space?*

Children: play suitability, attraction, growth value.

Parents: trust, emotional response, willingness to share.

Operators: management, maintenance, practical value.

#### Commercial Logic (weight 15)

Core question: *why does this project create value?*

Evaluate: attraction ability, communication value, customer response, operational potential, investment efficiency.

Important: commercial success cases should be studied even if design style differs from CaseOS preference. Successful business loops may reveal hidden knowledge.

---

## Decision 2. Case Transferability (NOT in score)

Transferability is a **separate attribute**, not part of `total_score`. It judges whether a case can be transferred to other projects.

```
transferability:
    level: high | medium | low
    applicable_project_types: []   # values from taxonomy/project_types.md
    limitations: []                # explicit caveats
```

Why separated: A world-class theme park may have a high Section 9 score but low transferability to kindergarten. Keeping transferability out of the score preserves the meaning of the 100-point scoring -- the score stays about *quality and reasoning*, not about *where you can apply it*.

### Level semantics

| Level | Meaning |
| --- | --- |
| `high` | The case "s logic transfers to most project types with little adaptation. Standard cases. |
| `medium` | The case transfers to several project types with adaptation. Useful for portfolio reach. |
| `low` | The case is context-bound (climate, budget, scale, programme). Citable only when context matches. |

### Constraints

- `applicable_project_types` is a non-empty array of values from `taxonomy/project_types.md`.
- `limitations` is a non-empty array. Even `high` cases need limitations (a Forest case still needs trees).

---

## Decision 3. Golden Case Threshold (operational)

The Section 9 score is the gate. The threshold defines three operational classes:

| Class | Threshold | Meaning |
| --- | --- | --- |
| Priority Golden Case | `total_score >= 90` | Always-citable, indexed first. |
| Candidate Golden Case | `80 <= total_score < 90` | High-priority, indexed normally. |
| Reference Case | `total_score < 80` | Browseable; cited only on direct match. |

The thresholds (`90` and `80`) are **operational tuning parameters** and may be revised by ADR. They are NOT schema fields; they are policy applied at retrieval / Librarian time.

---

## Schema Impact (v1.2)

`knowledge/cases/schema/cko_schema_v1.md` becomes `cko_schema_v1.2` (non-breaking additive extension).

Changes:

1. Header version bumped to **1.2**.
2. Section 9 added: `case_evaluation` object with five weighted scores + `total_score` + `transferability` object.
3. Sections 0..8 (incl. knowledge_source, learning_value) unchanged.

Required-vs-optional policy:

- `case_evaluation.total_score` MUST equal the sum of the five weighted components (CKO Validator will check).
- `case_evaluation.transferability.limitations` MUST be non-empty.
- `case_evaluation.transferability.applicable_project_types` MUST be non-empty.

This is non-breaking for Schema V1 / V1.1 consumers that ignore unknown fields. The CKO example is updated atomically with this ADR.

---

## Field Definitions (full)

### case_evaluation

| Field | Type | Required | Range | Description |
| --- | --- | --- | --- | --- |
| `case_evaluation.space_logic_score` | float | yes | 0..25 | Why the space works spatially. |
| `case_evaluation.experience_logic_score` | float | yes | 0..25 | Why users want to stay. |
| `case_evaluation.theme_meaning_logic_score` | float | yes | 0..20 | Why the space is memorable. |
| `case_evaluation.user_value_score` | float | yes | 0..15 | Why different users accept it. |
| `case_evaluation.commercial_logic_score` | float | yes | 0..15 | Why the project creates value. |
| `case_evaluation.total_score` | float | yes | 0..100 | Sum of the five weighted components. Validator checks the sum. |
| `case_evaluation.transferability.level` | enum | yes | `high` / `medium` / `low` | Whether the case applies elsewhere. |
| `case_evaluation.transferability.applicable_project_types` | array of enum | yes | non-empty | Where this case can be applied. Values from `taxonomy/project_types.md`. |
| `case_evaluation.transferability.limitations` | array of strings | yes | non-empty | What to watch when transferring. |

---

## Relationship to Sections 7 and 8

A case that scores high on Section 7 (great project quality) and high on Section 8 (great teachability) MAY still not be a Golden Case -- if Section 9 says the case is not transferable or has weak commercial logic, the gate downgrades it to Reference Case only.

Conversely, a case that scores low on Section 7 (modest project) but high on Section 8 (great teachability) AND high on Section 9 (great transferable logic) becomes a Golden Case. Section 9 is the **admission score**; Sections 7 and 8 are **descriptors** that the consumers read.

Example: A modest forest kindergarten with brilliant spatial logic, clear experience logic, and high transferability scores:

- Section 7: 8/9/6/5 (moderate project score)
- Section 8: 0.85/0.90/0.75/0.80/0.50 (avg 0.76, teaches well)
- Section 9: 22+23+16+13+7 = **81** (Candidate Golden, despite modest commercial)

---

## Maintenance

- Adding a new field to `case_evaluation`: breaking change, ADR.
- Renaming any field: breaking, ADR.
- Changing any weight (25/25/20/15/15): breaking, ADR.
- Changing any range (`0..25` to other): breaking, ADR.
- Changing any Golden threshold (80, 90): operational parameter, ADR.
- Adding a new value to `transferability.level`: breaking, ADR.

---

## Out of Scope (V1.2)

- Auto-scoring by LLM (scores are filled by CKO Librarian, not AI).
- Per-segment user score (children / parents / operators sub-scores). Future work.
- Composite Section 9 score + transferability into a single "admissibility" vector. Future work.
- Case-quality regression over time (Section 9 score drift across cases).

---

## Non Goals

This ADR does not deliver any runtime capability. It locks the schema, weights, and gate policy at V1.2.
