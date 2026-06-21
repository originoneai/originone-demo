# 影响分析：orders.drop refund_amount

## 查询条件

- table_name: `business_db.orders`
- change_type: `drop column`
- changed_field: `refund_amount`

## 受影响对象

| 层级 | 对象 | 影响 | 风险 |
|---|---|---|---|
| ODS | `ods.ods_order_di` | 同步字段缺失 | 高 |
| DWD | `dwd.dwd_order_wide_di` | `refund_amount` 与 `net_pay_amount` 计算失败 | 高 |
| ADS | `ads.ads_gmv_daily` | `refund_daily`、`net_gmv_daily` 异常 | 高 |
| 语义层 | GMV/退款指标口径 | 需要补充退款明细来源说明 | 中 |

## 改动方案

1. ODS 新增 `ods_order_refunds_di`。
2. DWD 增加退款明细聚合 CTE，按 `order_id` 关联回订单宽表。
3. ADS 保持指标名称不变，但把退款来源说明更新为 `order_refunds` 聚合。
4. wiki 回写一条规则：上游 `drop column` 不能只查字段名，还要查派生字段和指标口径。

## 需要人确认

- 退款明细表是否有全量历史数据。
- 退款发生在支付后几天内，是否需要重算历史分区。
- 业务方是否接受 `net_gmv_daily` 的口径说明变化。
