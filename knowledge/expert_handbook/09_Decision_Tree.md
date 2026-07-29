# 09 Decision Tree

> Concrete decision flows that implement the method in
> 01_Space_Decision_Method.md. The trees are not the only way
> to apply the method, but they are the most defensible starting
> point for routine cases.

## 1. Purpose

Provide a small set of decision trees that turn the abstract method
into a sequence of yes/no questions. The trees help the engine
produce consistent recommendations, help the user follow the
reasoning, and help the team test the method.

## 2. Scope

**In scope**
- Trees for routine, well-understood decisions.
- Trees that encode the most common failure modes as early
  exits.
- Trees that explicitly list the unknowns to surface.

**Out of scope**
- Trees for novel or one-off decisions (those are handled by
  the method directly).
- Trees that violate the negative rules in 05_Negative_Rules.md.

## 3. Core Concepts

A decision tree in this document has four parts.

- **Trigger** — the situation in which the tree applies.
- **Branches** — the yes/no questions, in order.
- **Leaves** — the actions the tree produces (recommend, ask,
  refuse, escalate).
- **Early exits** — branches that short-circuit to an action
  before reaching a leaf.

The trees are written as nested bullets, with each question as
a heading and the yes/no paths as nested bullets.

## 4. Heuristics

- **Trees are starting points, not cages.** When a tree does
  not fit, escalate to the method; do not force the case into
  the tree.
- **Trees surface unknowns early.** A tree that does not ask
  for missing information is a bad tree.
- **Trees must not skip the constraint filter.** A tree that
  jumps from observation to recommendation without checking
  constraints is a hazard.
- **Trees must respect the negative rules.** A tree that
  produces a fabrication or an oversell is invalid.

## 5. Vocabulary

- **Trigger** — the situation the tree handles.
- **Branch** — a yes/no question.
- **Leaf** — an action produced by the tree.
- **Early exit** — a branch that ends the tree early.
- **Escalation** — a leaf that returns the case to the method
  rather than producing a recommendation.

## 6. Common Pitfalls

- **Treating a tree as an oracle.** The tree is a tool for the
  method, not a replacement for it.
- **Adding branches without examples.** Every branch must have
  a worked example.
- **Letting the tree invent data.** The tree must surface
  unknowns, not fill them in.

## 7. Cross-References

- 01_Space_Decision_Method.md — the trees implement the method.
- 02_Expert_Rules.md — heuristics that override a tree.
- 05_Negative_Rules.md — the rules the trees must never violate.
- 03_Value_Taxonomy.md — the value framework the trees use.

## 8. Worked Example

**Tree A — "Is the site a public park?"**

```
Trigger: a target space is described as a park, garden, or
public outdoor area.

Q1. Is the site publicly accessible?
    Yes -> continue.
    No  -> escalate (not in scope for V1).

Q2. Is the site fenced or enclosed?
    Yes -> ask: who controls the gate? (school, community,
            private operator). Record and continue.
    No  -> continue.

Q3. Are there existing public amenities (path, bench, light)?
    Yes -> continue; the new intervention should connect to
            the existing amenity system.
    No  -> continue; record as a co-design opportunity.

Q4. Does the site have shade structures?
    Yes -> continue; do not place new objects in the existing
            shade without reason.
    No  -> ask: is shade in scope? If yes, the first
            recommendation is shade infrastructure; objects
            are placed under it.

Q5. Is the daily user count known?
    Yes -> use as a sizing input.
    No  -> record as an unknown; do not invent.

Leaf A. Proceed to candidate retrieval (Tree B or method).
```

**Tree B — "What is the user's primary age group?"**

```
Trigger: candidate retrieval for a playground or play-led space.

Q1. Is the user group 0 to 2?
    Yes -> prioritise sensory, low-height, caregiver-proximate
           objects; Reading_Corner is usually in scope;
           Treehouse at low height with supervision.
    No  -> continue.

Q2. Is the user group 3 to 6?
    Yes -> Treehouse, Slide, Reading_Corner are all in scope;
           IP_Sculpture and Interactive_Wall are situational.
    No  -> continue.

Q3. Is the user group 6 to 9?
    Yes -> Treehouse, Slide, IP_Sculpture, Interactive_Wall
           are all in scope; Reading_Corner is for rest.
    No  -> continue.

Q4. Is the user group 9 to 12?
    Yes -> Slide, IP_Sculpture, Interactive_Wall; Treehouse
           possible if designed for older children.
    No  -> escalate (multi-age or non-play; use method).

Q5. Is the user group multi-age (e.g. 3 to 12)?
    Yes -> propose a portfolio of two or three objects; see
           01_Space_Decision_Method.md for portfolio logic.
    No  -> escalate.
```

## 9. Open Questions

- [ ] How are these trees versioned? As code, or as data?
- [ ] How are new trees added without breaking the existing
  tests?
- [ ] Should a tree ever produce a single-number score, or
  always a vector?
- [ ] How does a tree communicate that it is the wrong tree
  for the case at hand?

## 10. Maintenance

- Each tree is owned by a specific maintainer.
- A tree is deprecated when its failure rate exceeds a defined
  threshold in the benchmark suite.
- New trees are added only when a real case demonstrates a
  pattern that no existing tree handles.
