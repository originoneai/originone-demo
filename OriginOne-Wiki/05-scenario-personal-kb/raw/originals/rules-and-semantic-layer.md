# 规则与语义层说明

## 项目规则

- raw/originals 是原始证据层，不做自动改写。
- raw/cards 是来源卡片层，记录 metadata、摘要、可信度和处理状态。
- wiki 是长期知识层，沉淀 project、concept、rules、semantic mapping。
- output 是任务产物层，保存本次生成的需求、诊断、清单。

## 语义层

这里的语义层不是一个玄学概念，而是项目里的可解释命名和规则集合：

- `source` 表示原始材料。
- `source_card` 表示可检索入口。
- `requirement` 表示被确认过的需求。
- `acceptance_check` 表示验收标准。
- `rule` 表示稳定约束。

## 维护规则

- 需求生成只能引用 processed 或 owner-approved 的 source card。
- output 不能自动覆盖 wiki。
- 如果规则冲突，output 里先生成候选方案，再由人确认回写。
