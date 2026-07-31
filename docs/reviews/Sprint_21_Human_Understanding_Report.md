# Sprint 21 -- Human Understanding Runtime V1

**Status**: complete
**Date**: 2026-07-31
**Sprint**: 21
**Source ADRs**: ADR-013 (Human Understanding Engine), ADR-014 (Decision Intelligence
Model), ADR-015 (Knowledge Object Model), ADR-016 (Intelligence Trust Model),
ADR-017 (Recommendation Engine), ADR-018 (Feedback Learning Loop), ADR-019
(Evidence Retrieval Intelligence Principle)
**Parent Sprint**: Sprint 20.7 (Corpus Intake Foundation V1)


## 1. Objective

Implement the first executable Human Understanding layer. Convert
structured project/user input into a `HumanContext` object that
influences the rest of the pipeline without ever deciding on the
user''s behalf.

The architecture boundary is preserved:

    Human Understanding (this sprint)
        |
        v
    Knowledge (Sprint 19.1+)
        |
        v
    Retrieval (Sprint 20 / ADR-019, extended this sprint)
        |
        v
    Decision (Sprint 19.2 / ADR-014, unchanged)
        |
        v
    Trust (Sprint 19.3 / ADR-016, unchanged)
        |
        v
    Recommendation (Sprint 19.4 / ADR-017, unchanged)
        |
        v
    Output (Sprint 19.4, extended this sprint)


## 2. What Was Built

### 2.1 New Module: `caseos.intelligence.human`

The Sprint 19.1 placeholder (which only set a stub object) is
replaced with executable layers:

| File | Responsibility |
|---|---|
| `object.py` | `HumanContext` dataclass + `UNKNOWN` sentinel |
| `extractor.py` | Project -> HumanContext, never invents |
| `validator.py` | `HumanValidationResult`: required + optional gaps |
| `module.py` | `HumanModule` (Stage subclass, name `human_understanding`) |
| `report.py` | Markdown renderer for the Human Understanding section |
| `__init__.py` | Public exports |

### 2.2 HumanContext Schema

`HumanContext` carries the eight ADR-013 fields:

| Field | Required | Sensor / source |
|---|---|---|
| `user_goal` | yes | `project.user_goal` |
| `business_context` | yes | `extras.business_context` / `extras.business` |
| `emotional_preference` | no | `extras.emotional_preference` / `extras.preference` |
| `budget_context` | no | `extras.budget_context` / `extras.budget` |
| `constraints` | no | `project.constraints` (str or list) |
| `success_definition` | yes | `extras.success_definition` / `extras.success` |
| `risk_tolerance` | no | `extras.risk_tolerance` / `extras.risk` |
| `decision_priority` | no | `extras.decision_priority` / `extras.priority` |

Important: `site_description` is **NOT** mapped to `business_context`.
Site description is spatial knowledge (Sprint 16 / Space Cognition);
`business_context` is human knowledge. Mixing them would violate
ADR-013''s "preserve original meaning" principle.

### 2.3 UNKNOWN Sentinel

Missing fields are stored as the literal string `"__UNKNOWN__"`
(rather than `None` or `""`). The sentinel is preserved through
serialisation so downstream rules can detect it without crashes:

```python
from caseos.intelligence.human import UNKNOWN, HumanContext
ctx = HumanContext()
assert ctx.user_goal == UNKNOWN
assert ctx.is_unknown("user_goal") is True
```

### 2.4 Pipeline Integration

The `HumanModule` is the first stage of the default pipeline.
It writes `ctx.human_context` and a small validation summary
under `ctx.metadata["human_validation"]`. The `metadata` block
also records `human_mapped_fields`, `human_skipped_fields`, and
`human_schema_version` for debugging and audit.

### 2.5 Retrieval Integration (Sprint 21 spec section 6)

The `RetrievalEngine.retrieve()` signature gains an optional
`human_context` parameter (default `None`, fully backward-compatible).
When provided, the engine computes a **bounded** keyword-overlap
score sourced from `user_goal`, `business_context`, and
`success_definition`. The boost is added to the **P1 contribution**
(internal score), so the rule list stays P1 -> P2 -> P3 -> P4 and
the priority order is unchanged.

Limits:

* `SCORE_HUMAN_BOOST_MAX = 15` (3+ overlaps -> +15; 2 -> +10; 1 -> +5).
* The boost is reported as part of the P1 contribution in
  `evidence_package.applicability_reason`. There is no new
  P-number; the rule list printed by `RULE_APPLICABILITY` is
  still `["P1", "P2", "P3", "P4"]`.

### 2.6 Markdown Output

The `markdown_renderer` now produces a section labelled
`# Human Understanding` immediately after the existing Project
Understanding block. The section lists every field, the unknowns,
and the validation verdict (VALID / INVALID with warnings + errors).


## 3. What Was NOT Built (per spec)

* No LLM calls.
* No NLP / chatbot / classification.
* No vision / image model.
* No user account / profile / persona database.
* No embedding / vector search.
* No new intelligence capability -- the Human Understanding
  layer is *input shaping*, not reasoning.

The Human Understanding layer reads structured input and shapes
it for the pipeline. It does not understand. It describes what
was given.


## 4. Architecture Boundary

The Human Understanding module does NOT import from:

* `caseos.knowledge.retrieval`
* `caseos.intelligence.decision`
* `caseos.intelligence.trust`
* `caseos.intelligence.recommendation`
* `caseos.knowledge.governance`
* `caseos.knowledge.intake`

This is enforced by `test_human_module_does_not_import_retrieval_or_decision_or_others`
which walks the AST of every human module file and rejects any
import that crosses the boundary.

The reverse direction is decided by the existing pipeline:
Stage 1 (Human) writes `ctx.human_context`; Stages 2+ consume it.
The Human module never reaches back into Stage 2+.


## 5. Pipeline Behaviour (Worked Example)

Input (`backend/caseos/examples/kindergarten.json`):

```json
{
  "project_id": "kg-outdoor-001",
  "project_type": "kindergarten_outdoor",
  "site_description": "500 sqm outdoor area ... lacks a memorable theme",
  "user_goal": "improve enrollment attraction",
  "constraints": "limited budget"
}
```

Pipeline execution:

1. **Human**: extracts `HumanContext`. Only `user_goal` and
   `constraints` are present in the project dict; everything else
   is `UNKNOWN`. Validation result: `INVALID` (1 error: missing
   `success_definition`; 5 warnings: missing optional fields).
2. **Knowledge**: loads the 5-subdir corpus (8 KOs).
3. **Retrieval**: `KnowledgeRetriever` consumes `ctx.human_context`
   (no human-keyword overlap because `__UNKNOWN__` values are
   filtered out). Retrieves 7 KOs based on P1 applicability.
4. **Decision**: R-01 fires ("Space lacks identity; equipment
   already exists"). Diagnosis = "not insufficient equipment but
   lack of spatial narrative"; decision = "Create a single
   thematically anchored experience".
5. **Trust**: Confidence = Medium (Tier_B Golden Case + Tier_C
   Decision Patterns).
6. **Recommendation**: All 7 ADR-017 sections composed.
7. **Output**: Markdown report with Human Understanding section
   + 7 ADR-017 sections + Evidence Package + Confidence + Caveats.

Markdown excerpt (Human Understanding section):

```
# Human Understanding

- User Goal: improve enrollment attraction
- Business Context: n/a
- Emotional Preference: n/a
- Budget Context: n/a
- Constraints:
  - limited budget
- Success Definition: n/a
- Risk Tolerance: n/a
- Decision Priority: n/a
- Unknowns: business_context, emotional_preference, budget_context, success_definition, risk_tolerance, decision_priority
- Validation: INVALID (warnings=5, errors=1)
  - WARN: optional field missing: budget_context
  - WARN: optional field missing: business_context
  - WARN: optional field missing: emotional_preference
  - WARN: optional field missing: risk_tolerance
  - WARN: optional field missing: decision_priority
  - ERROR: required field missing: success_definition
```


## 6. What Was Validated

* 8 acceptance tests (one per spec bullet) pass.
* 8 auxiliary tests pass (schema_version, sentinel, boundary,
  report, etc.).
* Existing 74 baseline tests remain green.
* Total: **90 / 90 tests pass**.


## 7. Decision Authority

The Decision Engine remains the authority. Sprint 21 changes
NEVER:

* Rewrite the Decision Object.
* Determine which rule fires.
* Override the Decision Engine''s refusal path
  ("More information required").

The Human Understanding layer only **shapes inputs**:
the Decision Engine still chooses the rule, the Trust Engine
still chooses the confidence, and the Recommendation Engine
still chooses the wording.


## 8. Future Work (Out of Scope for Sprint 21)

The Human Understanding Engine is V1. Future extensions:

* **User behaviour learning** (ADR-018): the spec already
  mentions "browsing behaviour, case preferences, feedback"
  as future Human Understanding inputs. Sprint 21 keeps this
  surface empty and the schema forward-compatible.
* **Feedback integration** (ADR-018): once the feedback loop
  is wired, HumanContext may evolve into a `HumanState`
  that includes prior preferences.
* **Operator-handled completion**: when a field is UNKNOWN,
  the next sprint may add a human-in-the-loop prompt for
  the operator to fill in the missing field. The schema
  already supports `validation.missing_required` for that.

None of these are implemented in Sprint 21. The boundary is
preserved: no LLM, no DB, no UI, no behaviour tracking.


## 9. Files Changed / Created

```
backend/caseos/intelligence/human/object.py        (new)
backend/caseos/intelligence/human/extractor.py     (new)
backend/caseos/intelligence/human/validator.py     (new)
backend/caseos/intelligence/human/module.py        (replaced placeholder)
backend/caseos/intelligence/human/report.py        (new)
backend/caseos/intelligence/human/__init__.py      (new)
backend/caseos/intelligence/output/module.py       (forward human_context)
backend/caseos/cli/markdown_renderer.py            (add Human Understanding section)
backend/caseos/knowledge/retrieval/module.py       (human_context boost)
backend/caseos/tests/test_human_understanding.py   (new; 16 tests)
docs/reviews/Sprint_21_Human_Understanding_Report.md (new)
```


## 10. Acceptance Criteria Checklist

| Criterion | Status |
|---|---|
| 1. HumanContext exists | done |
| 2. Human stage executable | done |
| 3. Unknown information preserved | done |
| 4. Retrieval can use human signals | done |
| 5. Decision authority unchanged | done |
| 6. No LLM / NLP introduced | done |
| 7. All tests pass | done (90/90) |
