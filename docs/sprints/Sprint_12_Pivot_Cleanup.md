# Sprint 12 -- Pivot Cleanup

- **Goal:** Clean up V1-era documentation that still references the
  "AI Playground Design Assistant" positioning, so the public docs
  surface (root README, docs/README, architecture/) matches the
  current product positioning (AI Space Advisor) and the highest-
  level philosophy (Constitution V1, Decision Principles V1,
  Product Blueprint V1).
- **Constraint:** documentation only. No code change. No schema
  change. No knowledge change. No taxonomy change. Schema canonical
  decisions are owned by ADR-008, not by this Sprint.
- **Status:** in progress
- **Date:** 2026-07-30

---

## 0. Why this sprint exists

The product pivot from "AI Playground Design Assistant" to
"AI Space Advisor" was carried into ADR-005, ADR-006, ADR-007,
ADR-008, the Constitution V1, the Decision Principles V1, the
Product Blueprint V1, the Space Character Dataset, and the
System Review 2026-07-30. However, several visible documents were
left untouched and still describe the playground-only product.

The System Review identified the leftovers as P0 / P1 / P2 items
under the heading "4.1 The product pivot is only half-carried".
This Sprint closes the documentation half of that finding.

## 1. Scope

In scope:

- Root `README.md` (project entry point).
- `docs/README.md` (docs folder map).
- `docs/architecture/Product.md` (legacy V1 product doc).
- `docs/architecture/Architecture.md` (pointer doc, keep).
- `docs/architecture/README.md` (ADR index, refresh list).
- `docs/knowledge/Playground_Ontology_V1.md` (domain-pack positioning).
- `docs/knowledge/theme_extension_log.md` (sprint log mis-placement).
- This Sprint record.

Out of scope:

- Any Python file. ADR-008 owns schema canonical decisions.
- Any taxonomy file under `knowledge/taxonomy/`. Playground domain
  pack stays as-is; it is the first domain pack, not the only one.
- Any `.json` schema file. ADR-008 already decided V3 is canonical.
- Any image, data, or runtime artifact.

## 2. Method

For each in-scope file:

1. Decide Keep / Refactor / Retire based on its current role.
2. Refactor in place if the file is still useful.
3. Rename to `*_OBSOLETE.md` if the file is historical reference only.
4. Add a one-line deprecation pointer if the file is superseded.
5. Update the docs folder map in `docs/README.md` accordingly.

## 3. Decisions (Keep / Refactor / Retire)

| # | File | Decision | Reason |
| --- | --- | --- | --- |
| 1 | `README.md` (root) | Refactor | Has the old "AI Case Engine for Playground Design" subtitle. Replace with the AI Space Advisor mission and a pointer to the Constitution section it already carries. |
| 2 | `docs/README.md` | Refactor | Folder map still treats `architecture/Product.md` as the product doc. Update to point at `product/CaseOS_Product_Blueprint_V1.md`. |
| 3 | `docs/architecture/Product.md` | Retire | Already carries a DEPRECATED banner. Rename to `CaseOS_Product_V1_OBSOLETE.md` for clarity. The Blueprint V1 inherits the role. |
| 4 | `docs/architecture/Architecture.md` | Keep | Already replaced the V1 ASCII sketch with a pointer doc. No change needed. |
| 5 | `docs/architecture/README.md` | Refactor | ADR list is current but could mention the Sprint 12 cleanup explicitly. |
| 6 | `docs/knowledge/Playground_Ontology_V1.md` | Refactor | Rename to `Playground_Domain_Pack_V1.md` and add a preamble that playground is the first domain pack, not the only one. |
| 7 | `docs/knowledge/theme_extension_log.md` | Move | This is a sprint completion log. Move it under `docs/sprints/` where it belongs. |
| 8 | `docs/sprints/Sprint_12_Pivot_Cleanup.md` | Create | This document. |

## 4. Review items being closed

From `docs/reviews/System_Review_2026_07_30.md`:

- **P0-1** V1-era product doc still references playground
  -> closed by decision #3 (retire).
- **P0-4** docs/architecture/Architecture.md is a 7-line ASCII sketch
  -> already closed by earlier edit; decision #4 keeps the pointer.
- **P1-3** docs/architecture/Product.md is the V1 product doc
  -> closed by decision #3 (retire).
- **P2-8** docs/knowledge/ overlaps with knowledge/
  -> partially closed by decision #6 (rename) and decision #7
     (move). The full closure happens when a future Sprint
     renames the folder itself.
- **P2-10** docs/README.md folder map is stale
  -> closed by decision #2.

Items that this Sprint does NOT close (and why):

- P0-2 ADR-006 Proposed -> closed by ADR-006a, not this Sprint.
- P0-3 Three Vision output shapes -> owned by ADR-008, not this Sprint.
- P0-5..P0-7 Constitution enforcement, examples/output, API surface
  -> outside documentation-only scope.

## 5. Acceptance criteria

- [x] `README.md` (root) opens with the AI Space Advisor mission.
- [x] `docs/README.md` folder map points at Blueprint V1, not Product V1.
- [x] `docs/architecture/Product.md` is renamed to a clearly obsolete file.
- [x] `docs/knowledge/Playground_Ontology_V1.md` is renamed to a clearly domain-pack-scoped file.
- [x] `docs/knowledge/theme_extension_log.md` is moved under `docs/sprints/`.
- [x] No new contradictory claims are introduced. Any retained
      playground-only document is explicitly labelled as the first
      domain pack.
- [x] No code, schema, or knowledge content is changed.

## 6. Execution log

- 2026-07-30: file created (this record).
- 2026-07-30: root README updated to AI Space Advisor mission.
- 2026-07-30: docs/README folder map updated.
- 2026-07-30: Product.md retired and renamed.
- 2026-07-30: Playground_Ontology_V1.md rebranded as domain pack.
- 2026-07-30: theme_extension_log.md moved to docs/sprints/.
- 2026-07-30: changes committed and pushed.

## 7. References

- docs/reviews/System_Review_2026_07_30.md -- source of P0/P1/P2 items.
- docs/architecture/Architecture.md -- pointer to authoritative docs.
- docs/product/CaseOS_Product_Blueprint_V1.md -- current product spec.
- docs/standards/CaseOS_Constitution_V1.md -- philosophy.
- docs/standards/CaseOS_Decision_Principles_V1.md -- implementation guide.
- ADR-008 -- schema canonical decision (out of scope for this Sprint).
