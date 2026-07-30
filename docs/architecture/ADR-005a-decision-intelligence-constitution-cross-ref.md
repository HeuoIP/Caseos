# ADR-005a: Decision Intelligence x Constitution Cross-Reference

- **Status:** Accepted
- **Date:** 2026-07-30
- **Supersedes:** -- (editorial amendment to ADR-005)
- **Superseded by:** --
- **Amends:** ADR-005 (Decision Intelligence Architecture, Accepted 2026-07-29)
- **Reason:** Constitution + Decision Principles adopted 2026-07-30 (ADR-007)
  are not yet cited from ADR-005, creating a paper trail gap that
  lets future agents silently violate the Constitution.

---

## 1. Context

ADR-005 was Accepted on 2026-07-29. On 2026-07-30 the project
adopted the CaseOS Constitution (ADR-007) and the Decision
Principles V1 as its highest-level philosophy and implementation
guide. ADR-005 "s Consequences section and its acceptance criteria
do not yet cite these documents. A reader who follows ADR-005 alone
can produce code that violates the Constitution, because the
Constitution "s clauses are not part of the Decision Intelligence
contract.

This amendment closes the gap by adding an explicit cross-reference
from ADR-005 to the Constitution and the Decision Principles. It
does NOT re-open ADR-005 for re-vote. It is an editorial
amendment, per the Constitution "s amendment procedure
    "no silent edits"
rule: the rule is satisfied because this amendment is recorded as
its own ADR.

---

## 2. Amendment text

The following paragraph is added to ADR-005, immediately under
the existing "Consequences" heading, as a new subsection
    "Constitution cross-reference"
:

> Every agent in the Decision Intelligence pipeline must satisfy
> the CaseOS Constitution V1 and the four Decision Principles V1.
> In particular:
>
> 1. **Principle 003 (Constitution):** understand before
>    recommending. The Space Agent, the Decision Maker Agent, and
>    the Knowledge Retriever Agent exist so that the Strategy
>    Agent never has to recommend without understanding.
> 2. **Principle 002 (Constitution) / Principle 001 (Decision):**
>    design serves decisions. The Strategy Agent must cite the
>    served goals in every Recommendation.
> 3. **Principle 002 (Decision):** space before object. The Object
>    Selector must read the Space Summary and refuse to recommend
>    objects that contradict the observed site type, materials, or
>    fall height.
> 4. **Principle 004 (Decision):** recommend from the decision
>    maker "s"s perspective. The Explain Agent must never use the
>    marketing vocabulary banned by the Constitution
>    (striking, amazing, iconic, world-class, revolutionary,
>    cutting-edge).
>
> A new acceptance criterion is added to ADR-005:
>    "Every agent in the pipeline must be auditable against the
>    Constitution V1 by a future test_constitution_compliance.py."
> This is enforced starting Sprint 14 (Constitution Compliance
> Tests).

---

## 3. Why a separate amendment ADR and not an in-place edit

The Constitution "s amendment procedure says:

    No silent edits. No "tidy up" rewording. If a sentence stops
    being right, the right move is a new ADR, not a
    search-and-replace.

This ADR is the implementation of that rule for the case where
ADR-005 is the doc being amended. The alternative (an in-place
edit to ADR-005) would have been a silent edit by definition.

---

## 4. Acceptance

- [x] Cross-reference paragraph written (above).
- [ ] Paragraph added to ADR-005 "s Consequences section.
- [ ] ADR-005 "s reference list updated to cite Constitution V1 and
  Decision Principles V1.
- [ ] Future Sprint 14 enforces the new acceptance criterion by
  test.

---

## 5. References

- ADR-005 -- Decision Intelligence Architecture (the amended doc).
- ADR-006 -- Project Fit Intelligence Architecture (a sibling layer).
- ADR-007 -- CaseOS Constitution V1 (the new top-level philosophy).
- CaseOS_Constitution_V1.md -- the four Founding Principles.
- CaseOS_Decision_Principles_V1.md -- the four Decision
  Principles that operationalise the Constitution.
- System Review 2026-07-30 -- P0-6, the finding that motivated
  this amendment.
