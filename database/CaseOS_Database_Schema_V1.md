# CaseOS Database Schema V1

Single source of truth for one playground case. One row = one case.

## Table: `cases`

| # | Field | Type | Description |
| --- | --- | --- | --- |
| 1 | `id` | `UUID` (PK) | Primary key. Generated on insert. |
| 2 | `title` | `TEXT` | Case title. May be the project name or a curated short label. |
| 3 | `description` | `TEXT` | One-paragraph case summary. |
| 4 | `theme` | `TEXT[]` | Theme tags. Use IDs from `CaseOS_Vision_Standard_V1.md` Theme Taxonomy, e.g. `NATURE.FOREST`. |
| 5 | `style` | `TEXT[]` | Style tags. Use Style Taxonomy IDs. |
| 6 | `site_type` | `TEXT` | Single site type. Use Site Type Taxonomy IDs (e.g. `SITE.PUBLIC_PARK`). |
| 7 | `age_group` | `TEXT[]` | Age range tags. Use Age Group Taxonomy IDs (e.g. `AGE.3_6`). |
| 8 | `play_behaviors` | `TEXT[]` | Behaviors the case supports. Use Play Behavior Taxonomy IDs. |
| 9 | `functional_units` | `TEXT[]` | Equipment / unit tags. Use Functional Unit Taxonomy IDs. |
| 10 | `materials` | `TEXT[]` | Material tags. Use Material Taxonomy IDs. |
| 11 | `colors` | `TEXT[]` | Color tags. Use Color Taxonomy IDs. |
| 12 | `design_keywords` | `TEXT[]` | Free-form design keywords (cross-cutting). |
| 13 | `quality_score` | `FLOAT` (0—1) | Quality score (0 = low, 1 = high). Used to rank candidates. |
| 14 | `embedding` | `VECTOR(N)` | Vector embedding for similarity search. N depends on the chosen embedding model. |
| 15 | `image_path` | `TEXT` | Path to the original site image. Stored on object storage (Alibaba OSS) and tracked via Git LFS in this repo. |
| 16 | `analysis_json` | `JSONB` | Raw Vision output for this case. Schema follows `schemas/case_analysis_v2.json`. |
| 17 | `created_at` | `TIMESTAMPTZ` | Insertion timestamp. Defaults to `NOW()`. |

## Required PostgreSQL Extensions

- `pgvector` — for the `embedding` column and similarity search (`<=>` operator).

## Notes

- Field order matters less; `id` and `embedding` are the most important.
- All taxonomy columns (`theme`, `style`, `age_group`, etc.) store **stable IDs**, not free Chinese / English text. This keeps filtering and joins deterministic across languages.
- `embedding` dimension (N) must match the model used for indexing. Common choices: 1024, 1536, 3072.
- `analysis_json` is a JSONB copy of `schemas/case_analysis_v2.json` for this case, so the whole vision output stays queryable from SQL.
- Vector search uses pgvector IVFFlat / HNSW index over `embedding`.
- For now only the `cases` table exists. Tag vocabularies and junction tables come in later versions when taxonomy reuse justifies them.
