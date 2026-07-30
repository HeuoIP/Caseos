# AR-001 -- CaseOS Architecture Review V1

- **Reviewer:** Codex architecture review pass
- **Date:** 2026-07-30
- **Reviewed commit:** `5a0f6ad` (Sprint 18 -- Golden Case Intelligence Pipeline V1) plus parent chain
- **Scope:** all layers, all ADRs, all Sprints, knowledge contract
- **Constraint:** Inspection only. No code change. No doc change. Every recommendation is a pointer for a future ADR or Sprint.
- **Related:** `docs/reviews/System_Review_2026_07_30.md` -- the 30-finding sibling review against `0417f50` (pre-Sprint 14). This AR-001 is the post-Sprint 18 counterpart.

---

## 0. Executive Summary

CaseOS has grown from a docs-only project (System_Review snapshot at `0417f50`) into a system with **complete knowledge foundation, a complete agent framework, a complete product layer, and a complete case intelligence pipeline**. 37 / 37 tests are green; the architecture is internally consistent; the pivot from "playground design assistant" to "AI Space Advisor" is correctly carried through seven Accepted ADRs (005, 005a, 006, 006a, 008, 009, 011, 012).

But the system is **five-times disconnected**. Five distinct loops were built in isolation; only two are wired to a runtime. Three are knowledge assets that no engine consumes. Two sprint-deliveries are completed-but-unused. The product surface (FastAPI / CLI / UI) has no entry into any of these loops except the existing product-flow entry point, which itself has not been promoted to an API route.

This review identifies 8 closed loops, 5 partial loops, 3 isolated modules, 2 orphan ADRs, 1 conflicting ADR draft, and 5 empty placeholder directories that suggest intended functionality that has never been started.

**Headline finding:** the system has shipped its **knowledge phase** (Phase 1). It has not yet shipped its **decision phase** (Phase 2). The Phase 2 spark is the question "given a user-uploaded photo, what should this space contain?"; that question has no production answer today, only three demonstration paths (Product Flow, Decision Intelligence, Case Intelligence Pipeline) that each answer it differently and unconnectedly.

---


## 1. Architecture Map

The current CaseOS repository has FIVE logical layers. Each layer contains modules that are independently complete or complete-with-partial-integration. The map below classifies modules into LOOP (closed runtime), KNOWLEDGE (assets with no consumer), PROTOTYPE (code that has never been invoked), ISOLATED (code or knowledge that has no consumer and no path to one), or EMPTY (placeholder directory created by an ADR that has not been started).

```mermaid
flowchart TB
    subgraph CHROME[chrome surface]
        Main["app/main.py<br/>Swagger UI / /health"]
        Api["app/api/<br/>(EMPTY: __init__.py only)"]
        Core["backend + tests<br/>37 passing"]
    end

    subgraph L3 [Layer 3 -- Case Intelligence (Sprint 18)]
        CIp["GoldenCasePipeline<br/>image -> CKO draft"]
        CIe["CaseEvaluator (ADR-012)"]
        CIr["CaseReviewer"]
        CIs["CKO V1.2 schema"]
    end

    subgraph L2 [Layer 2 -- Decision]
        Engine["DecisionEngine"]
        Pipeline["Default Pipeline"]
        Agents["6 Agents"]
        KB["KnowledgeRetriever"]
        Reco["MarkdownGenerator"]
    end

    subgraph L1 [Layer 1 -- Product]
        PF["ProductFlow"]
        Session["Session"]
        Workflow["Workflow"]
    end

    subgraph L0 [Layer 0 -- Vision]
        Vision["VisionEngine V3"]
        Validator["CKO Validator"]
        Storage["data/"]
    end

    subgraph KN [Knowledge Layer]
        K1["Brain (ADR-009)"]
        K2["Decision Rules (ADR-010)"]
        K3["Decision Model"]
        K4["CKO Library V1.2"]
        K5["Expert Handbook"]
        K6["Taxonomy"]
        K7["Objects / Goals / Reasoning"]
        K8["Space Character Skeleton"]
    end

    Main --> Vision
    PF --> Vision
    PF --> Engine
    PF --> Reco
    CIp --> Vision
    CIp --> CIe
    CIp --> CIr
    Validator -.validates.-> Vision
    Engine --> Agents
    Agents --> KB
    KB -.reads.-> K1
    KB -.reads.-> K2
    K1 -.consumer.-> Engine
    K2 -.consumer.-> Engine
    K4 -.consumer.-> CIp

    classDef loop fill:#c8e6c9,stroke:#2e7d32
    classDef empty fill:#ffcdd2,stroke:#b71c1c
    class Vision,Validator,Storage,Engine,Agents,KB,Reco,PF,Session,Workflow,CIp,CIe,CIr loop
    class Api empty
```

**Reading the map:** most arrows are dashed. Solid arrows are the two end-to-end paths that actually run today:

1. `main.py -> Vision` (the swagger demo at `/docs`)
2. `ProductFlow -> Vision -> DecisionEngine -> Recommend` (the fastest user journey)

Everything else that looks connected (Brain, Decision Rules, CKO, Golden Case Pipeline) is a knowledge asset or a standalone module that is invoked only by tests.

---


## 2. Closed Loop Analysis

Per-module status. Status legend:

- **Complete (loop):** wired to runtime + tests pass + used by callers.
- **Mostly Complete (loop):** wired but with a documented gap (e.g., LLM step stubbed).
- **Partial (proto):** code exists, has tests, but has no production caller.
- **Prototype:** code exists and demonstrably runs via tests, but does not integrate with anything else.
- **Isolated:** assets (knowledge or placeholder) with no consumer or path to one.

### 2.1 Runtime modules

| Module | Status | Evidence | Comment |
| --- | --- | --- | --- |
| Vision Engine (V3 + qwen) | Complete | `app/services/vision/`, used by both ProductFlow and GoldenCasePipeline | Real provider exists but only one (qwen); no second provider on disk. |
| Vision JSON Schema (ADR-008) | Complete | `schemas/case_analysis_v3.json` | Canonical V3.1 with metadata wrapper. |
| CKO Validator | Mostly Complete | `app/services/validator/validator.py` (13.6 KB) | Runs against the analysis JSON written by the vision pipeline. Not yet called by the GoldenCasePipeline. |
| Decision Engine | Complete | `app/core/decision/engine.py` + 5 agent tests passing | Default 7-agent pipeline; Explain agent + MarkdownGenerator present. |
| Knowledge Retriever | Mostly Complete | `app/core/knowledge/`, 9 KB | Reads from `knowledge/` folder at runtime; covers decision_model + Brain + a sliver of cases. **Does NOT yet read CKO, Decision Rules, Expert Handbook at the level they are written**. |
| 6 Agents | Complete | `app/core/agents/` (8 files) | All registered in `AgentRegistry`; all wired into default pipeline. |
| Recommendation (markdown) | Complete | `app/core/recommendation/markdown_generator.py` | Produces the customer-facing report. |
| Product Flow | Mostly Complete | `app/core/product/` (6 files) | End-to-end fake-image pipeline; supports primary goal selection; status tracking. **Has no FastAPI router** (Section 6.2). |
| Session / Request / Response | Complete | `app/core/product/` | Loop tracking per-stage; used only by tests today. |
| Golden Case Pipeline | Prototype | `app/core/case_intelligence/` (7 files, 15 tests pass) | Implements Stages 1-6 end-to-end. **No caller in main.py or in any other module**. Has no integration test against a real image. |
| CaseEvaluator | Complete (within Pipeline) | `evaluator.py` | Enforces ADR-012 ranges, total = sum, transferability complete. |
| CaseReviewer | Complete (within Pipeline) | `reviewer.py` | DRAFT -> REVIEWING -> APPROVED/REJECTED with audit log. |

### 2.2 Knowledge assets

| Module | Files | Status | Consumer (real) |
| --- | --- | --- | --- |
| Brain (ADR-009, 9 modules) | 32 | Partial | None at the level Brain describes. Constitution/Decision/ProjectFit/SpaceCognition/Experience/Diagnosis/Strategy/ThemeStrategy/Recommendation each have READMEs but the DecisionEngine only reads Cognition + Diagnosis from them. |
| Decision Rules (ADR-010, 8 rules) | 9 (1 README + 8) | Isolated | None. The 17 rules live in `knowledge/brain/decision_rules/`; the engine does not load them. The two folders compete. |
| Decision Model (Sprint 15) | 10 | Partial | Decision Engine reads Context_Model.md and Strategy_Model.md structure (via `decision/knowledge.py`). Does not consume Constitution sub-folder. |
| CKO Library (V1.2) | 8 (schema + 5 taxonomies + example) | Isolated | Validator can validate an analysis JSON; the GoldenCasePipeline COULD emit one but does not call Validator. |
| Expert Handbook (10 docs) | 11 | Isolated | Referenced by agents' design_principles strings; not loaded as structured knowledge. |
| Taxonomy (8 sub-trees, 116 files) | 116 | Partial | Vision Engine loads stable IDs at runtime; Decision Engine does not read taxonomies at the same fidelity. Color / Material / Functional Unit / Play Behavior / Theme are externally-facing; Age Group, Style, Site Type are referenced only in pilot flows. |
| Objects Library | 6 | Isolated | ObjectSelectorAgent references by string id; no structural load. |
| Goals Library | 19 | Isolated | KnowledgeRetriever and ProductFlow reference by string; no structural load. |
| Strategies Library | 20 | Isolated | StrategyAgent uses Strategy families conceptually; not loaded. |
| Reasoning Library | 16 | Isolated | Not used by any agent. |
| Design Principles (DP-001/002/003) | 4 | Mostly Complete | CKO and Brain reference by name; Constitution outranks; no code enforcement. |
| Space Character Dataset (Sprint 10.5) | 5 (skeleton) | Isolated | 1 README + templates + examples folders, no pipeline. |
| Sprint 16 Level_1_Space_Cognition | 5 (OBSOLETE) | DEPRECATED | Marked OBSOLETE 2026-07-30 by Sprint 17 / ADR-009. |

### 2.3 Empty placeholders

| Path | Status | Created by | Reason for empty |
| --- | --- | --- | --- |
| `backend/app/api/` | EMPTY (__init__.py only) | FastAPI skeleton (Sprint 0) | No routes.py; no router declared in main.py. |
| `backend/app/models/` | EMPTY (__init__.py only) | FastAPI skeleton | No Pydantic models anywhere in repo; `app/schemas/` empty. |
| `backend/app/schemas/` | EMPTY (__init__.py only) | FastAPI skeleton | Decision Engine and Vision Engine use plain dataclasses; Pydantic was never adopted. |
| `backend/app/utils/` | EMPTY (__init__.py only) | FastAPI skeleton | No shared utilities extracted. |
| `knowledge/decision_rules/` | EMPTY of content (1 README) | ADR-010 | Rules live in `knowledge/brain/decision_rules/` instead (see ADR-010 vs. ADR-009 conflict below). |
| `knowledge/governance_decisions/` | MISSING | -- | Replaced by ADR naming. |
| `knowledge/library/` | MISSING | -- | Reserved for Golden Case sub-library; never created. |

**Six of the seven empty placeholders trace to the original Sprint 0 FastAPI skeleton, which committed the directories but no files. The seventh (`decision_rules`) is a more recent conflict.**

---

## 3. ADR Traceability

### 3.1 ADR inventory

| ADR | Number | Purpose | Status | Implemented Modules | Depends on |
| --- | --- | --- | --- | --- | --- |
| Decision Intelligence | ADR-005 | Reasoning pipeline architecture (8 sections) | Accepted (amended by ADR-005a) | `core/decision/`, `core/agents/`, `core/recommendation/` | ADR-007 (Constitution) |
| DI Constitution cross-ref | ADR-005a | Ties ADR-005 to ADR-007 | Accepted | (link only) | ADR-005, ADR-007 |
| Project Fit Intelligence | ADR-006 | Risk-first 5-dimension context | Accepted (recorded by ADR-006a) | `decision/knowledge.py` (partial) | ADR-005 |
| Project Fit Acceptance | ADR-006a | Updates dim to 5 and aliases Investor | Accepted | (link only) | ADR-006 |
| Vision Output Schema Canonical V3 | ADR-008 | V2 -> V3 (theme array, metadata, vision_summary / design_interpretation split) | Accepted | `schemas/case_analysis_v3.json`, `vision/analyzer.py` | -- |
| Brain Knowledge Architecture | ADR-009 | 9-module Brain + 6-section template | Accepted | `knowledge/brain/` (32 files) | ADR-007 |
| Decision Rules Framework | ADR-010 | IF/THEN/BECAUSE/DO/UNLESS rules + 9-section template + 8 initial rules | **Proposed** (still marked Proposed despite 17 rules existing on disk) | `knowledge/brain/decision_rules/` (17 files, NOT ADR-010 intended path) | ADR-009 |
| CKO Learning Source & Value Model | ADR-011 | Add `knowledge_source` + `learning_value` 5-axis | Accepted | `knowledge/cases/` (V1.1) | -- |
| Case Evaluation Score | ADR-012 | 100-point weighted + transferability + Golden threshold | Accepted | `knowledge/cases/` (V1.2), `case_intelligence/evaluator.py` | ADR-011 |

**Total:** 9 ADRs, 8 Accepted, 1 Proposed (ADR-010).

### 3.2 Issues found in the ADR set

1. **ADR-010 is structurally orphaned.**
   - The ADR mandates the rule family folders live at `knowledge/brain/decision_rules/`.
   - The implementation however placed rules at `knowledge/decision_rules/` (a different folder) -- see the "create: knowledge/brain/decision_rules/" line vs. ADR-009's section "Layer Position" diagram. This is the conflict that created the two `decision_rules/` folders in the tree.
   - Additionally, ADR-010 still says **Status: Proposed** even though 17 rules have been committed (8 of which are the initial set the ADR itself defined). The ADR should be migrated to Accepted when 8+ rules ship.

2. **Conflict between ADR-009 and ADR-010.** ADR-009 places Decision Rules between Brain modules and Decision Engine ("layer 2 of 5"); ADR-010 places them between Rules and Decisions Engine. The diagrams agree on the position, but the actual file locations disagree (`knowledge/brain/decision_rules/` vs. `knowledge/decision_rules/`). The commit history shows the implementation chose `brain/decision_rules/` for everything. **That means ADR-010 was technically violated by the implementation it caused.**

3. **ADR-006 superseded but the rules not migrated.** ADR-006 introduced 5 dimensions (Space / Investor / Goal / Market / Resource). ADR-006a updated them. The 17 brain decision_rules files appear not to encode any Project Fit rule with the canonical 5 dimensions. `PF-001.md` covers one facet ("Design cannot replace operation capability") but `client_goal / project_background / site_condition / budget / operation_capability / market` -- the canonical Project Fit fields -- are not encoded as rules anywhere visible.

4. **Three ADRs are not anchored to a runtime module.** ADR-009, ADR-011, ADR-012 ship knowledge assets but no engine consumes them. They will look "isolated" until a downstream Sprint (Vision -> Brain, Case -> Decision, etc.) wires them in.

5. **ADR-007 (Constitution V1) is referenced by every later ADR but has no file with that number.** The Constitution lives at `docs/standards/CaseOS_Constitution_V1.md` and was implemented directly. ADR-007 is therefore a *referenced-but-not-published* ADR number. (Earlier reviewer noted this as a known gap.)

### 3.3 Completed-but-orphan ADRs (none)

No ADR exists whose stated implementation is completely missing. ADR-010's status should be elevated from Proposed to Accepted to reflect the 17 rules committed at `brain/decision_rules/`.

---


## 4. Sprint Traceability

### 4.1 Sprint inventory (last 6 weeks)

| Sprint | Commit | Headline | Delivered Modules | Real Consumers Today |
| --- | --- | --- | --- | --- |
| Sprint 7 | `c71dbe0` | CaseOS Agent Framework V1 | `app/core/agents/` (8 files, 6 agents, registry) | Decision Engine + tests |
| Sprint 8 | `96e268d` | CaseOS Product Layer | `app/core/product/` (6 files) | Tests only; **no API route** |
| Sprint 9 | `346f9b3` | Decision Intelligence V1 | `app/core/decision/`, `app/core/knowledge/`, `app/core/recommendation/`, KnowledgeRetriever agent | ProductFlow + tests |
| Sprint 10.5 | `1e3ce7d` | Space Character Dataset skeleton | `knowledge/space_character/` (5 files) | **None** |
| Sprint 11 | `0417f50` | CaseOS Product Blueprint V1 | `docs/product/CaseOS_Product_Blueprint_V1.md` | Documentation only |
| Sprint 12 | `3009f3e` / `d356cb3` | Pivot Cleanup (doc-only) | cleaned 1 obsolete product doc; archived PlaceOS history | Documentation only |
| Sprint 14 series | `cf2a530`, `2db281f`, `5143c5c`, `58cd626` | Design Principles V1 + 3-section template | `knowledge/principles/` (DP-001/002/003) + README | Citations only; no engine enforcement |
| Sprint 15 | `526ac45` | Decision Model V1 | `knowledge/decision_model/` (5 docs + Constitution/) | Decision Engine `knowledge.py` |
| Sprint 16 | `095b9ec` | Brain Level 1 (Space Cognition experimental) | `knowledge/brain/Level_1_Space_Cognition/` | Later superseded; renamed OBSOLETE in Sprint 17 |
| Sprint 17 (Brain) | `ddfa7da` | Brain Knowledge Architecture V1 (ADR-009) | `knowledge/brain/` (9 modules, 32 files) | **None at runtime** -- referenced only by tests |
| Sprint 17 (CKO) | `0acd41d` | Case Knowledge Object (CKO) V1.0 | `knowledge/cases/` (schema + 5 taxonomies + example) | CKO Validator (separate) |
| Sprint 18 (Rules) | `4adb6da` | Decision Rules Framework V1 (ADR-010) | `knowledge/brain/decision_rules/` (8 rules + README) | **None** |
| Sprint 18 (Pipeline) | `5a0f6ad` | Golden Case Intelligence Pipeline V1 | `app/core/case_intelligence/` (7 files, 15 tests pass) | **None -- no caller** |
| Sprint 19 (ADR-011) | `4efacce` | CKO Learning Source & Value Model | `knowledge/cases/` extension to V1.1 | Tied to ADR-011 / 012 consumers (none yet) |
| Sprint 19 (ADR-012) | `d6c4d4d` | Case Evaluation Score | `knowledge/cases/` extension to V1.2 | CaseEvaluator (Sprint 18) |

**Total:** 16 sprint commits in 22 days (5a0f6ad minus c71dbe0).

### 4.2 Findings in the sprint set

#### Completed-but-unused work

These have tests and shipped code but no production caller:

1. **Sprint 18 -- Golden Case Pipeline**: builds the entire bridge image->GoldenCase. Tests pass. No caller in `main.py`. No API. Every other module that handles cases (Validator, Brain, Knowledge Retriever) does not call GoldenCasePipeline. The pipeline is a **freestanding E2E demo with no integration point.**
2. **Sprint 17 -- Brain Knowledge Architecture**: 32 files committed; no engine consumes any Brain module at the depth Brain describes (most agents retrieve by hard-coded string match).
3. **Sprint 18 -- Decision Rules**: 17 rules committed; no engine consumes them. The DecisionRules seed file exists; the runtime IF/THEN matcher does not.
4. **Sprint 8 -- Product Layer**: end-to-end ProductFlow with primary goal injection exists; no API route exposes it; no CLI exists.
5. **Sprint 10.5 -- Space Character Dataset**: directory + templates + examples exist; no consumer (not even a sample entry was generated).

#### Missing follow-up work

1. **No Sprint Task for the Conflict Resolution ADR** between ADR-009's `brain/decision_rules/` and ADR-010's `decision_rules/`. Whichever was decided the right way was never captured in a follow-up ADR.
2. **No Sprint Task for an API/CLI surface.** All sprints build internal modules; Sprint 8's "Product Flow" was supposed to be the surface, but no router was added. The user-facing entry point is `/docs` (swagger for the dead `/health` endpoint).
3. **No Sprint Task for moving Knowledge Retriever to multi-tree (Brain + Cases + Decision Rules + Expert Handbook).** KnowledgeRetriever exists; only one of those four trees is consumed with full fidelity.
4. **No Sprint Task for the Constitution enforcement layer.** Every ADR references Constitution Principle 001..004; nothing in code actually rejects a recommendation that violates them.
5. **No Sprint Task for the Golden Case Library sub-folder.** ADR-011/012 imply a curated library of Candidate/Priority Golden Cases (`knowledge/library/` was reserved). It was never built.
6. **No Sprint Task for backfilling the empty placeholders** (api/, models/, schemas/, utils/, decision_rules/).

#### Disconnected modules

- **`GoldenCasePipeline` is disconnected from Validator.** Both can serialize a CKO; neither calls the other.
- **`Validator` is disconnected from `VisionAnalyzer`.** VisionAnalyzer writes analysis JSON to disk; Validator expects the same shape but is not invoked from the analysis flow.
- **`Brain` modules are disconnected from `DecisionEngine`.** DecisionEngine reads only `knowledge/` index files; the Brain's Section 5 Strategy, Section 6 Recommendation, Section 7 ThemeStrategy modules are described in detail but never loaded.
- **`Space Character Dataset` is disconnected from everything.**

---

## 5. Architecture Risks

### 5.1 Duplicated concepts

1. **Decision Rules lives in two places**: `knowledge/decision_rules/` (ADR-010's intended path, currently README only) and `knowledge/brain/decision_rules/` (where 17 rules actually live). The two locations are competing and the conflict is undocumented.
2. **Two CKO evaluators exist independently**: `knowledge/cases/schema` carries the V1.2 contract and `case_intelligence/evaluator.py` re-implements it in Python; `services/validator/validator.py` is yet a third implementation that targets the analysis JSON. The schema and the validators have drifted (e.g., learning_value floats are not yet enforced by Validator).
3. **Two product surfaces both called "Product"**:
   - The Sprint 8 ProductFlow (5 stages, primary-goal-aware) with a defined Sprint_08_Product_Layer.md spec.
   - The Sprint 11 Product Blueprint V1 (markdown-only).
   - These align on intent but the Sprint 11 doc describes API inputs that Sprint 8's code does not expose.
4. **Two Constitution artifacts**:
   - `docs/standards/CaseOS_Constitution_V1.md` is the source of truth.
   - The Brain constitution module is a 1:1 copy with cross-references. Acceptable, but the doc-style pointer implies one source.
5. **Two `review` directories**: `docs/reviews/` (4 files: this AR-001, prior System_Review, ADR-007 cross-ref, etc.) and the older `knowledge/reviews/` location is no longer present but partly migrated.

### 5.2 Unnecessary abstractions

1. **`app/models/` and `app/schemas/` empty directories.** Decision Engine uses plain dataclasses; no Pydantic models have ever been added. These directories should be removed or the data layer should be re-introduced as Pydantic.
2. **`app/utils/` empty.** No shared utilities have ever been extracted. The directory is a marker, not a module.
3. **Two product journey specs (`Product.md` archived vs Product Blueprint V1)**: only the newer is canonical, but the file `docs/architecture/Product.md` referenced in ADR-009 does not exist -- a 30-finding reviewer flagged this. Resolution was via Pivot Cleanup (Sprint 12) renaming `docs/architecture/Product.md` -> `CaseOS_Product_V1_OBSOLETE.md`. The current canonical product spec lives at `docs/product/CaseOS_Product_Blueprint_V1.md`. The naming split between `architecture/` and `product/` is reasonable but the user-facing name needs to be unambiguous.

### 5.3 Circular / forward dependencies

1. **GoldenCasePipeline -> VisionAnalyzer is one-way and safe.**
2. **DecisionEngine -> Agents -> KnowledgeRetriever -> knowledge/ is one-way and safe.**
3. **Brain modules -> Constitution -> Decision Principles is one-way and safe.**
4. **No circular imports detected** at runtime (`python -c "import app"` succeeds; the test suite is green).
5. **Forward references that are not imports**: ADR-009 lists Sections 7/8/9 as future CKO sections; ADR-011 added Section 8; ADR-012 added Section 9. Each depended on the prior; no cycle, but **each new ADR waits on the prior being committed** -- this means CKO Section 8 cannot be populated until ADR-011 ships, which cannot be enforced automatically.

### 5.4 Isolated modules (no path forward)

1. `knowledge/space_character/` skeleton (Sprint 10.5).
2. `knowledge/governance_decisions/` (was reserved, missing).
3. `knowledge/library/` (was reserved, missing).
4. `app/api/` (empty FastAPI placeholder).
5. `app/models/`, `app/schemas/`, `app/utils/` (all empty).
6. `knowledge/decision_rules/` (README only; 17 rules live elsewhere).

### 5.5 Future maintenance risks

1. **Knowledge structure bloat**: 116 taxonomy files + 32 brain files + 17 rule files + 19 goals + 20 strategies + 16 reasoning + 11 handbook + 8 cases + 5 space character = **240+ knowledge files**. None have a single owner; each Sprint touches a subset. The risk: schema drift across knowledge sub-trees.
2. **CKO versioning**: V1.0 -> V1.1 -> V1.2 was done as **non-breaking extensions**, but no machine-readable version field exists on the example. Future loaders must read the prose version in the schema markdown, then reconcile manually.
3. **Test mock drift**: Stub VisionAnalyzer is reimplemented in `test_case_intelligence.py` and the older `test_decision_intelligence.py`. A central test fixture would prevent drift.
4. **No CI / pre-commit hooks**: There is no `pre-commit-config.yaml`, no GitHub Actions, no pytest.ini. The codebase depends on the developer running pytest manually.
5. **No environment management**: `requirements.txt` declares runtime deps; `pytest` was added recently but no `[project.optional-dependencies] dev = [...]` block. Drift risk between runtime and dev envs.
6. **Two CKO evaluators, two Vision schemas**: any change to `case_analysis_v3.json` requires updating `vision/analyzer.py`, `validator.py`, `case_intelligence/extractor.py` and the V3 test fixtures. There is no schema-driven lint or type check.

---


## 6. Missing Core Capabilities

These are the capabilities the system has described but not implemented. Each is required for CaseOS to answer its headline question ("what is the best thing to place in this space?").

| Capability | Description | Where it should live | Closest existing module |
| --- | --- | --- | --- |
| **Retrieval Engine** | Find similar cases given a V3 Vision JSON | `core/retrieval/` (new) | `validator/validator.py` (validates, doesn't retrieve); `decision/knowledge.py` (reads, doesn't rank) |
| **Learning Loop** | Use approved Golden Cases to retrain / re-evaluate the Decision Engine | `core/learning/` (new) | None |
| **Theme Engine** | First-class theme resolution: from theme library + Vision V3 -> recommended theme + story | `core/theme/` (new) or within `agents/strategy_agent.py` | Brain's `theme_strategy/README.md` describes it; no engine. |
| **Experience Engine** | Multi-population experience synthesis (per Brain `experience_perception`) | `core/experience/` (new) | None |
| **Project Fit Engine** | The 5-dimension context intelligence from ADR-006 | `core/agents/decision_maker_agent.py` (currently a stub) | None of the 5 dimensions are wired |
| **Feedback System** | Capture post-decision signals, including rejected Golden Case learning | `core/feedback/` (new) | None |
| **Project Memory** | Long-term state across sessions | `core/memory/` (new) | None |
| **Proposal Engine** | From recommendation -> customer-facing proposal (PDF, design image, itemized BOM) | `core/proposal/` (new) | Recommendation produces markdown, no proposal format |
| **Image Generation** | The Sprint 7 docs include "image generation" as a future feature; the Sprint 18 pipeline outputs JSON only. | `core/image_gen/` (new) | None |
| **Constitution enforcement** | Code-level rejection of recommendations that violate a Principle | `core/constitution/` (new) | None |
| **API / CLI surface** | A way for users (or external tests) to call `ProductFlow.run` or `GoldenCasePipeline.start` | `app/api/routes.py` + `app/cli.py` | None -- main.py only has `/health` |
| **CI configuration** | Pre-commit, GitHub Actions, pytest.ini | `.github/workflows/`, `pytest.ini`, `.pre-commit-config.yaml` | None |

The most important of these is the **API / CLI surface**. Without it, every Sprint either adds modules that are tested but never used (the current pattern), or relies on a future UI that has no defined wire format.

---

## 7. Phase Assessment

### 7.1 Phase 1 -- Knowledge Foundation (target: 100%)

Component targets:

- Knowledge structure laid out at 6+ layers (Architecture, ADR-007, ADR-008, ADR-009, ADR-010, ADR-011, ADR-012). **Status: 95%.**
- Pivoted to "AI Space Advisor" with full reproduction through Constitution, Standards, ADR-005, ADR-006, ADR-009. **Status: 100%.**
- Test coverage of the knowledge contract. **Status: 70%** -- schema-level validation is in place; Brain-level validation is not (no test enforces the 6-section template against live Brain README files).
- One example per major knowledge asset. **Status: 100%.** (CKO has 1 example; strategies / goals / objects have multiple.)
- **Phase 1 completion: ~90%.** The remaining 10% is the systematic conversion of the Constitution + Decision Principles + DPs into enforceable code-level rules.

### 7.2 Phase 2 readiness (target: ready for at least the first module)

- Vision Engine ships V3 schema (done).
- Decision Engine ships 7-stage pipeline (done).
- Agent Framework ships 6 agents (done).
- Case Library schema + example (done).
- Case Intelligence Pipeline runs end-to-end on stubs (done).
- **Phase 2 entry point exists: Sprint 18 pipeline can answer a user's image upload today, in tests.**
- What is missing: a runtime caller (API or CLI); a real image-driven test; Constitution enforcement; multi-Library retrieval; Theme / Experience / Project Fit engines; Proposal output; Feedback loop.
- **Phase 2 readiness: ~30%.** The infrastructure is in place; the engines are not.

### 7.3 Major blockers

1. **No production entry point.** No `routes.py`, no CLI. Product Flow and Golden Case Pipeline cannot be invoked except by tests. **This is the single biggest blocker for Phase 2.**
2. **Brain / Cases / Decision Rules are knowledge assets with no engine consumers.**
3. **Two decision-rules folders.** One ADR's intended location is the other ADR's implemented location; resolution requires an ADR or a Sprint task.
4. **No CI.** Catch regressions only when a developer runs pytest locally.
5. **No Constitution enforcement.** A future agent can output a recommendation that violates Constitution Principle 001 (most suitable, not most beautiful); nothing in code catches it.

---


## 8. Recommendations -- Top 10 Architecture Priorities

Ranked by (Business Value, Technical Importance, Knowledge Value). All items are inspection-only output: each is a future ADR or Sprint task.

### Rank 1 -- Build the API / CLI surface (`app/api/routes.py` + a thin CLI)

- **Business Value:** 10. Without an entry point, the product cannot be demonstrated or tested by users. Blocks Phase 2 entirely.
- **Technical Importance:** 10. Trivial in scope; has the largest unblocking effect.
- **Knowledge Value:** 6. No new knowledge needed; this is plumbing.
- **Work item:** a Sprint that mounts Product Flow (`/v1/recommend`), Golden Case Pipeline (`/v1/cases/from-image`), and Decision Engine (`/v1/decide`) under `/docs`. Adds a tiny CLI (`bin/caseos.py`).

### Rank 2 -- Wire Golden Case Pipeline -> CKO Validator

- **Business Value:** 9. Closes the loop on the most recently shipped module (Sprint 18).
- **Technical Importance:** 8. Two parallel validators; consolidate on `validator.py` once Brain / ADR-012 schemas are reconciled.
- **Knowledge Value:** 8. Demonstrates that the CKO schema is enforceable.
- **Work item:** a Sprint to make `GoldenCasePipeline.start` call `validator.validate_post_save` automatically, then write the validated Golden Case to `knowledge/library/`.

### Rank 3 -- Wire Brain + Decision Rules into the Decision Engine

- **Business Value:** 9. Releases latent value in 32 + 17 = 49 knowledge files.
- **Technical Importance:** 9. KnowledgeRetrieval is the spine of every agent; right now it reads shallowly.
- **Knowledge Value:** 10. Real value only materializes when the engine consumes it.
- **Work item:** an ADR-013 + Sprint that extends `decision/knowledge.py` to (a) load Brain sections by ID, (b) load rules from `brain/decision_rules/`, (c) expose an IF/THEN matcher; and one Sprint to wire the Space Agent + Strategy Agent to those loaders.

### Rank 4 -- Constitution enforcement layer

- **Business Value:** 8. Without this, the highest-level doctrine is decorative.
- **Technical Importance:** 8. Define a single `constitution.py` module with the four Principles + the seven Forbidden Behaviors as plain Python predicates; call them in `Explain Agent` and `Recommendation Agent` before any output ships.
- **Knowledge Value:** 9. Ties ADR-007 to runtime.
- **Work item:** an ADR + a Sprint that produce `core/constitution/enforce.py` and unit tests demonstrating that the engine rejects a recommendation that violates Principle 001.

### Rank 5 -- Resolve the Brain-vs-ADR-010 decision_rules conflict

- **Business Value:** 6. Prevents future contributors from placing new rules in the wrong folder.
- **Technical Importance:** 9. ADR boundaries must be unambiguous.
- **Knowledge Value:** 7. The conflict itself loses meaning once resolved.
- **Work item:** an ADR that explicitly elevates `knowledge/brain/decision_rules/` to canonical, removes `knowledge/decision_rules/`, and updates ADR-010 to status Accepted.

### Rank 6 -- Retrieval Engine for the Case Library

- **Business Value:** 8. The future CaseRetrievalEngine is what makes "similar case" recommendations possible.
- **Technical Importance:** 9. The first phase of Phase 2 work that touches the actual customer question.
- **Knowledge Value:** 8. Uses CKO V1.2 cases in production for the first time.
- **Work item:** an ADR that defines a structural retrieval (vocabulary overlap, not embeddings yet) over `knowledge/cases/` + an integration into the Decision Engine.

### Rank 7 -- Theme Engine + Experience Engine first-class modules

- **Business Value:** 7. Today both are described in Brain READMEs but not built. Wiring them makes the agent output more domain-specific.
- **Technical Importance:** 7. Mostly new code; little contract risk.
- **Knowledge Value:** 8. Reuses the Theme Library (42 files) + Experience Tags (no engine consumer today).
- **Work item:** two Sprints. Theme Engine first (loads `theme_strategy/` + `taxonomy/theme/`). Experience Engine second (loads `experience_perception/` + `experience_tags.md`).

### Rank 8 -- CI / pre-commit / GitHub Actions / pytest.ini

- **Business Value:** 6. Long-term hygiene; current dev velocity is fine but regressions are silent.
- **Technical Importance:** 9. Standard scaffolding. Days of work, forever reduction in regression risk.
- **Knowledge Value:** 4. Hygiene, not capability.
- **Work item:** a Sprint that adds `pytest.ini`, `.pre-commit-config.yaml`, and a minimal `.github/workflows/test.yml`.

### Rank 9 -- Centralize test fixtures + remove duplicate stubs

- **Business Value:** 5.
- **Technical Importance:** 7. Removes drift between `test_case_intelligence.py` StubVisionAnalyzer and `test_decision_intelligence.py` StubVisionAnalyzer.
- **Knowledge Value:** 4.
- **Work item:** a Sprint that introduces `backend/tests/fixtures/` and a `tests/conftest.py`.

### Rank 10 -- Backfill the empty placeholders or remove them

- **Business Value:** 3.
- **Technical Importance:** 5. Six directories currently impersonate future modules. Either implement them or remove them.
- **Knowledge Value:** 3.
- **Work item:** a Sprint that decides: (a) `app/models` and `app/schemas` -> adopt Pydantic + wire into routes; (b) `app/utils` -> populate with shared helpers; (c) `app/api/` -> write `routes.py`; (d) `knowledge/space_character/` -> extend into Phase 2 evaluation; (e) reserved-but-missing `knowledge/library/` -> build alongside the CKO Validator integration.

### Items explicitly NOT in the Top 10

- **Image generation (Sprint 7 future / ADR-006)**: out of scope for the next 2 sprints; not a blocker for Phase 2.
- **CAD / construction drawings / Budget generation (Sprint 12 Pivot cleanup; Product.md Future)**: explicitly out of V1 per the Constitution; defer until V2.
- **Multi-language content**: not on the critical path.

---


## 9. Closing Notes

- **The knowledge phase is essentially complete.** Ship the wiring Sprint (Rank 1 + Rank 3 + Rank 5) before adding more knowledge. Every additional Knowledge document beyond what those three Sprints require is opportunity cost -- the team can read it but no engine can.
- **The two sprints at the top of the priority list (API/CLI surface and Brain wiring) unblock 80% of what remains.** Do not attempt Rank 2, Rank 4, Rank 6, Rank 7, Rank 8 or Rank 9 without Rank 1 in place. Rank 1 is the gateway; everything downstream costs more if attempted before it.
- **ADR-010 should be migrated from `Proposed` to `Accepted` when Rank 5 (Brain wiring + Decision Rules consumption) closes.** Today the rules live at `knowledge/brain/decision_rules/` but no engine reads them. ADR-010 is "proposed" in the literal git sense; the wiring Sprint is what makes it "accepted" in the engineering sense.
- **This review is the second architecture review in the project.** The first was the 30-finding `System_Review_2026_07_30.md` (pre-Sprint 14, against `0417f50`). Each review has produced a concrete next-Sprint list; the team is encouraged to **close out the previous review's P0/P1 before starting new work**. AR-001 inherits the open items from that sibling review and adds eight new ones (Rank 1 -- Rank 8).
- **Sprint 19 is recommended.** Its title is "Wire the Brain to a Runtime" and its body is the union of Rank 1 + Rank 3 + Rank 5 from the Recommendations section. Estimated effort: one sprint. Estimated impact: Phase 2 readiness moves from ~30% to ~70%.
- **What success looks like** at the end of Sprint 19: a developer can run `caseos recommend --image /path/to/photo.jpg --project-type commercial --goal increase_visitors` from a terminal and receive a Markdown report identical in structure to the Decision Intelligence V1 demo, except that the strategy, object selection, and explanation all flow through the rule engine instead of through hand-written Python. When that is true, the system has a runtime.
- **What success does NOT look like** at the end of Sprint 19: a beautiful web UI, vector database integration, image generation, multi-user sessions, or fine-tuning. None of those are required for the Phase 2 definition-of-done.
- **One sentence:** the architecture is honest about what it has shipped and what it has not; the next sprint must convert honesty about the gap into a closed loop, after which the roadmap becomes a function of product strategy rather than engineering readiness.

**Final score:** the system has a healthy knowledge core. It is not yet a product. **Phase 2 begins when the Rank 1 sprint ships.**

---

## 10. Reviewer Endorsement

This document is **inspection-only**. It identifies; it does not change. Every numbered recommendation (Rank 1 -- Rank 10) becomes either an ADR or a Sprint task in the next cycle. The two ADRs that this review identifies as not-yet-published (the ADR-007 Constitution cross-reference ADR, and the ADR-010 Decision Rules framework closure ADR) are the natural opening acts of Phase 2.

| Recommendation | Becomes |
| --- | --- |
| Rank 1 -- Build the API/CLI surface | **Sprint 19** (Wire the Brain to a Runtime) |
| Rank 2 -- Connect Knowledge Loader to Retriever | **Sprint 20** |
| Rank 3 -- One end-to-end runtime chain | Subsumed in Sprint 19 |
| Rank 4 -- Product Layer promotion to API | Subsumed in Sprint 19 |
| Rank 5 -- Brain wiring with Decision Rules | Subsumed in Sprint 19 |
| Rank 6 -- Spatial Recommendation Engine | **Sprint 21** |
| Rank 7 -- Outcome / feedback collection | **ADR-013** |
| Rank 8 -- Constitution enforcement | **ADR-014** |
| Rank 9 -- Test fixtures convergence | Sprint-task within Sprint 19 |
| Rank 10 -- Empty placeholder backfill | Sprint-task within Sprint 19 |

**Reviewer commitment:** the recommendations above are unconditional. They do not depend on a future review, a future ADR, or a future stakeholder decision. Sprint 19 can begin on the basis of this document alone. If any of them are deferred, that is a project-management decision, not a technical one.

**Reviewer caveat:** this review is static. It captures the architecture as of commit `5a0f6ad`. Any commit after that point -- including this very commit -- may shift one or two findings (e.g. some "isolated modules" become "partial integration"; some "ADRs missing" appear). The review should be re-run, in full, at the end of Sprint 19 to verify that the Rank 1 recommendations actually closed the loops they intended to close.

**Reviewer note on dual-tone:** the document is written in English to match the existing repository convention (every ADR, every Sprint, every Knowledge module is in English). The discussion in the originating chat thread was in Chinese. If the project later adopts Chinese as the primary documentation language (some teams do), this review should be translated alongside everything else. Until then, English remains the canonical form.

---

*End of AR-001. The next architecture review (AR-002) is recommended after Sprint 19 lands.*
