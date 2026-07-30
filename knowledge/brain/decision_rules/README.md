# Decision Rules (Brain Rules Layer)

- **Layer:** Brain (between modules and Decision Engine)
- **Pipeline Position:** "Stage --1" (consumed by every Brain
  module "s runtime check)
- **Status:** Accepted (Decision Rules Framework V1, 2026-07-30)
- **Source of truth:** `docs/architecture/ADR-010-decision-rules-framework.md`

## Purpose

Convert **professional spatial judgment** into **executable
decision rules** -- the "how" of judgment, complementing
the Brain modules " "what".

A Brain module (per ADR-009) describes a record: a
cognition, an experience, a diagnosis, a strategy,
etc. A Decision Rule describes a **reasoning pattern**:
if you observe X, the judgment is Y, the action is Z,
unless W.

Rules live in `knowledge/brain/decision_rules/`. They are
pure knowledge assets: no code, no agent, no
implementation. The future Decision Engine (ADR-011+)
will consume them.

## Layer Position

```
0 Constitution (philosophy)
  ↓
1 Brain modules (9 modules, ADR-009)
  ↓
2 Decision rules       <-- this folder
  ↓
3 Decision Engine      (runtime, future ADR)
  ↓
4 Product Layer / Agents
```

Rules sit **between** the Brain modules " output and the
Decision Engine "s logic. They are the **executable form
of design judgment**.

## Families

A rule "s family matches the pipeline stage its rule
serves. Rules are filed under the stage whose decisions
they influence.

| Folder | Family | Stage |
| --- | --- | --- |
| client_rules/ | CR | Client Understanding (Stage 1) |
| project_fit_rules/ | PF | Project Fit (Stage 2) |
| cognition_rules/ | CX | Space Cognition (Stage 3) |
| experience_rules/ | EX | Experience Perception (Stage 4) |
| diagnosis_rules/ | DR | Diagnosis (Stage 5) |
| strategy_rules/ | ST | Strategy (Stage 6) |
| theme_rules/ | TR | Theme Strategy (Stage 7) |
| recommendation_rules/ | RR | Recommendation (Stage 8) |

A rule filed under the wrong family is a defect; family
equals stage.

## Rule ID Convention

`<FAMILY>-<NUMBER>`

Examples:

- `CR-001` -- the first Client rule
- `PF-001` -- the first Project Fit rule
- `DR-001` -- the first Diagnosis rule
- `RR-001` -- the first Recommendation rule

NUMBER is monotonically increasing within a family. A
rule is never deleted; it is deprecated and superseded.

## Nine-section Template

Every rule file uses the same nine sections, in this
order. The numbering is binding.

```
1. Rule ID
2. Rule Name
3. Applicable Scenario
4. Observation Conditions
5. Judgment
6. Reasoning
7. Recommended Action
8. Exceptions
9. Example Cases
```

If a section is genuinely unknown in V1, it is left as
`Pending V2`. Inventing content violates Constitution V1
Forbidden Behavior 03 (`Never invent a fact to look
confident`).

## Rule shape

A rule is consumed as:

```
IF <observation conditions>
THEN <judgment>
BECAUSE <reasoning>
DO <recommended action>
UNLESS <exceptions>
```

This single shape keeps the rules human-readable, rule
designer-shared, and Decision Engine-friendly.

## Cross-references

- `docs/architecture/ADR-010-decision-rules-framework.md`
  -- the source of truth for this framework.
- `knowledge/brain/constitution/README.md` -- every rule
  must be consonant with the four Principles; violating a
  Principle makes the rule invalid.
- `knowledge/brain/decision_model/` (in `knowledge/`)
  -- runtime reasoning models that will consume these
  rules. Decision Model V1 is independent of the Rule
  Framework in V1; rules plug in from V2 onward.
- `knowledge/decision_model/Strategy_Model.md` --
  current nearest consumer of judgment patterns; will be
  re-pointed to rules in a future sprint.

## Maintenance

- New rule in existing family = non-breaking change
  (allowed without ADR), pass Authoring Discipline.
- New family = breaking change = requires ADR.
- Rename of an existing rule = breaking change = requires
  ADR. Publish new, deprecate old.
- Remove of an unreferenced rule = allowed without ADR.
- Remove of a referenced rule = requires ADR.
- Template change = breaking change = requires ADR.
