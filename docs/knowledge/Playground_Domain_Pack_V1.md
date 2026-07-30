# Playground Domain Pack V1

- **Status:** Accepted (domain pack content is unchanged from V1)
- **Date:** 2026-07-30 (rebranded by Sprint 12 Pivot Cleanup;
  original V1 content dated 2026-07-28)
- **Layer:** Knowledge (domain pack)
- **Purpose:** the playground industry's slice of CaseOS knowledge.

---

## 0. What this document is -- and is not

CaseOS is an **AI Space Advisor**, not an AI Playground Design
Assistant. The product answers "What is the most suitable content
for this space?", not "What playground case is similar?".

Playground is the **first domain pack** that CaseOS supports, not
the only one. A domain pack is the industry-specific knowledge
that wraps the domain-agnostic core (Vision Engine, Decision
Engine, Agent Framework). Future domain packs (street furniture,
shade, water play, education spaces, ...) will be expressed in
the same shape but with different content.

This document is the playground domain pack. It defines the
playground-specific taxonomy, behaviour vocabulary, and spatial
vocabulary. It is NOT the product spec. The product spec is
`docs/product/CaseOS_Product_Blueprint_V1.md`.

## 1. Why playground first

- The CaseOS founding team has deep playground industry
  experience, so the first domain pack is built from real
  vocabulary, not invented terms.
- Playground design is a high-stakes decision space (children,
  safety, public funds, brand), so it is a useful proving ground
  for the Constitution "fit-not-beauty" stance.
- The same Vocabulary shape (age / behaviour / value / theme /
  space / unit) generalises to most family-facing spaces with
  minor edits.

## 2. Playground Ontology V1 (content unchanged)

The taxonomy below is the original Playground_Ontology_V1 content,
preserved verbatim. Sprint 12 only rebranded the document.

### 第一章 儿童
- 0-2
- 2-3
- 3-6
- 6-9
- 9-12
- 12+

### 第二章 游乐行为
滑
爬
钻
跳
荡
旋转
平衡
追逐
社交
探索
角色扮演
观察
休息

### 第三章 成长价值
感统
前庭
平衡
协调
社交
创造力
勇气
认知
语言
合作

### 第四章 设计主题
森林
海洋
宇宙
动物
昆虫
恐龙
自然
未来
工业
童话

### 第五章 空间
入口
主游乐区
探索区
休息区
互动区
看护区
拍照点

### 第六章 功能单元
滑梯
攀爬
绳网
秋千
蹦床
沙坑
戏水
音乐
互动装置
迷宫

## 3. How a domain pack is used

At runtime, the playground domain pack contributes:

- **Playground age taxonomy** -- consumed by Vision Standard
  Section 7 (Age Group Taxonomy) when `domain_pack = playground`.
- **Playground behaviour vocabulary** -- consumed by Vision
  Standard Section 8 (Play Behavior Taxonomy) and by the
  Knowledge Retriever when scoring candidate snippets.
- **Playground growth-value vocabulary** -- consumed by the
  Explain Agent when translating a strategy into customer
  language.
- **Playground theme taxonomy** -- consumed by Vision Standard
  Section 4 (Theme Taxonomy); the playground theme library
  lives in `knowledge/taxonomy/theme/`.
- **Playground spatial vocabulary** -- consumed by the Space
  Agent when producing a Space Summary.
- **Playground functional unit vocabulary** -- consumed by the
  Object Selector when matching Objects to the strategy.

For domain packs other than playground, equivalent files live
under `knowledge/taxonomy/<other_domain>/` and a sibling domain
pack doc is added next to this one.

## 4. What this document is NOT

- It is NOT the product spec. (See Blueprint V1.)
- It is NOT the Vision standard. (See
  `docs/standards/CaseOS_Vision_Standard_V1.md`.)
- It is NOT a fixed domain boundary. A target space that mixes
  playground with retail, shade, or street furniture is allowed;
  the CaseOS Decision Engine will route the request through the
  right combination of domain packs.

## 5. References

- docs/product/CaseOS_Product_Blueprint_V1.md -- product spec.
- docs/standards/CaseOS_Vision_Standard_V1.md -- Vision standard.
- docs/standards/CaseOS_Constitution_V1.md -- philosophy.
- docs/standards/CaseOS_Decision_Principles_V1.md -- implementation guide.
- knowledge/taxonomy/theme/ -- the playground theme library.
- knowledge/objects/ -- the playground Object Library.
- docs/sprints/Sprint_12_Pivot_Cleanup.md -- the cleanup record
  that rebranded this document.
