# Case Knowledge Object (CKO) V1

- **Status:** Accepted (CKO V1, 2026-07-30)
- **Source of truth:** `knowledge/cases/schema/cko_schema_v1.md`

## What is a CKO

A **Case Knowledge Object (CKO)** is a complete professional
reasoning unit. It is **not** an image record and **not** a
project description. A CKO captures the **reasoning that made
a project work**, so that CaseOS can later reason about a new
space the way a senior designer would.

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

CaseOS V1 (per ADR-009) reasons about a new space through
eight stages: Cognition, Experience, Diagnosis, Strategy,
Theme, Recommendation. Each stage now needs **canonical
reference material**: what does a "good" diagnosis look
like; what does an "anchor" strategy look like in the wild;
what does "match before beauty" mean in a real project.

CKOs are that reference material. They are the **case
library** that the future Case Retrieval Engine will index
and that the Decision Engine will cite in its reasoning.

CKO is the **retrieval layer**; the Brain modules are the
**decision layer**. They are siblings, not parent-child.

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

CKOs sit between the rule layer and the Decision Engine.
They are the **evidence base** the rules and the engine
refer to.

## Folder Structure

```
knowledge/cases/
    README.md                  <-- this file
    schema/
        cko_schema_v1.md       8-section CKO definition
    examples/
        example_case.json      a full worked example
    taxonomy/
        space_types.md         spatial classification
        project_types.md       commercial / institutional
        diagnosis_types.md     positive / negative / edge
        strategy_types.md      5 strategy families + variants
        experience_tags.md     experience perception tags
```

## CKO Object Sections (V1)

A CKO has 8 sections. See `schema/cko_schema_v1.md` for
full definitions.

| # | Section | Purpose |
| --- | --- | --- |
| 0 | Case Identity | who is the case, which photo |
| 1 | Project Context | why this project exists |
| 2 | Space Cognition | what the space is |
| 3 | Experience Analysis | what the space feels like |
| 4 | Diagnosis | why it works or fails |
| 5 | Strategy | how the designer solved it |
| 6 | Recommendation Logic | when CaseOS should cite it |
| 7 | Professional Evaluation | 4-axis score + confidence |

Every CKO file in `examples/` must include all 8 sections.
A CKO with a missing section is incomplete and is **not**
indexed by the Retrieval Engine.

## Field Conventions

- Strings use **searchable, factual descriptors**. No
  marketing adjectives. No prohibited words (matching the
  `knowledge/brain/recommendation/README.md` "language
  discipline": striking, beautiful, amazing, impressive,
  iconic, world-class, ultimate, perfect).
- Enumerated fields use the controlled vocabulary in
  `taxonomy/` files. A CKO that introduces an unknown
  vocabulary value is rejected at index time.
- Scores are integers or `0..1` floats. Confidence is
  always `0..1`.
- Optional fields use `null` or are omitted.
- `image_reference` is a relative path under `data/`
  (e.g., `data/images/cases/017.jpg`). Absolute paths are
  rejected.
- IDs are CKO V1 format: `CKO-<4-digit-index>`. The index
  is allocated by the CKO Librarian in the next sprint.

## Relationship to Other Layers

| This folder | Reads from | Writes to |
| --- | --- | --- |
| `schema/` | `docs/standards/CaseOS_Constitution_V1.md`, `knowledge/brain/` modules | -- |
| `examples/` | `schema/cko_schema_v1.md`, `taxonomy/` | (the Retrieval Engine will read) |
| `taxonomy/` | existing `knowledge/taxonomy/` (age/color/material/etc.) | `schema/`, the index |

CKOs do not depend on any database, any AI extraction, or
any vector store in V1. The schema is **runtime-neutral**;
it is knowledge.

## Out of Scope (V1)

- CKO database schema (separate `database/CaseOS_Database_Schema_V1.md`).
- Vector search index over CKO embeddings.
- AI extraction pipeline (Vision --> CKO auto-fill).
- Case Retrieval Engine (separate sprint).

## Maintenance

- Schema change requires ADR (CKO is a binding contract
  with the future Retrieval Engine).
- New taxonomy leaf in an existing file: allowed without
  ADR.
- New taxonomy file (new classification axis): allowed
  without ADR.
- New CKO example: allowed without ADR; must pass schema
  validator before commit.
- Renaming a CKO field: breaking change, requires ADR.
