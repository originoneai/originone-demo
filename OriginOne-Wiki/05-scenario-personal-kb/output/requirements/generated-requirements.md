# 自动生成需求草案：导入原始材料并生成 Source Card

## 用户故事

作为个人开发者，我希望把会议记录、接口草稿、规则文档导入项目知识库，并为每份材料生成 source card，这样后续生成需求和任务时可以追溯来源。

## 功能范围

- 上传或粘贴一份原始材料。
- 保存到 `raw/originals`。
- 创建一张 `raw/cards` source card。
- 标记处理状态：processed / unprocessed / owner-approved。
- 在需求生成时引用 source card。

## 验收清单

- 导入材料后，原文没有被改写。
- source card 包含 source_ref、status、trust、owner。
- unprocessed 材料默认不进入自动需求生成。
- 生成的需求必须列出 source_refs。

## 开放问题

- source card 是否允许手动编辑摘要。
- owner-approved 是否需要审批记录。
- 规则冲突是否进入 output/diagnosis。
