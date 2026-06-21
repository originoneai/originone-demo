# 任务问题诊断：需求生成结果缺少引用

## 问题

生成需求时，模型给出了功能列表，但没有说明来自哪份项目材料，后续无法追溯。

## 诊断

- 需求生成没有强制要求 `source_refs`。
- source card 虽然存在，但没有作为检索入口被引用。
- output 结果没有经过验收清单检查。

## 修复

1. 在需求生成提示词里强制输出 `source_refs`。
2. 只允许 processed / owner-approved source card 进入自动生成。
3. 在 output 中保留 open_questions，不能把未确认内容直接写进 wiki。

## 回写规则

稳定规则：所有自动生成需求必须带引用来源和验收清单。
