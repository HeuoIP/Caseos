# ADR-009: CaseOS Brain Knowledge Architecture V1

- **Status:** Accepted
- **Date:** 2026-07-30
- **Supersedes:** the experimental `knowledge/brain/Level_1_Space_Cognition/`
  structure (Sprint 16, 2026-07-30); that folder is renamed to
  `Level_1_Space_Cognition_OBSOLETE/` and kept for history reference only.
- **Superseded by:** --
- **Numbering note:** the user-supplied identifier for this ADR
  was "ADR-008". The slot ADR-008 was already taken by the Vision
  Output Schema Canonical ADR (ADR-008, Accepted 2026-07-30).
  This ADR therefore uses ADR-009 (the next available). The
  content follows the user-supplied spec verbatim.

---

## 1. Context

CaseOS aims to transform professional spatial design experience
into an AI decision system.

Previous discussions have established that the core capability
is not image generation or recommendation, but **understanding
why a space should be transformed and what direction it should
take**.

The product pivot from "AI Playground Design Assistant" to
"AI Space Advisor" was carried into ADR-005, ADR-006, ADR-007,
ADR-008, the Constitution V1, the Decision Principles V1, and
the Product Blueprint V1. An experimental Brain layer
(`Level_1_Space_Cognition/`, Sprint 16) was created but
remained isolated from the rest of the architecture.

This ADR defines the **first complete knowledge architecture
of CaseOS Brain** -- a layered, module-based design that
covers every cognitive stage from philosophy to recommendation.

## 2. Decision

Create the following knowledge architecture:

```text
knowledge/brain/

  constitution/             -- the philosophy layer
  client_understanding/     -- know who the client is
  project_fit/              -- is the project worth doing
  space_cognition/          -- what is the space like
  experience_perception/    -- how does the space feel
  diagnosis/                -- what is wrong / right
  strategy/                 -- what direction
  theme_strategy/           -- what theme
  recommendation/           -- what to recommend
```

Each module "s README contains the same six sections:

1. **Purpose** -- why the module exists.
2. **Core Principles** -- the philosophical foundation.
3. **Decision Rules** -- the operational patterns.
4. **Inputs** -- what the module reads.
5. **Outputs** -- what the module writes.
6. **Examples** -- concrete cases.

## 3. Module definitions (per the user-supplied spec)

### 3.1 Constitution

**Purpose:** Define the highest-level philosophy and constraints
of CaseOS.

**Core Principle:** "方向对了，设计才有意义。设计应先解决
正确的问题，再创造方案。" (When the direction is right, the
design has meaning. Design must solve the right problem before
creating solutions.)

### 3.2 Client Understanding

**Purpose:** Understand why the project exists.

**Analyze:**
- Motivation
- Inspiration
- Expectation
- Resource transparency

### 3.3 Project Fit

**Purpose:** Evaluate whether project goals match reality.

**Evaluate:**
- Client capability
- Space condition
- Budget / resource
- Market / environment

**Core Principle:** A successful project is not the best
condition, but the best match.

### 3.4 Space Cognition

**Purpose:** Understand what kind of space exists.

**Analyze:**
- Spatial role
- Spatial position
- Spatial characteristics
- Spatial state

### 3.5 Experience Perception

**Purpose:** Understand human experience in space.

**Analyze:**
- Scale proportion
- Spatial relationship
- Atmosphere
- Story feeling
- Imagination
- Stay desire
- Vitality

**Core Principle:** Space is not an object to observe. Space
is a relationship between people and environment.

### 3.6 Diagnosis

**Purpose:** Identify why a space feels good or bad.

**Common diagnosis:**
- Discoordination
- Overloaded
- Empty
- Lack of focus
- Lack of vitality

### 3.7 Strategy

**Purpose:** Determine transformation direction.

**Core Principles:**
- Remove before add
- Space before object
- Find spatial eye
- Concentrate value
- Restraint creates quality

### 3.8 Theme Strategy

**Purpose:** Determine theme direction.

**Theme comes from:**
- Client vision
- Environmental potential
- Space condition
- User needs

**Theme must have:**
- Story
- Extension ability
- Experience path

### 3.9 Recommendation

**Purpose:** Convert strategy into solution direction.

**Core concepts:**
- Spatial Anchor
- Core experience
- Value concentration

**Rules:**
- Large theme facility: only when space lacks a core.
- Avoid: adding multiple competing cores.
- Budget limitation: protect core value first.

## 4. Module pipeline (order of execution)

The nine modules form a pipeline, in this order:

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

Each module "s output is the next module "s input. The pipeline
is **strictly sequential** per Constitution Principle 003
(Understand before recommending).

## 5. Layer relationships

The Brain modules are layered with the rest of CaseOS:

| Layer | Where it lives | Relationship |
| --- | --- | --- |
| Constitution | `docs/standards/CaseOS_Constitution_V1.md` + this Brain module | Outranks everything |
| Decision Principles | `docs/standards/CaseOS_Decision_Principles_V1.md` | Outranks Brain modules |
| Decision Model (V1) | `knowledge/decision_model/` | Outranks Brain modules in implementation |
| **Brain modules (this ADR)** | `knowledge/brain/` | Operational depth for each pipeline stage |
| Domain Packs | `knowledge/taxonomy/`, `knowledge/objects/` | Supply content to Brain modules |

When a Brain module and a Domain Pack disagree, the Brain module
wins (the Domain Pack supplies content; the Brain module
decides).

## 6. Relationship to existing ADR-005, ADR-006

- **ADR-005** (Decision Intelligence) defined the 6-stage Agent
  pipeline (Space -> Decision Maker -> Knowledge Retriever ->
  Strategy -> Object Selector -> Explain). The Brain modules
  **expand** ADR-005 "s pipeline into 9 modules, adding Client
  Understanding, Experience Perception, and Theme Strategy as
  explicit stages.
- **ADR-006** (Project Fit Intelligence) defined the 5-dimension
  Project Fit input / 6-field output. The Brain Project Fit
  module **subsumes** ADR-006 and adds Client Understanding as
  a separate, upstream stage.

## 7. Consequences

### Positive

- The Brain is now a **complete knowledge architecture** with
  9 modules covering philosophy to recommendation.
- Each module has the same 6-section template, making them
  easy to read, easy to compare, and easy to extend.
- The architecture is **stable**: future Sprints can add
  modules (e.g. Risk, Budget, Commercial) without breaking the
  pipeline.
- The architecture is **forward-only**: later modules cannot
  silently redefine earlier modules " outputs.

### Negative / Trade-offs

- The existing `decision_model/` (Sprint 15) and `principles/`
  (Sprint 14) folders overlap with some Brain modules. The
  overlap is **not duplication**: the Decision Model describes
  the **runtime reasoning**; the Brain modules describe the
  **cognitive knowledge**. They reference each other but are
  not interchangeable.
- The experimental `Level_1_Space_Cognition/` is retired.
  Its content is preserved as `Level_1_Space_Cognition_OBSOLETE/`
  for history reference only.

### Neutral

- No code is changed.
- No schema is changed.
- No ADR-005 / ADR-006 is amended.
- The next ADR (e.g. ADR-010) is reserved for API Surface V1,
  per `docs/architecture/README.md`.

## 8. Acceptance criteria

- [x] All 9 Brain module folders exist under `knowledge/brain/`.
- [x] Each module has a `README.md` with the 6 required sections.
- [x] `knowledge/brain/README.md` exists with the architecture
      overview and module order.
- [x] `Level_1_Space_Cognition/` is renamed to
      `Level_1_Space_Cognition_OBSOLETE/` with a deprecation
      banner pointing at `space_cognition/`.
- [x] No code change. No schema change. No ADR-005/006 amendment.

## 9. References

- ADR-005 -- Decision Intelligence Architecture.
- ADR-006 -- Project Fit Intelligence Architecture.
- ADR-007 -- CaseOS Constitution V1 (Constitution V1 lives at
  `docs/standards/CaseOS_Constitution_V1.md`; ADR-007 itself is
  not a separate file).
- ADR-008 -- Vision Output Schema Canonical V3.
- `docs/standards/CaseOS_Constitution_V1.md` -- the source of
  truth for the Constitution module.
- `docs/standards/CaseOS_Decision_Principles_V1.md` -- the four
  operational principles.
- `knowledge/decision_model/` -- the runtime reasoning model that
  operationalises the Brain modules.
- `knowledge/principles/` -- the three must-not-skip DPs.
- `knowledge/expert_handbook/` -- the operational handbook.
