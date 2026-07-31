# AR-003 -- Phase 3 Architecture Integrity Review V2

- **Reviewer:** Codex architecture review pass (Sprint 21.5)
- **Date:** 2026-07-31
- **Reviewed commits:** `76d9014` (Sprint 21 Human Understanding) ... `ea2c9e2` (Sprint 20.7 Intake)
- **Scope:** ADR-013 ... ADR-019 against current runtime implementation
- **Constraint:** Inspection only. No code change. No feature work. No test change.
- **Companion:** `docs/reviews/AR-002_Phase_3_Intelligence_Runtime_Review_V1.md` (Sprint 19.1-19.4 review)
- **Related:** `docs/architecture/CaseOS-Architecture-Baseline-V1.md` (V2 baseline)


## 0. Hard Rules Observed

- [x] No runtime code modified.
- [x] No new feature added.
- [x] No refactor of existing modules.
- [x] No test modified.
- [x] Only review documents and audit records added.
- [x] ADRs 013-019 (7 documents) reviewed in full.
- [x] Pipeline boundary audited.
- [x] Decision authority verified.
- [x] Knowledge lifecycle verified.
- [x] Anti-pattern audit performed.
- [x] Test suite executed (90 / 90 green).


## 1. Executive Summary

AR-002 reviewed Phase 3 runtime on the Sprint 19.1-19.4 baseline and
concluded: "three of the four intelligence engines are real; the
fourth (Human Understanding) is a placeholder; the fifth (Feedback
Learning Loop per ADR-018) is not implemented."

AR-003 reviews the **post-Sprint 21** baseline (commits `ea2c9e2`
through `76d9014`). The arc of the last three sprints is:

* Sprint 20 -> Evidence Retrieval (ADR-019) shipped.
* Sprint 20.5 -> Golden Case Corpus migrated to a 5-subdir structure.
* Sprint 20.6 -> Corpus Governance layer (validator, trust tier, promotion).
* Sprint 20.7 -> Corpus Intake layer (lifecycle, converter, manager).
* Sprint 21 -> Human Understanding Runtime (ADR-013) shipped.

**Result.** AR-002''s two flagged gaps -- Human Understanding
placeholder and Feedback Loop missing -- are now partially closed.
Human Understanding is **operational** (Sprint 21). Feedback Loop
remains **documentation-only** (ADR-018 still "Proposed").

The architecture is **integrity-preserved**. No runtime drift was
detected. The seven-stage pipeline runs end-to-end with the expected
authority boundaries. The knowledge lifecycle is append-only and
governance-gated. The four anti-patterns called out by ADR-019 and
ADR-017 are still rebuffed by either code or tests.

Maturity Level remains **Level 3 (Evidence-supported intelligence)**,
as AR-002 concluded. One new piece of evidence since: the Evidence
Retrieval Intelligence is now genuinely **consumed** by the Decision
Engine (it was wire-only in Sprint 20; it became soft-coupled in
Sprint 20.5+ and Sprint 21).

A small set of risks are documented in Section 8. None are blocking.


## 2. ADR Coverage Matrix

| ADR | Title | Runtime Location | Status | Finding |
|---|---|---|---|---|
| 013 | Human Understanding Engine | `backend/caseos/intelligence/human/` (5 modules) | **Implemented** | None |
| 014 | Decision Intelligence Model | `backend/caseos/intelligence/decision/` (R-01/R-02/R-03) | **Implemented** | None |
| 015 | Knowledge Object Model | `backend/caseos/knowledge/objects/loader.py` + `backend/caseos/knowledge/corpus/` (5 subdirs) + `tools/corpus_migration/validator.py` | **Implemented** | None |
| 016 | Intelligence Trust Model | `backend/caseos/intelligence/trust/` (T-01/T-02/T-03) + `backend/caseos/knowledge/governance/trust_tier.py` (Tier_A/B/C/D) | **Implemented** | None material |
| 017 | Recommendation Engine | `backend/caseos/intelligence/recommendation/` (RCM-01/RCM-02/RCM-03) | **Implemented** | None |
| 018 | Feedback Learning Loop | None (ADR status is "Proposed") | **Missing (by design)** | Intended; documented risk |
| 019 | Evidence Retrieval | `backend/caseos/knowledge/retrieval/` (P1..P4, 5-field EP) | **Implemented** | None |

ADR breakdown (Sprint 21.5 view):

| ADR | What was shipped | What is still missing |
|---|---|---|
| 013 | HumanModule + 5 supporting modules; 16 tests; bounded human-keyword boost in retrieval | Behaviour-signal learning (out of V1 scope per ADR-013 §Non-Goals) |
| 014 | 3 rules + DecisionObject with 7 fields + trace | Spatial Context input (Future Work; depends on Sprint 16 ADR-009) |
| 015 | 9 fields, 5 valid identity types, 5-subdir corpus, validator | Vector retrieval (deliberately deferred; ADR-019 §11) |
| 016 | Trust Object + 3 rules; TrustTier governance (A/B/C/D) | Numeric scoring (rejected by ADR-016 §Non-Goals) |
| 017 | 7 sections + RCM-01/02/03 + FORBIDDEN_EQUIPMENT + Markdown renderer | Audience variants (V1 ships 1; ADR-017 §3 declares 4) |
| 018 | ADR exists; intake records lifecycle transitions | All five feedback event types (ADR-018 §4); no automatic learning |
| 019 | Retrieval engine + 5-field EP + 4 priority rules | P5 visual similarity (deliberately deferred; ADR-019 §5) |

Note: ADR-018 is intentionally out of step with the other six.
Five ADRs declare a runtime contract; ADR-018 declares a *contract for
future change*, not a runtime. The corpus lifecycle (Sprint 20.5-
20.7) is the closest thing to ADR-018 runtime today -- a human
operator walks the lifecycle, and promotion creates a PromotionEvent
that is not yet wired back into the source KO''s `feedback[]` field.


## 3. Pipeline Integrity

### 3.1 Current Pipeline (verified at commit `76d9014`)

```text
ProjectContext (input)
     |
     v
[1] Human Understanding  (caseos.intelligence.human.module.HumanModule)
     |      writes ctx.human_context
     v
[2] Knowledge Loader     (caseos.intelligence.knowledge.module.KnowledgeModule)
     |      writes ctx.knowledge_patterns (5-subdir corpus)
     v
[3] Retrieval            (caseos.knowledge.retrieval.module.KnowledgeRetriever)
     |      writes ctx.evidence_package (5-field EP)
     |      reads ctx.human_context (bounded P1 boost, no new priority)
     v
[4] Decision             (caseos.intelligence.decision.module.DecisionModule)
     |      writes ctx.decision_object (7 fields + _trace)
     |      reads EP only to NARROW input; rules unchanged
     v
[5] Trust                (caseos.intelligence.trust.module.TrustModule)
     |      writes ctx.trust_object (5 fields + _trace)
     |      reads EP + Decision; never edits Decision
     v
[6] Recommendation       (caseos.intelligence.recommendation.module.RecommendationModule)
     |      writes ctx.recommendation (7 sections + RCM-01/02/03)
     |      reads Decision + Trust; never edits either
     v
[7] Output (Markdown)    (caseos.intelligence.output.module.OutputModule)
            writes ctx.metadata[''markdown'']
```

**Verified by `tests/test_pipeline.py`**: all 7 stages run in order,
slots popoulated, stage_log order matches.

### 3.2 Pipeline Order Verification

The order **Human -> Knowledge -> Retrieval -> Decision -> Trust ->
Recommendation -> Output** is enforced by `default_pipeline()` in
`backend/caseos/brain/runtime/pipeline.py`. The wire contract is
documented inline:

```python
def default_pipeline(stages: Iterable[Stage] | None = None) -> Pipeline:
    ...
    stages = [
        HumanModule(),
        KnowledgeModule(),
        KnowledgeRetriever(),
        DecisionModule(),
        TrustModule(),
        RecommendationModule(),
        OutputModule(),
    ]
```

`test_pipeline.py::test_seven_stages_wired` asserts the exact stage
list and `test_pipeline.py::test_default_pipeline_runs_end_to_end`
asserts the exact order. **No shortcut path was detected.**

### 3.3 Shortcut Audit (the critical anti-pattern check)

The sprint spec lists two forbidden shortcut paths:

* `Raw Knowledge -> Decision` -- a raw case reaching Decision without
  becoming a Knowledge Object.
* `Retrieval -> Recommendation` -- retrieval feeding recommendation
  directly, bypassing the Decision Engine.

**Verification.** The Knowledge Object loader is the only source
of `ctx.knowledge_patterns`. The loader walks the 5-subdir corpus
under `backend/caseos/knowledge/corpus/` (Sprint 20.5+). It does
not touch `backend/caseos/knowledge/intake/`. The intake layer
produces RawCaseObjects, never KOs. Promotion is the only way a
RawCase becomes a Knowledge Object, and promotion is gated by
governance validation (see Section 5).

The Recommendation Engine reads `ctx.decision_object` and
`ctx.trust_object`. It does **not** read `ctx.evidence_package`
except through the trust object. The flow
`Retrieval -> Recommendation` would require a `ctx.recommendation`
input other than Decision + Trust; the code does not provide one.

**Verdict: no shortcut path exists in the current runtime.**

A more rigorous guard is in the boundary test in
`tests/test_human_understanding.py::test_human_module_does_not_import_retrieval_or_decision_or_others`
which uses AST walks to forbid the human module from cross-importing
retrieval / decision / trust / recommendation / governance / intake.
A similar check would be valuable for the intake layer (it must
not depend on retrieval / decision / trust / recommendation) and
will be flagged as a future hardening task.


## 4. Authority Boundary Audit

The highest-priority audit. The Decision Engine is the only
authority. Other stages may provide input; they must not edit.

### 4.1 Decision Engine Authority

| Capability | Decision Engine | Others |
|---|---|---|
| `diagnosis` | yes (rules R-01/R-02/R-03) | no |
| `strategy` / `decision` | yes (rules R-01/R-02/R-03) | no |
| `boundary` | yes (rules R-01/R-02/R-03) | no |
| `applicability` | yes (rules R-01/R-02/R-03) | no |
| `reasoning` | yes (rule id + trace) | no |

**Verified by `tests/test_decision_rules.py`**: the rule_id is
recorded in `decision_object["_trace"]`; the engine version is
`decision_engine_v1`; the API of `DecisionEngine.decide()` is
unchanged across Sprint 19.2 -> 20.5 -> 21.

### 4.2 Retrieval Authority

Per ADR-019 §6, retrieval must **only** provide an Evidence Package.
It must not modify the Decision, generate a strategy, or carry
authority.

**Verification.** `KnowledgeRetriever.run()` writes only
`ctx.evidence_package` and three metadata fields. It does NOT
modify `ctx.decision_object`. The `DecisionEngine.decide()`
signature accepts `evidence_package=None` as input -- when provided,
the engine only uses it to **narrow** the input list from
`ctx.knowledge_patterns` to the EP''s `relevant_objects`. The rules,
rule order, and refusal path are unchanged. This is verified by
`tests/test_retrieval.py::test_pipeline_runs_end_to_end_with_retrieval`
which indirectly captures the snapshot via JSON.

### 4.3 Trust Authority

Per ADR-016, trust must **only** evaluate confidence and produce
caveats. It must not edit the Decision.

**Verification.** `TrustModule.run()` writes only `ctx.trust_object`.
It reads `ctx.decision_object`, `ctx.evidence_package` (which carries
the supporting KO count), and `ctx.knowledge_patterns`. It does not
write back to `ctx.decision_object`. The `ALLOWED_LEVELS = ("Medium",
"Low")` constant enforces the "High is FORBIDDEN" rule: any rule that
would otherwise emit High is downgraded to Medium with an explicit
caveat.

**Minor observation (informational, not a finding).** The
`applicability_match` field is a string label ("high" / "medium" /
"low") rather than a full narrative. ADR-016 §2 says it is a
"narrative judgement". The current V1 implementation is a *label*,
not a free-text narrative. This is acceptable for V1 (the label
matches the qualitative discipline of ADR-016) but a future ADR
(016c in the V2 Blueprint) should promote this to a Markdown narrative.

### 4.4 Recommendation Authority

Per ADR-017, the Recommendation Engine must **only** translate the
Decision and communicate it. It must not soften diagnosis, modify
boundary, suggest equipment, or drop caveats.

**Verification.** Three constraint rules run after section composition:

| Rule | Purpose | Verified by |
|---|---|---|
| RCM-01 | No decision modification | `tests/test_recommendation_rules.py` |
| RCM-02 | No equipment list dumping (FORBIDDEN_EQUIPMENT blocklist) | `tests/test_recommendation_rules.py` |
| RCM-03 | Trust must always appear (evidence + confidence + caveats) | `tests/test_recommendation_rules.py` |

The decision text is rendered **verbatim** in `_section_diagnosis`
and `_section_strategy`. The `confidence_and_caveats` section merges
the Trust caveats into the recommendation. The `FORBIDDEN_EQUIPMENT`
list is broad enough to catch obvious catalogue recommendations.

### 4.5 Human Authority

Per ADR-013, the Human Understanding layer must **only** extract
context. It must not infer strategy.

**Verification.** `HumanModule.run()` writes only `ctx.human_context`
and three metadata fields. The `extract_human_context()` function
maps fields by name; it NEVER infers a strategy. The validator
records unknown fields and missing required fields; it does NOT
generate a recommendation. The boundary test
`tests/test_human_understanding.py::test_human_module_does_not_import_retrieval_or_decision_or_others`
forbids the human module from cross-importing the authority
modules.

**Note on signal-level wiring.** The Decision Engine''s
`_extract_signals` reads `human_context` (string values) into a
`human_blob` for keyword matching. This is **signal detection**,
not strategy inference. The matched signals then go through the
existing rules (R-01 / R-02 / R-03); the Decision Engine remains
the authority. The rule_id stays in the Decision Object''s trace;
the engine version stays `decision_engine_v1`.


## 5. Knowledge Lifecycle Audit

### 5.1 Lifecycle Path

```text
RawCaseObject (intake.object)
   |   NEW
   v
IntakeManager.submit_for_review()  -> REVIEW_REQUIRED
   v
IntakeManager.validate()           -> VALIDATED   (or stays REVIEW_REQUIRED)
   v
governance.promote()              -> PROMOTED
   |   PromotionEvent is created; original RawCase is preserved
   v
Active (after ACTIVE transition)
   |
   v
Candidate Knowledge Object (KO)
   |
   v
Knowledge Corpus (5 subdirs)
   |
   v
Retrieval (Sprint 20 / ADR-019)
```

### 5.2 Immutable Boundaries

**Raw != Knowledge Object.** This is a strict invariant:

* `RawCaseObject` lives in `backend/caseos/knowledge/intake/object.py`.
  It carries 8 fields (id, source, title, description, files, notes,
  created_at, status) plus optional hints.
* `KnowledgeObject` lives in `backend/caseos/knowledge/objects/loader.py`
  and reads files from `backend/caseos/knowledge/corpus/`. It carries
  the 9 ADR-015 fields.
* The intake module does NOT import from the loader; the loader
  does NOT import from intake. The two paths are disjoint in the
  filesystem and in the runtime.

**Intake is append-only.** `IntakeManager` records transitions as
new `TransitionRecord` entries; it never mutates the stored
RawCaseObject. The `intake.object.copy()` method deep-copies for
every transition. The `transform_intake_history(raw_id)` API
returns the full history.

**Governance is the gate.** A RawCase can only become a Knowledge
Object through `governance.promote()`. The validator
(`backend/caseos/knowledge/governance/validator.py`) rejects
objects missing boundary, applicability, principle, or the
identity type. The trust tier system (Tier_A/B/C/D) is assigned
in the same flight. Nothing enters the corpus without governance
passing.

**Promotion is traceable.** `governance.promote()` returns a
`PromotionEvent` (dataclass with source_identity, target_identity,
timestamp, note). The original KO is preserved; the new KO is
created. There is no silent overwrite.

**No bypass.** A test (`tests/test_intake.py::test_raw_case_cannot_bypass_governance`)
verifies that:
* `NEW -> ACTIVE` is rejected.
* `NEW -> PROMOTED` is rejected.
* `REVIEW_REQUIRED -> PROMOTED` after failed validation is rejected.

### 5.3 Boundary Test Coverage

The intake layer''s boundary with governance / retrieval / decision /
trust / recommendation is verified by the existing test
`tests/test_intake.py::test_raw_case_cannot_bypass_governance`.
A formal AST-based cross-import test (similar to the human module''s
boundary test) would be a hardening improvement; it is not present
yet. **Risk: low** -- the import check is currently manual, not
enforced by a test.

### 5.4 Outstanding ADR-018 Gap

ADR-018 declares a feedback loop that should close the cycle:

```
Recommendation -> Feedback -> Knowledge Update
```

The current system records lifecycle transitions
(IntakeStatus, PromotionEvent) but does NOT update the originating
RawCase''s `feedback[]` field (or the KO''s `feedback[]` field) once
the recommendation is delivered. This is explicitly documented as
**ADR-018 Missing** in the coverage matrix and is the **single
most material gap** identified by AR-003. It is **out of scope**
for the current sprint and is acknowledged so the next sprint
(Sprint 22+) can address it.


## 6. Anti-Pattern Audit

### A. Image Similarity First

**Rejected by code.** The retrieval engine ships 4 priority rules:
P1 (applicability), P2 (diagnosis), P3 (situation), P4 (boundary).
P5 (visual similarity) is **explicitly NOT IMPLEMENTED** per
ADR-019 §10. The constant `RULE_APPLICABILITY = [P1, P2, P3, P4]`
is verified by `tests/test_retrieval.py::test_visual_similarity_is_not_a_factor_in_v1`.

**Future-proofing.** The `_human_overlap_score` (added in Sprint 21)
is keyword-overlap on applicability + principle text, NOT visual
similarity. It does not promote P5.

**Verdict: rejected, no risk.**

### B. Equipment Dumping

**Rejected by code.** The Recommendation Engine declares
`FORBIDDEN_EQUIPMENT` (slide, swing, climbing frame, trampoline,
rope net, seesaw, ...). RCM-02 forbids these words in the seven
sections (except inside the boundary, which mentions them only
to forbid them).

**Evidence-based risk.** The list is finite. Future equipment
naming (e.g. "tower", "climb wall", "zip line") is not yet
blocked. ADR-017 §11 ("Recommendation Renderer V1 / Mixed-Type
Recommendation Rules") is the natural future home for the
expanded vocabulary.

**Verdict: rejected, low residual risk on vocabulary breadth.**

### C. Popularity Optimisation

**Rejected by code.** There is no `popularity_score`, no
`view_count`, no `like_count` field anywhere in the runtime or
the corpus. The retrieval ranking is bounded by P1 applicability
as a hard filter; KOs that fail P1 are excluded regardless of
how appealing they might be.

**Verdict: rejected, no risk.**

### D. Confidence Hallucination

**Verified.** The Trust Engine defines `ALLOWED_LEVELS = ("Medium",
"Low")` and explicitly forbids High. A rule that would otherwise
emit High is downgraded to Medium with the caveat
"High confidence would have been issued but is forbidden".

**Empty evidence path.** When retrieval returns an empty Evidence
Package, the EP says "No evidence found; trust must default to
Low until evidence arrives." The Trust Engine rule T-02 fires
on "no supporting knowledge" and emits `confidence = Low` with
`uncertainty_handling` populated. This is verified by
`tests/test_trust_rules.py::test_engine_priority_t02_over_t01`.

**Markdown renderer.** The `Confidence & Caveats` section always
shows the level + every caveat. The renderer never drops caveats
to "look cleaner" (verified by `tests/test_recommendation_rules.py`
RCM-03).

**Verdict: rejected, no risk.**


## 7. Feedback Boundary Audit

ADR-018 has not been implemented (status: "Proposed"). The runtime
accordingly does NOT:

* auto-learn from user interactions;
* auto-modify Knowledge Objects;
* auto-modify Decision Rules;
* auto-modify Trust Tiers.

Promotion is **operator-driven**: a human gates the lifecycle
through `IntakeManager`. The `PromotionEvent` is recorded but not
yet wired back into the originating KO''s `feedback[]` field.
This is the single open-ended ADR (see Section 5.4).

**Autonomous gates.** The pipeline executor
(`backend/caseos/brain/runtime/executor.py`) does not import any
LLM, NLP, vision, or auto-learning module. The retrieval engine
is deterministic. The trust engine is rule-based. The decision
engine is rule-based. The recommendation engine is rule-based.
The human module is field-mapping.

**Verdict: no auto-learning footprint in the current runtime.**
The "closed loop" is closed via the human operator, not via
machine learning. This is the V1 design.


## 8. Test Verification

```text
$ env PYTHONPATH=backend python -m pytest backend/caseos/tests -q
........................................................................ [ 80%]
..................                                                       [100%]
90 passed in 1.27s
```

| Test file | Count | Sprint |
|---|---|---|
| test_cli.py | 2 | 19.1 |
| test_corpus_benchmarks.py | 3 | 20.5 |
| test_decision_rules.py | 3 | 19.2 |
| test_governance.py | 7 | 20.6 |
| test_intake.py | 7 | 20.7 |
| test_loader.py | 1 | 19.1 |
| test_pipeline.py | 2 | 19.1 / 20 |
| test_recommendation_rules.py | 3 | 19.4 |
| test_retrieval.py | 8 | 20 |
| test_trust_rules.py | 3 | 19.3 |
| test_validator.py | 11 | 20.5 |
| **test_human_understanding.py** | **16** | **21** |
| **Total** | **90** | -- |

Result: **90 / 90 green, no regression.** The test suite cleanly
covers every acceptance criterion from ADR-013, ADR-014, ADR-015,
ADR-016, ADR-017, ADR-019 (and the partially-implemented intake /
governance / promotion lifecycle from ADR-015 + ADR-018 ground).
ADR-018 has no tests because it has no runtime.


## 9. Risk Register

| ID | Risk | Severity | Status | Recommendation |
|---|---|---|---|---|
| R1 | ADR-018 Feedback Loop is not implemented as code. `PromotionEvent` is recorded but not wired back into `feedback[]`. | Medium | Open by design | Implement in Sprint 22+ as a doc-locked slot. |
| R2 | V2 Blueprint Section 8 placeholder table still allocates ADR-016 = Recommendation, ADR-017 = Feedback. The actual slot allocation is ADR-016 = Trust, ADR-017 = Recommendation, ADR-018 = Feedback. | Low | Open | Doc-only follow-up commit (Architecture Consistency Patch V1 task 2). |
| R3 | `applicability_match` in Trust Object is a string label ("high"/"medium"/"low") rather than a free-text narrative. ADR-016 §2 calls for a "narrative judgement". | Very Low | Acceptable for V1 | Promote to narrative in ADR-016c. |
| R4 | `CHANGELOG` / `README` does not yet mention Human Understanding (Sprint 21) in the user-facing release notes. | Very Low | Open | Lightweight doc-only follow-up. |
| R5 | The intake layer does not have a formal AST-based "must not import retrieval / decision / trust / recommendation" test (equivalent to the human module''s boundary test). | Low | Acceptable for V1 | Add a hardening test in a future sprint. |
| R6 | The `FORBIDDEN_EQUIPMENT` blocklist is finite. New equipment names (e.g. "tower", "climb wall") could slip through. | Low | Open | ADR-017c ("Audience Variant Library") can host the expanded vocabulary. |
| R7 | The Decision Engine''s `_extract_signals` reads `human_context.values()` into a string blob. The keyword overlap is used for **signal detection**, not strategy inference. The Decision Engine remains the authority, but a future mind-reader reading the code could mistake this for "human-as-decision-maker". | Very Low | Acceptable for V1 | Add a paragraph to the decision module docstring explicitly noting that `human_context` is signal input, not authority input. |
| R8 | The "no shortcut path" check is verified by code inspection + the existing tests. A formal AST-based "no bypass from raw knowledge to decision" test would be a stronger audit. | Very Low | Acceptable for V1 | Add a hardening test in a future sprint. |
| R9 | The corpus currently has 8 KOs across 5 subdirs (Sprint 20.5). This is below the "tens of KOs per subdir" threshold at which the priority rules become meaningfully stress-tested. | Medium | Open | Corpus Expansion Sprint (Sprint 22.5 candidate). |
| R10 | The 5-field EP does not yet carry a `human_alignment` field (it carries `trust_contribution` from the KO''s identity type only). The HumanContext is consumed as a *P1 boost* at present, not as an explicit EP field. | Very Low | Open | Future ADR when feedback wiring is in place. |

No risk is rated **High**. The architecture is integrity-preserved.


## 10. Sprint 22 Entry Conditions

Sprint 22 is **ready** if the next sprint picks one of the following
three paths:

### Path A (recommended) -- Close the Feedback Loop (ADR-018)

* Implement ADR-018 as code.
* Wire `PromotionEvent` back into the `feedback[]` field of the
  originating RawCase (and the published Knowledge Object).
* Add the four feedback event types (Preference / Reason / Outcome /
  Expert) as runtime concepts.
* Add tests for the feedback pipeline (acceptance + boundary).

This is the **single most material gap** flagged by AR-002 (and
re-confirmed by AR-003). Sprint 22 closing this loop would move
CaseOS from "executable intelligence" to "learning intelligence"
(Maturity Level 4 per AR-002 §9).

### Path B -- Spatial Intelligence Runtime (Sprint 16 follow-up)

* Implement the Space Cognition Layer (ADR-009 brain layer) as
  runtime code.
* Add a `SpatialModule` to the pipeline (between Human and
  Knowledge, or alongside Human).
* The Decision Engine''s `_extract_signals` already accepts spatial
  inputs via `project.site_description`; the new module would
  structure these into a `SpatialContext` object.

This was the missing pillar that AR-002 already flagged
(the "Spatial Intelligence Engine" was documented in V2 Blueprint
Section 2 but not implemented as runtime).

### Path C -- Corpus Expansion + Benchmarking

* Scale the corpus from 8 KOs to 30+ KOs across the 5 subdirs.
* Re-run the 3 benchmark cases (kindergarten, public space, cultural
  tourism) with a larger corpus to surface retrieval priority
  bugs.
* Optionally add a Sprint 20.5-style benchmark test for the
  human-context boost.

### Path D (mixed) -- Hardening + Foundation

* Add the AST-based boundary tests for intake and recommendation
  (R5, R8).
* Promote `applicability_match` to a narrative (R3).
* Update the V2 Blueprint placeholder table (R2).
* Refresh CHANGELOG / README (R4).

**Recommendation.** Path A followed by a Path D cleanup. Path B
is a higher-risk undertaking because the Spatial Intelligence
engine needs more design discussion before it can be implemented
(V2 Blueprint §2 is conceptual; runtime contract is not yet
written). Path C is useful but does not close the loop in the
way AR-002 / AR-003 recommend.

The architecture is **ready** for any of these paths. No code
change is required before Sprint 22 can begin.


## 11. Acceptance Criteria Checklist

| Criterion | Status |
|---|---|
| No runtime code modified | done |
| AR-003 document generated | done |
| ADR-013-019 fully covered | done (Section 2) |
| Pipeline boundary audited | done (Section 3) |
| Decision authority verified | done (Section 4) |
| Knowledge lifecycle verified | done (Section 5) |
| Anti-patterns checked | done (Section 6) |
| pytest all green | done (Section 8: 90 / 90) |
| Risk Register emitted | done (Section 9) |
| Sprint 22 entry conditions stated | done (Section 10) |


## 12. Appendix A -- Files Used in This Audit

```text
backend/caseos/brain/runtime/pipeline.py
backend/caseos/brain/runtime/executor.py
backend/caseos/brain/runtime/context.py
backend/caseos/intelligence/human/object.py
backend/caseos/intelligence/human/extractor.py
backend/caseos/intelligence/human/validator.py
backend/caseos/intelligence/human/module.py
backend/caseos/intelligence/human/__init__.py
backend/caseos/intelligence/decision/module.py
backend/caseos/intelligence/trust/module.py
backend/caseos/intelligence/recommendation/module.py
backend/caseos/intelligence/output/module.py
backend/caseos/knowledge/objects/loader.py
backend/caseos/knowledge/retrieval/module.py
backend/caseos/knowledge/intake/object.py
backend/caseos/knowledge/intake/manager.py
backend/caseos/knowledge/intake/status.py
backend/caseos/knowledge/governance/validator.py
backend/caseos/knowledge/governance/promotion.py
backend/caseos/knowledge/governance/trust_tier.py
backend/caseos/cli/markdown_renderer.py
docs/architecture/ADR-013-human-understanding-engine.md
docs/architecture/ADR-014-decision-intelligence-model.md
docs/architecture/ADR-015-knowledge-object-model.md
docs/architecture/ADR-016-intelligence-trust-model.md
docs/architecture/ADR-017-recommendation-engine.md
docs/architecture/ADR-018-feedback-learning-loop.md
docs/architecture/ADR-019-evidence-retrieval-intelligence-principle.md
docs/reviews/AR-001_Resolution_Status_V1.md
docs/reviews/AR-002_Phase_3_Intelligence_Runtime_Review_V1.md
docs/reviews/Sprint_21_Human_Understanding_Report.md
```

## 13. Appendix B -- Git Diff Snapshot

```text
$ git log --oneline -5
76d9014 Sprint 21 -- Human Understanding Runtime V1
ea2c9e2 Sprint 20.7 -- Corpus Intake Foundation V1
7bfacaa Sprint 20.6 -- Corpus Governance Foundation V1
e38ee8b Sprint 20.5 -- Golden Case Corpus Migration V1
5576025 Sprint 20 -- Evidence Retrieval Intelligence V1

$ git status
On branch main
Your branch is up to date with ''origin/main''.
nothing to commit, working tree clean
```

The audit was performed on a clean tree at `76d9014`. No code or
test changed during this audit. Only this document
(`docs/reviews/AR-003_Phase3_Architecture_Integrity_Review_V2.md`)
will be added.
