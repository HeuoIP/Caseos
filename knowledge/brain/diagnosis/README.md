# Diagnosis

- **Module:** Diagnosis
- **Layer:** Brain
- **Pipeline Position:** 5 (after Experience Perception,
  before Strategy)
- **Status:** Accepted
- **Date:** 2026-07-30

## Purpose

Identify **why a space feels good or bad** in the context of
the user "s goal. Diagnosis compares the four Brain inputs
(Space Cognition, Experience Perception, Client
Understanding, Project Fit) and produces a structured
judgment: where the space is strong, where it is weak, what
is missing, what is at risk.

Diagnosis is **judgment, not recommendation**. It identifies
the problem; Strategy proposes the direction; Recommendation
selects the solution.

## Core Principles

1. **Diagnosis is judgment, not prescription.** A good
   diagnosis names the issue; it does not name the fix.
2. **Diagnosis is comparative.** A space is weak only when
   measured against some standard (the user "s goal, the
   space "s potential, the comparator case).
3. **Diagnosis is honest.** A space without problems is a
   strong space; the diagnosis must say so.
4. **Diagnosis is multi-dimensional.** A single dimension
   (e.g., aesthetics) is not enough; diagnosis covers
   function, experience, fit, and risk.
5. **Diagnosis is sourced.** Every claim cites the module
   that produced it (Space Cognition, Experience Perception,
   Client Understanding, Project Fit).

## Decision Rules

Diagnosis applies **five diagnostic patterns** against the
Brain inputs. Each pattern maps the observed facts to a
verdict and an evidence trail.

### 1. Fit diagnosis

Does the space support the user "s primary goal?
- **Aligned** -- space and goal align.
- **Mismatched** -- space is not suited to the goal.
- **Unknown** -- the evidence is too thin to decide.

Inputs: `space_cognition/`, `client_understanding/`,
`project_fit/`.

### 2. Vitality diagnosis

Does the space have the energy, life, or activity it
should?
- **Lively** -- more activity than expected.
- **Quiet** -- less than expected.
- **Dormant** -- potential activity not realised.
- **Strained** -- activity exceeds capacity.

Inputs: `experience_perception/`, `space_cognition/`.

### 3. Focal diagnosis

Does the space have a clear anchor -- a point the eye,
body, or story can lock onto?
- **Clear** -- one dominant anchor.
- **Competing** -- multiple anchors competing.
- **Absent** -- no anchor; the space dissolves.
- **Misdirected** -- the strongest anchor is the wrong one.

Inputs: `experience_perception/`, `space_cognition/`.

### 4. Risk diagnosis

Does the space carry any hard constraints, conflicts, or
dangers?
- **None** -- no risks found.
- **Hard** -- cannot be solved by design (regulation,
  structural, financial).
- **Soft** -- can be mitigated by design (acoustics,
  visibility, circulation).
- **Latent** -- not yet visible but likely to emerge.

Inputs: `project_fit/`, `space_cognition/`,
`client_understanding/`.

### 5. Synthesis diagnosis

A one-line summary in the form: "The space is **<one
word state>** because **<one sentence evidence>**, and the
primary concern is **<one sentence priority>**."

## Inputs

- `space_cognition/` -- SpaceCognition record.
- `experience_perception/` -- ExperienceProfile record.
- `client_understanding/` -- ClientUnderstanding record.
- `project_fit/` -- ProjectFitReport.

## Outputs

A `DiagnosisReport`:

```text
DiagnosisReport = {
    fit: {
        verdict: "aligned" | "mismatched" | "unknown",
        confidence: float,                  // 0..1
        evidence: [str],                    // cited claims
        gap: str | null                     // if mismatched
    },
    vitality: {
        verdict: "lively" | "quiet" | "dormant" | "strained",
        confidence: float,
        evidence: [str]
    },
    focal: {
        verdict: "clear" | "competing" | "absent"
                 | "misdirected",
        confidence: float,
        evidence: [str]
    },
    risk: {
        verdict: "none" | "hard" | "soft" | "latent",
        hard_risks: [str],                  // hard-only
        soft_risks: [str],
        latent_risks: [str],
        evidence: [str]
    },
    synthesis: {
        one_word_state: str,                // "underused",
                                            // "misdirected",
                                            // "ready"
        one_sentence_evidence: str,
        priority: str                       // the one thing
                                            // to fix first
    },
    provenance_summary: {
        observed: int,
        inferred: int,
        unknown: int
    },
    unknowns: [str]
}
```

A `confidence < 0.4` in any verdict downgrades that verdict
to `unknown` and flags it in `unknowns`.

## Examples

### Example 1: Mismatched public square for a kindergarten

**Inputs (abbreviated):**
- Space Cognition: monumental plaza, hard paving, west sun,
  no shade.
- Experience Perception: scale = monumental, atmosphere =
  ceremonial, stay_desire = low for child_3_6.
- Client Understanding: kindergarten seeking "safe, child-
  scale outdoor play".
- Project Fit: budget = low, operation = one staff, land =
  leased.

**Outputs:**
- fit.verdict = mismatched (confidence 0.85)
- fit.evidence = ["child_scale requested", "monumental
  observed"]
- fit.gap = "scale and shade are wrong for the user group"
- vitality.verdict = strained (when used) or dormant (most
  of the day)
- focal.verdict = absent
- risk.verdict = soft + latent
- risk.soft_risks = ["heat exposure for children"]
- synthesis.one_word_state = "wrong-scale"
- synthesis.priority = "introduce child-scale refuge and
  shade"

### Example 2: Strong match -- forest clearing

**Outputs:**
- fit.verdict = aligned (confidence 0.9)
- focal.verdict = clear (mature trees as natural anchor)
- risk.verdict = soft only ("soft ground in heavy rain")
- synthesis.one_word_state = "ready"
- synthesis.priority = "do not over-design"

### Example 3: Unknown -- too little evidence

**Outputs:**
- fit.verdict = unknown, confidence 0.2
- unknowns flagged
- Diagnosis asks the Brain for more signal before passing
  to Strategy.

## Cross-references

- `constitution/` -- Principle 003 (Understand before
  recommending). Diagnosis is the **name the problem** step.
- `space_cognition/` -- upstream producer.
- `experience_perception/` -- upstream producer.
- `client_understanding/` -- upstream producer.
- `project_fit/` -- upstream producer.
- `strategy/` -- downstream consumer (Strategy reads the
  diagnosis report as its brief).
- `recommendation/` -- downstream consumer (Explain Agent
  cites diagnosis in customer-facing prose).
- `knowledge/decision_model/Project_Fit_Model.md` --
  the runtime shape used by the Decision Engine.

## Maintenance

- Adding a new diagnostic pattern (e.g., accessibility,
  acoustics) is a breaking change to the DiagnosisReport
  contract and requires ADR.
- Renaming a verdict is a breaking change and requires
  ADR.
- Adding a new verdict value (e.g., a new focal verdict
  "borrowed") is a breaking change and requires ADR.
- Threshold changes (e.g., confidence downgrade from
  0.4 to 0.5) is a non-breaking change (allowed without
  ADR).
