# CaseOS Docs

All CaseOS documentation lives in this folder.

The 7 subfolders correspond to the 3 input types Codex receives plus
4 supporting documentation categories.

## Folder map

| Folder | Star | Purpose | Input type |
| --- | --- | --- | --- |
| `architecture/` | ADR | Architecture Decision Records, high-level architecture maps, retired V1 product doc | ADR |
| `standards/` | Vision Standard | Vision Engine, Constitution, Decision Principles, and other behavioural rules | -- |
| `schemas/` | JSON Schema | Output schema documentation (the actual JSON files stay in `schemas/` at repo root) | -- |
| `database/` | Database Design | Database schema design and migrations | -- |
| `knowledge/` | Knowledge Rules | Domain-pack ontology, prompt principles, expert handbook | -- |
| `sprints/` | Sprint Records | Sprint task specs, completion logs, and Pivot Cleanup records | Sprint Task |
| `reviews/` | Sprint Review | Architecture reviews and retrospectives | Review Checklist |
| `product/` | Product Blueprint | Current product spec (Blueprint V1); the highest-level product reference | -- |

## Input types (from the user)

The user provides exactly three input types; this folder structure
mirrors them:

  1. **ADR** (Architecture Decision Record)
     -> written into `architecture/` as `ADR-NNN-*.md`
  2. **Sprint Task** (development task)
     -> written into `sprints/` as `Sprint_NN_*.md`
  3. **Review Checklist** (acceptance / sign-off)
     -> written into `reviews/` as `Review_<topic>_<date>.md`

## Where things live

### Standards
- `standards/CaseOS_Constitution_V1.md` -- the permanent philosophy.
- `standards/CaseOS_Decision_Principles_V1.md` -- the four operational principles.
- `standards/CaseOS_Vision_Standard_V1.md` -- how the Vision Engine analyses a space photo (24 sections, themed by domain pack).

### Knowledge rules
- `knowledge/Playground_Domain_Pack_V1.md` -- the playground domain pack (the first domain pack, not the only one; see the new positioning).
- `knowledge/Prompt_Principles.md` -- the 10 prompt rules all prompts must obey.

### Schemas
- `schemas/CaseOS_Output_Schema_V1.md` -- output schema doc (Markdown).
- Runtime JSON schemas live at repo root `schemas/case_analysis_v3.json` (canonical, per ADR-008) and `schemas/case_analysis_v2.json` (deprecated, kept for one release).

### Database
- `database/CaseOS_Database_Schema_V1.md` -- DB design V1.
- Runtime DB migrations will live under `database/` at repo root (when implemented).

### Architecture
- `architecture/Architecture.md` -- pointer to the authoritative architecture docs.
- `architecture/TechStack.md` -- tech stack decisions.
- `architecture/CaseOS_Product_V1_OBSOLETE.md` -- V1 product doc, **retired** by Sprint 12 (Sprint 12 Pivot Cleanup). The current product spec is `product/CaseOS_Product_Blueprint_V1.md`.
- `architecture/README.md` -- ADR convention + index of active ADRs.

### Product
- `product/CaseOS_Product_Blueprint_V1.md` -- the current product spec. Replaces the retired `architecture/CaseOS_Product_V1_OBSOLETE.md`.

### Sprints
- `sprints/Sprint_08_Product_Layer.md` -- Product Layer sprint record.
- `sprints/Sprint_09_Decision_Intelligence.md` -- Decision Intelligence sprint record.
- `sprints/Sprint_09_Review_Checklist.md` -- acceptance for Sprint 09.
- `sprints/Sprint_09_Review_Demo.md` -- demo Markdown report for the Sprint 09 review.
- `sprints/Sprint_12_Pivot_Cleanup.md` -- the documentation cleanup that aligned the docs surface with the AI Space Advisor pivot.
- `sprints/theme_extension_log.md` -- completion log of the theme extension work (moved from `docs/knowledge/` by Sprint 12).
- `sprints/README.md` -- sprint convention + template.

### Reviews
- `reviews/Architecture_Review_2026_07.md` -- 2026-07 architecture review that motivated the pivot.
- `reviews/System_Review_2026_07_30.md` -- 2026-07-30 system review; the Sprint 12 backlog originates here.

## Reading order for a new contributor

1. `README.md` (root) -- one-paragraph positioning + the four founding principles.
2. `architecture/Architecture.md` -- where every layer lives.
3. `product/CaseOS_Product_Blueprint_V1.md` -- what the product is becoming.
4. `standards/CaseOS_Constitution_V1.md` -- the philosophy.
5. `standards/CaseOS_Decision_Principles_V1.md` -- the four operational principles.
6. `standards/CaseOS_Vision_Standard_V1.md` -- how Vision works.
7. `knowledge/Playground_Domain_Pack_V1.md` -- what the playground domain pack covers (and, by implication, what future domain packs must add).
8. `knowledge/Prompt_Principles.md` -- how prompts are written.
9. `schemas/CaseOS_Output_Schema_V1.md` -- what the output looks like.
10. `database/CaseOS_Database_Schema_V1.md` -- how data is stored.
11. `reviews/Architecture_Review_2026_07.md` -- what changed and why (the pivot).
12. Latest `sprints/Sprint_NN_*.md` -- what is being built now.

## Reading order for an architecture reviewer

1. `architecture/README.md` -- index of accepted ADRs.
2. `architecture/ADR-005-decision-intelligence.md` -- the 6-stage Agent pipeline.
3. `architecture/ADR-005a-decision-intelligence-constitution-cross-ref.md` -- the Constitution cross-reference.
4. `architecture/ADR-006-project-fit-intelligence.md` -- the Project Fit layer.
5. `architecture/ADR-006a-project-fit-acceptance.md` -- the acceptance record.
6. `architecture/ADR-008-vision-output-schema-canonical.md` -- V3 is canonical.
7. `standards/CaseOS_Constitution_V1.md` and `standards/CaseOS_Decision_Principles_V1.md` -- the philosophy and the implementation guide.
