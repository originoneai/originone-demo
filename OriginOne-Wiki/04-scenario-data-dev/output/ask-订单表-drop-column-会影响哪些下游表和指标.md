# 回答：订单表 drop column 会影响哪些下游表和指标

## 简短回答

表结构变更要先查 wiki 里的字段血缘、指标口径和同步任务规则，再回到 raw 的 DDL、宽表 SQL、变更单核对证据。output 里应该保存影响表清单、风险等级和改动方案，而不是只给一句“可能有影响”。

## 引用来源

1. `wiki` `wiki/source-summary-cards-source-card-schema-change-md.md`，score=5
2. `wiki` `wiki/concept-data-quality.md`，score=2
3. `raw` `raw/originals/tickets/incident-gmv-drop.md`，score=13

## 人要检查

- 这次回答是否真的被引用来源支持。
- 如果 output 里出现了长期有用的判断，要回写到 wiki，而不是只留在 output。
