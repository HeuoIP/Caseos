# CaseOS Docs

All CaseOS documentation lives in this folder.

The 7 subfolders correspond to the 3 input types Codex receives plus
4 supporting documentation categories.

## Folder map

| Folder | Star | Purpose | Input type |
| --- | --- | --- | --- |
| `architecture/` | ADR | Architecture Decision Records, high-level architecture maps, product positioning | ADR |
| `standards/` | Vision Standard | How the vision engine / taxonomy should behave | -- |
| `schemas/` | JSON Schema | Output schema documentation (the actual JSON files stay in `schemas/` at repo root) | -- |
| `database/` | Database Design | Database schema design and migrations | -- |
| `knowledge/` | Knowledge Rules | Domain ontology, prompt principles, expert handbook | -- |
| `sprints/` | Sprint Records | Sprint task specs and completion logs | Sprint Task |
| `reviews/` | Sprint Review | Architecture reviews and retrospectives | Review Checklist |

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
- `standards/CaseOS_Vision_Standard_V1.md` -- how the Vision engine
  analyzes a playground image (24 sections).

### Knowledge rules
- `knowledge/Playground_Ontology_V1.md` -- playground domain ontology
  (children, play behaviors, growth value, themes, space, units).
- `knowledge/Prompt_Principles.md` -- the 10 prompt rules all prompts
  must obey.

### Schemas
- `schemas/CaseOS_Output_Schema_V1.md` -- output schema doc (Markdown).
- Runtime JSON schemas live at repo root `schemas/case_analysis_v3.json`.

### Database
- `database/CaseOS_Database_Schema_V1.md` -- DB design V1.
- Runtime DB migrations will live under `database/` at repo root
  (when implemented).

### Architecture
- `architecture/Architecture.md` -- high-level architecture map.
- `architecture/TechStack.md` -- tech stack decisions.
- `architecture/Product.md` -- product positioning (V1).
- `architecture/README.md` -- ADR convention + template.

### Sprints
- `sprints/theme_extension_log.md` -- log of theme extension work.
- `sprints/README.md` -- sprint convention + template.

### Reviews
- `reviews/Architecture_Review_2026_07.md` -- 2026-07 architecture review.

## Reading order for a new contributor

1. `architecture/Product.md` -- what is CaseOS?
2. `architecture/Architecture.md` -- how is it built?
3. `architecture/TechStack.md` -- what is it built with?
4. `standards/CaseOS_Vision_Standard_V1.md` -- how does Vision work?
5. `knowledge/Playground_Ontology_V1.md` -- what is the domain?
6. `knowledge/Prompt_Principles.md` -- how are prompts written?
7. `schemas/CaseOS_Output_Schema_V1.md` -- what does the output look like?
8. `database/CaseOS_Database_Schema_V1.md` -- how is data stored?
9. `reviews/Architecture_Review_2026_07.md` -- what changed and why?
10. Latest `sprints/Sprint_NN_*.md` -- what is being built now?