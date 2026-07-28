# Space Decision Principles

> Foundations for the future CaseOS **Space Decision Engine**.
> This document is **knowledge only**. No runtime decision engine is implemented yet. Today these principles are the rules the engine will obey; tomorrow the engine will operationalise them.

## 1. Core Question

> Given a target space, the intended users, the desired outcome, and the known constraints, **what is the best thing to place in this space?**

"Best" is never absolute. It is the answer that best satisfies a stated goal under stated constraints, supported by recorded evidence, and accompanied by visible trade-offs.

## 2. Decision Layers

The future Decision Engine will reason in five layers, in order:

1. **Evidence** — what we know from images, drawings, prior cases, and user-stated facts. Unknowns are first-class.
2. **Suitability** — what the space can physically, environmentally, legally, and operationally accept. Hard constraints are checked first and cannot be rescued by soft preferences.
3. **Goals** — what the user says they want. The engine does not invent goals; it asks when goals are missing.
4. **Trade-offs** — every candidate is described by what it gives up. A recommendation without trade-offs is incomplete.
5. **Action** — recommend, ask a question, or refuse. The engine never silently guesses.

## 3. Ten Principles

These principles are the rules of the road. They are not negotiable per project.

1. **Evidence before invention.** A visual observation supports a visual claim. It does not prove dimensions, jurisdiction, or budget.
2. **Hard constraints are not negotiable.** A candidate that fails a hard constraint (safety, footprint, climate, jurisdiction) is filtered out, not down-weighted.
3. **"Best" is conditional.** Every recommendation must state the goal, the constraints, the assumptions, and the evidence it relied on.
4. **Unknown is a valid answer.** When information is missing, the engine asks. A confident guess is worse than a transparent unknown.
5. **Multiple options beat one.** The engine returns a ranked set with a recommended option, alternatives, and a "why not" for the dropped candidates.
6. **Trade-offs must be visible.** A recommendation that hides a trade-off is treated as incomplete.
7. **Domain expertise matters.** Domain packs (playground, street furniture, vegetation, art) encode the structured knowledge the engine reasons from. Generic reasoning is not a substitute.
8. **User's stated goals win, within constraints.** When the user expresses a goal that survives the hard-constraint filter, the engine optimises for that goal subject to trade-off disclosure.
9. **Safety is non-negotiable.** No user preference, theme, or cost band overrides a safety standard.
10. **Decisions must be reproducible.** Every recommendation records the input snapshot, filters, weights, model versions, knowledge pack versions, and candidate set used. Re-running the same inputs returns the same output.

## 4. Decision Workflow

The future Decision Engine will execute a deterministic workflow. The workflow is the *how*; the principles above are the *what*.

```text
Target space analysis (observations, opportunities, unknowns)
↓
Domain routing (which intervention packs are eligible?)
↓
Hard-constraint filter (safety, dimensions, climate, jurisdiction, budget, utilities)
↓
Candidate retrieval (interventions + reference cases from knowledge)
↓
Suitability scoring and diversity-aware re-ranking
↓
Evidence-backed recommendation with trade-offs and questions
↓
Validator and immutable recommendation artifact
```

This is a **proposal-only** flow. The Decision Engine does not approve engineering, safety, or procurement decisions. It produces a defensible recommendation that a human professional still owns.

## 5. What the Engine Must NOT Do

- Treat an image as proof of dimensions, jurisdiction, climate, soil, or budget.
- Choose a single answer without showing alternatives.
- Hide unknowns to look confident.
- Override safety standards to satisfy a theme or a user preference.
- Fabricate quantities, costs, or compliance certifications.
- Use AI-generated concept imagery as if it were photographic reference evidence.
- Persist a recommendation without the lineage required to reproduce it.

## 6. Relationship to Other Layers

| Layer | Role | File location |
| --- | --- | --- |
| **Standard** | The behavior rules the engine obeys. | `docs/standards/` |
| **Knowledge** | The content the engine reasons from. | `knowledge/` (this folder, `knowledge/objects/`, `knowledge/taxonomy/`) |
| **Schema** | The shape the engine's outputs must take. | `schemas/` |

A change in one layer must not silently change another. Every recommendation records the version of each layer it used.

## 7. Vocabulary Used by the Engine

These terms will appear in engine output. Defining them here, before the engine exists, prevents later drift.

- **TargetSpace** — the physical place the user is asking about.
- **ReferenceCase** — a documented precedent used as evidence.
- **Intervention** — a candidate thing or package to place in a space (an Object from `knowledge/objects/`).
- **Suitability** — the scored, constraint-aware assessment of one intervention for one target space.
- **Recommendation** — a ranked set of interventions with evidence, rationale, assumptions, and trade-offs.
- **Proposal** — a presentable concept based on a selected recommendation.
- **Hard constraint** — a rule that, if violated, excludes a candidate.
- **Soft preference** — a goal, weight, or ranking signal.
- **Unknown** — a fact the engine does not have and is requesting.

## 8. Open Questions for the Future

- [ ] How is "cost band" anchored? Per region? Per year? Per project scale?
- [ ] How is "inclusive design" scored when the user does not specify?
- [ ] When the user gives conflicting goals, who breaks the tie?
- [ ] How does the engine request information without becoming an interrogation?
- [ ] How is a domain pack's authority weighted against another domain pack's authority?
- [ ] What is the minimum evidence required before the engine will issue a recommendation, not a question?

## 9. Maintenance

- This file is the **principles** layer. Detailed rules for specific topics (theme selection, object scoring, conflict resolution) belong in their own files under `knowledge/decision_rules/`.
- A change to a principle is a **breaking change** to the future engine. It must be reviewed and versioned.
