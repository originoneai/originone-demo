# 规则维护清单

## 本次要维护的规则

- raw/originals 不自动改写。
- raw/cards 记录 metadata、摘要、可信度、处理状态。
- output 不自动覆盖 wiki。
- 稳定规则必须人工确认后回写。

## 检查项

| 检查项 | 通过条件 | 处理 |
|---|---|---|
| 原件不可变 | 原始文件保留 source_ref | 必须通过 |
| 来源卡片完整 | status/trust/owner 不为空 | 必须通过 |
| 需求可追溯 | generated requirements 带 source_refs | 必须通过 |
| 规则冲突处理 | output 先给候选方案 | 人工确认 |

## 回写建议

把“output 不能自动覆盖 wiki”和“需求生成只能引用 processed 或 owner-approved source card”回写到长期规则页。
