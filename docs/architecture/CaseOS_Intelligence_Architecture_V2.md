# CaseOS Intelligence Architecture V2

- **Date:** 2026-07-31
- **Status:** Blueprint (informative; not yet an ADR)
- **Supersedes:** `Architecture.md` ASCII sketch (the seven-step "Input -> Vision AI -> Case Schema -> Database -> Vector Search -> LLM -> Proposal -> PDF" diagram from the V1 playground-only product)
- **Authoritative sources:** the ADRs in this folder (ADR-005 .. ADR-013). This document is the **map**, the ADRs are the **ground**.
- **Source of truth:** `docs/architecture/CaseOS_Intelligence_Architecture_V2.md`

---

## 1. Core Architecture Principle

CaseOS V2 redefines the system around **two complementary intelligences** combined by **two coordination engines**:

```
        Human Understanding Engine
                  +
        Spatial Intelligence Engine
                  =
        Decision Intelligence Engine
                  +
        Feedback Learning Engine
                  =
        CaseOS Intelligence
```

**Code is replaceable. Brain is cumulative.** Every layer below must expose
**Input / Processing / Output / Consumer**. An intelligence layer that has no
consumer is a documentation ghost; the AR-001 review already identified five
of those and they will not be allowed to reoccur.

### The four questions

| Engine | Question it answers |
| --- | --- |
| Human Understanding Engine | "What does this person really want?" |
| Spatial Intelligence Engine | "What does this space need?" |
| Decision Intelligence Engine | "What should we do?" |
| Recommendation Engine | "How should we express the solution?" |

The Feedback Learning Engine does not answer a question; it **closes the loop**
that lets every other engine improve.

---

## 2. The Four-Engine Model

### 2.1 Human Understanding Engine

**Purpose:** Understand the human behind the project.

**Input:**
- project goals
- explicit requirements
- budget
- constraints
- browsing behavior
- case preferences
- natural-language feedback

**Processing:** signal ingestion -> dimension tagging -> Human Understanding Model.

**Output:** Human Understanding Model.

**Consumer:** Decision Intelligence Engine, Recommendation Engine, Feedback Learning Engine.

**Authority:** ADR-013 (Proposed).

---

### 2.2 Spatial Intelligence Engine

**Purpose:** Understand the physical world.

**Input:**
- site images
- space conditions
- architecture relationship
- environment
- existing facilities

**Knowledge base:**
- CKO (Case Knowledge Object) -- ADR-011
- Golden Case selection -- ADR-012
- Decision Rules -- ADR-010
- Expert Principles -- `knowledge/expert_handbook/`
- Brain constitution modules -- ADR-009

**Processing:** vision analysis -> space cognition -> diagnosis -> strategy.

**Output:** Spatial Understanding Model.

**Consumer:** Decision Intelligence Engine, Recommendation Engine.

**Authority:** ADR-005 (Agent pipeline), ADR-008 (Vision Output Schema V3), ADR-009 (Brain Knowledge Architecture).

---

### 2.3 Decision Intelligence Engine

**Purpose:** Combine human understanding and spatial understanding.

**Question it answers:**
> "What is the best decision for **this specific person** and **this specific space**?"

**Input:**
- Human Understanding Model (from 2.1)
- Spatial Understanding Model (from 2.2)

**Processing:** cross-mapping -> problem diagnosis -> priority assignment -> strategy synthesis.

**Output:**
- problem diagnosis
- priority list
- strategy direction
- recommended experience logic

**Consumer:** Recommendation Engine.

**Authority:** ADR-005 (Decision Intelligence pipeline), ADR-006 (Project Fit Intelligence). The V2 Decision Intelligence Engine treats project fit as one of several decision-time dimensions, not a separate engine.

---

### 2.4 Feedback Learning Engine

**Purpose:** Allow CaseOS to continuously improve.

**Input:**
- user selections
- modifications requested
- satisfaction signals
- downstream project results (when available)

**Output updates:**
- Human Understanding Model (per user)
- Decision Rules (global)
- Golden Cases (intake/demotion)

**Consumer:** the three engines above. The Feedback Engine is the **only** engine whose output is allowed to overwrite prior engine outputs. It is a peer of the others, not a sub-module.

**Authority:** ADR-013 Section "Data Flywheel" (declared). No dedicated ADR file exists yet.

---

## 3. Architecture Diagram

```mermaid
flowchart TB
    User([User])
    FB([Feedback])

    subgraph PE[Product Layer]
        direction TB
        UI[Web / API / CLI]
    end

    subgraph Intel[Intelligence Layer]
        direction TB

        subgraph HE[Human Understanding Engine]
            HI[Signal Ingest<br/>goal, budget, behaviour, feedback]
            HU[Human Understanding Model]
            HI --> HU
        end

        subgraph SE[Spatial Intelligence Engine]
            SI[Vision Ingest<br/>image, conditions]
            SK[Knowledge Base<br/>CKO + Brain + Rules]
            SU[Spatial Understanding Model]
            SI --> SU
            SK --> SU
        end

        subgraph DE[Decision Intelligence Engine]
            DU[Decision Synthesis<br/>diagnosis + priority + strategy]
            DUOutput[Output<br/>decision + experience logic]
            DU --> DUOutput
        end

        subgraph RE[Recommendation Engine]
            RU[Recommendation Engine<br/>express the solution]
            RUOutput[Solution Output<br/>Markdown Report]
            RU --> RUOutput
        end

        subgraph FE[Feedback Learning Engine]
            FI[Feedback Ingest]
            FU[Update Models + Rules + Cases]
            FI --> FU
        end

        HU --> DU
        SU --> DU
        DUOutput --> RU
        FU -. updates .-> HU
        FU -. updates .-> SK
        FU -. updates .-> DU
    end

    User --> UI
    UI --> HE
    UI --> SE
    UI --> DE
    UI --> RE
    UI --> FE
    RUOutput -. delivered to .-> User
    User -. behaviour + feedback .-> FB
    FB --> FE
```

**Read this diagram from top to bottom, then from bottom back to top.** The forward path is the user journey; the backward path is the learning loop.

---

## 4. End-to-End Pipeline (text form)

```
User
  |
  v
Product Layer               (entry: image + project type + goal + style hint)
  |
  +--> Human Understanding Engine       ---+
  |                                          |
  +--> Spatial Intelligence Engine      ---+--> Decision Intelligence Engine
                                                |
                                                v
                                       Recommendation Engine
                                                |
                                                v
                                            Solution
                                                |
                                                v
                                          (delivered)
                                                |
                                                v
                                       Feedback Learning Engine
                                                |
                              +-----------------+-----------------+
                              |                 |                 |
                              v                 v                 v
                  Human Understanding   Knowledge Base    Decision Rules
                              \                 |                 /
                               +----------------+----------------+
                                                |
                                                v
                                    (closes the data flywheel)
```

The two vertical lines on the left (Human + Spatial Engines) **both** feed the
Decision Intelligence Engine. They are peers. Neither one is a sub-routine of the
other.

---

## 5. What Every Intelligence Layer Must Declare

To prevent the "isolated module" failure mode documented in AR-001, every
intelligence layer MUST publish four declarations:

```
1. Input    -- what this engine consumes (typed)
2. Processing -- the transform it performs (rules + LLM allowed, DB allowed)
3. Output   -- what this engine emits (typed)
4. Consumer -- who reads the output; if no one does, the layer does not ship
```

A layer with `Consumer = none` is forbidden by Constitution Principle 001
("Understand before recommending"): it means we built something nobody uses.

---

## 6. Current Completed Capabilities (mid-2026-07-31)

| Layer | Component | Status | Source |
| --- | --- | --- | --- |
| Product Layer | `core/product/product_flow.py`, `session.py`, `request.py`, `response.py`, `workflow.py` | COMPLETE (Sprint 8) | `backend/app/core/product/` |
| Spatial Intelligence - Vision | Qwen3.7-Plus provider, `analyzer.py`, schema V3 | COMPLETE | ADR-008, `backend/app/services/vision/` |
| Spatial Intelligence - Knowledge | CKO schema v1, taxonomy, examples | COMPLETE | ADR-011, ADR-012, `knowledge/cases/` |
| Spatial Intelligence - Brain modules | constitution, client_understanding, project_fit, space_cognition, experience_perception, diagnosis, strategy, theme_strategy, recommendation | STRUCTURE COMPLETE / INTEGRATION PARTIAL | ADR-009, ADR-010 |
| Spatial Intelligence - Decision Rules | 14 rules across 6 categories | DOCUMENT COMPLETE / NO ENGINE CONSUMES | ADR-010, `knowledge/brain/decision_rules/` |
| Human Understanding - signal scope | Three signal sources, four model dimensions | DOCUMENT COMPLETE | ADR-013 |
| Decision Intelligence - Agent pipeline | Space, DecisionMaker, KnowledgeRetriever, Strategy, ObjectSelector, Explain (six agents) | STRUCTURE COMPLETE | ADR-005, `backend/app/core/agents/` |
| Decision Intelligence - Project Fit | Project Fit Agent scaffold, output model | DOCUMENT COMPLETE | ADR-006 |
| Recommendation - Markdown generator | `recommendation/markdown_generator.py` | COMPLETE | Sprint 7 |
| Feedback Learning - data flywheel | Closed-loop diagram only | NOT STARTED (no ADR yet) | declared in ADR-013 |

---

## 7. Missing Capabilities (must be added before Phase 2 is "done")

1. **API / CLI surface** -- the system has no entry point. Every engine above
   is exercised through scripts, not through a stable interface. (AR-001 Rank 1)
2. **Retrieval Engine** -- the Spatial Intelligence Engine needs an actual
   case-retrieval implementation against the CKO library; today it has only the
   spec. (AR-001 Rank 2)
3. **Preference Signal Schema** -- ADR-013 declares a model; ADR-015 must fix
   the JSON schema and event names. (ADR-013 future ADR)
4. **Feedback Event Sink** -- no file, no DB, no queue exists for feedback yet.
   (future ADR)
5. **Recommendation Engine as a peer of Decision** -- today Recommendation is a
   Markdown printer co-located with the agents; it must be promoted to a peer
   per the V2 model.
6. **Constitution Enforcement Layer** -- Principle 001 (Understand before
   recommending) has no executable check. (AR-001 Rank 8)
7. **Long-Term User Modeling** -- ADR-013 declares that preferences are
   dynamic; no engine yet rolls signals into stable preference vectors.
8. **Theme Engine** -- ADR-009 lists `theme_strategy` as a brain module; no
   thematic reasoning exists at runtime.
9. **Experience Engine** -- ADR-009 lists `experience_perception`; no runtime
   consumer.

Items 2, 7, 8, 9 collectively form the **Phase 2 acceleration backlog**.
Items 1, 3, 4, 5, 6 form the **Phase 2 entry backlog** (must ship first).

---

## 8. Future ADR Mapping

ADR numbering convention: `ADR-NNN-short-name.md`. After ADR-013 (just filed),
the next numbers are:

| Slot | Topic | Relationship to existing ADRs |
| --- | --- | --- |
| **ADR-014** | Decision Intelligence Model V2 | Net-new. ADR-005 is the **pipeline**; ADR-014 is the **deep model**: how the synthesis output of "what should we do" is structured (problem / priority / strategy / experience logic) and how it composes with Project Fit. |
| **ADR-015** | Preference Signal Schema V1 | Net-new. ADR-013 declared the **scope**; ADR-015 fixes the field types, allowed values, and event names. |
| **ADR-016** | Recommendation Engine V1 | Net-new. The Markdown generator exists; the **engine** that turns a Decision into a Solution with explanation does not yet. |
| **ADR-017** | Feedback Learning Loop Contract V1 | Net-new. ADR-013 declared the **flywheel**; ADR-017 fixes the contract: what is recorded, where, and how it is replayed into engines 2.1, 2.2, 2.3. |

ADR numbers **014-017 are placeholders**, not commitments. If a different
architectural decision is required first (e.g. an API Surface ADR), the next
free number absorbs it. The four topics above are what the placeholders
*currently* point at; the placeholders can be renumbered.

---

## 9. Architectural Style Rules

These rules apply to every future Sprint touching this architecture.

1. **Every engine declares Input / Processing / Output / Consumer.**
2. **No engine writes into another's output store.** Cross-engine updates go
   through the Feedback Learning Engine.
3. **No persona tables.** Per ADR-013 Principle 1, personas emerge from
   behaviour, they are not declared first.
4. **No recommendation without decision.** Per Constitution Principle 001
   (ADR-007), no Solution leaves the Decision Intelligence Engine.
5. **Every knowledge base is a peer of Brain.** CKO, Rules, Expert Handbook,
   Theme Library are first-class citizens, not sub-folders.
6. **Code is replaceable, Brain is cumulative.** Refactors of `app/` are
   routine; refactors of `knowledge/` should be rare and ADR-numbered.
7. **Six ADRs are the spine.** New agents MUST extend the existing
   `agents/` directory; new domain knowledge MUST extend one of the existing
   `knowledge/brain/*` modules or be proposed in a new ADR. No silent
   new-modules-into-folder without architectural review.

---

## 10. Closing Statement

CaseOS V2 is what CaseOS V1 was always meant to be: a system that **understands
the human and the space before it recommends anything**.

V1 had a clever pipeline and no understanding. V2 keeps the pipeline, adds four
explicit intelligence engines around it, and forces every engine to declare its
consumer before it ships.

The next architecture review (AR-002) will re-check this map against the
commits produced after ADR-013 lands.

---

*End of CaseOS Intelligence Architecture V2.*