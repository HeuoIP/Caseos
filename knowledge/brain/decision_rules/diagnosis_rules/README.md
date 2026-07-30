# Diagnosis Rules (DR)

- **Family:** DR
- **Stage:** 5 -- Diagnosis
- **Source:** `docs/architecture/ADR-010-decision-rules-framework.md`

Rules in this folder govern **the judgment of why a
space feels good or bad** in the context of the user "s
goal. They fire when the Brain produces or consumes a
`DiagnosisReport`.

V1 ships three rules:

- **DR-001** -- Lack of spatial anchor.
- **DR-002** -- Existing anchor but lack of coherence.
- **DR-003** -- Visual attraction does not equal play
  value.

See each rule "s file (e.g., `DR-001.md`) for full
content.
