# ADR-005: Decision Intelligence Architecture

- **Status:** Accepted (amended by ADR-005a, 2026-07-30)
- **Date:** 2026-07-29
- **Supersedes:** --
- **Superseded by:** --

## Context

CaseOS V1 already has:

- Vision Engine
- Knowledge Library
- Object Library
- Decision Rules
- Agent Framework
- Product Layer

Current pipeline can process:

```
Image
  |
  v
Vision
  |
  v
Decision Engine
  |
  v
Report
```

However, current intelligence is mainly rule-driven.

To become a real **Space Advisor**, CaseOS needs the ability to:

- Understand project goals
- Retrieve relevant knowledge
- Reason about space problems
- Generate strategic recommendations

## Decision

CaseOS adopts a **hybrid Decision Intelligence Architecture**.

The intelligence layer consists of:

1. **Structured Rules** -- canonical knowledge stays in `knowledge/`.
2. **Knowledge Retrieval** -- case + theme + object + decision-rule lookup.
3. **LLM Reasoning** -- enhances, never replaces, structured knowledge.

Architecture:

```
User Input
  |
  v
Vision Analysis
  |
  v
Decision Maker Context
  |
  v
Knowledge Retrieval
  |
  v
Strategy Reasoning
  |
  v
Object Recommendation
  |
  v
Explanation Generation
```

## Agent Responsibilities

### Space Agent

- **Input:** Vision JSON
- **Understands:** space type, spatial characteristics, existing
  strengths, existing problems.
- **Output:** Space Context.

### Decision Maker Agent

- **Input:** Project Type, Primary Goal, User Context.
- **Infers:** decision maker profile, decision priorities,
  evaluation criteria.
- **Output:** Decision Context.

### Knowledge Retriever

- **Retrieves:** similar cases, theme knowledge, object knowledge,
  decision rules.
- **Output:** Relevant Knowledge Context.

### Strategy Agent

- **Generates:** space positioning, design strategy, experience
  strategy, investment logic.
- **Principle:** **Strategy first. Objects second.** Strategies
  address goals; objects implement strategies.

### Object Selector Agent

- **Recommends:** objects, facilities, spatial elements.
- **Based on:** Strategy. **Not** direct image similarity.

### Explain Agent

- **Converts:** AI reasoning into customer language.
- **Output:** why this recommendation, expected value, suitable
  scenarios.

## LLM Usage Principle

LLM should **enhance** reasoning.

LLM should **NOT replace**:

- Database
- Knowledge Structure
- Rules

**Structured knowledge remains the foundation.** LLM is a reasoning
amplifier sitting on top of the canonical knowledge layer.

## Future Extensions

The architecture should support (slots already reserved in the
pipeline):

- Budget Agent
- Safety Agent
- Commercial Agent
- Education Agent
- Psychology Agent
- Fengshui Agent

Adding any of them is one new class + one line in `DEFAULT_PIPELINE`.

## Consequences

### Positive

- Intelligence is now a layered concern. Each agent owns one slice.
- LLM can be slotted into any single agent without re-architecting.
- Knowledge remains the source of truth; reasoning is reproducible.
- Future agents (Budget, Safety, ...) plug in without breaking changes.

### Negative

- Knowledge Retrieval latency may dominate total response time
  if naive similarity search is added later.
- LLM output is non-deterministic; we must keep a deterministic
  fallback path (the current rule-based path) for tests.

## Non-Goals

This ADR does NOT include:

- Image generation
- CAD generation
- PDF generation
- UI development

## Cross-references

- Sprint 7 deliverable: `backend/app/core/agents/` -- Agent Framework V1.
- Sprint 8 deliverable: `backend/app/core/product/` -- Product Layer.
- Knowledge layer: `knowledge/{goals,strategies,reasoning,objects,taxonomy,decision_rules}/`.
- Architecture review: `docs/reviews/Architecture_Review_2026_07.md`.
## Constitution cross-reference (added by ADR-005a, 2026-07-30)

Every agent in the Decision Intelligence pipeline must satisfy the
CaseOS Constitution V1 and the four Decision Principles V1. In
particular:

1. **Constitution Principle 003** -- understand before recommending.
   The Space Agent, the Decision Maker Agent, and the Knowledge
   Retriever Agent exist so that the Strategy Agent never has to
   recommend without understanding.
2. **Constitution Principle 002 / Decision Principle 001** -- design
   serves decisions. The Strategy Agent must cite the served goals
   in every Recommendation.
3. **Decision Principle 002** -- space before object. The Object
   Selector must read the Space Summary and refuse to recommend
   objects that contradict the observed site type, materials, or
   fall height.
4. **Decision Principle 004** -- recommend from the decision maker 's
   perspective. The Explain Agent must never use the marketing
   vocabulary banned by the Constitution (striking, amazing,
   iconic, world-class, revolutionary, cutting-edge).

A new acceptance criterion is added: every agent in the pipeline
must be auditable against the Constitution V1 by a future
	est_constitution_compliance.py. This is enforced starting
Sprint 14 (Constitution Compliance Tests).

See:

- CaseOS_Constitution_V1.md (highest-level philosophy)
- CaseOS_Decision_Principles_V1.md (implementation guide)
- ADR-005a (the amendment that adds this section)
