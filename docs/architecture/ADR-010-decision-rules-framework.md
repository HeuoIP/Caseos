# ADR-010: CaseOS Decision Rules Framework V1

- **Status:** Proposed
- **Date:** 2026-07-30
- **Sprint:** 18
- **Layer:** Brain (rules layer, between modules and Decision Engine)

---

## Context

CaseOS Brain V1 established the knowledge architecture
(ADR-009). The Brain modules now describe **what** a
decision is: a Cognition record, an Experience Profile, a
Diagnosis report, a Strategy, a Theme, a Recommendation.

The next step is to convert **professional spatial
judgment** into **executable decision rules** -- the
"how" of judgement.

Decision rules are not AI code.

Decision rules are professional reasoning patterns. They
follow a single shape:

```
IF <observation conditions>
THEN <judgment>
BECAUSE <reasoning>
DO <recommended action>
UNLESS <exceptions>
```

Future Decision Engine implementations will **consume**
these rules. The rules themselves are pure knowledge
assets: no code, no agent, no implementation.

---

## Decision

Create a new Brain sub-folder:

```
knowledge/brain/decision_rules/
    client_rules/
    project_fit_rules/
    cognition_rules/
    experience_rules/
    diagnosis_rules/
    strategy_rules/
    theme_rules/
    recommendation_rules/
```

Each sub-folder holds rules of one family. The family
matches the pipeline stage its rules serve. Rules under
`diagnosis_rules/` apply during the Diagnosis stage;
rules under `recommendation_rules/` apply during
Recommendation; and so on.

A rule is **never** allowed to live outside its family --
"diagnosis rules" do not appear under `recommendation_rules/`,
even if they share a vocabulary.

### Nine-section rule template

Every rule has exactly nine sections, in this order:

1. **Rule ID** -- unique within the family (e.g., `CR-001`).
2. **Rule Name** -- short, imperative, professional.
3. **Applicable Scenario** -- the situation when this rule
   may fire.
4. **Observation Conditions** -- the IF; what the Brain
   must observe (typically combinations of cognition,
   experience, project fit, or client understanding
   fields).
5. **Judgment** -- the THEN; the professional verdict
   produced.
6. **Reasoning** -- the BECAUSE; the underlying design
   principle.
7. **Recommended Action** -- the DO; what the next stage
   should do.
8. **Exceptions** -- the UNLESS; conditions under which the
   rule does not fire, even if observations match.
9. **Example Cases** -- one or two concrete situations.

If a section is unknown (e.g., exceptions), it is left as
"pending" in V1 rather than filled with invented content.
This is a Constitution V1 / FB-03 constraint.

---

## Layer Position

```
0 Constitution
  ↓
1 Brain modules (9 modules per ADR-009)
  ↓
2 Decision rules        <-- this ADR
  ↓
3 Decision Engine (runtime)
```

Rules consume module outputs. The Decision Engine consumes
rules. Modules do not consume rules. This ordering is a
binding manifestation of Constitution V1 Principle 003
(*understand before recommending*).

---

## Initial Rules (V1)

This ADR introduces eight initial rules across four
families. Each rule is published as its own file
`<RULE_ID>.md`.

| ID | Family | Name |
| --- | --- | --- |
| CR-001 | client_rules | Do not design before project definition |
| CR-002 | client_rules | Beginner client does not equal bad client |
| CR-003 | client_rules | Clarify before creating |
| PF-001 | project_fit_rules | Design cannot replace operation capability |
| DR-001 | diagnosis_rules | Lack of spatial anchor |
| DR-002 | diagnosis_rules | Existing anchor but lack of coherence |
| DR-003 | diagnosis_rules | Visual attraction does not equal play value |
| RR-001 | recommendation_rules | Limited budget should concentrate value |

Future rules will be added to the appropriate family under
their own ADR. A rule that drifts (changes conditions,
judgment, action, or name) is a new rule with a new ID,
not an edit -- history is preserved through git.

---

## Rule Authoring Discipline

- **One rule, one file.** The file name is the rule ID
  (`CR-001.md`). The H1 is the rule name.
- **No implementation detail.** Rules never mention
  Python, agents, pipelines, models, embeddings, LLM
  calls, validators, or runtime stack. The Decision
  Engine reads the rules as input, but the rules
  themselves do not depend on a specific stack.
- **No marketing language.** Wording is professional,
  observable, falsifiable.
- **Provenance.** Every rule citation must trace to a
  Constitution principle, a Decision Principle, a Design
  Principle (DP-xxx), or a Brain module section.
- **Idempotence.** Two rule designers writing the same
  trigger and the same action must produce the same
  rule. The template enforces this.
- **Conflict discipline.** If two rules fire, the higher-
  numbered (more specific) rule wins, OR the rule authored
  more recently wins -- this ADR does not resolve the
  ordering yet; that is part of an ADR-011 (Rule Engine)
  to follow.

---

## Out of Scope

This ADR does NOT include:

- Rule Engine implementation (planned ADR-011).
- Auto-loading mechanism.
- Rule priority or weight model.
- Conflict resolution algorithm.

---

## Non Goals

This ADR does NOT add any new AI capability. Rules are
knowledge; the Engine is separate.

---

## Maintenance

- Adding a new rule to an existing family is a non-
  breaking change (allowed without ADR). **However**, the
  rule must still pass the Authoring Discipline above.
- Adding a new family is a breaking change to the Brain "s
  public contract and requires ADR.
- Renaming a rule (changing its Name) is a breaking change
  (history matters) and requires ADR -- publish as new
  rule, deprecate the old.
- Removing a rule is a non-breaking change **only** if the
  rule was never referenced. Otherwise require ADR.
- Updating the nine-section template itself is a breaking
  change and requires ADR.
