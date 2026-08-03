# Sprint 22.3.2 — Feedback Interpretation Policy Foundation V1

## Status

COMPLETED

ADR-018 stage: Interpretation policy layer added between the
Human Review Queue and any future Knowledge Evolution step.

```
Feedback
  |
  v
Feedback Runtime (22.1)
  |
  v
Evaluation (22.2-A)
  |
  v
Contradiction Analyzer (22.2-B)
  |
  v
Learning Proposal (22.3)
  |
  v
Human Review Queue (22.3.1)
  |
  v
Interpretation Policy (22.3.2)  <-- this sprint
  |
  v
ChangeIntent
  |
  v
(Future Sprint 22.4) Knowledge Evolution
```

## Scope of This Sprint

In scope (additions only):

- `backend/caseos/knowledge/feedback/interpretation/`
  - `__init__.py`
  - `object.py`        — `ChangeIntent` (frozen, JSON-safe)
  - `policy.py`        — `InterpretationPolicy.interpret()`
  - `validator.py`     — `validate_change_intent()`
  - `report.py`        — `generate_report()` (Markdown)
- `backend/caseos/tests/test_feedback_interpretation.py`
- `docs/reviews/Sprint_22_3_2_Feedback_Interpretation_Report.md`

Out of scope (not modified):

- `caseos.intelligence.decision / trust / recommendation`
- `caseos.knowledge.retrieval / governance / intake`
- Pipeline wiring
- Knowledge Object
- Decision / Trust / Recommendation rules
- Corpus, governance, intake
- LLM / embedding / vector DB / database / external API

## Deliverables

### 1. `ChangeIntent` (object.py)

Frozen dataclass with 11 fields:

- `intent_id`
- `proposal_id`
- `target_identity`
- `change_type`
- `target_field`
- `current_value`
- `proposed_value`      (always `None` in V1)
- `reason`
- `risk_level`
- `requires_human_review` (always `True` in V1)
- `created_at`

Constraints:

- `frozen=True` — every mutation raises `FrozenInstanceError`.
- `to_dict()` — JSON-safe (datetime serialised to ISO string).
- Module does NOT import from any forbidden prefix.

### 2. `InterpretationPolicy` (policy.py)

Pure function `interpret(proposal, knowledge_object) -> ChangeIntent | None`.

V1 supported mapping:

| proposal_type                | change_type        | target_field | risk_level |
|------------------------------|--------------------|--------------|------------|
| `boundary_update_candidate`  | `boundary_update`  | `boundary`   | `high`     |
| `principle_update_candidate` | `principle_update` | `principle`  | `high`     |

Anything else (e.g. `applicability_update_candidate`,
`metadata_update_candidate`, `unknown`) returns `None`.

Safety rules (all must pass, else `None`):

1. `proposal.requires_human_review` must be `True`
2. `proposal.status` must be `"APPROVED"`
3. Knowledge Object is never mutated (deepcopy-equal before/after)
4. Required fields (`target_identity`, `proposal_type`,
   `reason`) must be present and non-empty

`proposed_value` is always `None` in V1 — the policy never
invents the future Knowledge Object value. Sprint 22.4 (future)
will fill this in once a human approves the intent.

### 3. `validate_change_intent` (validator.py)

Returns `(is_valid: bool, message: str)`. Checks:

- Required string fields are non-empty
  (`intent_id`, `proposal_id`, `target_identity`,
  `change_type`, `target_field`, `reason`, `risk_level`)
- `change_type` in V1 allow-list
- `risk_level` in {`low`, `medium`, `high`}
- `requires_human_review is True`

Never raises on invalid input — defence-in-depth over the
policy's own filtering.

### 4. `generate_report` (report.py)

Markdown renderer with the seven required sections:

1. Target
2. Change Type
3. Target Field
4. Current Value
5. Proposed Value
6. Risk
7. Human Review Required

Pure function over a `ChangeIntent`; no I/O, no mutation.

### 5. `test_feedback_interpretation.py`

8 required tests (per spec) + auxiliary:

| # | Test                                                       | Status |
|---|------------------------------------------------------------|--------|
| 1 | Approved boundary proposal -> ChangeIntent                 | PASS   |
| 2 | Approved principle proposal -> principle_update            | PASS   |
| 3 | Pending (CREATED / PENDING_REVIEW / REJECTED) -> None      | PASS   |
| 4 | `requires_human_review=False` proposal -> None             | PASS   |
| 5 | Unknown / unsupported proposal_type -> None               | PASS   |
| 6 | Knowledge Object unchanged (deepcopy before/after)         | PASS   |
| 7 | `ChangeIntent` is frozen (mutation raises)                 | PASS   |
| 8 | AST boundary scan over 5 interpretation modules            | PASS   |

Plus auxiliary: validator unit tests, report rendering, JSON
roundtrip, `proposal.to_dict()` immutability, parametrized
non-approved statuses, parametrized unsupported proposal types.

## Architecture Boundary Verification

The interpretation package does NOT import from any of:

- `caseos.intelligence.decision`
- `caseos.intelligence.trust`
- `caseos.intelligence.recommendation`
- `caseos.knowledge.retrieval`
- `caseos.knowledge.governance`
- `caseos.knowledge.intake`

The boundary is enforced by `TestArchitectureBoundary`, which
parses all 5 interpretation modules with `ast` and asserts no
import matches a forbidden prefix. The test is parametrised.

Allowed imports:

- `caseos.knowledge.feedback` (parent package — proposal only)
- `caseos.knowledge.objects` (not actually used in V1, but
  explicitly allow-listed in the spec)
- stdlib (`dataclasses`, `typing`, `datetime`, `uuid`, `ast`,
  `json`, `copy`, `pathlib`)

## Pipeline Integrity

The interpretation package is a **side-channel**. It is not
inserted into:

```
Human -> Knowledge -> Retrieval -> Decision -> Trust
        -> Recommendation -> Output
```

Pipeline wiring is unchanged. The interpretation step is only
invoked by an operator (or a future Knowledge Evolution
sprint) after a proposal has been **human-approved** in the
Review Queue.

## Knowledge Object Safety

In V1, `InterpretationPolicy.interpret` performs only **reads**
on the Knowledge Object. The function:

- Reads `boundary` / `principle` by value (shallow-copies any
  list / dict before stringifying).
- Never writes back to the KO.
- Never touches the corpus, the loader, or the store.

Test 6 (parametrized over 4 sub-cases) confirms:

- `knowledge_object == deepcopy(knowledge_object)` before vs
  after `interpret(...)`.
- Same for the `LearningProposal` itself.

## Decision / Trust / Recommendation

Untouched. The interpretation package is downstream of the
human review gate and upstream of any future KO write-back;
the only consumer in V1 is the human reviewer and the report
generator.

## Why a Separate Layer?

Without a separate interpretation step, an `APPROVED` proposal
would either:

1. Be applied directly to the Knowledge Object (violates
   ADR-018 Section 1 — Human-in-the-loop), or
2. Be stored in the proposal store only and have no
   operator-facing audit artifact (violates ADR-018 Section 3
   — Interpretability).

`ChangeIntent` is the operator-facing artifact: a single
explicit, frozen, JSON-safe record of:

- which KO would change
- which field would change
- what the field is today
- who or what suggested the change (proposal id)
- why
- the risk level
- the human-review requirement

A future Sprint 22.4 (Knowledge Evolution) can consume
`ChangeIntent` after another human approval step, write the
new value to the Knowledge Object, and append a knowledge
evolution event to the audit log. The V1 layer only provides
the **safe bridge** — it does NOT write back.

## Next Steps (out of scope, future sprints)

Candidates:

- **Sprint 22.4 — Knowledge Evolution**: consume approved
  `ChangeIntent` and apply the change to the Knowledge Object
  (still under human review, with append-only audit trail).
- **ADR-018 doc patch**: add a paragraph describing the
  interpretation layer in the architecture document.
- **Test back-compat shim**: a few test files (e.g.
  `test_feedback_runtime.py`) predate some new attributes and
  may need a one-line fixture update.
- **ADR-019 — Memory Architecture**: define the long-term
  memory layer above the Feedback Learning Loop.

## Completion Report

```
Sprint 22.3.2 completed
Commit: <hash>
Files:
  - backend/caseos/knowledge/feedback/interpretation/__init__.py
  - backend/caseos/knowledge/feedback/interpretation/object.py
  - backend/caseos/knowledge/feedback/interpretation/policy.py
  - backend/caseos/knowledge/feedback/interpretation/validator.py
  - backend/caseos/knowledge/feedback/interpretation/report.py
  - backend/caseos/tests/test_feedback_interpretation.py
  - docs/reviews/Sprint_22_3_2_Feedback_Interpretation_Report.md
Tests:  <passed>/<total> passed
Pipeline modified:    NO
Intelligence modified: NO
Knowledge modified:    NO
Architecture boundary: PASS
```
