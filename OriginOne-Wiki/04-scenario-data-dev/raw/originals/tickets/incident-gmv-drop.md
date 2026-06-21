# 事故单：GMV 日报突然下降

## 背景

2026-06-21 早上，业务方反馈 GMV 日报里的 `net_gmv_daily` 比前一天低 18%。订单支付量没有明显下降，但退款字段出现大量空值。

## 初步现象

- `ads.ads_gmv_daily.net_gmv_daily` 异常。
- 上游 `dwd.dwd_order_wide_di.refund_amount` 从 02:00 分区开始为 null。
- 同步任务 `ods_order_di -> dwd_order_wide_di` 有 schema mismatch 告警。

## 需要 LLM-Wiki 帮忙回答

- 这个指标依赖哪些字段。
- 如果业务库 drop column，会影响哪些下游表和指标。
- 本次修复需要先改同步任务、宽表 SQL，还是指标口径。
