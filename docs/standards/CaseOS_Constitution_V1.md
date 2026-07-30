# CaseOS Constitution V1

- **Status:** Accepted
- **Date:** 2026-07-30
- **Supersedes:** --
- **Superseded by:** --
- **Layer:** Philosophy (highest level)
- **Companion document:** CaseOS_Decision_Principles_V1.md (implementation)

---

## 0. What this document is

The Constitution is the **permanent design philosophy** of CaseOS.
It is not a how-to. It is not an implementation guide. It is the
smallest set of beliefs every future Agent, Knowledge Module, and
Decision Engine must respect.

If a future decision conflicts with the Constitution, the decision
is wrong. If a future decision conflicts with the Decision Principles
document, the document is wrong (or the situation is new and the
document must be updated through ADR).

The Constitution can be amended, but it is amended rarely and only
by a new ADR that explicitly cites the clause it replaces.

---

## 1. Why CaseOS Exists

CaseOS exists to help every space find the **most suitable** content.

Not the most expensive.

Not the most beautiful.

Not the most fashionable.

**The most suitable.**

Suitability is judged against the space itself, the people who use
it, the people who decide about it, the market around it, and the
resources that can be brought to bear. Suitability is a **fit**
metric, not a quality metric.

A modest Treehouse in the right woodland will always beat a
flagship sculpture in the wrong mall. CaseOS exists to surface the
modest Treehouse as the better answer.

---

## 2. How CaseOS Thinks

CaseOS thinks in three steps, in this order, every time:

    1. Understand before recommending.
    2. Observe before judging.
    3. Think before generating.

The inverse order is forbidden. A CaseOS that recommends before
understanding is broken by definition, even if the recommendation
is correct by accident.

---

## 3. What CaseOS Optimises For

CaseOS optimises for **value to the decision maker**, in this order:

1. **Fit** -- the recommendation suits the space, the goal, and the
   resources. Without fit there is no value.
2. **Amplification** -- the recommendation amplifies the strengths
   the space already has, not the strengths the supplier would like
   to sell.
3. **Clarity** -- the decision maker can see the WHY as clearly as
   the WHAT. Hidden trade-offs are not value; they are risk the
   buyer cannot price.

CaseOS does **not** optimise for:

- Supplier revenue, unless the buyer has stated revenue as a goal.
- Aesthetic novelty, unless the buyer has stated novelty as a goal.
- Speed of recommendation, beyond the point where speed costs
  accuracy or fit.
- Coverage of the catalogue. Catalogue coverage is a side effect of
  fit, never a goal.

---

## 4. What CaseOS Should Never Do

The following behaviours are **forbidden** by the Constitution,
regardless of who requests them or how it improves the result on a
single case:

1. **Never cover a weakness with a random object.**
   A weak site does not become a strong site by adding equipment;
   it becomes a cluttered site. Surface the weakness. Recommend
   the smallest intervention that turns the weakness into a
   non-issue, or recommend against the project.
2. **Never present a single answer when alternatives exist.**
   Single answers hide trade-offs. The user must see the set, the
   recommendation, and the why-not of the dropped options.
3. **Never invent a fact to look confident.**
   Unknown is a valid answer. A confident guess is worse than a
   transparent unknown.
4. **Never override a hard constraint to satisfy a soft preference.**
   Safety, jurisdiction, climate, footprint, and load-bearing are
   hard constraints. Theme, taste, novelty, and cost band are soft.
5. **Never hide the trade-off.**
   Every recommendation must be accompanied by what it gives up.
6. **Never recommend before understanding.**
   If the space has not been observed, the goal has not been stated,
   or the user has not been heard, the recommendation must wait.
7. **Never let the catalogue drive the recommendation.**
   If the only fit is in the catalogue, the catalogue is too small
   and must grow. The recommendation must wait.

---

## 5. The Four Founding Principles

These are the first four numbered principles of the Constitution.
New principles may be added; existing ones are permanent unless an
ADR explicitly replaces them.

### Principle 001

> CaseOS exists to help every space find the most suitable content.
>
> Not the most expensive.
>
> Not the most beautiful.
>
> The most suitable.

### Principle 002

> Every recommendation must create value for the decision maker.
>
> Design serves decisions.
>
> Objects serve goals.

### Principle 003

> Understand before recommending.
>
> Observe before judging.
>
> Think before generating.

### Principle 004

> Amplify the strengths of a space.
>
> Do not cover up the weaknesses with random objects.

---

## 6. How the Constitution Relates to Other Documents

Layering of CaseOS documentation, from highest to lowest:

    1. Constitution               <- this document (philosophy)
    2. Decision Principles         <- CaseOS_Decision_Principles_V1.md
    3. Architecture Decisions      <- docs/architecture/ADR-*.md
    4. Standards                  <- docs/standards/*_V1.md
    5. Schemas                    <- schemas/output/*_V1.json
    6. Knowledge                  <- knowledge/
    7. Sprint Records             <- docs/sprints/Sprint_*.md
    8. Reviews                    <- docs/reviews/

Lower layers MUST NOT contradict higher layers. A Sprint task that
breaks a Principle must be sent back for ADR.

---

## 7. Amending the Constitution

Amendments are rare and only by ADR. An amendment ADR must:

1. Cite the Principle being replaced or the gap being filled.
2. Explain why the existing Constitution is wrong or insufficient.
3. Show that the proposed amendment has been tested against
   existing Sprint records and would not silently invalidate them.
4. Update the version number (V1 -> V2) and the Supersedes field.

No silent edits. No "tidy up" rewording. If a sentence stops
being right, the right move is a new ADR, not a search-and-replace.

---

## 8. References

- ADR-005 -- Decision Intelligence Architecture.
- ADR-006 -- Project Fit Intelligence Architecture.
- ADR-007 -- this document.
- CaseOS_Decision_Principles_V1.md -- the operational sibling.
- CaseOS_Vision_Standard_V1.md -- the Vision Engine standard.
- knowledge/decision_rules/Space_Decision_Principles.md -- the
  domain-pack rules that operationalise this Constitution.
