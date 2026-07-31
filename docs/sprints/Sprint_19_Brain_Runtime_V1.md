# Sprint 19 -- CaseOS Brain Runtime V1

- **Status:** _started_
- **Date opened:** 2026-07-31
- **Date closed:** (open)
- **Owner:** Architecture Consistency Patch V1 -> Sprint 19
- **Layer:** Phase 3 (Runtime Implementation)
- **Related ADRs (frozen contracts this Sprint consumes):**
  ADR-013 (Human Understanding), ADR-014 (Decision Intelligence),
  ADR-015 (Knowledge Object), ADR-016 (Trust Model),
  ADR-017 (Recommendation Engine), ADR-018 (Feedback Learning Loop).
- **Source of truth:** `docs/sprints/Sprint_19_Brain_Runtime_V1.md`
- **Companion documents:**
  - `CaseOS-Architecture-Baseline-V1.md` (the Architectural Baseline)
  - `Sprint_Roadmap.md` Section 3 (the rolling entry conditions)

---

## 1. Objective

The purpose of Sprint 19 is:

> Connect existing CaseOS intelligence contracts into a minimal executable reasoning pipeline.

Sprint 19 does **NOT** build the complete product.

It creates the **first working Brain Runtime prototype**.

The success condition:

> Given a project input,
> CaseOS can produce:
>
> understanding
> → diagnosis
> → decision
> → trust explanation
> → recommendation.

---

## 2. Architecture Context

Sprint 19 implements the transition:

```
Architecture Layer
   ↓
Runtime Layer
```

Existing contracts:

- ADR-013 -- Human Understanding Engine
- ADR-014 -- Decision Intelligence Model
- ADR-015 -- Knowledge Object Model
- ADR-016 -- Trust Model
- ADR-017 -- Recommendation Engine
- ADR-018 -- Feedback Learning Loop

These are **treated as frozen contracts** by Sprint 19. Sprint 19 wires
the contracts; it does not modify them. Modification belongs to a future
ADR.

---

## 3. Sprint Scope

Included:

- A. Runtime pipeline orchestration
- B. Decision generation pipeline
- C. Knowledge Object consumption
- D. Trust evaluation output
- E. Recommendation rendering
- F. CLI first interface

---

## 4. Not Included

Sprint 19 does **NOT** build:

- Web frontend
- User accounts
- Commercial platform
- Payment system
- Image generation
- CAD generation
- Full visual AI model pipeline
- Production deployment
- Large-scale database

These are deferred per Constitution, Decision Principles, the V2 Blueprint
Section 7 Phase roadmap, and the Architecture Baseline Section 6
Runtime Direction. Each non-included item is intentionally outside
Sprint 19 to keep Sprint 19's runtime minimal and verifiable.

---

## 5. Minimal Runtime Flow

### Input -- Project Context

Example:

```json
{
  "project_type": "kindergarten_outdoor",
  "site_description":
      "500 sqm outdoor area, lacks theme and memorable experience",
  "user_goal": "improve enrollment attraction",
  "constraints": "limited budget"
}
```

### Pipeline

```
Project Context
   ↓
Human Understanding Layer
   Output: Human Context Object
   ↓
Knowledge Retrieval Layer
   Input:  Knowledge Objects
   Output: Relevant patterns
   ↓
Decision Intelligence Layer
   Output: Decision Object
   ↓
Trust Layer
   Output: Trust Object
   ↓
Recommendation Layer
   Output: Human-readable recommendation
```

---

## 6. Sprint 19 Runtime Architecture

Create:

```
Brain Runtime
   |
   |--- pipeline  (orchestration, contract connection)
   |--- context   (shared mutable state across stages)
   |--- executor  (executes one stage)
```

Suggested directory structure:

```
brain/
   runtime/
      pipeline.py
      context.py
      executor.py
intelligence/
   human/
   decision/
   trust/
   recommendation/
knowledge/
   objects/
```

The directory layout is a **suggestion**, not a hard constraint. The
Sprint should respect what already exists under `backend/app/core/`
and integrate, not duplicate.

---

## 7. First Implementation Strategy

Do **NOT** start with complex AI models.

First implementation uses:

- structured inputs
- existing Knowledge Objects (per ADR-015)
- rule-based reasoning (per ADR-010 Decision Rules)

to validate architecture.

AI model integration comes later (a separate Sprint, gated on
Sprint 19 success).

---

## 8. First CLI Experience

Target command:

```
caseos analyze
```

Input: `project.json`.

Output: `case_analysis.md`.

Example output structure:

```
# Project Understanding

# Spatial Diagnosis

# Decision

# Evidence

# Confidence

# Recommendation
```

This is the **first moment** a user can run CaseOS from a terminal and
receive a structured result. The CLI is the operational proof that the
six intelligence components are wired together.

---

## 9. Deliverables

Required:

1. Sprint 19 Runtime module
2. Pipeline execution
3. Sample project input
4. Sample recommendation output
5. Basic tests

---

## 10. Acceptance Criteria

Sprint 19 succeeds when:

1. A complete reasoning pipeline executes.
2. ADR-014 Decision Object can be produced.
3. ADR-016 Trust explanation appears.
4. ADR-017 Recommendation output appears.
5. Output can be reviewed by a human expert.

---

## 11. Test Cases

### Test Case 1

**Kindergarten outdoor empty space.**

Expected:

- Not recommend equipment stacking.
- Identify: theme anchor, experience flow, space identity.

### Test Case 2

**Existing playground overloaded.**

Expected:

- Identify: visual disorder, lack of hierarchy, remove before adding.

### Test Case 3

**Budget conflict.**

Expected:

- Not hallucinate luxury solution.
- Explain constraints.

These three tests exercise the four behaviour truths the V2 Blueprint
Section 6 Runtime Direction requires (a-d).

---

## 12. Future Connection

After Sprint 19:

- **Sprint 20** -- Retrieval Engine V1 (per AR-001 Rank 2; ADR-015c).
- Future -- Vision model integration (per ADR-008 schema readiness).
- Future -- User interaction layer (per Product Blueprint V1).
- Future -- Feedback system runtime (per ADR-018 HITL thresholds; this
  Sprint ships the contract, Sprint 20+ runs it).
- Future -- Commercial platform (per Constitution deferred scope).

---

## Final Goal

Sprint 19 creates the first moment when:

> CaseOS stops being documentation
> and becomes a running intelligence system.

---

## Appendix -- Permissions / Out-of-Scope Authority

This Sprint task spec is consistent with:

- Constitution (ADR-007) Section 4 ("What CaseOS Should Never Do").
- Decision Principles V1 operational checklist (6 YES items; implicit
  7th from ADR-018 HITL per the Constitution Alignment Note V1).
- Architecture Baseline V1 Section 6 Runtime Direction.
- Sprint Roadmap V1 Section 3 (the original Sprint 19 spec).

Any deviation from this appendix must be justified in the Sprint 19
completion log.