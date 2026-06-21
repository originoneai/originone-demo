# 诊断记录：net_gmv_daily 下降

## 结论

`net_gmv_daily` 下降不是业务真实下滑，而是上游订单表删除 `refund_amount` 后，DWD 宽表和 ADS 指标仍然引用旧字段，导致退款金额链路断裂。

## 排查顺序

1. 从 output 问题进入：`net_gmv_daily` 异常。
2. 检索 wiki：查 GMV 指标口径、字段血缘、schema change 规则。
3. 回 raw 查证据：DDL、宽表 SQL、ADS SQL、变更单、事故单。
4. 输出本次诊断：影响对象、风险等级、修复方案。

## 后续动作

- 修同步任务。
- 修 DWD 宽表 SQL。
- 修语义层指标说明。
- 把稳定规则回写到 wiki。
