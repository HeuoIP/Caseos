# Architecture Decision Records (ADR)

This folder holds ADRs and other architecture-level documents.

## What goes here

- **ADRs** -- Architecture Decision Records. Each ADR captures one
  decision: the context, the choice, the consequences, and the
  trade-offs. Naming convention: `ADR-NNN-short-title.md` (e.g.
  `ADR-001-product-positioning.md`).
- **High-level architecture maps** -- e.g. `Architecture.md`,
  `TechStack.md`.
- **Retired product documents** -- e.g.
  `CaseOS_Product_V1_OBSOLETE.md`. The current product spec is
  `docs/product/CaseOS_Product_Blueprint_V1.md`.

## What does NOT go here

- Sprint task specs (use `../sprints/`).
- Architecture reviews / retrospectives (use `../reviews/`).
- Schema documentation (use `../schemas/`).
- Knowledge rules (use `../knowledge/`).
- The current product spec (use `../product/`).

## ADR template (future ADRs)

```
# ADR-NNN: <Title>

Status: Proposed | Accepted | Superseded by ADR-XXX
Date: YYYY-MM-DD

## Context

What is the issue / driver?

## Decision

What did we choose?

## Consequences

What becomes easier? What becomes harder?

## Alternatives Considered

What other options were on the table, and why did we reject them?
```

## Active ADRs

- **ADR-005** -- Decision Intelligence Architecture (Accepted
  2026-07-29, amended by ADR-005a 2026-07-30)
- **ADR-005a** -- Decision Intelligence x Constitution
  Cross-Reference (Accepted 2026-07-30)
- **ADR-006** -- Project Fit Intelligence Architecture (Accepted
  2026-07-30, recorded by ADR-006a; generalised from
  investor-centric to generic Project Fit on the same day)
- **ADR-006a** -- Project Fit Architecture Acceptance (Accepted
  2026-07-30)
- **ADR-007** -- CaseOS Constitution V1 (Accepted 2026-07-30;
  codified as `docs/standards/CaseOS_Constitution_V1.md`)
- **ADR-008** -- Vision Output Schema -- Canonical V3 (Accepted
  2026-07-30; supersedes the V2/V3 ambiguity identified in the
  System Review)

## Pending ADR slots

The Sprint 12 Pivot Cleanup intentionally does NOT file new ADRs.
The cleanup is documentation-only and the policy changes implied
by it are already codified in ADR-005 / ADR-005a / ADR-006 /
ADR-006a / ADR-007 / ADR-008. The next ADR slots that are likely
to be opened (no promises) are:

- **ADR-009** -- API Surface V1 (Sprint 13 deliverable).
- **ADR-010** -- Constitution Compliance Tests (Sprint 14 deliverable).
- **ADR-011** -- LLM Swap-In (Sprint 15 deliverable).
- **ADR-012** -- Space Character Dataset seed (Sprint 16 deliverable).

A new ADR is required whenever one of the following is true:

1. A document in `docs/standards/`, `docs/schemas/`, or
   `docs/database/` is amended in a way that changes a contract.
2. A new agent is added to `backend/app/core/agents/`.
3. A new domain pack is added to `knowledge/`.
4. A new schema version is published under `schemas/`.
5. The Constitution is amended (very rare; only by ADR).

## Sprint 12 (Pivot Cleanup) outcome

Sprint 12 (2026-07-30) re-aligned the visible documentation
surface with the AI Space Advisor pivot. No new ADR was filed;
the cleanup only renamed, retired, and re-pointed documents that
were left over from V1. See `docs/sprints/Sprint_12_Pivot_Cleanup.md`
for the record. The review findings that motivated the cleanup
live in `docs/reviews/System_Review_2026_07_30.md`.

## References

- `docs/architecture/Architecture.md` -- pointer to authoritative
  architecture sources.
- `docs/architecture/TechStack.md` -- current tech stack (V1).
- `docs/architecture/CaseOS_Product_V1_OBSOLETE.md` -- the V1
  product spec, retired by Sprint 12.
- `docs/product/CaseOS_Product_Blueprint_V1.md` -- the current
  product spec.
- `docs/sprints/Sprint_12_Pivot_Cleanup.md` -- the cleanup record.
