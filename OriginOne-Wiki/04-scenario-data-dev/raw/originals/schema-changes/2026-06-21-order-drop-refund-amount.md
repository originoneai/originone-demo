# 表结构变更单：orders.drop refund_amount

## 变更

- source table: `business_db.orders`
- change type: `drop column`
- field: `refund_amount`
- planned time: 2026-06-21 01:30
- reason: 业务库退款逻辑改为单独退款明细表 `business_db.order_refunds`

## 已知影响

业务应用认为订单主表不再维护退款金额。数据侧如果还从 `orders.refund_amount` 取数，会出现字段不存在或空值。

## 希望 LLM-Wiki 输出

- 受影响的 ODS/DWD/ADS 表清单。
- 受影响指标：`refund_daily`、`net_gmv_daily`。
- 改动方案：从 `order_refunds` 聚合退款金额后回填到订单宽表。
- 风险：如果只删除字段不更新宽表 SQL，GMV 报表会低估或净值异常。
