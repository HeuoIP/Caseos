# AR-002 -- Phase 3 Intelligence Runtime Review V1

- **Reviewer:** Codex architecture review pass
- **Date:** 2026-07-31
- **Reviewed commits:** `1a7f7f2` ... `2576a4c` (Sprint 19.1 ... Sprint 19.4)
- **Scope:** all Phase 3 runtime code, the full ADR-013 ... ADR-018 set, the
  Phase 3 sprint deliverables, Sprint 20 readiness
- **Constraint:** Inspection only. No code change. No feature work.
  Every recommendation is a pointer for a future ADR or Sprint.
- **Related:** `docs/reviews/AR-001_CaseOS_Architecture_Review_V1.md`
  (the pre-Phase-3 review, dated 2026-07-30).

---

## 0. Executive Summary

Phase 3 has successfully transitioned CaseOS from **documented
intelligence architecture** (Phase 2 close) to **executable
intelligence runtime** (Phase 3 close). The four sprints 19.1--19.4
landed a six-stage pipeline, three real reasoning engines, an
evidence-based trust evaluator, and a customer-facing recommendation
composer. **30/30 tests are green**; the end-to-end flow
`Human -> Knowledge -> Decision -> Trust -> Recommendation -> Markdown`
runs from CLI; the e2e output matches ADR-017 Section 8 worked example.

However, the transition is **half complete**. Three of the four
intelligence engines that ADR-013 promised are real. The fourth
(Human Understanding) is still a placeholder. The fifth
(Feedback Learning Loop per ADR-018) is **not even a placeholder** --
no code, no slot, no test. The V2 Blueprint's
**Human Understanding Engine** + **Feedback Learning Engine** are
the two pillars that distinguish CaseOS V2 from a one-shot advisor;
both remain documentation-only.

The first intelligence loop is now closed end-to-end. The **learning
loop** is still open. Maturity is **Level 2 (Reasoning modules
executable), transitioning to Level 3 (Evidence-supported
intelligence)**. To reach Level 3 we need Sprint 20 (Evidence
Retrieval); to reach Level 4 we need ADR-018 implemented as code.

| Engine / Module | ADR | Status |
|---|---|---|
| Human Understanding | ADR-013 | **Missing** (placeholder only) |
| Knowledge / CKO | ADR-015 | **Partial** (loader + 3 sample KOs; no retrieval) |
| Decision Intelligence | ADR-014 | **Implemented** (Sprint 19.2: R-01/02/03) |
| Trust Intelligence | ADR-016 | **Implemented** (Sprint 19.3: T-01/02/03) |
| Recommendation | ADR-017 | **Implemented** (Sprint 19.4: RCM-01/02/03) |
| Feedback Learning | ADR-018 | **Missing** (zero code) |
| Pipeline + Stage | -- | **Implemented** (Sprint 19.1) |
| CLI + Markdown | -- | **Implemented** (Sprint 19.1 + 19.4) |

---

## 1. Review Context

### 1.1 Milestones reviewed

| Commit | Sprint | Subject |
|---|---|---|
| `d81d496` | Sprint 19 | CaseOS Brain Runtime V1 -- spec landed |
| `1a7f7f2` | Sprint 19.1 | Brain Runtime Skeleton Implementation |
| `d7e0aa8` | Sprint 19.2 | Decision Intelligence Runtime V1 |
| `1ef7f6d` | Sprint 19.3 | Trust Intelligence Runtime V1 |
| `2576a4c` | Sprint 19.4 | Recommendation Intelligence Runtime V1 |

### 1.2 Primary review question

> Has CaseOS successfully transitioned from **documented intelligence
> architecture** to **executable intelligence runtime**?

**Answer: Yes for 3 of 4 engines; partial for Knowledge; no for
Human and Feedback.** The transition closes the most important loop
(a decision + trust + recommendation can be produced for a real
project.json), but two of the four V2 Blueprint engines
(`Human Understanding` and `Feedback Learning`) remain
documentation-only.

---

## 2. Runtime Architecture Map

### 2.1 Current pipeline (6 stages, 1 placeholder)

The runtime pipeline assembled by `default_pipeline()` in
`backend/caseos/brain/runtime/pipeline.py`:

```text
Input (ProjectContext)
   v
Human Understanding       <-- placeholder (HumanModule, ~20 LOC)
   v
Knowledge                 <-- loader + 3 sample KOs
   v
Decision (Sprint 19.2)    <-- DecisionEngine + RuleR1/R2/R3
   v
Trust    (Sprint 19.3)    <-- TrustEngine + T-01/T-02/T-03
   v
Recommendation (19.4)     <-- RecommendationEngine + RCM-01/02/03
   v
Output (Markdown render)
```

`PipelineContext` carries the shared mutable state across the
six stages; each stage reads and writes one slot.

### 2.2 Slot-level state machine

| Slot | Written by | Read by |
|---|---|---|
| `human_context` | HumanModule | (currently nobody) |
| `knowledge_patterns` | KnowledgeModule | Decision, Trust |
| `decision_object` | DecisionModule | Trust, Recommendation |
| `trust_object` | TrustModule | Recommendation, Output |
| `recommendation` | RecommendationModule | Output |
| `metadata.markdown` | OutputModule | CLI / e2e |

The state machine is clean: each stage has one writer, one or more
readers, no cycle. The empty column for `human_context` (no readers
in Phase 3) is the smoking gun for ADR-013.

---

## 3. Architecture-to-Runtime Traceability (ADR-by-ADR)

### 3.1 ADR-013 -- Human Understanding Engine

- **Status:** Documented, **not implemented**.
- **Runtime mapping:** `backend/caseos/intelligence/human/module.py`,
  30 lines, one class (`HumanModule`), five stub fields.
- **What works:** the module writes a `human_context` dict into the
  pipeline context, so the wire contract is preserved.
- **What is missing:**
  - No `user_goal` parsing beyond string pass-through.
  - No preference model (Decision + Emotion + Style are stubs).
  - No user signal collection (no clicks, no feedback ingestion).
  - No decision_style inference; the field is hard-coded
    `"supportive"`.
- **Verdict:** **placeholder only**. The engine cannot capture
  intent, cannot read feedback, cannot adapt.

### 3.2 ADR-014 -- Decision Intelligence Model

- **Status:** **Implemented** in Sprint 19.2.
- **Runtime mapping:** `backend/caseos/intelligence/decision/module.py`
  + `tests/test_decision_rules.py`.
- **What works:** `DecisionEngine` with three rules (R-01, R-02,
  R-03) implementing the spec's three V1 cases. Trace carries
  `rule_id` + matched signals. Refusal path returns the
  `_more_information_required` shape.
- **Coverage of ADR-014 spec:**
  - 7 Decision Object fields: all emitted.
  - `Observation / Diagnosis / Root Cause / Priority / Strategy /
    Experience Logic / Recommendation Direction`: surface in the
    reasoning text. Some are merged into single fields
    (`decision` carries both strategy and experience logic; that is
    documented in the module docstring as a Sprint 19.2 -> ADR-014
    field-name mapping).
- **Tests:** 7 decision tests cover R-01, R-02, R-03, the
  `no-rule-matched` refusal path, and the first-rule-wins ordering.
- **Verdict:** **complete for V1**. Field-name mapping to ADR-014
  wording is preserved as a follow-up for a future Sprint 19.x
  renaming ADR.

### 3.3 ADR-015 -- Knowledge Object Model

- **Status:** **Partial** (loader + 3 sample KOs; no retrieval).
- **Runtime mapping:** `backend/caseos/knowledge/objects/loader.py`
  + `samples/{golden_case,failure_pattern,decision_pattern}.json`.
- **What works:** the loader respects the ADR-015 contract
  (loads every `.json` under a directory, requires `identity`).
  The 9 ADR-015 fields are visible across the three samples
  (`identity`, `situation_context`, `observation`, `diagnosis`,
  `decision`, `principle`, `applicability`, `boundary`, `feedback`).
- **What is missing:**
  - No retrieval. Decision and Trust receive the *entire* loaded
    set; the `applicability_match` in the trust object is currently
    computed by simple substring equality on `suitable[]`.
  - No CKO `user_affinity` extension from ADR-013.
  - No Golden Case vs Failure Pattern vs Decision Pattern typed
    discrimination -- the loader treats them uniformly.
  - No evaluation score from ADR-012; samples carry no `learning_value`
    or scoring fields.
- **Tests:** 3 loader tests pass. No retrieval tests because there
  is no retrieval.
- **Verdict:** **prototype**. Knowledge is loadable but not
  retrievable; the system is "evidence-aware" in name only.

### 3.4 ADR-016 -- Trust Intelligence Model

- **Status:** **Implemented** in Sprint 19.3.
- **Runtime mapping:** `backend/caseos/intelligence/trust/module.py`
  + `tests/test_trust_rules.py`.
- **What works:** `TrustEngine` with three rules (T-01, T-02, T-03)
  covering full evidence, decision-without-evidence, and
  contradictory evidence. The Trust Object carries the five
  ADR-016 fields (`evidence`, `source_reliability`,
  `applicability_match`, `confidence`, `uncertainty_handling`).
- **Coverage of ADR-016 spec:**
  - The V1 `ALLOWED_LEVELS = ("Medium", "Low")` invariant is
    enforced in `_finalise()`. High is structurally impossible.
  - Contradiction heuristic now reads `principle + boundary`
    (str-or-list tolerant) and uses a narrow
    "remove-before-<verb> <noun>" matcher to avoid false positives
    on benign "create an experience" decisions.
  - The canonical Sprint 19.3 caveat ("No site image analysis
    available yet...") is appended to every Trust Object so the
    user always sees what is unknown.
- **Tests:** 8 trust tests cover T-01, T-02, T-03, the
  T-03-over-T-01 priority, the `High`-forbidden invariant, the
  canonical caveat invariant, the no-decision-object path, and
  the stage wire contract.
- **Verdict:** **complete for V1**. One known follow-up: ADR-018
  will replace the contradiction heuristic with semantic
  comparison.

### 3.5 ADR-017 -- Recommendation Engine

- **Status:** **Implemented** in Sprint 19.4.
- **Runtime mapping:** `backend/caseos/intelligence/recommendation/module.py`
  + `tests/test_recommendation_rules.py`.
- **What works:** `RecommendationEngine` composes the seven
  ADR-017 sections from Decision + Trust. Three constraint rules
  (RCM-01/02/03) validate the composition: no decision
  modification, no equipment list dumping, trust always appears.
- **Coverage of ADR-017 spec:**
  - 7 sections emitted in canonical order
    (situation_understanding, problem_diagnosis, strategic_direction,
    experience_concept, implementation_direction, evidence,
    confidence_and_caveats).
  - Decision's diagnosis preserved verbatim (RCM-01).
  - Equipment-list anti-pattern blocked (RCM-02).
  - Trust evidence + confidence + caveats always present (RCM-03).
  - The `_trace` block records both source rule IDs
    (`decision_rule_id` and `trust_rule_id`) so the full audit chain
    `Human -> Knowledge -> Decision (R-01) -> Trust (T-01) ->
    Recommendation (RCM-01/02/03) -> Markdown` is visible.
  - The renderer produces the seven-section Markdown matching
    spec section 8 worked example.
- **Tests:** 10 recommendation tests cover the three spec domain
  cases (R-01 / R-03 / low-confidence more-info) plus 7 invariants
  (canonical order, RCM-01/02/03 each always pass, stage wire
  contract, missing-Decision and missing-Trust do not crash).
- **Verdict:** **complete for V1**.

### 3.6 ADR-018 -- Feedback Learning Loop

- **Status:** **Documented, not implemented**.
- **Runtime mapping:** **none**. No `caseos.intelligence.feedback`
  package, no stage, no test.
- **What is missing:** everything. The four feedback voices
  (preference / project outcome / expert evaluation / system
  self-evaluation) have no consumer. The `feedback` field on the
  three sample Knowledge Objects is a static array, not a stream.
- **Verdict:** **ADR exists, zero code**. This is the single
  largest gap in Phase 3.

---

## 4. Runtime Pipeline Review

### 4.1 Are stage boundaries clear?

**Yes.** Each stage has:

- A `name` class attribute (e.g. `name = "decision"`).
- A `run(ctx) -> ctx` method.
- One or two well-defined `ctx` slots to read/write.

The `PipelineContext` is a frozen dataclass container
(`ctx.project`, `ctx.human_context`, `ctx.knowledge_patterns`,
`ctx.decision_object`, `ctx.trust_object`, `ctx.recommendation`,
`ctx.metadata`); each stage touches only its own slots. Stage
boundaries are clean.

### 4.2 Are responsibilities correctly separated?

**Mostly yes**, with one exception:

| Concern | Owner | Correct? |
|---|---|---|
| Project input -> situation | HumanModule | yes (placeholder) |
| Project input -> known KOs | KnowledgeModule | yes |
| Signals -> Decision | DecisionModule | yes |
| Decision + Knowledge -> Trust | TrustModule | yes |
| Decision + Trust -> Recommendation | RecommendationModule | yes |
| Recommendation -> Markdown | OutputModule | yes |

**Exception -- Trust reads `decision_object.decision` text to do
contradiction detection.** This is a soft responsibility leak:
Trust is supposed to *render* a verdict, not to *parse* the
Decision's wording. The current V1 heuristic is a placeholder;
ADR-018 will replace it. Acceptable for V1; flag for follow-up.

### 4.3 Are any modules leaking responsibility?

- **Decision into Trust** (the contradiction heuristic): noted
  above. Acceptable for V1; documented as ADR-018 follow-up.
- **Recommendation preserves Decision** (RCM-01 enforces
  substring presence): correct in spirit -- the constraint lives
  in the *recommender* because only the recommender writes the
  output, but it is effectively a property of the boundary between
  Decision and Recommendation. Worth a future ADR if the
  constraint list grows.
- **Knowledge into Decision** (signal extraction reads
  `knowledge_patterns[*].principle`): this is correct. The
  Decision Engine uses knowledge to *narrow the diagnosis* but
  the decision rule is still rule-driven; knowledge is
  supporting evidence, not a decision itself.

No hard leaks. The architecture is layered.

---

## 5. Intelligence Capability Assessment

### 5.1 Human Understanding

| Question | Status |
|---|---|
| Can system capture user intent? | **Partial** -- only `user_goal` pass-through |
| Is preference model executable? | **No** -- stub fields, no model |
| Is user signal collection missing? | **Yes, entirely missing** |

**Rating: Prototype (placeholder).** ADR-013 is the V2 Blueprint
promise that distinguishes CaseOS from a one-shot advisor; the
runtime has not caught up.

### 5.2 Knowledge Intelligence

| Question | Status |
|---|---|
| Is Knowledge Object contract respected? | **Yes** for the 9 ADR-015 fields |
| Is retrieval missing? | **Yes, entirely missing** |
| Are evidence sources sufficient? | **No** -- 3 sample KOs only |

**Rating: Partial (loader + samples).** No retrieval = no
selective evidence = no scalability story. Sprint 20 should
land a retrieval engine.

### 5.3 Decision Intelligence

| Question | Status |
|---|---|
| Are decisions explainable? | **Yes** -- `_trace.rule_id` + matched signals |
| Are boundaries preserved? | **Yes** -- `boundary` field always emitted |
| Can decisions refuse? | **Yes** -- `_more_information_required` path |

**Rating: Implemented.** 7/7 decision tests pass; refuse path
emits "More information required" per ADR-014 Principle 5.

### 5.4 Trust Intelligence

| Question | Status |
|---|---|
| Is confidence evidence-based? | **Yes** -- derived from rule match + applicable KOs |
| Can system avoid hallucinated certainty? | **Yes** -- High is structurally impossible in V1 |

**Rating: Implemented.** 8/8 trust tests pass. The `_finalise()`
downgrade + caveat guarantee that no V1 trust object can read as
"certain".

### 5.5 Recommendation Intelligence

| Question | Status |
|---|---|
| Does output preserve decision? | **Yes** -- RCM-01 substring check |
| Is customer-readable? | **Yes** -- 7 ADR-017 sections in user language |
| Does it avoid equipment dumping? | **Yes** -- RCM-02 forbidden vocabulary check |

**Rating: Implemented.** 10/10 recommendation tests pass. The
Markdown output matches the spec section 8 worked example.

### 5.6 Feedback Intelligence

| Question | Status |
|---|---|
| Is ADR-018 implemented? | **No** |
| Can outcomes modify knowledge? | **No** -- KOs are static JSON |
| Is learning loop missing? | **Yes, entirely** |

**Rating: Missing.** This is the largest single gap in Phase 3.

---

## 6. Runtime Gaps (A / B / C / D)

A = Completed; B = Implemented but Prototype; C = Architecture
exists but Runtime missing; D = Future capability.

| Module | Class | Notes |
|---|---|---|
| Pipeline + Stage contract | **A** | Six stages wired, immutable interface |
| ProjectContext + PipelineContext | **A** | Frozen dataclass + mutable shared state |
| Decision Engine (R-01/02/03) | **A** | 7 tests, refuse path, trace |
| Trust Engine (T-01/02/03) | **A** | 8 tests, V1 `High`-forbidden, canonical caveat |
| Recommendation Engine (RCM-01/02/03) | **A** | 10 tests, 7 sections, customer language |
| Markdown renderer (7 sections) | **A** | Matches ADR-017 section 8 |
| CLI (`caseos analyze`) | **A** | Subprocess test green |
| Knowledge loader + 3 sample KOs | **B** | Loader is real; 3 KOs is a demo set |
| Human Understanding Engine | **C** | ADR-013 documented; 30-LOC placeholder only |
| Feedback Learning Loop | **C** | ADR-018 documented; zero code |
| Knowledge Retrieval | **C** | Implied by ADR-015 + Sprint 20 spec; not started |
| CKO typed discrimination (GC vs FP vs DP) | **C** | All KOs load as `KnowledgeObject` dicts |
| CKO evaluation score (ADR-012) | **C** | `learning_value` field is a doc; no scorer |
| Golden Case -> Failure Pattern mapping | **C** | Decision Engine reads `principle` only |
| LLM-assisted reasoning | **D** | Explicitly out of scope in Sprint 19.x |
| Web UI / API surface | **D** | AR-001 noted `app/api/` is empty; still empty |
| User tracking / feedback ingestion | **D** | Depends on ADR-018 + product layer |
| Image generation / design rendering | **D** | Explicitly out of scope per ADR-005 |
| Vector database | **D** | Not needed before Sprint 20+ |

**B-class count: 1. C-class count: 6. D-class count: 5.**

The single B (Knowledge loader) is acceptable as a starting
point; the six C items define the next two sprints' worth of
work.

---

## 7. Sprint 20 Readiness Review

Sprint 20 is "Evidence Retrieval Intelligence V1" per the
existing roadmap. Four review questions:

### 7.1 What evidence does Decision Engine need?

- **Currently:** all 3 KOs are loaded; signals scan the project
  text but ignore KOs except for "overloaded" detection.
- **For Sprint 20:** the Decision Engine needs **applicable
  Knowledge Objects** -- the subset of KOs whose
  `applicability.suitable` matches the project type. This is
  exactly what `_supporting_knowledge()` already does in
  `trust/module.py`; that helper should be promoted to a
  shared utility in the retrieval module.

### 7.2 What Knowledge Objects should Retrieval search?

- Three categories from the samples:
  - **GoldenCase** (`golden_case.json`) -- the *target*
    outcome the design should approach.
  - **FailurePattern** (`failure_pattern.json`) -- the
    *anti-target* the design must avoid.
  - **DecisionPattern** (`decision_pattern.json`) -- the
    *strategy move* that translates diagnosis into direction.
- For Sprint 20, retrieval needs at minimum: tag-based filter
  (project_type), text-match on `situation_context` and
  `observation`, and ordering by `learning_value` (once ADR-012
  is scored).
- No vector DB required for V1. Substring + applicability
  matching is sufficient for the sample corpus and is
  deterministic / testable.

### 7.3 Should Retrieval optimize similarity or applicability?

- **Applicability first.** The Decision Engine needs KOs that
  apply to its project type, not the most visually similar KO.
  The current `applicability_match` is a binary "yes/no"; V1
  retrieval can rank by:
  1. `applicability.suitable` membership (hard filter).
  2. `principle` keyword overlap with the project text
     (soft score).
  3. KO `learning_value` from ADR-012 (when available).
- The mental model is "library lookup", not "image similarity".

### 7.4 What should Trust consume from Retrieval?

- Trust already consumes the full `knowledge_patterns` list.
  After Sprint 20, Trust should consume **only the
  retrieved subset** so its `applicability_match` can move from
  binary to a ranked score. The `_finalise()` and
  `source_reliability` logic do not need to change; only the
  input list does.
- The trust object should expose a new field
  `evidence_count` (number of KOs that actually supported the
  decision) so the recommendation engine can narrate it
  faithfully.

### 7.5 Sprint 20 boundary

**Recommend: Sprint 20 lands a KnowledgeRetriever stage that
sits between the existing `knowledge` stage and the `decision`
stage.** Pipeline becomes 7 stages. The retriever:

- Reads the project + the loaded KOs.
- Filters / ranks by `applicability` + principle overlap.
- Writes a `retrieved_knowledge_patterns` slot on the context.
- Decision and Trust are rewired to read that slot.

No LLM, no vector DB, no embedding -- per Sprint 20 spec
boundary.

---

## 8. Critical Architecture Risks

### Risk 1 -- Rules becoming too hard-coded

- **Status:** **Active.**
- **Where:** `decision/module.py` has 3 hand-written rules
  (R-01/02/03) with 5 hand-written signal regexes
  (`_SIGNAL_PATTERNS`). Each new rule or signal is a code
  change, not a knowledge entry.
- **Impact:** the Decision Engine cannot grow without
  re-deployment. This is OK for V1 (3 rules cover the spec)
  but is the wrong shape for V2.
- **Mitigation:** in Sprint 21+ migrate each rule to a
  Knowledge Object (e.g. a `DecisionPattern` whose `principle`
  carries the rule and whose `applicability` carries the
  signals). The Decision Engine becomes a generic matcher.

### Risk 2 -- Knowledge remaining static

- **Status:** **Active.**
- **Where:** the 3 sample KOs are checked into the repo.
  There is no ingestion path.
- **Impact:** the system cannot learn from real cases. The
  pipeline is a closed loop with a frozen knowledge base.
- **Mitigation:** Sprint 20 (retrieval) + ADR-018 (feedback).
  Even without a UI, the case intelligence pipeline from
  Sprint 18 (GoldenCasePipeline) can be wired to *write* into
  the sample directory.

### Risk 3 -- Retrieval becoming image similarity search

- **Status:** **Watch.**
- **Where:** Sprint 20 spec leaves the door open. If retrieval
  optimises on visual similarity (CLIP-style) instead of
  applicability, the system will return cases that look like
  the user's site but solve the wrong problem.
- **Impact:** false confidence. Trust T-01 would still fire
  (we have a "matching" KO) but the recommendation would be
  wrong.
- **Mitigation:** Sprint 20 ADR should explicitly state
  "applicability-first retrieval" and lock similarity as a
  later, optional, ranking signal. This review recommends
  the Sprint 20 ADR include the applicability-first rule
  in its decision section.

### Risk 4 -- Feedback loop never activated

- **Status:** **Active.**
- **Where:** ADR-018 is documented but has no slot, no
  consumer, no test.
- **Impact:** without the feedback loop, the system is a
  one-shot advisor. It can never be a "continuously-evolving
  brain" per V2 Blueprint Section 2.4.
- **Mitigation:** the cheapest V1 feedback loop is a
  append-only `feedback_log.json` that records the
  Recommendation's `_trace` and a user-supplied outcome
  label. Sprint 21+ can consume it.

### Risk 5 -- Human Understanding remaining shallow

- **Status:** **Active.**
- **Where:** `human/module.py` is 30 LOC, five stub fields.
  No signal collection, no preference model.
- **Impact:** every recommendation is audience-agnostic.
  ADR-013's promise of "an AI spatial decision platform
  centred on understanding users" cannot be fulfilled
  without this engine.
- **Mitigation:** Sprint 22 (Human Understanding Runtime V1)
  is the next slot. Until then, the Recommendation Engine's
  `audience_variant` is a hard-coded string.

---

## 9. Final Assessment -- Phase 3 Maturity

The V2 Blueprint's maturity ladder (Levels 0 -- 4):

| Level | Definition | Reached? |
|---|---|---|
| 0 | Documentation only | **Yes** (pre-Phase 3) |
| 1 | Pipeline exists | **Yes** (Sprint 19.1) |
| 2 | Reasoning modules executable | **Yes** (Sprints 19.2 -- 19.4) |
| 3 | Evidence-supported intelligence | **Partial** -- Trust exists, but retrieval does not |
| 4 | Learning intelligence | **No** -- ADR-018 not implemented |

**Current maturity: Level 2, transitioning to Level 3.**

The "transitioning" qualification is precise: Sprint 20
(Evidence Retrieval Intelligence V1) is the gate. Once a
retrieval stage exists between Knowledge and Decision, and
Trust consumes the retrieved subset, the system will be
Level 3.

Why this is a meaningful transition (not Level 2 with extra
steps):

1. **Three of the four V2 Blueprint engines are real.** The
   V2 Blueprint promised four intelligence engines; we have
   three. The fourth (Human Understanding) is a placeholder
   but the *wire contract* is in place, so a real
   implementation can drop in without changing the rest of
   the system.
2. **The first end-to-end loop is closed.** A
   `project.json` can flow through
   `Human -> Knowledge -> Decision -> Trust -> Recommendation
   -> Markdown` and produce a customer-readable report with
   confidence + caveats. The audit chain (every stage's
   `_trace`) is preserved across the whole run.
3. **The architecture is layered, not coupled.** A change to
   any one engine is contained: the Trust Engine can be
   swapped, the Recommendation Engine's section generators
   can be LLM-replaced, the Decision Engine's rules can be
   migrated to Knowledge Objects, all without touching the
   others. The Sprint 19.x pattern of "preserve wire
   contract, change implementation" worked.

Why this is **not** Level 3 yet:

1. **No retrieval.** Trust's `applicability_match` is binary.
2. **Human Understanding is a stub.** The system cannot
   adapt to the user.
3. **Feedback loop does not exist.** The system cannot
   learn.

---

## 10. Top 5 Recommendations

Each recommendation is one phase-3 follow-up: an ADR pointer
plus a Sprint pointer plus a priority.

### 1. Land Sprint 20 -- Evidence Retrieval Intelligence V1

- **Why:** the single highest-value next step. Without
  retrieval, Knowledge is a frozen library; with retrieval,
  the library becomes searchable evidence that Decision and
  Trust can selectively consume.
- **Impact:** unlocks Level 3 maturity; reframes Trust from
  binary applicability to ranked applicability; gives the
  Recommendation Engine a narrative for *why* this KO was
  chosen.
- **Priority:** **P0**.
- **Related:** Sprint 20 spec; ADR-015 (Knowledge Object);
  ADR-016 Section 3.3 (applicability matching); AR-001
  finding "Retrieval Engine".

### 2. Implement ADR-013 -- Human Understanding Runtime

- **Why:** the V2 Blueprint's brand promise
  ("understanding users") is unmet. The wire contract is in
  place; only the engine itself is missing.
- **Impact:** allows audience-aware recommendations (Sprint
  19.4's `audience_variant` becomes real); enables feedback
  ingestion (the user-side half of the feedback loop);
  unblocks the Product Layer's interview-style input.
- **Priority:** **P0** (or **P1** if Sprint 20 must go
  first for capability reasons).
- **Related:** ADR-013; V2 Blueprint Section 2.1; Product
  Blueprint V1 Section 4.

### 3. Implement ADR-018 -- Feedback Learning Loop V1 (append-only)

- **Why:** without it, the system cannot learn. The cheapest
  V1 is an append-only `feedback_log.json` that records
  `Recommendation._trace` + a user-supplied outcome label.
  No database, no analytics, no UI required.
- **Impact:** establishes the data flywheel; unlocks Level 4
  maturity (learning intelligence); provides the substrate
  for ADR-013's preference model.
- **Priority:** **P1**.
- **Related:** ADR-018; V2 Blueprint Section 2.4; AR-001
  finding "Feedback system".

### 4. Promote contradiction heuristic + rule base to Knowledge Objects

- **Why:** Risk 1 (rules becoming too hard-coded) is active.
  Three rules in code are manageable; thirty are not. The
  shape of the Decision Engine should converge with the
  shape of the Knowledge Object.
- **Impact:** the Decision Engine becomes a generic matcher;
  new rules are knowledge entries, not code changes; the
  Sprint 19.2 / 19.3 / 19.4 pattern of
  `engine + Rule[N] + _trace` becomes a *loader* not a
  *programmer*.
- **Priority:** **P2**.
- **Related:** ADR-010 (Decision Rules Framework); ADR-015
  Section "DecisionPattern"; CKO Decision Pattern samples
  (already in `samples/decision_pattern.json`).

### 5. Establish the Sprint 20 ADR with an applicability-first lock

- **Why:** Risk 3 (retrieval becoming image similarity
  search) is the most likely future regression. It is much
  cheaper to lock the principle in the ADR than to undo the
  pattern after Sprint 20.
- **Impact:** prevents the system from drifting into
  "looks-like" matching when it should be doing
  "applies-to" matching.
- **Priority:** **P0** (because the lock must precede the
  Sprint 20 implementation).
- **Related:** Sprint 20 spec; ADR-015; ADR-016 Section
  3.3; AR-001 finding "Theme Engine vs Retrieval Engine".

---

## 11. Out-of-Scope / Non-Goals (this review)

This document is inspection only. The following are
**explicitly NOT** addressed here and require their own
sprints:

- Product Layer (CLI only; no FastAPI / UI / database)
- User tracking, behavior collection
- Image generation, design rendering
- Vector database, embedding service
- Fine-tuning, training data pipelines
- Multi-tenancy, authentication, billing

These are all `D`-class in Section 6. They will become
relevant in Phase 4 (Continuous Space Advisor) per the V2
Blueprint roadmap.

---

## 12. Acceptance Criteria Self-Check

The AR-002 brief required five acceptance criteria. Status:

| # | Criterion | Status |
|---|---|---|
| 1 | Complete ADR-013 ... ADR-018 runtime audit | **Done** -- Section 3 |
| 2 | Assess Sprint 19 implementation | **Done** -- Sections 4, 5 |
| 3 | Define Sprint 20 boundary | **Done** -- Section 7 |
| 4 | Identify missing intelligence capabilities | **Done** -- Section 6 |
| 5 | Provide architecture maturity assessment | **Done** -- Section 9 |

All five acceptance criteria are met. No code was modified;
no feature was added; the document is inspection only.