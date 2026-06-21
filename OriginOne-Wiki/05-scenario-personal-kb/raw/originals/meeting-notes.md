# 会议记录：任务管理助手第一次需求讨论

## 背景

现在项目材料分散在聊天、Markdown、接口草稿和 issue 里。每次要开发新功能，都要重新读一遍上下文。

## 讨论结论

- source/originals 区域必须保留原件，不能被 Agent 自动改写。
- source card 负责记录 metadata、摘要、关键事实、可信度和关联页面。
- wiki 里要有 project、concept、rules 三类页面。
- output 保存本次生成结果，比如需求草案、任务拆分、验收清单。
- 稳定规则需要从 output 回写到 wiki。

## 待确认

- unprocessed 的原件是否允许进入检索。
- 需求生成时是否必须引用 source card。
- 规则冲突时由人确认，还是由 Agent 给出候选方案。
