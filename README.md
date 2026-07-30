# CaseOS

AI Case Engine for Playground Design

Mission:

    Upload a site photo.
    |
    v
    Find similar cases.
    |
    v
    Generate professional playground concepts.

---

## CaseOS Constitution

The highest-level design philosophy of this project lives in
docs/standards/CaseOS_Constitution_V1.md. It defines what CaseOS
exists for, how it thinks, what it optimises for, and what it must
never do. Every Agent, Knowledge Module, and Decision Engine in
the codebase is bound by the Constitution.

The Constitution "s implementation guide lives next to it as
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
