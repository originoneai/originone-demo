---
card_type: source_card
source_ref: ../originals/ddl/ods_order.sql
status: processed
trust: medium
owner: data-dev-demo
---

# Source Card：订单业务表 DDL

## 摘要

`business_db.orders` 是订单主表，上游同步到 `ods.ods_order_di`，下游进入 `dwd.dwd_order_wide_di` 和 `ads.ads_gmv_daily`。

## 关键事实

- `refund_amount` 曾经直接来自订单主表。
- `net_pay_amount` 和 `net_gmv_daily` 都依赖退款金额。
- 如果发生 `drop column`，需要检查 ODS 同步、DWD 宽表、ADS 指标三层。

## 关联页面

- data-warehouse-lineage
- schema-change-impact
- data-quality
