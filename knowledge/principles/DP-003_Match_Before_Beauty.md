# DP-003: Match Before Beauty

- **ID:** DP-003
- **Status:** Accepted
- **Date:** 2026-07-30
- **Layer:** Knowledge (Design Principle)
- **Companion documents:**
  - `knowledge/decision_rules/Space_Decision_Principles.md` -- top-level principles
  - `docs/standards/CaseOS_Constitution_V1.md` -- philosophy
  - `docs/standards/CaseOS_Decision_Principles_V1.md` -- implementation guide

---

## 1. Statement

> **Suitability precedes aesthetics.**
> A beautiful but mismatched object is worse than a plain but matched one.
> "Match" means the object serves the goal, suits the space, fits the user,
> respects the climate, and fits the budget -- all at the same time.
> Beauty is a secondary filter, applied only to candidates that have already
> passed the suitability filter.

## 2. Why this principle exists

- Constitution Principle 001 -- *CaseOS exists to help every space
  find the most suitable content. Not the most expensive. Not the
  most beautiful. **The most suitable.*** This DP is the operational
  expression of that principle at the candidate-object layer.
- Constitution Principle 003 -- *Understand before recommending.*
  Match is impossible without the understanding DP-002 demands.
- Decision Principle 004 -- *Recommend from the Decision Maker "s
  Perspective.* "Match" is judged from the user "s perspective, not
  the designer "s, the vendor "s, or the catalogue "s.

This principle exists because "beautiful" is the easiest attribute
to optimise. A vendor can rank objects by aesthetic and produce a
recommendation that looks coherent in a PDF and fails on the day
of opening. DP-003 forces the harder optimisation first.

## 3. What it means

A candidate intervention passes the **match filter** when, and
only when, all five of the following tests succeed at once:

1. **Goal match.** The intervention serves the primary function
   (DP-001) and one or more of the user's stated goals.
2. **Space match.** The intervention fits the space per the five
   axes recorded under DP-002 (dimensions, light/climate,
   surroundings, existing features, atmosphere).
3. **User match.** The intervention suits the user population
   (age, ability, group size, cultural context, supervision
   model). An object that does not match the user is unusable,
   no matter how beautiful.
4. **Climate match.** The intervention survives the local
   climate for its expected service life with realistic
   maintenance. Climate mismatch is the single most common cause
   of early replacement.
5. **Budget match.** The intervention is within the user's
   stated budget band (or, if budget is unknown, within the
   realistic cost band for the intervention's category). Budget
   match is not the lowest price; it is the absence of price
   surprise.

Only after all five tests succeed does **beauty** enter the
ranking. Beauty is judged along the dimensions the user has
signalled (style, theme, atmosphere, brand) -- never on the
engine "s aesthetic preferences.

Three direct consequences:

1. **Beauty cannot rescue a failed match.** A beautiful object
   that fails any of the five tests is dropped, not down-weighted.
2. **A plain object that passes all five tests is a valid
   recommendation.** Plainness is not a flaw.
3. **Match is a verb, not a state.** A recommendation is matched
   to a specific space, user, goal, climate, and budget. The same
   intervention can match one site and fail another. The engine
   does not promote an intervention to "universally beautiful".

## 4. When to apply

Apply DP-003 at every one of the following moments:

- Whenever a candidate set is being filtered to a ranked
  recommendation.
- Whenever the user asks for "the most beautiful" or "the most
  impressive" option.
- Whenever the recommendation set starts to converge on a
  single visual style (the engine has likely confused match
  with beauty).
- Whenever a vendor catalogue is being scored (the catalogue
  is biased toward beauty; the engine must compensate).
- Whenever an explain-recommendation paragraph uses marketing
  language. Marketing language is the prose form of the beauty-
  over-match failure mode.

## 5. When NOT to apply

DP-003 yields in three well-defined situations:

1. **The user has explicitly asked for beauty first.** If the
   user states "I want this to be iconic; fit is secondary",
   the engine records the priority inversion, runs the match
   filter anyway (because hard constraints still dominate), and
   applies beauty as the dominant soft filter among the
   surviving candidates. The priority inversion is logged.
2. **The user has explicitly asked for cost-first.** Same shape:
   the engine records the inversion, runs the match filter, and
   applies cost among the survivors.
3. **Beauty *is* the primary function.** Some spaces have a
   primary function that is itself aesthetic (an art
   installation, a flagship lobby). In that case, "beauty" is
   one of the goal-match axes, not a competing filter. DP-001
   and DP-003 are reconciled through the primary function.

## 6. Failure modes

When DP-003 is ignored, four predictable failures occur.

1. **Beautiful-but-wrong.** A striking object ships and the
   primary user cannot use it (wrong age, wrong height, wrong
   climate). The recommendation reads well in the PDF and fails
   on day one.
2. **Catalogue default.** A space receives the vendor "s flagship
   object because it is in the catalogue. The space "s actual
   conditions and the user "s actual goals have not constrained
   the choice at all.
3. **Style monoculture.** Every recommendation looks the same,
   because the engine has ranked on style and ignored the
   climate, the user, and the goal. The portfolio looks coherent
   and feels generic.
4. **Marketing-prose contamination.** The Explain Agent describes
   the recommendation in marketing language ("striking",
   "world-class", "iconic"). Constitution Principle 4 (Never
   invent a fact to look confident) and Decision Principle 004
   (no marketing jargon) are violated in prose form.

## 7. Worked example

**Target space.** A 300 m² corner of a public park in a coastal
city, salty air, hot summers, used mainly by retirees in the
morning and families with toddlers in the late afternoon.

**Without DP-003.** A proposal centred on a "signature stainless
steel sculpture with mirror finish" wins on beauty. Stainless
steel in salt air requires constant cleaning; the mirror finish
shows salt haze within weeks. Retirees cannot sit near it (no
seating). Families with toddlers find no shade.

**With DP-003.**

- Goal match: serve retirees " morning exercise + families " toddler
  play in shade.
- Space match: 300 m², partial shade from existing trees, west
  wind off the sea.
- User match: low-impact ground surface, stable seating with
  backrests, fenced toddler area, accessible paths.
- Climate match: salt-resistant materials (Robinia wood, marine-
  grade stainless, hot-dip galvanised steel, FRP), shade
  structures, drainage for sudden rain.
- Budget match: mid-band municipal budget, replaceable parts,
  low maintenance.
- Beauty filter, applied last: a coherent timber-and-galvanised
  material palette, one calm focal planting bed (no signature
  sculpture), warm-tone indirect lighting for evenings.

Outcome: no signature sculpture, no mirror finish. The space
looks plain in the supplier "s PDF and works on the day of
opening. The match filter wins.

## 8. Cross-references

- **Constitution P001** -- The most suitable, not the most
  beautiful.
- **Constitution P003** -- Understand before recommending.
- **Decision Principle 004** -- Recommend from the Decision
  Maker "s Perspective. Marketing language is forbidden.
- **Space_Decision_Principles.md** -- principle 2 (*Hard
  constraints are not negotiable*), principle 6 (*Trade-offs
  must be visible*).
- **DP-001** -- Match cannot be evaluated before the primary
  function is identified.
- **DP-002** -- Match cannot be evaluated before the space is
  examined.
- **Expert Handbook 03 Value Taxonomy** -- the seven value
  dimensions are how match is measured.
- **Expert Handbook 08 Object Value Map** -- the bridge between
  candidate objects and the value dimensions, used to score
  match.
- **Expert Handbook 05 Negative Rules** -- the rule "do not let
  beauty override fit" is the negative form of this DP.
- **ADR-005 Decision Intelligence** -- the Object Selector Agent
  is the runtime expression of DP-003.
- **ADR-006 Project Fit Intelligence** -- Project Fit is a
  pre-match filter that runs before the match filter, not a
  substitute for it.

## 9. Maintenance

- A change to the five-match tests is a breaking change to the
  Object Selector Agent and to every ranked recommendation that
  has cited a match score.
- The five tests are not exhaustive. A new test (e.g.
  *inclusive-design match*, *cultural-context match*) may be
  added by appending, not by replacing. Versioned.
- DP-003 does not prescribe how "beauty" is scored; the
  Visual Style Taxonomy (`knowledge/taxonomy/style/`) and the
  user "s stated style preference are the inputs. The engine
  does not invent a beauty score of its own.
