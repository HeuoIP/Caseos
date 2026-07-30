# CaseOS Product V1 -- OBSOLETE

> **Status:** OBSOLETE -- retired 2026-07-30 by Sprint 12
> (Pivot Cleanup). Kept for git history reference only. Do not edit.
>
> **Superseded by:**
> `docs/product/CaseOS_Product_Blueprint_V1.md` (Blueprint V1).
>
> **Reason for retirement:**
> The product has been repositioned from "AI Playground Design
> Assistant" to "AI Space Advisor". The five V1 features listed
> below and the Future backlog are playground-only. The Blueprint
> V1 is the current product spec.

---

# CaseOS Product V1 (original)

> The text below is preserved verbatim from the V1 spec so that
> anyone who needs the original wording -- e.g. to compare V1
> expectations against Blueprint V1 reality -- can find it in
> git history. The text is no longer authoritative.

## 1、项目愿景（Vision）

CaseOS is an AI-powered playground case engine that helps designers and customers quickly generate professional playground concepts from site photos.

## 2、目标用户（Target Users）

- 幼儿园
- 地产
- 文旅
- 商业综合体
- 儿童乐园
- 设计公司

以后可以再补充更多用户类型。

## 3、用户流程（User Flow）

上传场地照片

|

v

AI 分析场地

|

v

推荐相似案例

|

v

解释推荐原因

|

v

生成概念方案

|

v

导出 PDF

## 4、V1 功能（Must Have）

1. 上传图片
2. 案例搜索
3. 案例解析
4. 方案生成
5. PDF 导出

## 5、以后版本（Future）

- 施工图
- 预算
- 工程量
- CAD
- AI 视频
- 自动营销

以上内容全部放在后续版本，不污染 V1。

## 6、一句话使命（Mission）

Help playground professionals generate better concepts in minutes instead of days.

---

## What changed at retirement

- **Positioning:** "AI Playground Design Assistant" ->
  "AI Space Advisor". The new core question is
  "What is the most suitable content for this space?", not
  "What playground case is similar?".
- **V1 features (1-5) are superseded.** Blueprint V1 keeps the
  photo-in, recommendation-out shape, but the recommendation is
  a defensible Space Diagnosis + Strategy + Content set, not
  "PDF 导出". PDF export is explicitly listed as a V2 deliverable
  in Blueprint V1.
- **Future backlog (5/6) is preserved in spirit but not in shape.**
  施工图 / CAD belong to the engineering layer, not the product
  layer. 预算 / 工程量 belong to the Project Fit layer (ADR-006).
  AI 视频 / 自动营销 belong to V3+ of the blueprint and are not
  on the V1 critical path.
- **Mission wording:** "Help playground professionals generate
  better concepts in minutes instead of days" is replaced by the
  Constitution Principle 001: "the most suitable content",
  qualified by "for every space", not "for every playground".

## References

- docs/product/CaseOS_Product_Blueprint_V1.md -- the current spec.
- docs/reviews/Architecture_Review_2026_07.md -- the review that
  triggered the pivot.
- docs/reviews/System_Review_2026_07_30.md -- P0-1, the finding
  that closed with this rename.
- docs/sprints/Sprint_12_Pivot_Cleanup.md -- the cleanup record.
