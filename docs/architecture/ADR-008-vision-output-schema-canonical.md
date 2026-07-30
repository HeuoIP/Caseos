# ADR-008: Vision Output Schema -- Canonical V3

- **Status:** Accepted
- **Date:** 2026-07-30
- **Supersedes:** --
- **Superseded by:** --
- **Replaces:** -- (deprecates nothing; see Migration Plan below)

---

## 1. Context

The Vision Engine currently ships two JSON Schemas:

- schemas/case_analysis_v2.json -- nested (12 top-level sections,
  no metadata block, no vision_summary / design_interpretation
  split).
- schemas/case_analysis_v3.json -- nested (12 top-level sections
  plus a metadata block, plus ai_analysis.vision_summary and
  ai_analysis.design_interpretation as separate fields).

Three on-disk artifacts are out of sync with both:

1. data/analysis/cases/0001.json and 0002.json -- flat shape,
   with project_name, vision_summary, design_interpretation
   at the top level (not under ai_analysis), and a top-level
   metadata block.
2. examples/output/snow_playground_case.json -- V1 shape, free-
   form age_group (e.g. 3-5 years), a description field instead of
   vision_summary / design_interpretation.
3. data/analysis/cases/sample_playground.json -- mixed V1/V2
   shape, used only as a fixture.

The downstream effects are real:

- KnowledgeRetriever._retrieve_cases reads ai_analysis.keywords
  and ai_analysis.vision_summary, but the real cases store those
  fields at the top level. Cross-case retrieval returns empty for
  the real cases. This is System Review follow-up #1 (P1-1).
- docs/database/CaseOS_Database_Schema_V1.md says analysis_json
  follows case_analysis_v2.json, but the runtime is on V3. If the
  database is built, it will store V2-shape data while the
  analyzer produces V3-shape data (P1-6).
- The V1 snow case in examples/output/ is a misleading
  reference (P2-2).

---

## 2. Decision

**The canonical Vision output Schema is V3**
(schemas/case_analysis_v3.json). The Vision prompt, the
analyzer, the retriever, the database design, and all future
downstream consumers MUST target V3.

V3 is canonical because:

1. It already exists and is wired to the prompt + analyzer
   (backend/app/services/vision/factory.py).
2. It has a metadata block, which is the provenance contract
   that System Review P2-9 (per-case metadata) requires.
3. It separates vision_summary (for vector retrieval) from
   design_interpretation (for AI recommendations), which is the
   split the user explicitly approved during the V1 -> V2 prompt
   evolution.
4. The existing analyzer / prompt / retriever code is already
   aligned with V3 shape. Adopting V2 instead would mean
   rewriting the prompt and the analyzer, and re-running all
   analyses.

V2 is deprecated. The JSON file schemas/case_analysis_v2.json
will be kept for one release (until the database design catches up)
and then removed.

---

## 3. Migration plan

Four concrete changes land in this commit:

### 3.1 Promote V3 + add migration note to V2

- schemas/case_analysis_v3.json becomes the canonical Vision
  output schema. No file change needed (it was already
  canonical-shape).
- schemas/case_analysis_v2.json gets a top-level _deprecated field
  pointing at V3, and a 1-line note at the top of the file.

### 3.2 Re-shape real cases to V3

- data/analysis/cases/0001.json: wrap top-level fields under
  V3 nested sections; move vision_summary and
  design_interpretation under ai_analysis; add a top-level
  metadata block if missing (0002 is missing one; 0001 has it
  in V2 shape, needs promotion).
- data/analysis/cases/0002.json: same, plus add the missing
  metadata block (closes Review P2-9).
- data/analysis/cases/sample_playground.json: also promoted to
  V3 for consistency.
- A small Python helper (scripts/migrations/v2_to_v3.py) is
  added to document the conversion. It is runnable and
  idempotent. Future re-analysis of any case can re-emit V3 from
  the Vision prompt directly.

### 3.3 Delete V1 fixture

- examples/output/snow_playground_case.json is deleted. It is
  V1, free-form, and has no relationship to any real project.
  (Closes Review P2-2.)
- examples/output/README.md is updated to point at the new
  canonical location (data/analysis/cases/*.json).

### 3.4 Database design doc update

- docs/database/CaseOS_Database_Schema_V1.md says analysis_json
  follows case_analysis_v3.json (was V2). Closes Review P1-6.

### 3.5 Knowledge retriever V2 fallback

- backend/app/core/knowledge/retriever.py keeps the primary
  path (read V3 ai_analysis wrapper). It also gains a thin
  fallback: if the V3 wrapper is missing, it reads top-level
  vision_summary and design_keywords directly. This is the
  fix for Review P1-1 / Sprint 9 follow-up #1.
- The acceptance test test_decision_intelligence.py is tightened
  to assert that the V2 case in data/analysis/cases/0002.json
  now populates related_cases (not just that the Markdown
  header exists).

---

## 4. Consequences

### Positive

- One canonical schema. Future agents, prompts, and database
  columns all point at the same contract.
- metadata provenance is enforced by the schema, not by hand.
- Cross-case retrieval starts working for the real cases today,
  not in a future Sprint.
- The V1 fixture is gone; the examples/ tree no longer carries a
  misleading demo.

### Negative / Trade-offs

- The two existing real cases are reshaped by hand. This is a
  one-time data cleanup; future cases are produced V3-shape by
  the analyzer.
- V2 JSON file is kept for one release. A future Sprint must
  delete it. (Tracked.)
- The Python conversion helper scripts/migrations/v2_to_v3.py
  is a fixture for one case. It is NOT a general-purpose ETL.

### Neutral

- The Vision prompt is unchanged. The Vision Factory is unchanged.
- The Decision Engine and Product Layer are unchanged.
- Existing 22 tests are preserved; one test is tightened.

---

## 5. Acceptance criteria

- [x] V3 declared canonical.
- [x] V2 JSON file annotated as deprecated.
- [x] All real cases reshaped to V3 with metadata block.
- [x] V1 fixture deleted; examples/output/README.md updated.
- [x] Database design doc updated to V3.
- [x] Knowledge retriever falls back to top-level V2 fields when
  ai_analysis is absent.
- [x] Acceptance test tightened; 22 / 22 tests still green.

---

## 6. References

- schemas/case_analysis_v2.json (deprecated by this ADR).
- schemas/case_analysis_v3.json (canonical after this ADR).
- ADR-005 -- Decision Intelligence Architecture (downstream
  consumer of Vision JSON).
- backend/app/core/knowledge/retriever.py -- the consumer this
  ADR fixes (P1-1).
- System Review 2026-07-30 -- P0-3, P1-1, P1-6, P2-2, P2-9.
