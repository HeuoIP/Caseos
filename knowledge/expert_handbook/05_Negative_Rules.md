# 05 Negative Rules

> The things the CaseOS Space Decision Engine must NEVER do.
> A negation-first document: the rules here are framed as forbidden
> behaviours, not as positive guidance. The future engine treats a
> violation of any rule in this document as a hard fault.

## 1. Purpose

Codify the engine's hard "do not" list. These rules are the engine's
safety rail. They are the rules that, if broken, mean the engine is
no longer CaseOS.

## 2. Scope

**In scope**
- Behaviors the engine must avoid, regardless of how plausible the
  output would be.
- Behaviors that would mislead a user, a designer, or a regulator.
- Behaviors that would compromise the system's defensibility.

**Out of scope**
- Things the engine is *encouraged* to do (see 02_Expert_Rules.md).
- Things the engine is *allowed* to do but should not do routinely
  (see 05 vs 02 in the future).
- Things that are merely bad practice (those are pitfalls, not
  negative rules).

## 3. Core Concepts

Negative rules are organised by the *kind of harm* they prevent.
There are seven kinds of harm in scope.

1. **Fabrication** — the engine invents a fact, a dimension, a
   standard, or a cost that it does not actually know.
2. **Oversell** — the engine communicates a confidence or a
   performance the system cannot deliver.
3. **Hidden risk** — the engine omits a known risk, contraindication,
   or maintenance cost from a recommendation.
4. **Substitution** — the engine replaces a user's stated goal with
   a different goal because the original goal is hard to serve.
5. **Speculation** — the engine speaks about a future outcome
   (sales, footfall, child-development gains) as if it were a fact.
6. **Invisibility** — the engine makes a decision without showing the
   inputs, the filter, the weight vector, or the trade-offs.
7. **Irreversibility** — the engine takes a user-visible action
   (purchase, commit, publish) without explicit confirmation.

## 4. Heuristics

- **When in doubt, refuse.** A defensible "I need more information"
  is preferred to a guess.
- **A negative rule is more important than a positive one.** If a
  positive heuristic and a negative rule conflict, the negative rule
  wins.
- **Negative rules do not have exceptions.** A one-time exception
  becomes a precedent. If an exception seems necessary, the rule
  itself should be revised.
- **Negative rules are reported, not hidden.** When the engine is
  about to violate a rule, it must say so and stop, not silently
  change its output.

## 5. Vocabulary

- **Hard fault** — a violation of a negative rule. The engine must
  stop and report.
- **Soft fault** — a violation of a heuristic or pitfall. The engine
  may continue but should disclose.
- **Invisibility** — the absence of an explanation, not the presence
  of a wrong answer.
- **Substitution** — replacing a user's goal with the engine's
  preference, even when the engine is "trying to help."

## 6. Common Pitfalls

(These are the most common ways the engine drifts toward a negative
rule without noticing.)

- **Drift toward overconfidence.** A model that returns well-formatted
  JSON is not necessarily correct. Formatting is not a confidence
  signal.
- **Drift toward completeness.** Filling in missing facts to make the
  answer look complete.
- **Drift toward friendliness.** Softening a contraindication because
  the user "probably will not like the answer."
- **Drift toward helpfulness.** Inventing a use case the user did not
  mention.

## 7. Cross-References

- 01_Space_Decision_Method.md — the method must enforce the negative
  rules at every step.
- 02_Expert_Rules.md — many expert rules are the positive form of a
  negative rule.
- `knowledge/decision_rules/Space_Decision_Principles.md` — the
  ten principles are the philosophical version of the negative rules.
- `docs/review/Architecture_Review_2026_07.md` — the proposal pipeline
  must not bypass negative rules for visual reasons.

## 8. Worked Example

**Scenario.** A user asks for "an exciting dragon-themed playground
for 4 to 9 year olds" but does not specify safety surfacing budget.

**Negative rule application.**
- Fabrication: the engine must NOT invent a budget figure.
- Oversell: the engine must NOT claim the playground is "safe" without
  surfacing information.
- Hidden risk: the engine must NOT omit the need for impact-attenuating
  surfacing in the output.
- Substitution: the engine must NOT replace the dragon theme with a
  forest theme just because forest is easier to recommend.
- Speculation: the engine must NOT claim footfall or developmental
  outcomes.
- Invisibility: the engine must NOT hide the unknowns.
- Irreversibility: the engine must NOT place an order or commit to
  a vendor.

**Output.** A recommendation that names the dragon theme as
plausible, lists the recommended object set with explicit "requires
safety surfacing budget" annotations, returns a list of unknowns
(budget, jurisdiction, soil, user counts), and asks the user to
confirm before any next step.

## 9. Open Questions

- [ ] Should there be an explicit "negative rules" pre-check before
  the engine returns a recommendation?
- [ ] How does the engine report a violation to the user without
  sounding accusatory?
- [ ] How do negative rules interact with user overrides ("I know the
  rule, do it anyway")?
- [ ] Are some negative rules stronger than others, or are they all
  equal?

## 10. Maintenance

- A negative rule may be added, but never removed silently. Removal
  requires an ADR.
- Each negative rule must have at least one worked example and at
  least one attempted counter-example.
- When a negative rule is violated in practice, the rule is examined
  for clarity, not relaxed.
