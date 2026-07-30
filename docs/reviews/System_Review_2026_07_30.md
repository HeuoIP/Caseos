# CaseOS System Review -- 2026-07-30

- **Reviewer:** Codex (architecture review pass)
- **Date:** 2026-07-30
- **Repo:** HeuoIP/Caseos @ 0417f50
- **Scope:** full system. Code, knowledge, documentation, schemas,
  contracts, ADRs, sprint records.
- **Constraint:** Review only. No code change. No doc change.
  All findings are pointers; each one needs its own ADR or Sprint
  task before it can be fixed.

---

## 0. Executive Summary

The CaseOS repo has shipped six accepted layers (Vision Engine,
Knowledge Library, Agent Framework, Product Layer, Decision
Intelligence, Constitution + Decision Principles) and one
blueprint (Product Blueprint V1) in the last 10 days. 22 / 22 tests
are green. The product pivot from AI Playground Design Assistant to
AI Space Advisor has been correctly carried into ADR-005, ADR-006,
ADR-007, and the Constitution.

However, the pivot is only half-carried. Many of the older V1-era
artifacts still describe the playground-only product, and several
contracts have drifted in incompatible ways. There is no
enforcement of the Constitution principles at code level. The
blueprint product surface has no API, no main.py, no Dockerfile.

The system is healthy enough to keep building on. The findings
below are categorised P0 / P1 / P2. P0 items block the credibility
of the system documentation and contracts. P1 items are design
inconsistencies that will become expensive soon. P2 items are
hygiene and quality.

Counts:

- **P0 (must fix before the next user-facing release):** 7 items.
- **P1 (should fix in the next 1-2 sprints):** 12 items.
- **P2 (clean-up, no rush):** 11 items.

---

## 1. P0 -- Must fix

### P0-1. V1-era product doc still references playground

docs/architecture/Product.md still says
AI-powered playground case engine with 5 playground-only V1
features and a playground-only Future list (施工图 / 预算 /
工程量 / CAD / AI 视频 / 自动营销). It contradicts ADR-006
(Project Fit, generic) and the Constitution fit-not-beauty stance.
The doc was not retired when the Blueprint V1 was written.

- **Fix path:** either delete the old file and let Blueprint V1
  inherit the role, or rename it to
  CaseOS_Product_V1_OBSOLETE.md with a one-line deprecation
  banner pointing at Blueprint V1.
- **ADR needed:** no (cosmetic move).

### P0-2. ADR-006 has been Proposed for two days, never Accepted

ADR-006 status field is still Proposed. Sprint 9 Review Checklist
notes that ADR-006 has 6 acceptance criteria. Nothing in the repo
has moved it to Accepted or Rejected. Per ADR convention the doc
should be either Accepted, Rejected, or have an explicit
on-hold-until-ADR-008 addendum.

- **Fix path:** either accept it (it has been reviewed and the v2
  generalisation addressed the major feedback), or split it into a
  smaller Accepted piece (the input model + output model) and a
  larger Proposed piece (the future Project Intelligence Layer).
- **ADR needed:** yes (amendment).

### P0-3. Three different Vision output shapes co-exist

The repo has three different Vision output shapes in use at the
same time:

1. schemas/case_analysis_v2.json -- nested, has design /
   target_users / play_experience / etc.
2. schemas/case_analysis_v3.json -- nested, has the same plus a
   metadata block; used by the prompt and the analyzer.
3. Real analysis files in data/analysis/cases/0001.json and
   0002.json -- flat, with top-level project_name,
   vision_summary, design_interpretation, no ai_analysis
   wrapper. They look like V2 in spirit but not in shape.
4. examples/output/snow_playground_case.json -- even older V1
   shape with a description field and free-form age_group like 3-5 years.

The case retriever in Sprint 9 only reads ai_analysis.keywords /
ai_analysis.vision_summary, so it returns empty on the real flat
V2 cases. This is follow-up #1 from the Sprint 9 Review Checklist.
It is still open.

- **Fix path:**
  1. Decide whether V2 (flat) or V3 (nested) is canonical. The
     fact that the real cases on disk are flat suggests V2 is the
     de-facto format.
  2. If V2 is canonical, delete v3.json and rewrite the prompt to
     produce flat output. If V3 is canonical, re-analyse all
     cases to V3 shape and update the case retriever to read
     either.
  3. Delete the V1 snow playground case from examples/output/.
- **ADR needed:** yes (schema decision; affects prompt, analyzer,
  retriever, database, blueprint).

### P0-4. docs/architecture/Architecture.md is a 7-line ASCII sketch

It reads:

    Input -> Vision AI -> Case Schema -> Database -> Vector Search
           -> LLM -> Proposal -> PDF

This contradicts the actual 6-stage Agent pipeline
(space -> decision_maker -> knowledge_retriever -> strategy
-> object_selector -> explain) and the 10-step Blueprint V1 user
journey. It also references a Case Schema node that no longer
exists (it is now an Output Schema, not a stage), and a
Vector Search node that Sprint 9 explicitly deferred (Constitution
says structured knowledge is the foundation, not vector). A new
contributor reading this file first will be misled.

- **Fix path:** rewrite Architecture.md as a pointer to ADR-005 /
  Blueprint V1 / Pipeline diagrams. Do not keep a separate ASCII
  flow that contradicts both.
- **ADR needed:** no (documentation only).

### P0-5. Constitution is not enforced anywhere in code

The Constitution V1 says:

    Every Agent, Knowledge Module, and Decision Engine in the
    codebase is bound by the Constitution.

There is no test, no decorator, no lint that verifies any agent
follows the four Founding Principles or the four Decision
Principles. A new agent added tomorrow could violate the
Constitution and no CI signal would fire.

- **Fix path:** add a tests/test_constitution_compliance.py that
  asserts, for every agent class registered:
  - has a name and display_name (Principle: speakable);
  - has a docstring that names the principles it implements;
  - for the Explain agent, the explanation template does not
    contain the forbidden marketing words (already partially
    tested in test_decision_intelligence.py);
  - for the Object Selector, recommendations cap at 5 (Principle:
    small set beats long list).
- **ADR needed:** no (test code).

### P0-6. ADR-007 / Decision Principles not cited from existing ADRs

ADR-005 (Accepted) was written before ADR-007. Its acceptance
criteria and Consequences do not mention the Constitution or the
Decision Principles. ADR-006 (Proposed) was written in parallel
with the Constitution; its reference list does not yet cite the
Constitution (it predates the Constitution ratification).

Net effect: a reader can follow ADR-005 and produce code that
silently violates the Constitution.

- **Fix path:** add a one-paragraph cross-reference at the top of
  ADR-005 Consequences section pointing at
  CaseOS_Constitution_V1.md and the four Decision Principles. The
  ADR is Accepted, so the change should be an editorial amendment
  (not a re-vote), per the Constitution amendment procedure
  (no silent edits). A short ADR-005a amendment ADR is appropriate.
- **ADR needed:** yes (amendment).

### P0-7. Product Blueprint V1 has no API surface

The Blueprint V1 promises a user journey that ends in
Implementation Suggestions, but there is no FastAPI endpoint that
takes the Blueprint V1 input model (Goal + Space + Project Type +
Optional Info) and returns the Blueprint V1 output model (Diagnosis
+ Direction + Contents + Why + Suggestions).

backend/app/main.py does not exist (or is a stub). The Product
Layer built in Sprint 8 has the engine; the engine is reachable
only from Python, not from a client.

- **Fix path:** add a thin FastAPI surface in a future Sprint:
  POST /v1/recommend (multipart image + JSON body),
  GET /v1/health, GET /v1/version. All endpoints return the
  same ProductResponse shape the product layer already produces.
  No new pipeline; no new agent.
- **ADR needed:** yes (API contract, request / response schema,
  idempotency, error model).

---

## 2. P1 -- Should fix in the next 1-2 sprints

### P1-1. Sprint 9 follow-up #1 is still open

Case retriever V2 compatibility. Tracked since 2026-07-30. The
acceptance test for the V2 case is misleading because it asserts
only that the Markdown report contains ## Retrieved Knowledge (which
it does), not that the related_cases list is populated. The test
should be tightened at the same time as the fix.
- **Fix path:** see P0-3 above.

### P1-2. Sprint 9 follow-up #2 is still open (LLM swap-in)

StrategyAgent._build_analysis and ExplainAgent._select_template
are template renderers, not real LLM calls. The contract is already
there; the LLM side is a stub. Tracked since 2026-07-30.
- **Fix path:** new Sprint, real LLM call, same schema. Test for
  that the LLM-side renderer can be swapped without changing the
  agent interface.

### P1-3. Vision Standard V1 has 24 mostly-empty sections

docs/standards/CaseOS_Vision_Standard_V1.md lists 24 sections.
Only the first 4 sections have real content (Sections 1, 2, 3, and
4.1). Sections 5 through 24 are placeholder headers. This is a
standard, and a standard with empty sections gives the wrong
impression of completeness.
- **Fix path:** either fill the empty sections with the actual
  rules (most can be lifted from the existing knowledge files), or
  remove the placeholder headers and add a Future sections list at
  the bottom.

### P1-4. Prompt Principles has no link to Decision Principles

docs/knowledge/Prompt_Principles.md lists 10 hard rules. The
Decision Principles document lists 4. The relationship is not
spelled out. Constitution Principle 001 (suitable, not most) is not
mentioned in the Prompt Principles. The 10 prompt rules look like
a separate code of conduct, not a specialisation of the
Constitution.
- **Fix path:** prepend a one-paragraph preamble to
  Prompt_Principles.md that says these 10 rules are the
  constitution prompt-level operationalisation, and that the
  Decision Principles outrank them when they conflict.

### P1-5. ADR-006 + ADR-007 not cited from Blueprint V1

docs/product/CaseOS_Product_Blueprint_V1.md cites Constitution and
Decision Principles. It does not cite ADR-006 by name (it
mentions Project Fit in passing), nor does it cite ADR-007 (the
Constitution ADR). This is a paper trail gap.
- **Fix path:** add a one-line citation block to the References
  section of Blueprint V1.

### P1-6. Database design doc still references v2 schema

docs/database/CaseOS_Database_Schema_V1.md says analysis_json
follows schemas/case_analysis_v2.json, but the runtime is on V3
(per the Vision Factory). If the database is ever built, it will
store V2-shape data while the analyzer produces V3-shape data.
Drift.
- **Fix path:** tied to P0-3.

### P1-7. Ontology name is locked to playground

docs/knowledge/Playground_Ontology_V1.md is the only case-facing
ontology doc. ADR-006 generalises the product beyond playground
(Space Advisor for any industry). The file name
Playground_Ontology_V1 is a blocker for the generic story, even if
the content can be lifted into a more generic ontology.
- **Fix path:** either keep the playground ontology as a domain
  pack (and rename the doc to
  CaseOS_Playground_Ontology_V1.md so the prefix is consistent), or
  generalise the content into CaseOS_Space_Ontology_V1.md and keep
  the playground subset as a domain pack under
  knowledge/domain_packs/playground/.
- **ADR needed:** yes (domain pack model).

### P1-8. Constitution Principle 004 needs a runtime check

Amplify the strengths of a space. Do not cover up the weaknesses
is not testable in code today. The Object Selector ranks by
served-strategies; it does not check whether the top-N
recommendations cover up a known weakness (e.g. recommending more
climbing equipment in a site that already has too much climbing).
- **Fix path:** a future Space Character Agent (ADR-008 candidate)
  can own this. Until then, document it as a known untested
  principle.

### P1-9. No ADR-001 to ADR-004

docs/architecture/README.md documents the ADR convention but the
first ADR is ADR-005. Either the early decisions (1-4) were never
written, or the numbering is intentional. The current README only
lists ADR-005 in its Active ADRs section. ADR-006 and ADR-007 are
missing from the list. The README is stale.
- **Fix path:** either accept the numbering gap and document why,
  or renumber the existing ADRs to fill the gap. The list in
  docs/architecture/README.md should be updated regardless.

### P1-10. No async / job model for long-running analysis

The Blueprint V1 says image -> recommendation in V1. The Vision
Engine call is synchronous and can take seconds. The Product Flow
is synchronous. A future Web UI cannot poll for a finished
recommendation. The blueprint anticipates this in V2 multi-space
planning, but the V1 plumbing is missing.
- **Fix path:** add a job-id model to the future API (P0-7) and a
  simple in-memory job queue for V1.

### P1-11. No Dockerfile / container spec

docs/architecture/TechStack.md lists Docker as the deployment
option. There is no backend/Dockerfile, no docker-compose.yml, no
environment file committed, no example .env outside the backend
folder. The self-host story is in the Blueprint but not in the
repo.
- **Fix path:** add a minimal backend/Dockerfile (Python 3.12
  slim, install requirements, expose 8000) and a top-level
  docker-compose.yml for the dev setup.

### P1-12. No CI configuration

There is no .github/workflows/, no pre-commit, no lint. The 22
tests are green today because a human ran them. A bad commit can
break the build without anyone noticing.
- **Fix path:** add a ci.yml that runs pytest backend/tests/ -q
  and a ruff config for Python lint. Cheap to set up.

---

## 3. P2 -- Clean-up, no rush

### P2-1. docs/sprints/theme_extension_log.md is in the wrong folder

It is a knowledge / taxonomy extension log, not a sprint record.
It should move to docs/knowledge/ or to knowledge/taxonomy/ with a
link from a future Sprint if it was done in one.

### P2-2. examples/output/snow_playground_case.json is V1

It uses V1 shape (free-form age_group like 3-5 years, no stable
IDs, a description field instead of vision_summary /
design_interpretation). Either delete it or mark it as PLACEHOLDER
+ bump to V3 shape so it does not mislead a future reader.

### P2-3. docs/architecture/TechStack.md still lists MiniMax M3 as the LLM

This was a V1 decision. The LLM is not yet integrated. Either
update the file to reflect the current Qwen for vision + Qwen or
MiniMax for text state, or annotate that this is a future
selection.

### P2-4. TechStack LLM should be picked at implementation time

The Decision Principles document does not name an LLM. TechStack
naming one is fine, but the V1 stack should be specific: which
provider, which model, which prompt language. A single source of
truth would be the V1 inference config (future).

### P2-5. Architecture.md ASCII conflicts with the real pipeline

Already covered under P0-4, but listed here because the file is
the most visible bit of stale content in the repo.

### P2-6. No language / locale policy for docs and data

Root README and most docs are in English. ADR-006 / Blueprint V1
mix English and Chinese. Case analysis JSON has a Chinese
project_name (日晕乐园). The Vision prompt is in English. The
Explain agent template is in English. There is no ADR that says
which surface is in which language. Likely fine for V1, but the
policy should exist before V2 (Web UI in which language?).

### P2-7. Knowledge files do not have an explicit version field

knowledge/taxonomy/theme/Forest.md does not declare a
schema_version. A change to the file is invisible to the
Constitution amendment procedure. Cheap fix: add a
schema_version: V1 header to every knowledge file.

### P2-8. docs/knowledge/ overlaps with knowledge/

docs/knowledge/ currently has Playground_Ontology_V1.md and
Prompt_Principles.md, which are rules about knowledge (meta). The
actual knowledge lives in knowledge/. The naming is easy to
misread. Either rename docs/knowledge/ to docs/meta_knowledge/ or
move the meta files into knowledge/META/.

### P2-9. data/analysis/cases/0001.json and 0002.json lack metadata

The Sprint 9 metadata contract is model / vision_standard /
output_schema / analyzed_at. 0001 has it, 0002 does not. Even
within the same hand-curated batch the metadata is inconsistent.
- **Fix path:** small re-analysis batch in a future sprint.

### P2-10. docs/architecture/Product.md is not in the docs map

docs/README.md folder map does not list architecture/Product.md
even though the file exists and is the de-facto product V1 doc.
It also does not list product/CaseOS_Product_Blueprint_V1.md. The
folder map is stale.

### P2-11. The Architecture_Review_2026_07 follow-ups are not closed in any later doc

docs/reviews/Architecture_Review_2026_07.md lists P0 / P1 / P2
recommendations from the playground->Space Advisor pivot. None of
those recommendations are explicitly closed in any later ADR or
sprint. A future reviewer cannot tell which ones are still open.
- **Fix path:** turn the 2026-07 review into a tri-state list
  (Open / In Progress / Closed) and update it in a future review
  pass.

---

## 4. Cross-cutting recommendations

Three themes cut across the findings above.

### 4.1 The product pivot is only half-carried

ADR-006 + ADR-007 + Blueprint V1 + Space Character Dataset are the
new layer. The old V1 layer (Product.md / Architecture.md /
TechStack.md / Theme extension log / snow case JSON / 7-line
architecture sketch / playground-only ontology) is still visible
from the repo root. Every P0 item except P0-5 and P0-7 is a
leftover from the pivot. A pivot cleanup sprint would close all of
them.

### 4.2 The Constitution has no enforcement

A philosophy with no enforcement is a suggestion. P0-5 + P1-8 +
P1-4 are all about turning the Constitution principles into testable
contracts. The Constitution amendment procedure says no silent
edits; the same rule should apply to the principles themselves:
they must be either enforced by a test, or honestly listed as
un-tested in the doc.

### 4.3 The product surface (API, UI, container) is missing

The Blueprint V1 is a user-journey spec for a future Web UI. The
Web UI itself is V2. But the V1 plumbing underneath the Web UI
(FastAPI, main.py, Dockerfile, .env.example, error model,
idempotency) is also missing. The minimum viable product is
therefore blocked by both the surface layer and the contract
layer. A single Sprint focused on the API + container could close
P0-7, P1-10, P1-11 at once.

---

## 5. Suggested Sprint / ADR ordering

To close the highest-leverage findings in a sensible order:

1. ADR-005a (amendment): cite Constitution + Decision Principles
   from ADR-005. Closes P0-6.
2. ADR-006a (status change): move ADR-006 to Accepted, with the
   clause that Project Intelligence Layer Agents come under future
   ADRs. Closes P0-2.
3. ADR-008 (Vision Output Schema V2 vs V3): the most
   consequential open decision. Closes P0-3 + P1-1 + P1-6 + P1-9.
4. Sprint 12 (Pivot Cleanup): doc edits only. Closes P0-1, P0-4,
   P1-3, P1-4, P1-5, P2-1, P2-2, P2-3, P2-5, P2-7, P2-8, P2-10.
5. Sprint 13 (API + Container V1): FastAPI surface, main.py,
   Dockerfile, error model, idempotency. Closes P0-7, P1-10,
   P1-11, P1-12.
6. Sprint 14 (Constitution Compliance Tests): add
   test_constitution_compliance.py. Closes P0-5, P1-8.
7. Sprint 15 (LLM swap-in): replace the strategy / explain
   template renderers with real Qwen / MiniMax calls. Closes P1-2.
8. Sprint 16 (Space Character Dataset seed): first real
   dataset/*.yaml from the 0001 / 0002 cases. Closes the open
   item from Sprint 10.5.

After Sprint 16, a second system review (this one sibling) is
appropriate.

---

## 6. References

- docs/reviews/Architecture_Review_2026_07.md -- the earlier
  review that motivated the playground -> Space Advisor pivot.
- ADR-005 / ADR-006 / ADR-007 -- the three architectural decisions
  taken after that review.
- CaseOS_Constitution_V1.md / CaseOS_Decision_Principles_V1.md --
  the highest-level philosophy and implementation guide.
- CaseOS_Product_Blueprint_V1.md -- the user-journey spec for the
  next product layer.
- Sprint 9 Review Checklist -- the follow-ups (#1, #2) referenced
  in this review.
