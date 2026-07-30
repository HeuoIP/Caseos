# CaseOS Design Principles

> Foundational design principles for the future CaseOS Decision Engine.
> Each principle is short, sharp, and operationalisable by exactly one
> future pipeline stage. The three principles here are the spine of the
> engine "s object-selection reasoning.

## Purpose

The CaseOS Design Principles are the **knowledge-layer rules of the road**
that sit between the Constitution (philosophy) and the Expert Handbook
(operational depth). They are shorter and sharper than the handbook,
longer and more concrete than the Constitution, and they map 1-to-1 onto
the Decision Engine "s main pipeline stages.

Three reasons this layer exists:

1. **A clear middle ground.** The Constitution says *what is right*.
   The Expert Handbook says *how to do it well*. The Design Principles
   say *what must never be skipped*. The middle ground is missing
   otherwise.
2. **A 1-to-1 map to pipeline stages.** Each DP has a single home in
   the future pipeline (DP-001 to the Goal Agent, DP-002 to the Space
   Agent, DP-003 to the Object Selector). The map is the first thing
   an implementer reads.
3. **A test target.** When a future behaviour regresses, the test
   that catches it lives next to one of these DPs, not next to a
   handbook chapter.

## The Three Principles

| ID | Title | One-line rule | Pipeline stage it operationalises |
| --- | --- | --- | --- |
| **DP-001** | [Primary Function First](DP-001_Primary_Function_First.md) | Every space should first fulfill its primary function. | Goal Agent + Decision Maker Agent |
| **DP-002** | [Space First, Object Second](DP-002_Space_First_Object_Second.md) | Examine the space before proposing any object. | Space Agent |
| **DP-003** | [Match Before Beauty](DP-003_Match_Before_Beauty.md) | Suitability precedes aesthetics. | Object Selector Agent |

## How the Three DPs Work Together

The three DPs are applied **in order**. Skipping or re-ordering them
produces a predictable failure mode (see each DP "s negative examples).

```text
DP-001  Identify primary function            (decision side)
   |
   v
DP-002  Observe the space                    (site side)
   |
   v
DP-003  Filter candidates by match,           (intervention side)
        rank survivors by beauty last
   |
   v
Handbook  Apply expert rules and methods     (depth side)
```

A correct CaseOS recommendation passes through all three gates in
order.

## Unified Template

Every DP follows this 3-section template. The shape is binding;
the content varies. Future DPs must use this template unless the
Maintenance section justifies an exception.

### 1. Principle

> A single one-line statement of the rule.
> Must be expressible as a short imperative or assertion.
> Must be readable in isolation.

### 2. Explanation

> A short prose explanation of *why* the principle exists and *what*
> it requires. Two to four paragraphs is the right size.
>
> Contains two sub-sections:
>
> - **Examples** -- 2 to 4 positive examples that show the principle
>   in action. Each example is one short line.
> - **Negative Examples** -- 2 to 4 examples that show the principle
>   being violated. Each example is one short line.

### 3. Design Implication

> A single one-line constraint -- the rule the engine must never
> break, phrased as a "never ..." or "always ..." statement.

After the 3-section template, each DP carries a metadata header
(Status, Date, Layer, Pipeline Stage) and a small footer:

- **Cross-references** -- the related Constitution clauses,
  Decision Principles, Top-Level Principles, other DPs, Expert
  Handbook chapters, and ADRs.
- **Maintenance** -- how to amend this DP.

The 3-section shape is binding. A future DP that omits any of the
three sections must justify the omission in the Maintenance section.

## Why a 3-Section Template

The earlier draft of these DPs used a 9-section template borrowed
from the Expert Handbook. The 3-section template was adopted
because:

1. **A DP is shorter and sharper than a handbook chapter.** The
   "what" can be one line. The "why" can be a few paragraphs.
   The "never" can be one line. That is enough for a rule of the
   road.
2. **Examples do more work than heuristics.** A short list of
   positive and negative examples is more teachable than a
   multi-paragraph discussion of edge cases.
3. **Maintenance, cross-references, and metadata are appendices.**
   They do not need to interrupt the reading flow.
4. **One principle per file.** The DP "s metadata header is enough
   to orient the reader; the body is the rule.

## Relationship to Other Layers

| Layer | Role | Where it lives |
| --- | --- | --- |
| **Constitution** | The permanent philosophy. What CaseOS is for, how it thinks, what it optimises for, what it must never do. | `docs/standards/CaseOS_Constitution_V1.md` |
| **Decision Principles** | The four operational principles the pipeline obeys. The bridge between philosophy and code. | `docs/standards/CaseOS_Decision_Principles_V1.md` |
| **Top-Level Principles** | The ten space-decision principles the future Decision Engine will obey. | `knowledge/decision_rules/Space_Decision_Principles.md` |
| **Design Principles (this folder)** | The three must-not-skip rules for object selection. Short and sharp. | `knowledge/principles/` |
| **Expert Handbook** | The deep, expert-level method, rules, vocabulary, decision trees, and worked examples. | `knowledge/expert_handbook/` |
| **Domain Packs** | The industry-specific knowledge (playground is the first). | `knowledge/taxonomy/`, `knowledge/objects/`, `docs/knowledge/Playground_Domain_Pack_V1.md` |

When two layers disagree, the higher layer wins. The Constitution
outranks the Decision Principles, which outrank the top-level Space
Decision Principles, which outrank the Design Principles here, which
outrank the Expert Handbook. The Domain Packs supply **content** to
all of the above; they do not override the principles.

## Cross-Reference Matrix

Each DP cites specific Constitution clauses, Decision Principles,
Top-Level Principles, Expert Handbook chapters, and ADRs. The matrix
below is the consolidated view.

| From | Constitution | Decision Principles | Top-Level Principles | Other DPs | Expert Handbook | ADRs |
| --- | --- | --- | --- | --- | --- | --- |
| **DP-001 Primary Function First** | P002, P004 | 003 (Content serves Purpose) | 8 (User "s goals win) | -- | 01 Method (step 2), 03 Value Taxonomy, 05 Negative Rules | ADR-005, ADR-006 |
| **DP-002 Space First Object Second** | P003, P004 | 002 (Space before Object) | 1 (Evidence before invention), 2 (Hard constraints) | DP-001 (the goal comes first) | 01 Method (step 1), 06 Space Psychology | ADR-005 |
| **DP-003 Match Before Beauty** | P001, P003 | 004 (Decision Maker "s Perspective) | 2 (Hard constraints), 6 (Trade-offs visible) | DP-001, DP-002 (match needs both goal and space) | 03 Value Taxonomy, 05 Negative Rules, 08 Object Value Map | ADR-005, ADR-006 |

## Naming and Numbering

- **ID format:** `DP-NNN` where `NNN` is a zero-padded sequence
  number starting at `001`. IDs are permanent; a DP "s number is
  never re-used after retirement.
- **File name:** `DP-NNN_<Title_With_Underscores>.md`. The title
  matches the file "s H1 header.
- **Status:** every DP carries one of `Proposed`, `Accepted`,
  `Superseded`. Status changes go through ADR.
- **Versioning:** DPs are versioned by ADR. A breaking change to a
  DP produces a new DP (e.g. `DP-001a`) rather than a silent edit.

## Open Questions for the Future

- [ ] How many DPs is the right number? The current three cover
  goal, space, and intervention. Future candidates include
  *DP-004: User First, Group Second* (population-axis analogue
  to DP-002), *DP-005: Honest Over Persuasive* (Explain-Agent
  rule), *DP-006: Small Set Beats Long List* (UI rule).
- [ ] When a DP conflicts with another DP (e.g. DP-002 vs DP-003
  in a constrained space), which outranks? The Constitution is
  silent because it lives one layer above. A future ADR or DP
  addendum may need to set the tie-break.
- [ ] How are the DPs enforced in CI? A simple presence check is
  easy; a behaviour test against the Decision Engine is the
  real enforcement and requires the engine to exist.
- [ ] When a Domain Pack contradicts a DP (e.g. a hypothetical
  Playground Pack that prefers "decoration-first" briefs),
  which outranks? The Constitution answer is "DPs outrank" but
  the question has not been exercised yet.

## Maintenance

- This folder is the **principles layer**. Detailed rules for
  specific topics (theme selection, object scoring, conflict
  resolution) belong in their own files under
  `knowledge/decision_rules/` or `knowledge/expert_handbook/`.
- A change to an existing DP is a **breaking change** to the
  future Decision Engine. It must be reviewed and versioned.
- Adding a new DP is allowed without ADR; promoting a new DP to
  *Accepted* requires ADR.
- A change to the 3-section template itself is a breaking change
  to the whole principles folder and must be reflected in every
  existing DP.
- The three existing DPs were accepted together (2026-07-30) as
  the V1 spine of the Decision Engine "s object-selection
  reasoning. Future DPs will be added one at a time.

## References

- `docs/standards/CaseOS_Constitution_V1.md` -- the philosophy.
- `docs/standards/CaseOS_Decision_Principles_V1.md` -- the four
  operational principles.
- `knowledge/decision_rules/Space_Decision_Principles.md` --
  the ten top-level space-decision principles.
- `knowledge/expert_handbook/` -- the operational handbook.
- `docs/architecture/ADR-005-decision-intelligence.md` -- the
  Decision Intelligence pipeline that these DPs operationalise.
- `docs/architecture/ADR-006-project-fit-intelligence.md` -- the
  Project Fit pre-filter that runs before DP-003.
