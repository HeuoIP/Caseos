# CaseOS Docs

This directory holds the canonical documentation for CaseOS. We follow
three layers:

- **Standard** (rules / behavior) lives in `docs/standards/`.
- **Knowledge** (content) lives in `knowledge/` (long-lived taxonomies, libraries).
- **Schema** (data shape) lives in `schemas/`.

## Index

| Section | Purpose | Path |
| --- | --- | --- |
| Product | What CaseOS is, who it is for, what V1 does | `product/Product.md` |
| Architecture | System flow at a glance | `architecture/Architecture.md` |
| Tech Stack | Decisions: language, model, infra | `architecture/TechStack.md` |
| Standards | Vision rules, ontology rules, prompt rules | `standards/` |
| Benchmark | Reserved for future eval and benchmark work | `benchmark/` |

## Subdirectories

- `product/` — Product framing. No tech, no infra.
- `architecture/` — System flow and tech decisions.
- `standards/` — Authoritative specs (Vision, Ontology, Prompt Principles):
  - `CaseOS_Vision_Standard_V1.md`
  - `Playground_Ontology_V1.md`
  - `Prompt_Principles.md`
- `benchmark/` — Reserved for future benchmarking artifacts.

## Schemas and Knowledge

Schemas and knowledge artifacts are spread across two locations:

- `../knowledge/` — long-lived knowledge JSON / libraries:
  - `taxonomy/theme/` — 41 leaf theme MDs (one per theme), plus `README.md` index.
  - `taxonomy/style/` — 8 style leaves + `README.md`.
  - `taxonomy/site_type/` — 8 site-type leaves + `README.md`.
  - `taxonomy/age_group/` — 6 age-group leaves + `README.md`.
  - `taxonomy/play_behavior/` — 13 play-behavior leaves + `README.md`.
  - `taxonomy/functional_unit/` — 10 functional-unit leaves + `README.md`.
  - `taxonomy/material/` — 10 material leaves + `README.md`.
  - `taxonomy/color/` — 12 color leaves + `README.md`.
  - `playground_ontology_v1.json` — playground ontology (6 groups + 5 stage journey).
- `../schemas/` — input/output schemas:
  - `case_analysis_v2.json` — vision analysis output (12 groups, free text).
  - `case_analysis_v3.json` — vision analysis output (stable-ID taxonomy fields).
  - `output/CaseOS_Output_Schema_V1.md` — output contract for one case.
