---
card_type: source_card
source_ref: ../originals/rules-and-semantic-layer.md
status: processed
trust: medium
owner: project-owner-demo
---

# Source Card：规则与语义层

## 摘要

项目把 raw/originals、raw/cards、wiki、output 分成不同职责，并用语义层维护 source、source_card、requirement、acceptance_check、rule 等命名。

## 关键事实

- source card 必须有处理状态和可信度。
- 需求生成只能引用 processed 或 owner-approved 的来源。
- output 不能自动覆盖 wiki。

## 处理状态

processed：可以进入规则 wiki 和语义层 wiki。
