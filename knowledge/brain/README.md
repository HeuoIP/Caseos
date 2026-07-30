# CaseOS Brain

> The cognitive knowledge architecture of CaseOS.
> Established by ADR-009 (Accepted 2026-07-30).

The Brain is the **knowledge layer** that supports the Decision
Engine. The Decision Engine is the **runtime implementation**.
The Brain has no code; the Decision Engine has no opinions.

## Purpose

The Brain transforms accumulated design reasoning into
**structured knowledge layers**. Each layer is one module;
each module has the same six-section shape (Purpose, Core
Principles, Decision Rules, Inputs, Outputs, Examples).

The Brain is **read by the Decision Engine**, **amended by ADR**,
**queried by future user-facing products**, and **referenced by
the Constitution**.

## The nine modules

The Brain has nine modules, in pipeline order:

```text
Constitution
   |
   v
Client Understanding
   |
   v
Project Fit
   |
   v
Space Cognition
   |
   v
Experience Perception
   |
   v
Diagnosis
   |
   v
Strategy
   |
   v
Theme Strategy
   |
   v
Recommendation
```

| # | Module | Role |
| --- | --- | --- |
| 0 | `constitution/` | The philosophy layer. Every module obeys. |
| 1 | `client_understanding/` | Understand who the client is and why the project exists. |
| 2 | `project_fit/` | Evaluate whether project goals match reality. |
| 3 | `space_cognition/` | Understand what kind of space exists. |
| 4 | `experience_perception/` | Understand how people experience the space. |
| 5 | `diagnosis/` | Identify why a space feels good or bad. |
| 6 | `strategy/` | Determine transformation direction. |
| 7 | `theme_strategy/` | Determine theme direction. |
| 8 | `recommendation/` | Convert strategy into solution direction. |

## Why nine, not one

A single "Brain" document cannot capture the depth required by
each stage. A nine-module structure lets each stage be:

- **read independently** (a future contributor can read
  `strategy/` without reading `space_cognition/`);
- **tested independently** (a future test can target one module "s
  decision rules without involving the others);
- **amended independently** (a future Sprint can revise
  `theme_strategy/` "s vocabulary without touching `diagnosis/`).

The cost is nine documents to maintain instead of one. The
benefit is **focused depth at every stage of reasoning**.

## The six-section template

Every Brain module "s README has the same six sections:

1. **Purpose** -- why the module exists, what job it does.
2. **Core Principles** -- the philosophical foundation that the
   module cannot violate.
3. **Decision Rules** -- the operational patterns the module
   follows when reasoning.
4. **Inputs** -- what the module reads from upstream modules.
5. **Outputs** -- what the module writes for downstream modules.
6. **Examples** -- concrete cases showing the module in action.

The template is **binding**. A module that omits any section
must justify the omission in its Maintenance subsection.

## Layering with the rest of CaseOS

The Brain is one layer of CaseOS. It sits between the philosophy
layer (Constitution, Decision Principles, DPs) and the runtime
layer (Decision Engine).

| Layer | Location | Role |
| --- | --- | --- |
| **Constitution** | `docs/standards/CaseOS_Constitution_V1.md` | The philosophy. |
| **Decision Principles** | `docs/standards/CaseOS_Decision_Principles_V1.md` | The four operational principles. |
| **Top-Level Principles** | `knowledge/decision_rules/Space_Decision_Principles.md` | The ten space-decision principles. |
| **Design Principles** | `knowledge/principles/` | The three must-not-skip rules. |
| **Brain (this folder)** | `knowledge/brain/` | The cognitive knowledge, module by module. |
| **Decision Model V1** | `knowledge/decision_model/` | The runtime reasoning model. |
| **Expert Handbook** | `knowledge/expert_handbook/` | The operational handbook. |
| **Knowledge Libraries** | `knowledge/{goals,strategies,reasoning,objects,taxonomy}/` | The content. |
| **Domain Packs** | `knowledge/taxonomy/`, `knowledge/objects/`, `docs/knowledge/Playground_Domain_Pack_V1.md` | The industry-specific content. |

When two layers disagree, the **higher** layer wins. The
Constitution outranks the Brain outranks the Domain Packs.

## Relationship to existing folders

- **`knowledge/decision_model/`** describes the **runtime
  reasoning** (Context Model, Project Fit Model, Strategy
  Model). The Brain "s `project_fit/`, `strategy/`, and
  `recommendation/` modules describe the **cognitive
  knowledge** behind those runtime stages. The two folders
  reference each other; they are not duplicates.
- **`knowledge/principles/`** (DP-001, DP-002, DP-003) carries
  the three must-not-skip rules. The Brain "s `constitution/`
  and `diagnosis/` modules cite the DPs as binding.
- **`knowledge/expert_handbook/`** carries the deep operational
  methods. The Brain modules cite relevant chapters as depth
  resources.

## Reading order for a new contributor

1. This README.
2. ADR-009 (the source of this architecture).
3. `constitution/README.md` -- the philosophy every module obeys.
4. Each remaining module "s README, in pipeline order, from
   `client_understanding/` to `recommendation/`.
5. `knowledge/decision_model/` -- how these modules are
   operationalised by the runtime pipeline.

## Reading order for a future module author

1. This README.
2. ADR-009.
3. The module "s parent: Constitution + Decision Principles +
   the existing module whose output your module consumes.
4. The six-section template, applied verbatim.
5. Three concrete examples in the Examples section, each
   showing the module "s decision rules in action.

## Maintenance

- The nine-module structure is **stable**. Reordering or
  removing a module is a breaking change and requires ADR.
- Adding a new module is allowed; promoting a new module to
  Accepted status requires ADR.
- Amending an existing module "s content (a new Decision Rule,
  a new vocabulary term, a new Example) is allowed without
  ADR as long as the module "s six-section shape is preserved.
- Changing the **six-section template** itself is a breaking
  change to the Brain "s interface and requires ADR.
- The folder `Level_1_Space_Cognition_OBSOLETE/` (preserved
  for history) is **not** part of the Brain "s V1 architecture
  and is excluded from the maintenance rules above.

## References

- ADR-009 -- CaseOS Brain Knowledge Architecture V1.
- ADR-005 -- Decision Intelligence Architecture.
- ADR-006 -- Project Fit Intelligence Architecture.
- ADR-007 -- CaseOS Constitution V1 (lives at
  `docs/standards/CaseOS_Constitution_V1.md`).
- ADR-008 -- Vision Output Schema Canonical V3.
- `docs/standards/CaseOS_Constitution_V1.md`.
- `docs/standards/CaseOS_Decision_Principles_V1.md`.
- `knowledge/principles/DP-001_Primary_Function_First.md`,
  `DP-002_Space_First_Object_Second.md`,
  `DP-003_Match_Before_Beauty.md`.
- `knowledge/decision_model/Decision_Model_V1.md`.
- `knowledge/expert_handbook/01_Space_Decision_Method.md` through
  `10_Interview_Log.md`.
