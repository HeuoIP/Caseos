# Recommendation Rules (RR)

- **Family:** RR
- **Stage:** 8 -- Recommendation
- **Source:** `docs/architecture/ADR-010-decision-rules-framework.md`

Rules in this folder govern **the conversion of a
strategy + theme into a RecommendationSet**. They enforce
the seven Rule of Recommendation (anchor-or-not gate,
one core, five-match test, theme binding, budget
preservation, trade-off disclosure, language
discipline) defined in
`knowledge/brain/recommendation/README.md`.

V1 ships one rule:

- **RR-001** -- Limited budget should concentrate
  value.

See `RR-001.md` for full content.
