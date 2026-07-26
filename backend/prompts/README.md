# CaseOS Backend Prompts

本目录用于存放后端在推理阶段使用的 prompt 模板（system / user 提示词）。

它与仓库根目录的 `prompts/` 是不同范畴：

- 根目录 `prompts/` 记录产品级 / 文档级 prompt 指南，例如《Prompt 十条原则》。
- `backend/prompts/` 仅存后端代码加载、传给 LLM 的纯文本模板与少量元数据。

建议命名约定

- `case_analysis.system.md`     — vision 模块使用的系统提示词
- `case_analysis.user.md`       — vision 模块使用的用户提示词
- `proposal.system.md`          — 方案生成阶段的系统提示词
- `proposal.user.md`            — 方案生成阶段的用户提示词

所有 prompt 模板必须遵守《Prompt 十条原则》，详见 `docs/PromptPrinciples.md`。