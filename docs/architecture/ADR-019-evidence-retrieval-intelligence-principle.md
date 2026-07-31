# ADR-019: CaseOS Evidence Retrieval Intelligence Principle V1

- **Status:** Proposed
- **Date:** 2026-07-31
- **Layer:** Intelligence (Evidence Pipeline)
- **Affects:** Sprint 20 (Evidence Retrieval V1), Knowledge Module,
  Decision Engine (consumes Evidence Package), Trust Engine
  (applicability ranking), Recommendation Engine (renders evidence
  count), future Vision Model integration.
- **Related ADRs:** ADR-014 (Decision Intelligence Model),
  ADR-015 (Knowledge Object Model), ADR-016 (Intelligence Trust
  Model), ADR-017 (Recommendation Engine), ADR-018 (Feedback
  Learning Loop)
- **Implements:** the **Evidence Retrieval Intelligence** declared in
  AR-002 Section 6 (C-class gap) and the Sprint 20 backlog row of
  `docs/sprints/Sprint_Roadmap.md` Section 4.
- **Triggers:** Sprint 20 implementation; a doc-only follow-up to
  the V2 Blueprint Section 8 placeholder table to add this slot.
- **Supersedes:** none
- **Source of truth:** `docs/architecture/ADR-019-evidence-retrieval-intelligence-principle.md`

> **Reading note (model, not implementation).** Inherited from
> ADR-014 through ADR-018: this ADR defines **the principle and
> contract of an Evidence Package** -- what Retrieval is and what
> it is not. It does not define vector databases, embedding
> services, ranking algorithms, or UI surfaces. Where a
> "Knowledge Object" appears below, it is a unit per ADR-015.
> Where a "Decision" appears, it is a unit per ADR-014. Where a
> "Trust Object" appears, it is a unit per ADR-016.

---

## 1. Context

CaseOS Phase 3 Runtime (Sprint 19.1 -- 19.4) supports the
end-to-end loop:

```text
Human Understanding -> Knowledge -> Decision -> Trust -> Recommendation -> Output
```

`docs/reviews/AR-002_Phase_3_Intelligence_Runtime_Review_V1.md`
(Section 6, C-class gaps; Section 7, Sprint 20 Readiness; Section
8, Risk 3) identified the next missing capability:

> **Evidence Retrieval Intelligence.**

The Knowledge Module currently **loads** every Knowledge Object
under a directory and hands the full set to the Decision Engine
and the Trust Engine. There is no **retrieval** step that
selects, ranks, and narrates the evidence that supports a
particular decision.

Without an explicit retrieval contract, a future Sprint 20
implementation is at risk of optimising for one of:

- image similarity (visual matching)
- popularity ranking
- superficial style matching
- equipment catalogue search

These optimise the wrong objective. A case that *looks like*
the user's site is not the same as a case that *applies to* the
user's problem.

This ADR is the **principle** that Sprint 20 will implement
against. It exists to lock the philosophy **before** the
implementation, so that the temptation to drift toward
"image-similarity search" is documented as a rejected
anti-pattern.

---

## 2. Core Decision

CaseOS Retrieval is **not**:

> "Find similar images."

CaseOS Retrieval **is**:

> "Find applicable knowledge evidence that supports a spatial
> decision."

Primary objective:

> **Decision Applicability > Visual Similarity**

This is the single most important sentence in the ADR. Every
implementation choice in Sprint 20 should be testable against
it: does this change bring us closer to "applicable evidence"
or closer to "visual similarity"? When the two diverge,
applicability wins.

---

## 3. Retrieval Object Definition

Retrieval searches **Knowledge Objects** (ADR-015), not raw
images, not reference boards, not equipment catalogues.

The five primary Knowledge Object types that retrieval is
allowed to return:

| Type | Purpose |
| --- | --- |
| **Golden Case** | Find proven successful examples. |
| **Decision Pattern** | Find previous judgment structures. |
| **Expert Principle** | Find professional reasoning. |
| **Failure Pattern** | Find situations where similar decisions failed. |
| **User Preference** | Understand human alignment. |

Retrieval **must not** return:

- raw images as primary results (images are evidence inside
  a Golden Case, not retrieval results themselves);
- Pinterest-style reference boards;
- equipment catalogues ("projects with slides");
- popularity rankings.

---

## 4. Evidence Package Contract

Retrieval output is **not a list**. It is an **Evidence Package**.

An Evidence Package has five components:

1. **Relevant Knowledge Objects** -- the KOs that match.
2. **Applicability Reason** -- *why* this evidence matches the
   current situation (project type, decision rule id, etc.).
3. **Supporting Principle** -- the design or decision principle
   the KO contributes.
4. **Boundary Warning** -- when this evidence should **not** be
   applied (mirrors the KO's `boundary` field).
5. **Trust Contribution** -- how this evidence moves the
   confidence of the eventual decision (up, down, or
   ambiguous).

This five-field shape is the input contract for the Trust
Engine (ADR-016). Trust consumes the Evidence Package; it does
**not** re-derive it.

---

## 5. Retrieval Priority Model

When ranking KOs, retrieval must order by the following
priority list. P1 beats P2 beats P3 ... always.

| Priority | Factor |
| --- | --- |
| **P1** | Decision applicability |
| **P2** | Situation similarity |
| **P3** | Project constraints |
| **P4** | User preference alignment |
| **P5** | Visual similarity |

**Visual similarity is the LAST factor.** It is not forbidden;
it is permitted to break ties, but it is never the primary
sort key.

The Sprint 20 implementation should be testable on this
ordering: a deliberately-applicable-but-not-visually-similar
KO must rank above a visually-similar-but-not-applicable KO.

---

## 6. Relationship With Decision Engine

Retrieval does **not** make decisions.

**Wrong (bypass pattern):**

```text
Retrieval: "Here are similar playgrounds."
        v
Recommendation
```

**Correct (serving pattern):**

```text
Decision: "Need experience anchor."
        v
Retrieval: "Find evidence supporting experience-anchor decisions."
        v
Trust: "Evaluate evidence quality."
        v
Recommendation
```

The Decision Engine is the **authority**. Retrieval serves the
Decision Engine, not the other way round. Sprint 20 must
preserve this directionality in the pipeline; the
`KnowledgeRetriever` stage is to be placed **between** the
existing `Knowledge` stage and the existing `Decision` stage
(see AR-002 Section 7.5).

---

## 7. Relationship With Trust Intelligence

Trust consumes the **Evidence Package** as input.

Trust evaluates:

- **source reliability** (per ADR-016 Section 2.2);
- **applicability** (P1 of the priority model above);
- **repeated success** (per ADR-012 evaluation score, when
  available);
- **uncertainty** (what remains unknown after the evidence is
  considered).

The ADR-016 rule "no evidence -> no High confidence" (Section
2.4) is preserved: if Retrieval returns an empty Evidence
Package, Trust must emit `confidence = Low` and the canonical
"no supporting evidence" caveat.

---

## 8. Anti-Patterns

The following four anti-patterns are explicitly rejected. Each
is named so that future reviews can call it out.

### Anti-pattern 1 -- Image similarity first

> "Find playgrounds visually similar to the user's photo."

Rejected because **appearance does not equal suitability**. A
visually similar playground may have a different budget, a
different user population, or a different climate. The
Recommendation Engine would then propose a solution that looks
right but solves the wrong problem.

### Anti-pattern 2 -- Popularity retrieval

> "Show the most liked cases."

Rejected because **popular does not equal applicable**. A
high-engagement case may be in a context that does not apply
to the current project (different project type, different
budget envelope, different region).

### Anti-pattern 3 -- Equipment retrieval

> "Find projects with slides / swings / climbing frames."

Rejected because **equipment is not intelligence**. A
recommendation built from an equipment list is the
"equipment-dumping" anti-pattern that ADR-017 Section 7.2
already rejects at the recommendation layer; the rejection must
extend to the retrieval layer.

### Anti-pattern 4 -- Recommendation bypass

> Retrieval directly generates a solution without going through
> the Decision layer.

Rejected because **the Decision layer must remain authority**.
Retrieval is a server, not a chef.

---

## 9. Retrieval Lifecycle

The correct architecture:

```text
Experience Data
        v
Knowledge Object (ADR-015)
        v
Retrieval (Sprint 20)
        v
Evidence Package (this ADR)
        v
Decision (ADR-014)
        v
Trust (ADR-016)
        v
Recommendation (ADR-017)
        v
Feedback (ADR-018)
```

The arrow direction is enforced. Retrieval may not feed
Recommendation directly; it may not feed Trust directly; it
may not be skipped. The only valid consumer of an Evidence
Package is the Decision Engine (and transitively Trust, which
re-evaluates the Decision's evidence).

The Feedback loop (ADR-018) writes back into the Knowledge
Object layer, not into the Retrieval layer. Retrieval is
deterministic and stateless; learning happens in the
Knowledge Object corpus.

---

## 10. Sprint 20 Implementation Boundary

Sprint 20 may implement:

- Knowledge Object retrieval
- applicability matching
- evidence package generation
- retrieval trace
- ranking per the priority model (Section 5)
- tests for the four anti-patterns (Section 8)

Sprint 20 must not implement:

- image recommendation engine
- public ranking
- social popularity
- frontend search
- vector database optimisation
- autonomous recommendation
- LLM-based retrieval

The boundary mirrors the discipline of Sprints 19.1 -- 19.4:
**structure first, intelligence second, no LLM, no network
calls.** Sprint 20 is the gate from Maturity Level 2 to
Maturity Level 3 per AR-002 Section 9.

---

## 11. Future Evolution

Embeddings may be used as **infrastructure**, not as the
intelligence itself.

Concretely: a future Sprint may add an embedding index to
**speed up** the applicability filter, but the ranking
contract (Section 5) does not change. Visual similarity may
**not** move up the priority list even when an embedding
service exists.

A future Vision Model integration (post-Phase 3) feeds the
Decision Engine's `observation` slot; it does **not** become
the primary input to Retrieval. The vision observation is a
new piece of evidence; retrieval's job is unchanged.

---

## 12. Acceptance Criteria

ADR-019 is accepted when:

1. Retrieval purpose is clearly defined as "find applicable
   knowledge evidence that supports a spatial decision"
   (Section 2), not image similarity.
2. Decision remains the authority (Section 6); the pipeline
   direction is preserved; no bypass path is documented.
3. The Evidence Package is defined (Section 4) with the five
   components.
4. The Trust relationship is defined (Section 7); empty
   Evidence Package yields Low confidence + canonical caveat.
5. Visual similarity is explicitly constrained to P5
   (Section 5) and rejected as the primary ranking factor
   (Section 8 anti-pattern 1).
6. The Sprint 20 implementation boundary is established
   (Section 10); no LLM, no network, no vector DB in V1.

---

## Final Principle

> CaseOS does not retrieve what looks similar.
>
> CaseOS retrieves what helps make better decisions.

This sentence is the audit anchor. Every Sprint 20 review
question -- "is the retrieval engine behaving correctly?" --
reduces to: "does this behaviour bring us closer to
'applicable evidence' or closer to 'visual similarity'?"

When the answer drifts, the architecture review (next AR-NNN)
names the drift, the ADR is amended, and the implementation is
corrected. The principle is permanent.