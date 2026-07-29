# CaseOS Expert Handbook

> The "knowledge brain" of CaseOS.
> This handbook is the deep, expert-level companion to the operational
> principles in `knowledge/decision_rules/Space_Decision_Principles.md`.
> It is content, not code. No runtime decision engine reads it yet.
> The future Space Decision Engine will operationalise it.

## Purpose

The handbook captures the *how* of space decisions at expert level:
the method, the rules, the value vocabulary, the positioning
grammar, the safety rail, the psychological basis, the lifestyle
model, the object-to-value map, the concrete decision trees, and
the process for capturing more expert knowledge over time.

It is deliberately separated from:

- **`knowledge/decision_rules/Space_Decision_Principles.md`** —
  the top-level principles. The handbook is operational; the
  principles are philosophical.
- **`knowledge/objects/`** — the object library. The handbook
  describes how to reason about objects; the library describes
  the objects themselves.
- **`knowledge/taxonomy/theme/`** — the theme library. The
  handbook describes how to reason about themes; the library
  describes the themes themselves.
- **`docs/standards/`** — the standards. The handbook is
  expert opinion; the standards are rules.

## The 10 Documents

| # | File | One-line purpose |
| --- | --- | --- |
| 01 | [`01_Space_Decision_Method.md`](01_Space_Decision_Method.md) | The deterministic procedure for going from input to recommendation. |
| 02 | [`02_Expert_Rules.md`](02_Expert_Rules.md) | The implicit rules experienced designers follow. |
| 03 | [`03_Value_Taxonomy.md`](03_Value_Taxonomy.md) | The seven dimensions of value a space can deliver. |
| 04 | [`04_Positioning_Method.md`](04_Positioning_Method.md) | The four axes along which a space is positioned. |
| 05 | [`05_Negative_Rules.md`](05_Negative_Rules.md) | The things the engine must NEVER do. |
| 06 | [`06_Space_Psychology.md`](06_Space_Psychology.md) | How people perceive, feel, and behave in spaces. |
| 07 | [`07_Lifestyle_Model.md`](07_Lifestyle_Model.md) | How the target user's lifestyle shapes the design. |
| 08 | [`08_Object_Value_Map.md`](08_Object_Value_Map.md) | How the five starter objects map to the seven value dimensions. |
| 09 | [`09_Decision_Tree.md`](09_Decision_Tree.md) | Concrete decision flows that implement the method. |
| 10 | [`10_Interview_Log.md`](10_Interview_Log.md) | A template and process for capturing expert interviews. |

## Unified Format

Every handbook document follows the same 10-section template, so
the future engine can rely on a consistent structure.

1. Purpose
2. Scope
3. Core Concepts
4. Heuristics
5. Vocabulary
6. Common Pitfalls
7. Cross-References
8. Worked Example
9. Open Questions
10. Maintenance

The intent is that a reader (or the future engine) can find the
same kinds of content in the same order across all 10 documents.

## Cross-Link Matrix

The documents reference each other. The matrix below shows the
strongest cross-link from each document.

| From | Strongest link to | Why |
| --- | --- | --- |
| 01 Method | 02 Rules, 09 Trees | The method is operationalised by expert rules and decision trees. |
| 02 Rules | 06 Psychology, 07 Lifestyle | Most rules have a psychological or lifestyle basis. |
| 03 Value | 08 Object Map | The value vocabulary is operationalised by the object map. |
| 04 Positioning | 03 Value, 07 Lifestyle | Positioning changes the value weight vector and the lifestyle narrative. |
| 05 Negative Rules | 01 Method, 02 Rules | The negative rules are the safety rail on the method and the expert rules. |
| 06 Psychology | 02 Rules, 03 Value | Psychology underlies the emotional and social value dimensions. |
| 07 Lifestyle | 03 Value, 04 Positioning | Lifestyle changes the weight vector and the positioning narrative. |
| 08 Object Map | 03 Value, 01 Method | The object map is the bridge from objects to value and to the method. |
| 09 Trees | 01 Method, 05 Negative Rules | The trees are concrete implementations of the method that respect the negative rules. |
| 10 Interviews | All of the above | Interviews feed every other document. |

## How to Read This Handbook

- **First read.** 01 Method and 05 Negative Rules. These are the
  spine.
- **Second read.** 02 Rules, 03 Value, 06 Psychology, 07 Lifestyle,
  08 Object Map. These are the substance.
- **Third read.** 04 Positioning, 09 Trees, 10 Interview Log.
  These are the application.

The intended reading order is not strict; each document is
self-contained. But the order above is the one an experienced
designer would follow if they were teaching the engine from
scratch.

## Maintenance Rules

- A change to the unified 10-section format is a breaking change
  to the whole handbook.
- A change to a single document that affects another document
  must be reflected in the affected document's cross-references.
- Worked examples accumulate; heuristics and rules are revised
  only with a counter-example.
- The 10 Interview Log is the only document expected to grow
  monotonically; the other nine are revised, not appended to.

## Relationship to the Decision Principles

`knowledge/decision_rules/Space_Decision_Principles.md` defines
**ten principles** the future engine will obey. This handbook
**operationalises** those principles: it explains the method, the
rules, the value vocabulary, the safety rail, and the process for
adding more expert knowledge.

When the two documents disagree, the principles win. The
handbook is operational; the principles are philosophical. The
handbook should be revised until it is consistent with the
principles, not the other way around.

## Open Questions for the Future

- [ ] How are the 10 documents weighted when the engine reasons
  across them? Some may be constraints, others scoring inputs.
- [ ] How is the unified 10-section format enforced in CI?
- [ ] How is the cross-link matrix maintained when documents
  evolve?
- [ ] When is a new document added to the handbook (i.e. 11,
  12)? Only when a real case demonstrates that 01 to 10 cannot
  cover it.
