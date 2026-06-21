---
wiki_kind: source_summary
source_ref: ../raw/cards/source-card-schema-change.md
confidence: medium
---

# 来源摘要：Source Card：orders.drop refund_amount

## 一句话摘要

摘要 业务库把退款金额从订单主表迁移到退款明细表，导致依赖 `orders.refund_amount` 的同步任务、宽表 SQL 和 ADS 指标都要重算影响。 ## 关键事实 - 变更类型是 `drop column`，不是简单改名。 

## 这份 raw 适合回织到哪里

- llm-wiki
- source-summary
- data-quality
- data-warehouse-lineage
- schema-change-impact
- source-card

## 人要检查什么

- 原文有没有被误读。
- 这个摘要是否足够支持后面的长期 wiki。
- 如果要公开使用，是否需要脱敏或审批。
