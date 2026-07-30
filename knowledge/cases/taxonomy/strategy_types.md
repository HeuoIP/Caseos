# Strategy Types

Controlled vocabulary for `strategy_type` in the CKO
Schema V1 Section 5.

This vocabulary is identical to the **five strategy
families** in `knowledge/brain/strategy/README.md`:
Landmark / Journey / Field / Layered / Anchor. CKOs are
the **case evidence** that those families are real, not
aspirational.

## Values

| Value | Definition | Brain source |
| --- | --- | --- |
| `landmark` | One dominant feature organises the whole site. Use when Diagnosis reports focal = absent. | `brain/strategy/` Family 1. |
| `journey` | Sequenced experience from arrival to departure. Use when vitality = dormant and the user wants narrative. | `brain/strategy/` Family 2. |
| `field` | Diffuse, varied landscape; many small moves together make the place. Use when the space is already strong and the move is gentle. | `brain/strategy/` Family 3. |
| `layered` | Multiple horizontal layers with different programs. Use when the space has vertical potential. | `brain/strategy/` Family 4. |
| `anchor` | One existing element becomes the centre; the strategy protects and amplifies it. Use when Diagnosis reports focal = clear and the project is amplification. | `brain/strategy/` Family 5. |
| `hybrid` | Two families coexist with a documented rule for how they coexist (e.g., Anchor carrying a Landmark). Use sparingly; document the rule in `design_principles`. | New in CKO V1. |

`hybrid` is a CKO-only value. The Brain "s five families
are pure moves; `hybrid` describes the **case** that has
two moves woven together with intent.

## Why mirror the Brain "s families

If a Brain strategy has **no CKO evidence**, the strategy
is a hypothesis. CKOs are the proof.

If a CKO demonstrates a strategy pattern **not** in the
Brain "s families, the CKO is **pending review**: either
the Brain needs to add a new family (requiring ADR-009)
or the CKO is misclassified (Librarian "s call).

## Use

A CKO picks exactly one `strategy_type`. The chosen type
must be defensible against `diagnosis.problem_type`:

- A CKO with `problem_type = positive_strong_anchor`
  typically uses `strategy_type = landmark` or `anchor`.
- A CKO with `problem_type = positive_experience_depth`
  typically uses `strategy_type = journey`.
- A CKO with `problem_type = positive_amplify_strengths`
  typically uses `strategy_type = anchor` or `field`.

The CKO Validator (future) flags mismatches between
`problem_type` and `strategy_type`.

## Variants

Strategies have **variants**. A CKO may carry a variant
label in `design_principles` (e.g., "anchor / tree variant",
"landmark / tower variant") but the CKO `strategy_type`
remains the canonical five-family label. Variants are a
Brain Concern (future sprint), not a CKO concern.

## Maintenance

- Adding a value (other than `hybrid`): breaking, requires
  ADR-009 + ADR-driven CKO update.
- Adding `hybrid`-like meta-values: non-breaking (allowed
  without ADR), but the rule for coexistence must be
  documented in `design_principles`.
- Renaming a value: breaking, requires ADR.
- Removing a value still in use: breaking, requires ADR.
