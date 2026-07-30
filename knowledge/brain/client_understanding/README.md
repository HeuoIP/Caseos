# Client Understanding

- **Module:** Client Understanding
- **Layer:** Brain
- **Pipeline Position:** 1 (after Constitution, before Project Fit)
- **Status:** Accepted
- **Date:** 2026-07-30

## Purpose

Understand **why the project exists** before designing **what
the project will be**. A project that solves the wrong problem
is more dangerous than a project that solves the right problem
poorly -- because the wrong-problem project consumes resources
silently, with no signal of failure until the user notices.

Client Understanding produces a structured profile of the
client (decision maker, stakeholder, organisation) that every
downstream module reads.

## Core Principles

1. **Listen before assuming.** The user "s stated motivation is
   the primary input; inferred motivation is secondary.
2. **The client is a stakeholder, not just a buyer.** A client
   who is also a future user, an investor, a parent, or a
   principal has multiple decision criteria; a single "buyer"
   lens misses them.
3. **Resource transparency is mandatory.** A project that
   under-reports budget or timeline fails later and costs
   more than a project that over-reports at the start.
4. **Decision style matters as much as decision content.** A
   client who decides quickly and a client who decides slowly
   are both valid; the Brain must serve both.
5. **Inferred profile is `inferred`, not `stated`.** A profile
   built from photo alone carries lower confidence than a
   profile built from a stated user goal.

## Decision Rules

1. **Infer client type** from project context. The starter
   taxonomy is:

   - **EDUCATION** -- kindergarten, school, after-school program.
     Profile: EDUCATOR. Decision priorities: child safety,
     developmental value, parental approval.
   - **COMMERCIAL** -- mall, hotel, retail. Profile: COMMERCIAL
     OPERATOR. Decision priorities: foot traffic, dwell time,
     differentiation.
   - **PUBLIC_PARK** -- municipal, community. Profile: PUBLIC
     ADMIN. Decision priorities: durability, accessibility,
     public value.
   - **COMMUNITY** -- neighbourhood, association, non-profit.
     Profile: COMMUNITY OPERATOR. Decision priorities:
     inclusivity, low maintenance, community identity.
   - **FAMILY** -- private residence, family compound. Profile:
     RESIDENTIAL OPERATOR. Decision priorities: child
     engagement, aesthetic fit, family use.

2. **Infer decision priorities** from project context. Up to
   3 priorities from a starter set: cost, quality, speed,
   brand, safety, accessibility, sustainability, novelty.

3. **Record capability match.** Three axes:

   - **Experience** -- has the client done this kind of project
     before?
   - **Budget capability** -- is the stated budget realistic for
     the project "s ambition?
   - **Operational capability** -- can the client maintain the
     outcome post-handover?

4. **When uncertain, ASK.** A profile that cannot be inferred
   is recorded as `unknown`, not guessed. The Brain surfaces
   the unknown to the user; the user supplies the missing
   input.

5. **Independence from goal and space.** Client Understanding
   profiles the client "s perspective, not the project "s
   ambition. The project "s ambition is captured separately
   (in `project_fit/` and downstream).

## Inputs

- The Vision Engine "s V3 JSON (per ADR-008) -- the photo
  carries implicit signals about the project "s context.
- Optional user-stated profile (if the user supplied
  text or a questionnaire).
- Optional market context (the client "s neighbourhood,
  industry, or stated market).

## Outputs

A `ClientProfile` record:

```text
ClientProfile = {
    client_type: enum,            // EDUCATION | COMMERCIAL | ...
    decision_priorities: [str],   // up to 3 from the starter set
    capability_match: {
        experience: enum,         // novice | intermediate | expert
        budget: enum,             // tight | realistic | ambitious
        operational: enum         // limited | adequate | strong
    },
    motivation: { observed: bool, value: str, source: str },
    inspiration: { observed: bool, value: str, source: str },
    expectation: { observed: bool, value: str, source: str },
    resource_transparency: { observed: bool, value: str, source: str },
    confidence: float,
    unknowns: [str]
}
```

Every field carries its provenance: `observed` (user-stated) /
`inferred` (deduced) / `unknown` (not observable).

## Examples

### Example 1: Education client

**Input:** Photo of a small playground attached to a private
kindergarten, 3-6 year olds, 9-month use year.

**Output (inferred):**
- client_type = EDUCATION
- decision_priorities = [child_safety, developmental_value, parent_approval]
- capability_match = {experience: intermediate, budget: tight, operational: adequate}
- motivation: observed = "幼儿园户外课堂" (inferred from context)
- confidence = 0.7

### Example 2: Commercial client

**Input:** Photo of a rooftop terrace on a commercial
building, urban setting.

**Output (inferred):**
- client_type = COMMERCIAL
- decision_priorities = [foot_traffic, differentiation, dwell_time]
- capability_match = {experience: expert, budget: ambitious, operational: strong}
- motivation: observed = "吸引周边白领" (inferred from urban context)
- confidence = 0.5

### Example 3: Unknown (low signal)

**Input:** A single photo, no stated context, ambiguous
setting.

**Output:**
- client_type = unknown
- decision_priorities = []
- capability_match = {experience: unknown, budget: unknown, operational: unknown}
- motivation: observed = false
- confidence = 0.2
- unknowns = [client_type, decision_priorities, capability_match]

The Brain asks the user for the missing inputs before
proceeding.

## Cross-references

- `constitution/` -- the Philosophy principles this module
  obeys.
- `project_fit/` -- downstream consumer of the ClientProfile.
- `knowledge/decision_model/Context_Model.md` Section 4
  (Goal sub-model) -- the ClientProfile "s decision_priorities
  shape the downstream Goal sub-model.
- `knowledge/expert_handbook/02_Expert_Rules.md` -- the
  expert-rule basis for the client-type taxonomy.
- `knowledge/expert_handbook/04_Positioning_Method.md` --
  client positioning as one of the four positioning axes.
- `knowledge/principles/DP-001` -- the ClientProfile "s
  primary function is set by the client "s stated goal, not
  the Brain "s inference.

## Maintenance

- A change to the client-type taxonomy (adding or renaming a
  type) is allowed without ADR; renames are non-breaking if
  the old name is preserved as an alias for one release.
- A change to the decision-priorities starter set is allowed
  without ADR.
- A change to the capability-match axes (adding a new axis)
  is a breaking change and requires ADR.
- A change to the `ClientProfile` output shape is a breaking
  change (downstream modules consume the fields) and requires
  ADR.
