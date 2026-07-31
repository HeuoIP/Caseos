# ADR-013: Human Understanding Engine Foundation V1

- **Status:** Proposed
- **Date:** 2026-07-31
- **Layer:** Intelligence (Human Side)
- **Affects:** CKO `user_affinity` extension, Recommendation Engine inputs, Product Layer
- **Related ADRs:** ADR-005 (Decision Intelligence), ADR-006 (Project Fit), ADR-009 (Brain), ADR-011 (CKO), ADR-012 (Evaluation)
- **Source of truth:** `docs/architecture/ADR-013-human-understanding-engine.md`

---

## Context

CaseOS was initially designed as an AI spatial design intelligence system.

After architecture review and product direction refinement, CaseOS is upgraded into:

> An AI spatial decision and design platform centered on understanding users.

The core differentiation is **not** image generation.

The core differentiation is:

- Understanding Human Intent
- Understanding Spatial Intelligence

Therefore CaseOS requires a **Human Understanding Engine**.

---

## Decision

Create the **Human Understanding Engine** as a core intelligence layer.

CaseOS therefore consists of two intelligence systems:

### 1. Spatial Intelligence Engine

Responsible for understanding:

- space
- environment
- design logic
- experience
- architecture
- cases

### 2. Human Understanding Engine

Responsible for understanding:

- user goals
- user preferences
- emotional expectations
- decision behavior
- feedback patterns

Together:

```
Human Understanding + Spatial Intelligence = CaseOS Intelligence Core
```

---

## Human Understanding Engine Scope

The engine learns from three signal sources:

### 1. Explicit User Input

Examples:

- project goals
- budget
- requirements
- constraints

### 2. User Interaction Behavior

Examples:

- cases viewed
- cases liked
- cases disliked
- cases saved
- directions selected
- modifications requested

### 3. Feedback Loop

Examples of natural-language feedback:

- "too ordinary"
- "too expensive"
- "not suitable"
- "more natural"
- "more interactive"

These become **preference signals**.

---

## Human Understanding Model V1

### 1. Project Goal

Examples:

- improve enrollment attraction
- improve children's play experience
- upgrade kindergarten image
- increase commercial value

### 2. Design Preference

Style:

- natural
- futuristic
- playful
- minimalist
- cultural

Emotion:

- warm
- energetic
- adventurous
- educational
- premium

### 3. Decision Preference

Examples:

- prefers safe choices
- prefers innovation
- prefers visual impact
- prefers operational value

### 4. Constraint Understanding

Examples:

- budget level
- space limitation
- maintenance ability
- construction condition

---

## Golden Case Extension

Golden Case must not only contain:

> "Why is this case good?"

It must also contain:

> "Who will like this case and why?"

Add to the CKO evaluation block:

```
user_affinity:
  target_users:        []
  emotional_keywords:  []
  suitable_projects:   []
  avoid_users:         []
```

This **extends** ADR-012 (Case Evaluation Score V1). It does not redefine it.

Section 10 (intake + transferability) and this Section 11 (user affinity) together form the **Golden Case Selector** criteria.

---

## Data Flywheel

CaseOS learning loop:

```
User interaction
        ↓
Preference signal
        ↓
Human Understanding Model
        ↓
Better case recommendation
        ↓
Better user satisfaction
        ↓
More interaction data
```

This is the **closed loop** that converts users into long-term CaseOS intelligence.

---

## Important Principles

1. Do **not** create fixed user personas first. User understanding should emerge from behavior.
2. Do **not** ask unnecessary questions. Understand users while helping them solve problems.
3. User preference is dynamic. The system should continuously update understanding.

---

## Architectural Placement

The Human Understanding Engine is a **peer** of the Spatial Intelligence Engine, not a sub-module of it.

```
                     +----------------------------+
                     |       Product Layer        |
                     +-------------+--------------+
                                   |
              +--------------------+----------------+
              |                    |                |
              v                    v                v
   +--------------------+ +--------------------+ +--------------------+
   |  Human             | |  Spatial           | |  Knowledge /       |
   |  Understanding     | |  Intelligence      | |  Case Library      |
   |  Engine            | |  Engine            | |  (CKO + Brain)     |
   +--------------------+ +--------------------+ +--------------------+
              |                    |                |
              +--------------------+----------------+
                                   v
                          Recommendation
```

Both engines feed the Decision / Strategy agents defined in ADR-005 / ADR-009.

---

## Cross-Reference to Existing Layers

| Existing | Touch point with Human Understanding Engine |
| --- | --- |
| ADR-005 Decision Intelligence | Decision Maker Agent receives **Decision Context** (goal + preference), not only project type. |
| ADR-006 Project Fit Intelligence | Project Fit Agent must read user capability + expectation from this engine. |
| ADR-009 Brain Knowledge Architecture | Add a new module `human_understanding` to the brain layout (placed beside `client_understanding`). |
| ADR-011 CKO Learning Value Model | The `user_logic` axis already touches affinity; Section 11 formalises it. |
| ADR-012 Case Evaluation Score | Section 10 (intake + transferability) + new Section 11 (user affinity) = full Golden Case gate. |
| Product Layer (`core/product/`) | `request.py` will accept preference + emotion signals; `workflow.py` records them into the Human Understanding store. |

---

## Non-Goals (this ADR)

Do **NOT** implement yet:

- recommendation algorithm
- user database
- frontend
- behavior tracking system
- persona templates
- LLM-based sentiment classification

This ADR **only** defines the intelligence foundation.

Future ADRs will cover each capability above one at a time.

---

## Acceptance Criteria

The following must exist after this ADR is merged:

1. This document (`ADR-013-human-understanding-engine.md`).
2. Future ADRs / Sprints reference this document when proposing preference, feedback, or persona work.
3. The CKO evaluation section is incremented to v1.3 by adding `user_affinity` (deferred to a follow-up ADR; not part of this commit).
4. The Brain architecture diagram reflects the `human_understanding` peer placement when ADR-009 is next revised.

---

## Future Extensions (suggested order)

- **ADR-014** -- Preference Signal Collection Schema V1 (what fields, what types)
- **ADR-015** -- Feedback Loop Contract V1 (event names, sinks)
- **ADR-016** -- Human Understanding Store V1 (storage shape; not yet a runtime DB)
- **ADR-017** -- Long-Term User Modeling V1 (roll-up of signals into stable preferences)

These are **not** committed. They are listed so that the next reviewer can pick which one becomes Sprint 19 / 20.

---

*End of ADR-013.*