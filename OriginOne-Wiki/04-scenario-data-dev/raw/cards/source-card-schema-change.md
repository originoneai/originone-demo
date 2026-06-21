---
card_type: source_card
source_ref: ../originals/schema-changes/2026-06-21-order-drop-refund-amount.md
status: processed
trust: medium
owner: data-dev-demo
---

# Source Card：orders.drop refund_amount

## 摘要

业务库把退款金额从订单主表迁移到退款明细表，导致依赖 `orders.refund_amount` 的同步任务、宽表 SQL 和 ADS 指标都要重算影响。

## 关键事实

- 变更类型是 `drop column`，不是简单改名。
- 受影响指标至少包括 `refund_daily` 和 `net_gmv_daily`。
- 修复方向是新增 `order_refunds` 聚合链路，而不是在下游硬填 0。

## 处理状态

processed：已经可以进入 wiki 编织，并作为 impact-analysis 的证据。
