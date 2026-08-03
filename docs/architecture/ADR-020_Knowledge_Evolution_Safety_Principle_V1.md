# ADR-020: CaseOS Knowledge Evolution Safety Principle V1

- **Status:** Proposed
- **Date:** 2026-08-03
- **Layer:** Learning (the closing transaction of the Feedback
  Learning Loop)
- **Affects:** Future Sprint 22.4 (Knowledge Evolution V1),
  Knowledge Object lifecycle, append-only audit log, future
  Retrieval Engine (reads updated KO).
- **Related ADRs:** ADR-014 (Decision), ADR-015 (Knowledge
  Object), ADR-016 (Trust), ADR-017 (Recommendation), ADR-018
  (Feedback Learning Loop), ADR-019 (Evidence Retrieval
  Intelligence Principle).
- **Implements:** the **Safety Principle** that the Sprint
  22.3.3 ADR-018 Architecture Stabilization explicitly carved
  out as the next architectural step. This ADR does **NOT**
  implement the evolution runtime; it locks the **rules** that
  a future Sprint 22.4 must obey.
- **Supersedes:** none
- **Source of truth:** `docs/architecture/ADR-020_Knowledge_Evolution_Safety_Principle_V1.md`
- **Triggers:** Sprint 22.4 (Knowledge Evolution V1) when
  Approved. Until then, this ADR is documentation-only.

> **Reading note.** This ADR is a **principle document**, not
> an implementation. It does not define transactions, version
> stores, audit tables, or rollback services. It defines the
> rules that a future implementation must satisfy. The Sprint
> 22.4 implementation Sprint will translate these rules into
> concrete modules, gated on the same `requires_human_review=True`
> discipline that ADR-018 mandates.

---

## Context

ADR-018 (Feedback Learning Loop) is now runtime-complete
through `ChangeIntent` (Sprints 22.1 → 22.3.2, frozen by Sprint
22.3.3). The runtime pipeline is:

```
Feedback
   |
   v
Feedback Runtime -> Evaluation -> Contradiction
   |
   v
Learning Proposal -> Human Review -> Interpretation Policy
   |
   v
ChangeIntent
   |
   v
(?) Knowledge Evolution
```

The remaining gap is the last arrow: turning an approved
`ChangeIntent` into an actual Knowledge Object change. ADR-018
explicitly says (Rule 3) that `ChangeIntent` is the **last safe
layer** — it does not mutate. This ADR defines the **safety
principle** that the future mutation step must obey.

Without these rules, a future implementation could:

- directly apply a `ChangeIntent` to the KO without a second
  human approval,
- overwrite the KO without keeping history,
- break the append-only audit contract that ADR-016 Rule 6
  and ADR-018 Rule 10 set,
- silently rewrite Decision, Trust, or Recommendation logic
  in the name of "evolution".

This ADR is the floor that prevents all four.

---

## Decision

Create **CaseOS Knowledge Evolution Safety Principle V1**.

The principle is one sentence:

> **Approved learning proposal may suggest knowledge evolution,
> but never directly mutate knowledge.**

Future Sprint 22.4 (Knowledge Evolution V1) must implement
evolution as a **transactional, versioned, audited, and
rollback-able** operation that is gated by a second human
approval step and is forbidden from touching any
intelligence-engine state.

---

## 1. Core Principle

```
Approved learning proposal may suggest knowledge evolution,
but never directly mutate knowledge.
```

The principle is the **single sentence** that every future
Sprint 22.4 implementation must be able to defend. If a future
implementation can be reduced to "this directly mutates the
Knowledge Object from a proposal", it violates the principle.

The translation of the principle into a runtime is the
**Evolution Pipeline** below.

---

## 2. Evolution Pipeline

Future Sprint 22.4 must implement the following sequence:

```
ChangeIntent
   |
   v
Evolution Transaction
   |
   v
Governance Validation
   |
   v
Knowledge Version Update
   |
   v
Audit Record
```

| Stage | Owner | Purpose |
| --- | --- | --- |
| `ChangeIntent` | Interpretation Policy (Sprint 22.3.2) | The single safe input. |
| `Evolution Transaction` | (future) Knowledge Evolution V1 | Wraps the change as an atomic operation. |
| `Governance Validation` | (future) Knowledge Governance | Validates against the corpus, taxonomy, and the existing KO version. |
| `Knowledge Version Update` | (future) KO Store | Writes a new `version`; never overwrites. |
| `Audit Record` | (future) Append-only Audit Log | Records `before`, `after`, `reason`, `proposal_id`, `reviewer`, `timestamp`. |

Sprint 22.4 is **NOT** in scope of the current sprint (22.3.3).
The pipeline is the **target shape** that a future sprint must
realise without violating any of the Mandatory Rules below.

---

## 3. Mandatory Rules

### Rule 1 — No Direct Mutation

The forbidden shortcut is:

```
Proposal -> KO update
```

The required path is:

```
Proposal -> Transaction -> Validated update
```

No future Sprint 22.x implementation is allowed to write
directly to the Knowledge Object from a `Proposal` or
`ChangeIntent` without going through an Evolution Transaction
and a Governance Validation step. The Transaction is the
unit of atomicity. The Validation is the unit of safety.

### Rule 2 — Version Required

The Knowledge Object must support a `version` field. Updates
are not overwrites.

```
v1
 |
 v
v2
```

Each evolution produces a new KO version. The old version is
preserved verbatim. Future Retrieval consumes the latest
version, but historical versions are queryable for audit and
rollback.

The `version` field is **append-only**. The KO loader of
Sprint 22.4 must treat `version` as an integer that only
increments; downgrades are forbidden.

### Rule 3 — Audit Required

Every evolution must record:

- `before` (the KO state at the previous version),
- `after` (the KO state at the new version),
- `reason` (the `ChangeIntent.reason` that triggered the
  evolution),
- `proposal_id` (the `LearningProposal.proposal_id` that
  originated the change),
- `reviewer` (the human who approved the change in the
  Review Queue),
- `timestamp` (UTC ISO 8601).

The audit record is **append-only**. No implementation may
delete, edit, or overwrite an audit record. Corrections
arrive as new audit records, not as edits.

### Rule 4 — Rollback Required

Any evolution must be rollback-able. A future operator must
be able to:

- identify the version they want to roll back to,
- verify that the rollback does not violate any other
  Mandatory Rule (e.g. Audit Required),
- re-activate the previous version as the new "latest" version
  (the rollback itself is an evolution with its own audit
  record).

No evolution is "final". Every evolution can be reverted by
a new evolution that obeys the same rules.

### Rule 5 — No Intelligence Rewrite

Evolution is **not** allowed to modify:

- Decision rules (`caseos.intelligence.decision`),
- Trust rules (`caseos.intelligence.trust`),
- Recommendation logic
  (`caseos.intelligence.recommendation`),
- Retrieval ranking (`caseos.knowledge.retrieval`).

The single allowed write target of the Evolution Transaction
is the **Knowledge Object field** that the `ChangeIntent`
named. Future Retrieval reads the updated KO on its next pass.
No intelligence engine state is mutated.

A future ADR is required to relax any of these five rules.

---

## 4. Architecture Boundary (inherited from ADR-018)

ADR-018 Rule 4 (Intelligence Authority Protection) is the
**parent** of ADR-020 Rule 5 (No Intelligence Rewrite). The
two rules are co-enforced:

- ADR-018 Rule 4 is enforced at the **proposal, review, and
  interpretation layers** (AST-tested, see Sprint 22.3.2
  `TestArchitectureBoundary`).
- ADR-020 Rule 5 is enforced at the **evolution layer** that
  a future Sprint 22.4 will introduce.

The combined boundary is the **single allowed write target**
of the entire Feedback Learning Loop. Any future ADR that
proposes a second write target is a hardening violation.

---

## 5. Acceptance Criteria

ADR-020 is **Proposed** until Sprint 22.4 lands. It is
considered **Accepted** when:

1. Sprint 22.4 ships a runtime that satisfies Rules 1-5.
2. The runtime is covered by AST tests that re-state the
   six forbidden prefixes (`caseos.intelligence.decision`,
   `caseos.intelligence.trust`,
   `caseos.intelligence.recommendation`,
   `caseos.knowledge.retrieval`,
   `caseos.knowledge.governance`,
   `caseos.knowledge.intake`).
3. The audit log is append-only by construction and the test
   suite proves it (e.g. forbidden `update` / `delete` /
   `overwrite` methods raise `TypeError`, mirroring the
   Review Queue Sprint 22.3.1 discipline).
4. The KO version field is enforced to be monotonically
   increasing; downgrades raise an exception.
5. A rollback is demonstrable end-to-end with a working
   test case.

Until all five are green, ADR-020 stays **Proposed** and the
Evolution layer must not be considered shipped.

---

## 6. Non-Goals (explicit)

ADR-020 does **NOT** define:

- the implementation of the Evolution Transaction,
- the storage backend of the KO version history,
- the schema of the audit log beyond the six fields above,
- the rollback service or the operator CLI,
- automatic learning of any kind,
- LLM / embedding / vector DB / database choices.

ADR-020 is the **principle**; Sprint 22.4 is the **runtime**.

---

## 7. Future Extensions (in declared order)

| Slot | Topic | Note |
| --- | --- | --- |
| **Sprint 22.4** | Knowledge Evolution V1 (Runtime) | The first sprint that may implement this principle. The runtime is gated on the five Mandatory Rules above. |
| (future) | **ADR-020b** Evolution Transaction Schema V1 | If the Transaction abstraction proves to need its own ADR. |
| (future) | **ADR-020c** KO Versioning Schema V1 | If the KO's `version` field needs more than an integer (e.g. semantic versioning). |
| (future) | **ADR-020d** Audit Log Schema V1 | If the audit log gains fields beyond the six mandated by Rule 3. |

These are **candidate** slots. None are committed.

---

*End of ADR-020. The next architectural change in this lineage
is Sprint 22.4 (Knowledge Evolution V1) implementation, gated
on this ADR being Accepted and on every Mandatory Rule being
defensible by a concrete test.*
