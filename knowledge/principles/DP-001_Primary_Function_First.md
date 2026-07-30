# DP-001: Primary Function First

- **ID:** DP-001
- **Status:** Accepted
- **Date:** 2026-07-30
- **Layer:** Knowledge (Design Principle)
- **Companion documents:**
  - `knowledge/decision_rules/Space_Decision_Principles.md` -- top-level principles
  - `docs/standards/CaseOS_Constitution_V1.md` -- philosophy
  - `docs/standards/CaseOS_Decision_Principles_V1.md` -- implementation guide

---

## 1. Statement

> Every space exists to serve a **primary function**.
> Before recommending anything, identify and protect that primary function.
> If a recommendation does not serve the primary function, it is decoration.

## 2. Why this principle exists

- Constitution Principle 002 -- *Every recommendation must create
  value for the decision maker. Design serves decisions. Objects
  serve goals.* A space has a primary function the way a decision
  has a primary goal: without it, there is no value to create.
- Constitution Principle 004 -- *Amplify the strengths of a space.
  Do not cover up the weaknesses with random objects.* A space's
  primary function is its single greatest strength. Suppressing it
  in favour of "extras" is a category error.
- Decision Principle 003 -- *Content serves Purpose.* Every
  recommended object, strategy, or intervention must be traceable
  to a stated goal. The primary function is the goal's anchor.

The principle exists because CaseOS frequently sees targets where
the decision maker has not articulated the primary function, and
where the supplier defaults to "what looks good" instead of "what
the space is for". This principle forces the question before the
recommendation.

## 3. What it means

A space has exactly one **primary function** -- the thing the
space is for, judged from the user's point of view, not from the
designer "s or the supplier "s. Other functions may co-exist, but
they are secondary. The primary function is what the space would
be defended by if its existence were questioned.

Three direct consequences:

1. **Identify first.** Before any candidate intervention is
   considered, the primary function is stated explicitly. If the
   decision maker has not stated it, CaseOS asks. CaseOS does NOT
   infer a primary function from the site's prior use, the
   supplier "s catalogue, or visual cues alone.
2. **Protect it.** Every recommendation must be checked against
   the primary function. A recommendation that does not serve it
   is dropped, down-weighted, or labelled as "decoration only".
   Decoration is allowed only when the primary function is already
   served and the user has signalled budget for the extra.
3. **Do not confuse function with form.** A "Forest theme" is a
   form, not a function. A "high-climb challenge course" may be a
   function in one space and a distraction in another. Form follows
   function, not the other way around.

## 4. When to apply

Apply DP-001 at every one of the following moments:

- The first time a target space is described.
- The first time a recommendation set is being shaped.
- Whenever the user proposes an object that does not obviously
  serve the primary function.
- Whenever two domain packs (e.g. playground + retail) are both
  eligible and the primary function of the space has not been
  confirmed for one of them.
- Whenever the recommendation set starts to drift toward "more
  is better" without a function check.

## 5. When NOT to apply

DP-001 yields to other rules in three well-defined situations:

1. **Hard constraints dominate.** Safety, jurisdiction, climate,
   footprint, and load-bearing override function. A primary
   function that cannot be met under hard constraints becomes a
   question, not a recommendation.
2. **The user has stated a multi-function brief.** Some spaces
   are explicitly dual- or multi-function (e.g. a schoolyard that
   must serve PE class, recess, and after-hours community use).
   In that case, the primary function is the **dominant** function
   in the stated brief, not a single function the engine picks.
3. **The primary function itself is in question.** If the user
   says "I don't know what this space is for", DP-001 forces the
   engine to ask, not to guess. The recommendation waits.

## 6. Failure modes

When DP-001 is ignored, four predictable failures occur.

1. **Decoration-as-strategy.** The recommendation reads as a
   shopping list of "objects that look nice" without a stated
   purpose. The user has to invent the purpose after the fact.
2. **Theme over function.** A "Forest theme" or "Space theme"
   dominates the recommendation even when the space has no
   thematic brief. The result looks coherent but serves nothing.
3. **Supplier catalogue leakage.** Objects appear because they
   are in the catalogue, not because they serve the function.
   Constitution Principle 4 (Never let the catalogue drive the
   recommendation) is violated.
4. **Silent goal drift.** The recommendation set drifts from
   "serve the primary function" to "increase visitor numbers" or
   "showcase the designer's range" without the user ever agreeing
   to the new goal. The original goal is now an afterthought.

## 7. Worked example

**Target space.** A 120 m² rooftop terrace attached to a private
kindergarten, used 9 months per year for outdoor class.

**Without DP-001.** A standard kindergarten-supplier proposal
delivers a colourful plastic play set, an artificial grass mat,
and a climbing frame. Total spend: high. Function served: visual
splash for parents.

**With DP-001.**

- Primary function identified: enable outdoor classroom
  activities for 3-6 year olds, 9 months per year, with storage
  for class materials.
- Hard constraints checked: load capacity of the rooftop,
  wind exposure, drainage, child safety rail height.
- Recommendation: a weather-treated timber deck, a foldable
  shade canopy, two low storage cabinets for class materials,
  a small planting bed for the class garden, and one quiet
  corner with a reading rug. No climbing frame. No plastic
  play set. Total spend: lower.
- Outcome: every element serves the primary function. The
  recommendation is defensible, lower-cost, and aligned with
  the decision the school actually has to make.

## 8. Cross-references

- **Constitution P002** -- Objects serve goals.
- **Constitution P004** -- Amplify the strengths.
- **Decision Principle 003** -- Content serves Purpose.
- **Space_Decision_Principles.md** -- principles 3 ("Best is
  conditional"), 5 ("Multiple options beat one"), 8 ("User "s
  stated goals win, within constraints").
- **Expert Handbook 01 Method**, step 2 (Identify primary
  function) and step 4 (Hard-constraint filter). DP-001 is the
  knowledge that step 2 operationalises.
- **Expert Handbook 03 Value Taxonomy** -- primary functions
  map to one or more of the seven value dimensions.
- **Expert Handbook 05 Negative Rules** -- the rule
  "do not let form precede function" is the negative form of
  this DP.

## 9. Maintenance

- A change to DP-001 is a breaking change to any future
  Decision Engine that has implemented the "identify primary
  function" step. The change must be reviewed and versioned.
- DP-001 interacts with ADR-006 (Project Fit Intelligence).
  If Project Fit introduces a new way of capturing the
  primary function, DP-001 must be reviewed for consistency.
- DP-001 does not enumerate what counts as a valid primary
  function. The vocabulary of primary functions belongs to the
  Goal Library (`knowledge/goals/`) and to the Domain Packs.
