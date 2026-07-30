# CKO Schema V1

- **Version:** 1
- **Status:** Accepted
- **Date:** 2026-07-30
- **Mandatory:** every CKO file in `examples/` must match
  this schema "s 8 sections.

---

## Section 0. Case Identity

The unique handle for the case. No two CKOs share an ID.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `case_id` | string | yes | Pattern `^CKO-\d{4}$`. Allocate in order. |
| `title` | string | yes | One-line factual title (no marketing adjectives). |
| `source` | string | yes | Where the case was observed (publication, project archive, field visit, etc.). |
| `image_reference` | string | yes | Relative path under `data/images/cases/`. Image must exist at index time. |
| `project_type` | enum | yes | One of the values in `taxonomy/project_types.md`. |

---

## Section 1. Project Context

Why this project exists. The **why** of the CKO.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `client_goal` | string | yes | Stated goal of the client in plain language. |
| `project_background` | string | yes | One-paragraph project history. |
| `target_users` | array of strings | yes | Each entry is a user segment (e.g., "child_3_6", "parent", "tourist"). |
| `site_condition` | string | yes | Brief factual summary of the site at project start. |
| `budget_level` | enum | no | One of `low` / `mid` / `high` / `unknown`. Null allowed. |

---

## Section 2. Space Cognition

What the space is. Factual, no judgment. Cites
`knowledge/brain/space_cognition/README.md` vocabulary.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `spatial_role` | enum | yes | From `taxonomy/space_types.md`. |
| `spatial_position` | enum | yes | From `taxonomy/space_types.md`. |
| `spatial_scale` | enum | yes | From `taxonomy/space_types.md`. |
| `existing_elements` | array of strings | yes | Observable features before intervention. |
| `environmental_relationship` | string | yes | Relationship to surroundings (city / nature / hybrid). |

---

## Section 3. Experience Analysis

What the space feels like. Cites
`knowledge/brain/experience_perception/README.md`.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `atmosphere` | string | yes | One dominant mood word plus one sentence context. |
| `emotional_response` | array of strings | yes | Population-specific responses (e.g., "wonder", "shelter"). |
| `child_behavior` | array of strings | yes | Observed or designed-for behaviours per population. |
| `interaction_type` | enum | yes | One of `passive` / `light` / `active` / `social`. |
| `stay_value` | enum | yes | One of `low` / `mid` / `high`. |

---

## Section 4. Diagnosis

Why this case works or fails. Cites
`knowledge/brain/diagnosis/README.md`.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `problem_type` | enum | yes | One of the values in `taxonomy/diagnosis_types.md`. |
| `diagnosis` | string | yes | The one-sentence verdict. |
| `evidence` | array of strings | yes | Three to five observable evidence points. |
| `key_observation` | string | yes | The single most important observation. |

---

## Section 5. Strategy

How the designer solved the problem. Cites
`knowledge/brain/strategy/README.md`.

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
| `applicable_conditions` | array of strings | yes | Two to four conditions under which this case is a strong reference. |
| `recommended_for` | array of strings | yes | User profiles this case is recommended for. |
| `not_recommended_for` | array of strings | yes | User profiles this case should NOT be cited for. |
| `risk_warning` | string | no | One-sentence warning when applicable. Null if none. |

---

## Section 7. Professional Evaluation

Four-axis professional scoring. All scores are integers in
`0..10`. `confidence` is a float in `0..1`.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `design_quality_score` | int | yes | Spatial composition + detailing + coherence. |
| `experience_score` | int | yes | Multi-population experience depth. |
| `innovation_score` | int | yes | Originality within the project_type band. |
| `commercial_value_score` | int | yes | Brand / footfall / revenue / share-of-voice potential. |
| `confidence` | float | yes | Evaluator "s confidence in the four scores. |

The four scores are independent. A case may be high on
`experience` but mid on `commercial_value`, and that is a
**legitimate CKO value**, not a defect.

---

## Enumerations

All `enum` fields above resolve through the controlled
vocabulary in `knowledge/cases/taxonomy/`. Each taxonomy
file lists the allowed values, a one-sentence definition,
and one example.

A CKO with an unknown enum value is rejected at index time
by the future CKO Validator. V1 validation is by a manual
review (Librarian); V2 is automated.

## Compatibility Notes

- The shape of `spatial_role` / `spatial_position` is
  aligned with `knowledge/brain/space_cognition/README.md`
  but not identical. If the Brain ever changes its
  vocabulary, the CKO taxonomy may need a matching
  update; that change requires ADR.
- The strategy vocabulary in Section 5 is the **canonical
  five families** from `knowledge/brain/strategy/README.md`.
  New families added to the Brain will require ADR-009 +
  matching update here.

## Out of Scope

- Database row shape (see `database/CaseOS_Database_Schema_V1.md`).
- Vector embedding format.
- AI extraction pipeline.
- Case Retrieval Engine contract.

Those are separate deliverables, separate docs.
