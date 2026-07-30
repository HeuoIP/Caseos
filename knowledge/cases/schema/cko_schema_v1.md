# CKO Schema V1

- **Version:** 1.2
- **Status:** Accepted
- **Date:** 2026-07-30
- **Schema extensions:** 2026-07-30 V1.1 added `knowledge_source` to Section 0 and added Section 8 `learning_value`. 2026-07-30 V1.2 added Section 9 `case_evaluation` (5 weighted scores 0..25/0..25/0..20/0..15/0..15 summing to 100, plus `transferability` object). Both are non-breaking.
- **Source ADR:** `docs/architecture/ADR-011-cko-learning-source-value-model.md`
- **Mandatory:** every CKO file in `examples/` must match this schema (9 sections).

---

## Section 0. Case Identity

The unique handle for the case. No two CKOs share an ID.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `case_id` | string | yes | Pattern `^CKO-\d{4}$`. Allocate in order. |
| `title` | string | yes | One-line factual title (no marketing adjectives). |
| `source` | string | yes | Where the case was observed. |
| `image_reference` | string | yes | Relative path under `data/images/cases/`. |
| `project_type` | enum | yes | One of the values in `taxonomy/project_types.md`. |
| `knowledge_source` | enum | yes (V1.1) | At V1 only `external_excellent_case` is allowed. Future values require ADR. |

### Section 0a. Knowledge Source Taxonomy (V1.1)

| Value | Definition |
| --- | --- |
| `external_excellent_case` | The case originates from an external, recognised professional source. |
| `design_firm_award_shortlist` | (Future) Industry-award shortlist. |
| `academic_case_study` | (Future) Peer-reviewed academic study. |
| `internal_company_case` | (Future, V3+) Internal delivered case. Deliberately excluded at V1. |
| `partner_contributed` | (Future) Partner-firm anonymous donation. |
| `ai_synthetic_case` | (Future, V3+, with rationale) AI-synthesised case. |

A CKO with a non-V1 value is rejected by the future CKO Validator at index time.

---

## Section 1. Project Context

Why this project exists. The **why** of the CKO.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `client_goal` | string | yes | Stated goal of the client in plain language. |
| `project_background` | string | yes | One-paragraph project history. |
| `target_users` | array of strings | yes | Each entry is a user segment. |
| `site_condition` | string | yes | Brief factual summary of the site at project start. |
| `budget_level` | enum | no | One of `low` / `mid` / `high` / `unknown`. Null allowed. |

---

## Section 2. Space Cognition

What the space is. Factual, no judgment. Cites `knowledge/brain/space_cognition/README.md` vocabulary.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `spatial_role` | enum | yes | From `taxonomy/space_types.md`. |
| `spatial_position` | enum | yes | From `taxonomy/space_types.md`. |
| `spatial_scale` | enum | yes | From `taxonomy/space_types.md`. |
| `existing_elements` | array of strings | yes | Observable features before intervention. |
| `environmental_relationship` | string | yes | Relationship to surroundings. |

---

## Section 3. Experience Analysis

What the space feels like. Cites `knowledge/brain/experience_perception/README.md`.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `atmosphere` | string | yes | Dominant mood word plus one sentence. |
| `emotional_response` | array of strings | yes | Population-specific responses. |
| `child_behavior` | array of strings | yes | Designed-for behaviours per population. |
| `interaction_type` | enum | yes | One of `passive` / `light` / `active` / `social`. |
| `stay_value` | enum | yes | One of `low` / `mid` / `high`. |

---

## Section 4. Diagnosis

Why this case works or fails. Cites `knowledge/brain/diagnosis/README.md`.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `problem_type` | enum | yes | One of the values in `taxonomy/diagnosis_types.md`. |
| `diagnosis` | string | yes | The one-sentence verdict. |
| `evidence` | array of strings | yes | Three to five observable evidence points. |
| `key_observation` | string | yes | The single most important observation. |

---

## Section 5. Strategy

How the designer solved the problem. Cites `knowledge/brain/strategy/README.md`.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `strategy_type` | enum | yes | One of `landmark` / `journey` / `field` / `layered` / `anchor`. |
| `design_principles` | array of strings | yes | The 2-4 principles applied, citing DP / Brain module / Expert Handbook. |
| `spatial_organization` | string | yes | One paragraph describing the physical organisation. |
| `theme_logic` | string | no | If a theme is applied, the binding logic. Null if no explicit theme. |

---

## Section 6. Recommendation Logic

When CaseOS should cite this case to a new user.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `applicable_conditions` | array of strings | yes | Two to four conditions where this case is a strong reference. |
| `recommended_for` | array of strings | yes | User profiles this case is recommended for. |
| `not_recommended_for` | array of strings | yes | User profiles this case should NOT be cited for. |
| `risk_warning` | string | no | One-sentence warning. Null if none. |

---

## Section 7. Professional Evaluation

Four-axis professional scoring. Scores are integers in `0..10`. `confidence` is a float in `0..1`.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `design_quality_score` | int | yes | Spatial composition + detailing + coherence. |
| `experience_score` | int | yes | Multi-population experience depth. |
| `innovation_score` | int | yes | Originality within the project_type band. |
| `commercial_value_score` | int | yes | Brand / footfall / revenue / share-of-voice potential. |
| `confidence` | float | yes | Evaluator confidence in the four scores. |

The four scores are independent. A case may be high on `experience` but mid on `commercial_value`; that is a legitimate CKO value, not a defect.

---

## Section 8. Learning Value (V1.1)

Five-axis learning-value scoring. Each axis is an independent `0..1` float. **Distinct from Section 7.** Section 7 scores how good the project is; Section 8 scores how much the case can teach.

See `docs/architecture/ADR-011-cko-learning-source-value-model.md` for full rationale.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `learning_value.space_logic` | float | yes | Why the space works spatially. |
| `learning_value.experience_logic` | float | yes | Why users want to stay. |
| `learning_value.theme_logic` | float | yes | Why the space is memorable. |
| `learning_value.user_logic` | float | yes | Why different users accept it. |
| `learning_value.commercial_logic` | float | yes | Why the project creates value. |

### Quality Gate (V1.1)

A CKO whose average across the five axes is below `0.4` is flagged for manual review at V1 and dropped at V2. The threshold is a tuning parameter and may be revised by ADR.

### Low-value vs High-value Cases

Low-value cases (rejected): only attractive rendering, only colour inspiration, only equipment display.

High-value cases (welcomed): clear space logic, clear experience logic, reusable design principles that cite Constitution / DPs / Brain modules / Expert Handbook.

---

## Enumerations

All `enum` fields above resolve through the controlled vocabulary in `knowledge/cases/taxonomy/`. Each taxonomy file lists the allowed values, a one-sentence definition, and one example.

`knowledge_source` is an enum governed by Section 0a above; `learning_value` fields are floats, not enums.

A CKO with an unknown enum value is rejected at index time by the future CKO Validator. V1 validation is by a manual review (Librarian); V2 is automated.

## Section 9. Case Evaluation Score (V1.2)

Five weighted dimensions summing to 100 points; `transferability` is a separate attribute and is NOT part of `total_score`.

See `docs/architecture/ADR-012-case-evaluation-score.md` for full rationale, including the three-evaluation-layer architecture (Section 7 / Section 8 / Section 9).

| Field | Type | Required | Range | Description |
| --- | --- | --- | --- | --- |
| `case_evaluation.space_logic_score` | float | yes | 0..25 | Why the space works spatially. |
| `case_evaluation.experience_logic_score` | float | yes | 0..25 | Why users want to stay. |
| `case_evaluation.theme_meaning_logic_score` | float | yes | 0..20 | Why the space is memorable. |
| `case_evaluation.user_value_score` | float | yes | 0..15 | Why different users accept it. |
| `case_evaluation.commercial_logic_score` | float | yes | 0..15 | Why the project creates value. |
| `case_evaluation.total_score` | float | yes | 0..100 | Sum of the five weighted components; validator checks the sum. |
| `case_evaluation.transferability.level` | enum | yes | `high` / `medium` / `low` | Whether the case applies elsewhere. |
| `case_evaluation.transferability.applicable_project_types` | array of enum | yes | non-empty | Values from `taxonomy/project_types.md`. |
| `case_evaluation.transferability.limitations` | array of strings | yes | non-empty | What to watch when transferring. |

### Weights

The five weights are 25 / 25 / 20 / 15 / 15 and sum to 100. Weights are part of the schema "s public contract; changing any weight is breaking and requires ADR.

### Validation (CKO Validator at V2)

- `total_score` equals `space_logic_score + experience_logic_score + theme_meaning_logic_score + user_value_score + commercial_logic_score` (within 0.01 tolerance).
- Each score stays in its declared range.
- `transferability.applicable_project_types` is non-empty and each value is in `taxonomy/project_types.md`.
- `transferability.limitations` is non-empty.

### Operational Threshold (NOT a field)

The CKO Librarian applies these operational tiers on the `total_score`:

- `total_score >= 90` -- Priority Golden Case.
- `80 <= total_score < 90` -- Candidate Golden Case.
- `total_score < 80` -- Reference Case only.

Thresholds are operational tuning parameters and may be revised by ADR; they are NOT schema fields.

---

- Section 9 "s 100-point total and `transferability` are **distinct** from Section 7 (4 axes 0..10) and Section 8 (5 axes 0..1). See ADR-012 for the three-layer architecture.

## Compatibility Notes

- The shape of `spatial_role` / `spatial_position` is aligned with `knowledge/brain/space_cognition/README.md` but not identical. If the Brain ever changes its vocabulary, the CKO taxonomy may need a matching update; that change requires ADR.
- The strategy vocabulary in Section 5 is the canonical five families from `knowledge/brain/strategy/README.md`. New families require ADR-009 + matching update here.
- Section 8 "s five axes are **distinct** from Section 7 "s four. Section 7 = how good is this project; Section 8 = how much can this case teach us.

## Out of Scope

- Database row shape (see `database/CaseOS_Database_Schema_V1.md`).
- Vector embedding format.
- AI extraction pipeline.
- Case Retrieval Engine contract.

Those are separate deliverables, separate docs.
