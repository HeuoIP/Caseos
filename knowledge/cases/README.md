# Case Knowledge Object (CKO) V1.2

- **Status:** Accepted (CKO V1.1, 2026-07-30)
- **Source of truth:** `knowledge/cases/schema/cko_schema_v1.md`
- **Latest extension ADR:** `docs/architecture/ADR-011-cko-learning-source-value-model.md`

## What is a CKO

A **Case Knowledge Object (CKO)** is a complete professional reasoning unit. It is **not** an image record and **not** a project description. A CKO captures the **reasoning that made a project work**, so that CaseOS can later reason about a new space the way a senior designer would.

A CKO carries:

```
Case Image
  + Space Understanding
  + Problem Diagnosis
  + Design Strategy
  + Recommendation Logic
  + Applicable Conditions
```

in a single retrievable object.

## Why CKO exists

CaseOS V1 (per ADR-009) reasons about a new space through eight stages: Cognition, Experience, Diagnosis, Strategy, Theme, Recommendation. Each stage now needs **canonical reference material**: what does a "good" diagnosis look like; what does an "anchor" strategy look like in the wild; what does "match before beauty" mean in a real project.

CKOs are that reference material. They are the **case library** that the future Case Retrieval Engine will index and that the Decision Engine will cite in its reasoning.

CKO is the **retrieval layer**; the Brain modules are the **decision layer**. They are siblings, not parent-child.

## V1.1 Additions (2026-07-30)

CKO V1.1 adds two new fields, both required:

1. **`case_identity.knowledge_source`** -- restricts the CKO library at V1 to external excellent cases only. Internal projects are explicitly excluded at V1 (lock at the source).
2. **`learning_value`** -- five-axis scoring (space / experience / theme / user / commercial, each 0..1) for **how much the case can teach**, distinct from Section 7 evaluation which scores **how good the project is**.

The extension is **non-breaking and additive**: every V1 field is preserved, every existing CKO example remains valid, and a CKO Validator (future) only needs to know one new enum (the `knowledge_source` taxonomy) and one new object (`learning_value`).

Full rationale in `docs/architecture/ADR-011-cko-learning-source-value-model.md`.


## V1.2 Additions (2026-07-30)

CKO V1.2 adds a third evaluation layer, in addition to V1 "s Section 7 (project quality) and V1.1 "s Section 8 (learning value):

3. **`case_evaluation`** -- a 100-point weighted score plus a `transferability` object. This is the **gate** that decides whether a CKO is a **Priority Golden Case** (>=90), a **Candidate Golden Case** (80..89), or a **Reference Case only** (<80). Section 9 is what the CKO Librarian reads to admit or reject a case.

The V1.2 schema is non-breaking: every V1 and V1.1 field remains unchanged; the Section 9 fields are additive and required.

### The Three Evaluation Layers (V1.2)

| Layer | Section | Question | Scale |
| --- | --- | --- | --- |
| Project Quality | Section 7 | How good is this project? | 4 axes 0..10 int |
| Learning Value | Section 8 | How much can this case teach us? | 5 axes 0..1 float |
| Case Evaluation | Section 9 (NEW) | Is it worth keeping + is it transferable? | 5 weighted scores 0..100 + transferability object |

The three layers are **orthogonal by design** and feed different consumers:

- **Decision Engine** reads Section 7 (quality) and Section 9 (gate).
- **Retrieval Engine** reads Section 8 (teachability) and Section 9 (transferability).
- **CKO Librarian** reads Section 9 alone to decide admission.

Full rationale in `docs/architecture/ADR-012-case-evaluation-score.md`.

### Operational Threshold (NOT a schema field)

The CKO Librarian applies these tiers on `case_evaluation.total_score`:

- `total_score >= 90` -- **Priority Golden Case**.
- `80 <= total_score < 90` -- **Candidate Golden Case**.
- `total_score < 80` -- **Reference Case only**.

The thresholds are operational tuning parameters and may be revised by ADR; they are NOT schema fields. See ADR-012 Section "Decision 3".

### Transferability

`case_evaluation.transferability` is a separate attribute, not part of `total_score`. It carries a `level` (`high` / `medium` / `low`), an `applicable_project_types` list (non-empty, vocabulary-bound), and a `limitations` list (non-empty, free-text). A world-class theme park may have a high Section 9 score but low transferability to kindergarten; the separation preserves the meaning of both signals.

---

## CKO Quality Principle

> **A beautiful image does not equal a valuable case.**

Low-value cases (rejected at intake):

- only an attractive rendering (no reasoning visible).
- only a colour inspiration (no space, no behaviour, no theme logic).
- only an equipment display (no spatial organisation).

High-value cases (welcomed at intake):

- clear space logic (readable from the CKO evidence).
- clear experience logic (behaviour argument is readable).
- reusable design principles (cites Constitution / DPs / Brain modules / Expert Handbook).

See ADR-011 for the **Quality Gate**: a CKO whose average `learning_value` is below `0.4` is flagged for manual review at V1 and dropped at V2.

## Layer Position

```
0 Constitution         (philosophy)
  ↓
1 Brain modules         (decision knowledge, ADR-009)
  ↓
2 Decision rules        (judgment patterns, ADR-010)
  ↓
3 Case library (CKO)   <-- THIS FOLDER
  ↓
4 Decision Engine       (runtime, future)
  ↓
5 Product Layer / Agents
```

CKOs sit between the rule layer and the Decision Engine. They are the **evidence base** the rules and the engine refer to.

## Folder Structure

```
knowledge/cases/
    README.md                       <-- this file
    schema/
        cko_schema_v1.md            9-section CKO definition (V1.1)
    examples/
        example_case.json           a full worked example
    taxonomy/
        space_types.md              spatial classification
        project_types.md            commercial / institutional
        diagnosis_types.md          positive / negative / edge
        strategy_types.md           5 strategy families + variants
        experience_tags.md          experience perception tags
```

## CKO Object Sections (V1.1, 9 sections)

A CKO has 9 sections. See `schema/cko_schema_v1.md` for full definitions.

| # | Section | Purpose |
| --- | --- | --- |
| 0 | Case Identity | who is the case, which photo, source provenance |
| 1 | Project Context | why this project exists |
| 2 | Space Cognition | what the space is |
| 3 | Experience Analysis | what the space feels like |
| 4 | Diagnosis | why it works or fails |
| 5 | Strategy | how the designer solved it |
| 6 | Recommendation Logic | when CaseOS should cite it |
| 7 | Professional Evaluation | 4-axis score (0..10) + confidence (0..1) |
| 8 | Learning Value (V1.1) | 5-axis learning value (0..1) |

Section 7 and Section 8 answer different questions:

- Section 7: **how good is this project?**
- Section 8: **how much can this case teach us?**

Both are required.

Every CKO file in `examples/` must include all 9 sections. A CKO with a missing section is incomplete and is **not** indexed by the Retrieval Engine.

## Field Conventions

- Strings use **searchable, factual descriptors**. No marketing adjectives. No prohibited words (matching the `knowledge/brain/recommendation/README.md` language discipline: striking, beautiful, amazing, impressive, iconic, world-class, ultimate, perfect).
- Enumerated fields use the controlled vocabulary in `taxonomy/` files. A CKO that introduces an unknown vocabulary value is rejected at index time.
- Section 7 scores are integers in `0..10`. Section 8 `learning_value` axes are floats in `0..1`. Section 7 `confidence` is a float in `0..1`.
- Optional fields use `null` or are omitted.
- `image_reference` is a relative path under `data/` (e.g., `data/images/cases/017.jpg`). Absolute paths are rejected.
- IDs are CKO V1 format: `CKO-<4-digit-index>`. The index is allocated by the CKO Librarian in the next sprint.
- `knowledge_source` is required at V1.1 and currently only accepts `external_excellent_case`. Future values require ADR.

## Relationship to Other Layers

| This folder | Reads from | Writes to |
| --- | --- | --- |
| `schema/` | `docs/standards/CaseOS_Constitution_V1.md`, `knowledge/brain/` modules | -- |
| `examples/` | `schema/cko_schema_v1.md`, `taxonomy/` | (the Retrieval Engine will read) |
| `taxonomy/` | existing `knowledge/taxonomy/` (age/color/material/etc.) | `schema/`, the index |

CKOs do not depend on any database, any AI extraction, or any vector store in V1. The schema is **runtime-neutral**; it is knowledge.

## Out of Scope (V1.2)

- Internal case ingestion (locked at source by ADR-011).
- AI-synthesised cases (locked at source by ADR-011).
- Crowdsourced cases (locked at source by ADR-011).
- Per-segment user-score rollups in Section 9 (children / parents / operators sub-scores). Future work.
- Auto-scoring of any Section by LLM (filled by CKO Librarian, not AI).
- CKO database schema (separate `database/CaseOS_Database_Schema_V1.md`).
- Vector search index over CKO embeddings.
- AI extraction pipeline (Vision --> CKO auto-fill).
- Case Retrieval Engine (separate sprint).


## Maintenance

- Schema change requires ADR (CKO is a binding contract with the future Retrieval Engine).
- New taxonomy leaf in an existing file: allowed without ADR.
- New taxonomy file (new classification axis): allowed without ADR.
- New CKO example: allowed without ADR; must pass schema validator before commit.
- Renaming a CKO field: breaking change, requires ADR.
- Adding a new `knowledge_source` value: requires ADR (per ADR-011).
- Changing the Section 8 average threshold (default 0.4): requires ADR (per ADR-011).
- Adding a new field to `case_evaluation`: breaking change, requires ADR (per ADR-012).
- Changing any weight in Section 9 (25/25/20/15/15): breaking, requires ADR (per ADR-012).
- Changing the Golden thresholds (80, 90 default): operational tuning, requires ADR (per ADR-012).
