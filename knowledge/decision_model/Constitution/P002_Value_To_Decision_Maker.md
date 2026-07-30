# P002 -- Value to Decision Maker Binding

- **Binds to:** Constitution Principle 002 (*Every recommendation
  must create value for the decision maker. Design serves
  decisions. Objects serve goals.*)
- **Source of truth:** `docs/standards/CaseOS_Constitution_V1.md`
- **Stages it manifests in:** Decision Maker Agent, Strategy
  Agent, Object Selector Agent, Explain Agent (cross-cutting).
- **Status:** Accepted, enforced by DP-001.

## Clause

The engine "s output must create value for the **decision maker**,
not for the supplier, the catalogue owner, or the design
community. A recommendation that looks good but does not help
the decision maker decide is not a recommendation; it is
decoration.

## Manifestation rule

Every object, strategy, or recommendation emitted by the engine
must be **traceable to a stated user goal** captured in
`DecisionContext.goal`.

- **Decision Maker Agent:** the engine must infer the user "s
  goals (from primary_function, secondary_goals, and stated
  constraints) before any strategy is produced. The user "s
  stated goal outranks any inferred goal.
- **Strategy Agent:** every strategy must declare which
  served_goals it addresses.
- **Object Selector Agent:** every recommended object must
  declare which served_goals and served_strategies it supports.
- **Explain Agent:** every prose explanation must lead with the
  value to the decision maker, not with the aesthetics of the
  object.

## Failure mode

The engine recommends a beautiful object that does not serve
any of the user "s stated goals. The decision maker accepts
because the object is attractive, then cannot defend the
purchase to stakeholders. The recommendation "s value is
zero, even if its visual appeal is high.

A subtler variant: the engine recommends an object that serves
a **supplier goal** (catalogue coverage, new-line promotion)
disguised as a user goal. The recommendation reads as
user-centred but is in fact supplier-centred.

## Test that catches it

- For each strategy, assert that `served_goals` is non-empty
  and references goals from `DecisionContext.goal`.
- For each recommended object, assert that it is linked to at
  least one strategy and that the strategy has at least one
  served_goal.
- For each prose explanation, assert that the first sentence
  references a user goal, not an object attribute.

## Cross-references

- Constitution V1, Principle 002.
- DP-001 (*Primary Function First*) -- the operational rule
  that enforces P002 at the goal-identification layer.
- `knowledge/goals/` -- the Goal Library that supplies the
  served_goals values.
- `../Strategy_Model.md` -- where served_goals are declared.
- `../Context_Model.md` -- where `DecisionContext.goal` lives.

## Maintenance

- This binding is **enforced** by DP-001 and by the future
  `test_constitution_compliance.py` suite.
- A new Goal Library entry does not require an ADR. A change
  to the served_goals contract on Strategy or Recommendation
  objects does.
