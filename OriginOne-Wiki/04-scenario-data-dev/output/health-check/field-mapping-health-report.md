# 字段映射健康度报告：orders -> dwd_order_wide -> ads_gmv_daily

## 输入

- `raw/originals/ddl/ods_order.sql`
- `raw/originals/ddl/dwd_order_wide.sql`
- `raw/originals/sql/ads_gmv_daily.sql`
- `raw/originals/schema-changes/2026-06-21-order-drop-refund-amount.md`

## 总结

健康度：不通过。

核心原因：`business_db.orders.refund_amount` 被删除，但 `dwd.dwd_order_wide_di.refund_amount` 和 `ads.ads_gmv_daily.refund_daily/net_gmv_daily` 仍然直接依赖这个字段。

## 字段映射检查

| 下游字段 | 上游字段 | 状态 | 风险 |
|---|---|---|---|
| dwd_order_wide_di.pay_amount | orders.pay_amount | ok | 低 |
| dwd_order_wide_di.refund_amount | orders.refund_amount | broken | 高 |
| dwd_order_wide_di.net_pay_amount | pay_amount - refund_amount | broken | 高 |
| ads_gmv_daily.refund_daily | dwd_order_wide_di.refund_amount | broken | 高 |
| ads_gmv_daily.net_gmv_daily | pay_amount - refund_amount | broken | 高 |

## 修复建议

1. 新增 `ods_order_refunds_di` 同步退款明细。
2. 在 DWD 层按 `order_id` 聚合退款金额。
3. 修改 `dwd_order_wide_di.refund_amount` 来源为退款明细聚合结果。
4. 重跑 `ads_gmv_daily`，并用 `net_gmv_daily = gmv_daily - refund_daily` 做校验。

## 是否回写 wiki

本报告是 output。只有“drop column 必须沿 ODS/DWD/ADS 查字段血缘”这类稳定规则，才应该回写到 wiki。
