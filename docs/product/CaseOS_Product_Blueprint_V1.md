# CaseOS Product Blueprint V1

- **Status:** Proposed (V1)
- **Date:** 2026-07-30
- **Supersedes:** --
- **Superseded by:** --
- **Layer:** Product (highest-level product reference)
- **Companion documents:**
  - docs/standards/CaseOS_Constitution_V1.md (philosophy)
  - docs/standards/CaseOS_Decision_Principles_V1.md (implementation guide)
  - docs/architecture/ADR-006-project-fit-intelligence.md (project fit)

---

# 1. Product Vision

CaseOS is NOT an AI design software.

CaseOS is NOT a chatbot.

CaseOS is NOT a generic image generator.

**CaseOS is an AI Space Advisor.**

An advisor listens first, asks questions, understands the problem,
and only then proposes an answer. CaseOS does the same: it starts
from the user "s spatial problem, and ends with a defensible recommendation
that the user can act on.

Mission:

    "让每一处空间，都找到最适合它的内容。"

The "suitable" is a fit metric, not a quality metric. CaseOS does not
promise the most beautiful, the most fashionable, or the most
expensive. It promises the most suitable. That is a smaller promise
and a harder one to keep, and it is the one that customers will
trust.

---

# 2. Product Philosophy

The product starts from the user "s problem.

**NOT from AI capability.**

Most AI products are designed backwards: a model has a capability,
so the product is wrapped around that capability. CaseOS is
designed forwards: a user has a problem, and the product is shaped
around the journey from problem to defensible answer.

Three direct consequences:

1. **Users do not come to generate images.** They come to solve
   spatial problems. Image generation, when it eventually appears in
   the product, is a means, not a destination.
2. **Users do not come to chat with an AI.** They come to make a
   decision. The conversational surface exists only because some
   decisions require clarification; it is not the product itself.
3. **Users do not come to browse a catalogue.** They come because
   they are about to spend money, time, or political capital on a
   space. Every screen in the product must reduce the risk of that
   decision, not increase the entertainment value of the visit.

If a feature increases the entertainment value of the visit without
reducing the risk of the decision, it does not belong in V1.

---

# 3. Core User Journey

This is the single most important section of the blueprint. The
user "s thinking process is the product. The UI is a thin layer on top.

    1. Discover
       |
       v
    2. Define Goal
       |
       v
    3. Upload Space
       |
       v
    4. AI Understands
       |
       v
    5. User Confirms
       |
       v
    6. Space Diagnosis
       |
       v
    7. Strategy Thinking
       |
       v
    8. Content Recommendation
       |
       v
    9. Value Explanation
       |
       v
   10. Implementation Suggestions

What the user is THINKING at each step, not what they are clicking:

### 3.1 Discover

The user becomes aware of CaseOS because they have a problem, not
because they want an AI tool. The problem is concrete: a site that
needs a design, a proposal that needs evidence, a budget that needs
defending, a stakeholder who needs persuading. The product must
speak to that concrete problem from the first impression, not to a
generic "AI for designers."

### 3.2 Define Goal

Before any photo, the user is asked to state what they want this
space to DO. The choices are deliberately business-language, not
design-language:

- Increase enrollment (幼儿园招生)
- Increase visitors (文旅 / 商业 客流)
- Improve brand (品牌差异化)
- Improve experience (体验升级)
- Optimise space (存量改造)
- Not sure (引导式澄清)

If the user picks "Not sure", the product does not invent a goal. It
asks. Constitution Principle 002 applies: design serves decisions,
and a goal is the smallest unit of a decision.

### 3.3 Upload Space

The user uploads a photo (V1), a video (V2), or a CAD plan (V3).
In V1 the photo is the only input that matters, but the input
model is built to accept more so the product does not need to be
rebuilt later.

The user does not need to label the photo. They do not need to
classify the site. They do not need to clean it up. They snap and
send.

### 3.4 AI Understands

The Vision Engine reads the photo. The user sees a short
understanding confirmation, not a paragraph of text. Three to
five bullet points: site type, primary theme, dominant material,
visible age group. The product deliberately does NOT show
probabilities, embeddings, or model version. Those are implementation
details; the user does not need them to make a decision.

### 3.5 User Confirms

The user confirms, corrects, or adds one short sentence. The
correction is treated as more authoritative than the AI "s first read,
because the user knows the site. The product never argues. If the
AI read the site as indoor and the user says outdoor, the AI is
outdoor.

This step is non-negotiable. Constitution Principle 003:
understand before recommending. The user "s confirmation is part of
the understanding.

### 3.6 Space Diagnosis

The product shows a short, structured diagnosis:

- Project Strength
- Project Risk
- Capability Match (between the user / project owner and the project)
- Recommended Direction
- Avoid Direction
- Confidence

This is the Project Fit Report (ADR-006). It is the FIRST thing the
user sees about the recommendation. If the diagnosis says "this project
is not worth doing in the current form", the rest of the journey is
different. The product does not pretend the rest of the journey is
still appropriate.

### 3.7 Strategy Thinking

The product shows the strategic frame: how this space should be
positioned, what design direction makes sense, where the budget
should concentrate. The user does not need to read all of it; the
product makes the strategy the BASIS for what comes next, not a
long preamble.

### 3.8 Content Recommendation

A small, ranked set of recommendations (typically 3-5), each with:

- Name and category
- Score
- Why it is here
- What it serves (goals, strategy)

Constitution Principle 001: the most suitable, not the most.
A small set beats a long list. The product never shows more than
five recommendations at a time.

### 3.9 Value Explanation

For each recommendation, the product says in plain language what
value it creates, for whom, and at what cost. Constitution
Principle 004 and Decision Principle 004 both apply: speak the
decision maker "s language, never the supplier "s language. No
marketing words. No AI jargon. Physical features only.

### 3.10 Implementation Suggestions

A short list of next steps: what to ask a contractor, what to
verify on site, what to budget, what to delay. V1 keeps this list
small and conservative. It is advice, not a contract.

---

# 4. Product Input Model

The product collects four groups of input. They are listed in the
order the user encounters them, not in the order the AI needs them.

## 4.1 User Goal (required)

Examples the product offers:

- **Increase Enrollment**         (e.g. 幼儿园招生)
- **Increase Visitors**           (e.g. 商场 / 文旅 客流)
- **Improve Brand**               (e.g. 品牌差异化)
- **Improve Experience**          (e.g. 体验升级)
- **Optimise Space**              (e.g. 存量改造)
- **Not Sure**                    (引导式澄清)

In V1 the user picks one. In V2 the user may layer a primary and a
secondary goal. Multi-goal scenarios are common in real projects
but the product must not pretend the goals are equally weighted.

## 4.2 Space (required)

Input formats and their availability:

- **Photo**   (V1, single or multiple)
- **Video**   (V2, for ambient context and child behaviour)
- **CAD**     (V3, for plan-level reasoning)
- **3D scan** (V3+, for accurate dimensions)

V1 accepts photo only. The product must be honest about this and
not pretend that photo equals a full site survey.

## 4.3 Project Type (required)

Examples:

- Kindergarten
- Public Park
- Commercial Space
- Community
- Family / Residential
- Cultural / Museum
- Tourism / Scenic
- Other (free text)

V1 covers the first five. The list grows with the knowledge library,
not before.

## 4.4 Optional Information

Always optional, never required:

- **Budget**              (low / medium / high, or a range)
- **Special requirements** (accessibility, climate, jurisdiction,...)
- **Preferred style**     (a tag the user already has in mind)
- **Timeline**            (when the project must be operational)
- **Stakeholder context** (who decides, who operates, who pays)

Constitution Principle 001: missing data must NEVER be invented. If
the user does not provide a budget, the product either asks, or
clearly labels the recommendation as "budget-independent."

---

# 5. AI Thinking Journey

This is the product "s view of the AI pipeline, deliberately simplified
to the level a product manager can read and an engineer can map to
the real pipeline in ackend/app/core/.

    Space Understanding
      |
      v
    Project Fit
      |
      v
    Goal Understanding
      |
      v
    Knowledge Retrieval
      |
      v
    Decision Making
      |
      v
    Strategy
      |
      v
    Recommendation
      |
      v
    Explanation

What happens at each step:

### 5.1 Space Understanding

The Vision Engine reads the photo and produces a structured
description: site type, theme, style, age group, dominant
materials, functional units, vision summary, design interpretation.
This is governed by the Vision Standard V1 and the Output Schema
V2 / V3.

### 5.2 Project Fit

Before deciding what to recommend, the engine decides whether the
project is worth recommending for at all, and in which direction.
This is the Project Fit Agent from ADR-006: Strength / Risk /
Capability Match / Recommended Direction / Avoid Direction /
Confidence.

### 5.3 Goal Understanding

The user "s stated goal is turned into a stable Goal reference, then
enriched with inferred secondary goals from the Decision Maker
profile.

### 5.4 Knowledge Retrieval

The engine pulls the relevant slices of the knowledge library:
similar cases, themes, objects, decision rules, expert handbook,
reasoning patterns. This is the Knowledge Retriever from Sprint 9.

### 5.5 Decision Making

The Decision Maker Agent infers a profile (e.g. PUBLIC_ADMIN,
EDUCATOR, COMMERCIAL_OPERATOR) and resolves goal priorities. If the
user has stated a primary goal, it stays at the top.

### 5.6 Strategy

The Strategy Agent selects the strategic moves that serve the
goals, resolves conflicts, and emits a StrategyAnalysis with a
positioning, a core problem, a design direction, and an investment
logic.

### 5.7 Recommendation

The Object Selector Agent ranks concrete objects (Treehouse,
Reading Corner, IP Sculpture, ...) that implement the strategy. The
top 3-5 become the user-facing recommendations.

### 5.8 Explanation

The Explain Agent turns the recommendation into a short,
customer-language paragraph per recommendation, citing goals,
strategies, and the chosen theme.

The product wraps the whole chain in a Markdown report and shows
it to the user at the right time, in the right slices, with the
right emphasis.

---

# 6. Product Output

The end product of a CaseOS run is a structured recommendation that
the user can act on, defend, or send to a contractor. The product
shows it in eight slices:

1. **Space Diagnosis**          -- what the space IS
2. **Priority Problems**        -- what is in the way
3. **Opportunities**            -- what the space already has that can be amplified
4. **Recommended Direction**    -- which way to go (the strategic frame)
5. **Recommended Contents**     -- the 3-5 ranked recommendations
6. **Why**                      -- the reasoning, in the user "s language
7. **Implementation Suggestions** -- the next concrete steps
8. **Future Expansion**         -- what this recommendation leaves on the table,
   intentionally, so the user can choose to invest more later

V1 outputs are Markdown-first. PDF is a future export. The product
does not promise any of the slices it does not yet generate.

---

# 7. Product Principles

The product inherits from the Constitution and the Decision
Principles. The following product-level principles are not new
philosophy; they are the user-facing translation.

- **Decision before Design**
  The product asks for the goal before it asks for the photo. The
  user sees the strategy before the recommendations. Every
  recommendation cites the goal it serves.

- **Space before Object**
  The product never leads with a catalogue. The space diagnosis is
  always shown before any object. If the diagnosis is weak, the
  object recommendation is weak too, and the product says so.

- **Content serves Purpose**
  Every recommendation is linked to a goal. A recommendation with
  no served goal is not shown.

- **Recommend from the Decision Maker "s Perspective**
  The product "s language matches the user "s language. Designers see
  designer language. Operators see operator language. Parents see
  parent language. No marketing words. No AI jargon.

- **Amplify Existing Strengths**
  The product "s recommendations start from what the space already has,
  not from what the supplier would like to add. If the space has a
  great lawn, the recommendations use the lawn.

- **Surface Unknown, do not Invent**
  When the user does not provide budget, timeline, or stakeholder
  context, the product labels the recommendation "unknown" in those
  dimensions. It does not invent a number to look confident.

- **Small Set beats Long List**
  The product never shows more than five recommendations at a
  time. Trade-offs are visible. The user is never asked to compare
  20 things.

---

# 8. Future Evolution

The product is a long-term advisor, not a one-shot tool. The
version roadmap below is a guide; each version is gated by its own
ADR.

### V1 (current target)

    Image -> Recommendation

- Photo in, ranked recommendation out.
- Single goal, single site, single recommendation set.
- Markdown report as the primary export.
- No login required, no history kept beyond the session.

### V2

    Multi-space Planning

- Multiple photos per project (entry, core, edge, ...).
- Multi-goal projects with explicit primary / secondary.
- Comparison view: how two recommendation sets differ.
- PDF export for the report.

### V3

    Continuous Space Advisor

- Project history: the user "s previous recommendations, what they
  chose, what was built, what worked.
- Space Character dataset feeds back into the model: every new
  reviewed case strengthens the next recommendation.
- Optional login, so a designer "s library of past projects is
  searchable.

### V4

    Personal AI Space Consultant

- Per-user tuning: the advisor learns the user "s industry, vocabulary,
  and decision style.
- Stakeholder mode: a non-designer (e.g. a kindergarten principal)
  gets a version of the report that is tuned to her role.
- Live integration: the advisor is reachable where the decision
  is being made (phone, in a meeting, on site).

---

# 9. Non Goals

The product is NOT:

- **A rendering software.** The product does not pretend to produce
  build-ready visuals. Image generation, when it appears, is a
  means of helping the user understand the recommendation, not a
  deliverable.
- **A CAD software.** CaseOS does not produce drawings, sections, or
  construction documents. That is the next layer down, owned by
  humans and dedicated tools.
- **A chatbot.** CaseOS has a conversational surface, but only for
  clarification. The product is a structured recommendation engine
  with a thin conversational interface, not the other way around.
- **A generic image generator.** CaseOS does not generate images on
  prompt alone. Every image the product ever shows is anchored to a
  recommendation, which is anchored to a goal, which is anchored
  to a stated user problem.

**The product is an intelligent spatial decision platform.**

It is the advisor the decision maker did not have when they were
last asked to commit money, time, or political capital to a space.
It is not a tool. It is a colleague.

---

## Acceptance Criteria

A blueprint, not a build. Acceptance is measured by clarity, not by
test count. The blueprint is acceptable when:

1. The Product Vision is unambiguous: CaseOS is an AI Space Advisor,
   not a design tool or a chatbot.
2. The Core User Journey covers the user "s thinking process, not just the
   UI flow.
3. The Product Input Model is honest about what V1 actually requires
   versus what V2 / V3 will accept.
4. The AI Thinking Journey is mappable to the existing pipeline in
   ackend/app/core/.
5. The Product Output is act-on-able: a user can hand the output to
   a contractor without rewriting it.
6. The Future Evolution is gated by ADRs; no version is implicit.
7. The Non Goals are explicit. Any future proposal that conflicts
   with a Non Goal must go through ADR.

---

## References

- docs/standards/CaseOS_Constitution_V1.md -- the philosophy the
  product inherits.
- docs/standards/CaseOS_Decision_Principles_V1.md -- the
  implementation guide the product obeys.
- docs/architecture/ADR-005-decision-intelligence.md -- the
  pipeline the product is built on top of.
- docs/architecture/ADR-006-project-fit-intelligence.md -- the
  Project Fit layer that drives the Space Diagnosis step.
- docs/sprints/Sprint_08_Product_Layer.md -- the Product Layer
  the product wraps.
- docs/sprints/Sprint_09_Decision_Intelligence.md -- the
  Decision Intelligence the product surfaces to the user.
- docs/standards/CaseOS_Vision_Standard_V1.md -- the Vision
  standard that feeds Space Understanding.
