# P003 -- Understand Before Recommending Binding

- **Binds to:** Constitution Principle 003 (*Understand before
  recommending. Observe before judging. Think before generating.*)
- **Source of truth:** `docs/standards/CaseOS_Constitution_V1.md`
- **Stages it manifests in:** ALL stages (ordering constraint).
- **Status:** Accepted, enforced by DP-002 and the pipeline order.

## Clause

The inverse order is forbidden. A CaseOS that recommends before
understanding is broken by definition, even if the recommendation
is correct by accident. The pipeline is sequential, not
parallel; an agent may not skip ahead.

## Manifestation rule

The pipeline is **strictly sequential**:

```text
Vision -> Project Fit -> Space -> Decision Maker ->
Knowledge Retrieval -> Strategy -> Object Selector -> Explain
```

- An agent may not write a `DecisionContext` field that an
  upstream agent has not yet filled.
- An agent may not read a `DecisionContext` field that an
  upstream agent has explicitly marked as `unknown`.
- An agent that needs information it does not have must **ask**,
  surface the unknown, or refuse to run. It must NOT guess.

This is an **ordering constraint**, not a quality constraint.
The engine is allowed to recommend an imperfect object; it is
not allowed to recommend before understanding.

## Failure mode

The engine recommends an object based on the user "s stated
goal without examining the space. The recommendation reads as
goal-aligned but ignores space constraints; the object fails
on day one.

A subtler variant: the engine runs two agents in parallel to
save time, and the Object Selector proposes candidates before
the Space Agent has filled `DecisionContext.space`. The
candidates are filtered against an empty space context and
the result is a catalogue-driven recommendation.

## Test that catches it

- For every agent invocation, assert that all
  `DecisionContext` inputs are either filled by an upstream
  agent or explicitly marked `unknown`.
- For every recommendation, assert that the Space Agent,
  Decision Maker Agent, and Knowledge Retriever have all run
  before the Object Selector.
- For every prose explanation, assert that the first paragraph
  is a Space Summary, not a catalogue pitch.

## Cross-references

- Constitution V1, Principle 003.
- DP-002 (*Space First, Object Second*) -- the operational
  rule that enforces P003 at the space layer.
- ADR-005, Section 6 -- the 6-stage Agent pipeline.
- `../Decision_Model_V1.md` -- the pipeline diagram.

## Maintenance

- This binding is **enforced** by the pipeline "s sequential
  structure and by DP-002.
- Adding a new agent to the pipeline requires ADR.
- Reordering existing agents requires ADR (breaking change).
- Adding parallelism to a single agent "s internal work is
  allowed without ADR, as long as the agent "s inputs and
  outputs are unchanged.
