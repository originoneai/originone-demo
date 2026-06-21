---
wiki_kind: source_summary
source_ref: ../raw/cards/source-card-ods-order.md
confidence: medium
---

# 来源摘要：Source Card：订单业务表 DDL

## 一句话摘要

摘要 `business_db.orders` 是订单主表，上游同步到 `ods.ods_order_di`，下游进入 `dwd.dwd_order_wide_di` 和 `ads.ads_gmv_daily`。 ## 关键事实 - `re

## 这份 raw 适合回织到哪里

- source-summary
- data-quality
- data-warehouse-lineage
- schema-change-impact
- source-card

## 人要检查什么

- 原文有没有被误读。
- 这个摘要是否足够支持后面的长期 wiki。
- 如果要公开使用，是否需要脱敏或审批。
