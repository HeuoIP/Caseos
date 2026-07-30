# ADR-006: Project Fit Intelligence Architecture

- **Status:** Proposed
- **Date:** 2026-07-30
- **Supersedes:** --
- **Superseded by:** --

## 1. Background

CaseOS 的核心目标：

    "让每一处空间，都找到最适合它的内容。"

当前系统已经具备：

- Vision Engine
- Knowledge System
- Decision Engine
- Recommendation Pipeline

但是当前系统主要解决：

    "这个空间适合放什么？"

真实商业项目中，更重要的问题是：

    "这个空间、这个投资人、这个目标，是否匹配？"

很多项目失败并不是设计问题，而是：

- 投资能力与项目目标不匹配
- 运营能力不足
- 市场环境不支持
- 场地条件不适合
- 客户认知与项目定位冲突

因此增加 Project Fit Intelligence。

---

## 2. Decision

新增：

    Project Fit Agent

位置：

    core/agents/project_fit_agent.py

职责：

在设计策略之前，对项目进行适配性判断。

---

## 3. Core Principle

CaseOS 不直接回答：

    "做什么最漂亮"

而优先回答：

    "什么是这个项目最合适的选择"

判断维度：

- **Space** -- 空间本体
- **Investor** -- 投资方能力
- **Goal** -- 项目目标
- **Market** -- 市场环境
- **Resource** -- 资源条件

---

## 4. Input Model

Project Context:

### 4.1 Space Context

包含：

- site type
- area
- location level
- surrounding environment
- existing condition

### 4.2 Investor Context

包含：

- experience
- budget capability
- operation capability
- decision style

### 4.3 Project Goal

包含：

- business growth
- education improvement
- branding
- public value
- experience

### 4.4 Market Context

包含：

- competition
- surrounding population
- regional characteristics

---

## 5. Output Model

Project Fit Report:

### 5.1 Project Strength

项目优势。

### 5.2 Project Risk

项目风险。

### 5.3 Capability Match

投资人与项目匹配程度。

### 5.4 Recommended Direction

推荐项目方向。

### 5.5 Avoid Direction

不建议方向。

### 5.6 Confidence

判断置信度。

---

## 6. Agent Relationship

Pipeline:

    Vision
      |
      v
    Space Agent
      |
      v
    Decision Maker Agent
      |
      v
    Project Fit Agent          <-- NEW
      |
      v
    Knowledge Retrieval
      |
      v
    Strategy Agent
      |
      v
    Object Selector
      |
      v
    Explain Agent
      |
      v
    Report

Project Fit Agent 位于 Decision Maker 之后、Knowledge Retrieval 之前。
它在设计策略生成之前，先回答 "这个项目是否值得做、应该往哪个方向做"。

---

## 7. Intelligence Principle

Project Fit Agent 不替代设计。

它负责：

    "是否值得这样设计"

Strategy Agent 负责：

    "应该如何设计"

两个 Agent 分工明确：

- Project Fit Agent = 是否 (whether)
- Strategy Agent     = 如何 (how)

---

## 8. Future Extension

未来支持：

- Commercial Evaluation Agent
- Budget Agent
- Safety Agent
- Education Agent
- Psychology Agent
- Fengshui Agent

这些 Agent 与 Project Fit Agent 处于同一决策层（位于 Strategy 之前），
共同构成 CaseOS 的 Project Intelligence Layer。

---

## 9. Non Goals

本阶段不实现：

- 自动投资分析
- 财务预测
- 市场数据爬取
- 用户画像系统

当前目标：

建立行业专家判断框架。

Project Fit Agent 在 V1 中是基于规则的专家判断 (rule-based expert
heuristics)，不调用任何外部数据源，也不预测财务回报。

---

## 10. Consequences

### Positive

- 把 "是否合适" 显式建模为决策的一等公民，不再隐藏在 strategy 选型中。
- 让推荐系统在 strategy 之前先做一次 sanity check，避免给不合适的项目生成详细方案。
- 与 ADR-005 的 Decision Intelligence 互补：
  - ADR-005 回答 "在已经决定做的项目上，如何最优"
  - ADR-006 回答 "这个项目本身应不应该做、应不应该这样定位"
- 为未来 Budget / Safety / Commercial Agent 留出统一的决策前层。

### Negative / Trade-offs

- 流水线多了一个 Agent，单次运行时间略增。
- Project Fit Report 本身是 V1 的规则化判断，可能与资深从业者的直觉不完全一致。
- 客户提交的项目上下文可能不完整，Agent 必须能处理缺字段。

### Neutral

- 不影响现有 agent 接口、context schema、markdown 报告格式。
- 不引入新数据库、不引入新外部依赖。

---

## 11. Acceptance Criteria

一个 ADR 本身的验收不是代码，而是判断本身是否清晰可执行。
判断通过 = 满足以下 5 条：

1. Project Fit Agent 的输入、输出、位置都已定义，无歧义。
2. 与 ADR-005 的 Decision Intelligence 不冲突，且互补。
3. Non Goals 明确，本 ADR 不要求实现财务预测或市场爬取。
4. Future Extension 列出但不强加，明确 V1 范围。
5. 该 Agent 可以在不改现有任何 agent 接口的前提下，插入到当前流水线。

待人工评审通过后，本 ADR 升级为 Accepted。

---

## 12. References

- ADR-005 -- Decision Intelligence Architecture (current accepted).
- Sprint 09 -- Decision Intelligence V1 (the V1 implementation of ADR-005).
- Sprint 09 Review Checklist -- the 14/14 acceptance report for ADR-005 V1.
- knowledge/decision_rules/Space_Decision_Principles.md -- the
  expert-heuristics that Project Fit Agent will codify in V1.
- knowledge/expert_handbook/01_Space_Decision_Method.md -- the
  decision method whose "five layers" maps to this ADR.
