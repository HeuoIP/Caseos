# CaseOS Decision Model V1

- **Status:** Accepted
- **Date:** 2026-07-30
- **Layer:** Knowledge (Decision Model -- top-level architecture)
- **Purpose:** the reasoning architecture behind the future
  CaseOS Decision Engine.

## 0. What this document is

This document is the **reasoning model** that the future CaseOS
Decision Engine implements. It is not code. It is not a database
schema. It is the prose description of *how the engine thinks*.

The model has four parts, each its own file in this folder:

| Part | File | Role |
| --- | --- | --- |
| Constitution bindings | `Constitution/` | How each Constitution clause and Forbidden Behavior manifests in the engine. |
| Context Model | `Context_Model.md` | The shape of the shared `DecisionContext` object. |
| Project Fit Model | `Project_Fit_Model.md` | How the engine judges whether the project is worth doing. |
| Strategy Model | `Strategy_Model.md` | How the engine converts context + project fit into a direction. |

This file ties the four parts together and shows how they
compose into the end-to-end pipeline.

## 1. Why a Decision Model

Three reasons.

1. **Separation of what and how.** The Constitution says *what
   is right*. The Decision Principles say *what the engine must
   do*. The Top-Level Principles and the Design Principles say
   *what must never be skipped*. The Expert Handbook says *how
   to do it well*. None of these, by themselves, say *how the
   engine reasons*. The Decision Model fills that gap.
2. **Stable architecture, evolvable detail.** The architecture
   (the four parts, the order, the inputs and outputs of each
   sub-model) is stable. The detail (specific scoring
   algorithms, candidate-retrieval rules, prose templates)
   will evolve. The Model records the stable part.
3. **Cross-cutting visibility.** A reader can answer "where does
   this principle manifest?" by following the cross-references
   from any Constitution clause into the Decision Model.
   Without the Model, the principle lives in one document and
   its manifestation lives in another, with no trace between
   them.

## 2. The Four Parts (summary)

### 2.1 Constitution/ (bindings)

The Constitution "s four principles and seven forbidden
behaviors each have a binding document under `Constitution/`.
A binding records:

- The Constitution clause being bound.
- The Decision Engine stage(s) where it manifests.
- The manifestation rule.
- The failure mode if the clause is violated.
- The test that catches the violation.

Bindings are the **bridge** between philosophy and
implementation. They are the smallest unit of decision-model
reasoning that has a Constitution trace.

See `Constitution/README.md` for the index.

### 2.2 Context Model

The engine represents the world through a `DecisionContext`
object that is shared across all agents and stages. The Context
Model defines:

- The fields of `DecisionContext`.
- Which fields are inputs (read-only for an agent) and which
  are outputs (writable).
- The order in which fields are filled.
- The invariants each field must satisfy.

The Context Model is **mutable state with a contract**. Each
agent reads the fields it needs, mutates the fields it owns,
and leaves the others alone.

See `Context_Model.md`.

### 2.3 Project Fit Model

Project Fit is the first reasoning stage after the Vision
Engine and before the Strategy stage (per ADR-006). It answers:
**is this project worth doing, and in which direction?**

Project Fit reads five input dimensions (Space, Stakeholder,
Goal, Market, Resource) and produces a Project Fit Report with
six output fields (Strength, Risk, Capability Match,
Recommended Direction, Avoid Direction, Confidence).

The Project Fit Model is **judgment before taste**. It exists
to filter out projects that look attractive but are not
feasible, and to surface projects that look unremarkable but
are feasible.

See `Project_Fit_Model.md`.

### 2.4 Strategy Model

Strategy is the reasoning stage that converts Context +
Project Fit + Retrieved Knowledge into a positioning and a
direction. It answers: **given that the project is worth
doing, what is the right way to approach it?**

The Strategy Model produces a list of strategies with seven
fields each (space_positioning, core_problem,
design_direction, investment_logic, served_goals,
knowledge_refs, status). Strategies fall into five broad
categories: Landmark, Journey, Field, Layered, Anchor.

Strategy is **direction before objects**. It exists so that
objects are chosen to serve a strategy, not to fill a
catalogue.

See `Strategy_Model.md`.

## 3. End-to-End Pipeline

The four parts compose into the following pipeline, in order.
Each stage is an agent; each agent reads from and writes to
the shared `DecisionContext`.

```text
Vision Engine (V1 V3 JSON, per ADR-008)
   |
   v
Constitution Bindings (cross-cutting constraints)
   |
   v
Project Fit Agent
   |  reads:  Vision JSON + User Context
   |  writes: DecisionContext.project_fit
   v
Space Agent
   |  reads:  Vision JSON + User Context
   |  writes: DecisionContext.space
   v
Decision Maker Agent
   |  reads:  Vision JSON + User Context
   |  writes: DecisionContext.goal
   v
Knowledge Retriever
   |  reads:  Vision JSON + DecisionContext.space
   |          + DecisionContext.goal
   |  writes: DecisionContext.knowledge_context
   v
Strategy Agent
   |  reads:  DecisionContext (all of the above)
   |  writes: DecisionContext.strategies
   v
Object Selector Agent
   |  reads:  DecisionContext.strategies
   |          + DecisionContext.knowledge_context
   |          + DecisionContext.space
   |          + DecisionContext.goal
   |  writes: DecisionContext.recommendations
   v
Explain Agent
   |  reads:  DecisionContext.recommendations
   |          + DecisionContext.strategies
   |          + DecisionContext.project_fit
   |          + DecisionContext.space
   |  writes: DecisionContext.explanation
   v
Markdown Report Generator
```

The pipeline is **strictly sequential** (per Constitution P003
binding). No agent may write a field that an upstream agent
has not yet filled. No agent may read a field that an upstream
agent has explicitly marked `unknown`.

## 4. Cross-cutting Constraints

The Constitution Bindings apply **across the pipeline**, not
at one stage. They are evaluated continuously.

| Binding | Where it is checked |
| --- | --- |
| **P001** (suitable, not beautiful) | Object Selector ranking + Explain prose |
| **P002** (objects serve goals) | Every strategy + every recommendation |
| **P003** (understand before recommending) | Pipeline ordering |
| **P004** (amplify strengths) | Project Fit (Strength / Risk) + Strategy (core_problem) |
| **FB-01..07** | Pipeline-level hard constraints |

The Forbidden Behaviors (FB-01..07) are **hard constraints**.
A behavior that violates a Forbidden Behavior cannot be
issued, regardless of how attractive the recommendation would
be.

## 5. The Three Modes of Reasoning

The Decision Model "s reasoning operates in three modes,
depending on the data available.

### 5.1 Complete mode

All inputs are observed. The pipeline runs in full, produces
a full recommendation, and emits a Markdown report with all
sections.

### 5.2 Partial mode

Some inputs are missing. The pipeline runs as far as the data
allows, surfaces the unknowns, and asks the user for the
missing inputs. A partial report is emitted; the engine does
NOT pad unknowns with guesses.

### 5.3 Recommend-against mode

Project Fit returns `recommend against`. The pipeline
terminates at Project Fit. No Strategy, no Object Selector,
no Explain. The Markdown report is a single sentence:
**"This project is not recommended."** plus the Project Fit
Report "s Strength / Risk rationale.

## 6. Relationship to Other Layers

| Layer | Role | Where it lives |
| --- | --- | --- |
| **Constitution** | The philosophy. | `docs/standards/CaseOS_Constitution_V1.md` |
| **Decision Principles** | The four operational principles. | `docs/standards/CaseOS_Decision_Principles_V1.md` |
| **Decision Model (this folder)** | The reasoning architecture. The how of thinking. | `knowledge/decision_model/` |
| **Top-Level Principles** | The ten space-decision principles. | `knowledge/decision_rules/Space_Decision_Principles.md` |
| **Design Principles** | The three must-not-skip rules. | `knowledge/principles/` |
| **Expert Handbook** | The operational handbook. The how of doing. | `knowledge/expert_handbook/` |
| **Knowledge Libraries** | The content (goals, strategies, reasoning, objects, taxonomy). | `knowledge/goals/`, `knowledge/strategies/`, `knowledge/reasoning/`, `knowledge/objects/`, `knowledge/taxonomy/` |
| **Domain Packs** | The industry-specific content (playground first). | `knowledge/taxonomy/`, `knowledge/objects/`, `docs/knowledge/Playground_Domain_Pack_V1.md` |

When two layers disagree, the higher layer wins. The
Constitution outranks the Decision Model outranks the Expert
Handbook outranks the Domain Packs.

## 7. Versioning

The Decision Model is versioned by ADR.

- **V1** (this document) is the first accepted version.
- A breaking change to the pipeline order requires ADR.
- A breaking change to a sub-model "s shape requires ADR.
- A breaking change to a binding "s manifestation rule
  requires ADR.
- A change to a sub-model "s internal reasoning (without
  changing its inputs/outputs) is a non-breaking change but
  should still be versioned.

## 8. Maintenance

- This folder is the **reasoning architecture**. Implementation
  details (specific algorithms, weights, thresholds) belong in
  the engine code, not in this folder.
- A change to the pipeline order is a breaking change.
- A change to a sub-model "s inputs or outputs is a breaking
  change.
- A change to a sub-model "s internal reasoning (without
  changing its inputs/outputs) is a non-breaking change but
  should still be versioned.

## 9. Open Questions for the Future

- [ ] Should the Knowledge Retriever be split into two stages
  (case-retrieval vs theme-retrieval) for finer provenance?
- [ ] Should the Object Selector "s `strength_alignment` score
  be moved into the five-match test (making it a six-match
  test) for simplicity?
- [ ] Should the Explain Agent emit structured prose (paragraphs
  with explicit claim IDs) to support future user Q&A?
- [ ] When the user asks a clarification question mid-pipeline,
  where does the engine "loop back" to? Is the loop-back
  re-entrant (same agent re-runs) or re-start (pipeline re-
  starts from Vision)?
- [ ] When two Domain Packs both apply (e.g. playground + shade
  for a schoolyard), how does the pipeline route?

## References

- ADR-005 -- Decision Intelligence Architecture.
- ADR-006 -- Project Fit Intelligence Architecture.
- ADR-008 -- Vision Output Schema Canonical V3.
- `docs/standards/CaseOS_Constitution_V1.md`.
- `docs/standards/CaseOS_Decision_Principles_V1.md`.
- `knowledge/principles/DP-001`, `DP-002`, `DP-003`.
- `knowledge/decision_rules/Space_Decision_Principles.md`.
- `knowledge/expert_handbook/` (10 documents).
- `Constitution/README.md` (Constitution bindings index).
- `Context_Model.md`.
- `Project_Fit_Model.md`.
- `Strategy_Model.md`.
