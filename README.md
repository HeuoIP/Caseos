# CaseOS

**CaseOS is an AI Space Advisor.**

It does not answer "what should this space look like?"
It answers **"what is the most suitable content for this space?"**

Mission:

    Upload a space photo.
    |
    v
    State the goal.
    |
    v
    Receive a defensible recommendation.

---

## CaseOS Constitution

The highest-level design philosophy of this project lives in
docs/standards/CaseOS_Constitution_V1.md. It defines what CaseOS
exists for, how it thinks, what it optimises for, and what it must
never do. Every Agent, Knowledge Module, and Decision Engine in
the codebase is bound by the Constitution.

The Constitution is implemented by
docs/standards/CaseOS_Decision_Principles_V1.md. If you are
building a new agent or extending an existing one, start there:
the four Decision Principles tell you what the agent must and must
not do.

Constitution and Decision Principles can only be amended through an
ADR. The current ADRs live in docs/architecture/.

---

## Four Founding Principles

    001  CaseOS exists to help every space find the most suitable
         content. Not the most expensive. Not the most beautiful.
         The most suitable.

    002  Every recommendation must create value for the decision
         maker. Design serves decisions. Objects serve goals.

    003  Understand before recommending. Observe before judging.
         Think before generating.

    004  Amplify the strengths of a space. Do not cover up the
         weaknesses with random objects.

Full text: docs/standards/CaseOS_Constitution_V1.md.

---

## Where to start reading

1. docs/architecture/Architecture.md -- the architecture pointer
   and where every layer lives.
2. docs/product/CaseOS_Product_Blueprint_V1.md -- the user journey
   and what the product is becoming.
3. docs/standards/CaseOS_Constitution_V1.md -- the philosophy.
4. docs/standards/CaseOS_Decision_Principles_V1.md -- the four
   operational principles.
5. docs/reviews/Architecture_Review_2026_07.md -- the pivot from
   "AI Playground Design Assistant" to "AI Space Advisor".
