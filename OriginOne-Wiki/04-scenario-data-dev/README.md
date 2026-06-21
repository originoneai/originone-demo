# 04 场景一：数仓日常工作的 LLM-Wiki MVP

这一阶段不再只演示“查指标口径”，而是抄数仓日常工作里的三个核心场景：

- 数据问题排查：GMV 为什么突然下降。
- 任务问题诊断：同步任务是不是因为字段变化失败。
- 数据需求开发：业务库表结构变更后，下游宽表、指标、语义层怎么改。

目标不是做一个完整数仓平台，而是做一个离线数仓项目 wiki 的最小 MVP：把 DDL、宽表 SQL、事故单、变更单先放进 raw，再编织出字段血缘、指标口径、排查规则，最后在 output 里保存本次健康报告和影响分析。

## 目录怎么倒推

这次先问以后要取什么：

- 输入 `table_name + 变更字段`，能找出受影响的下游表、指标和任务。
- 输入一个指标异常，能看到它的口径、上游字段、常见故障和排查顺序。
- 输入一段 DDL 和宽表 SQL，能生成字段映射健康度报告。

所以本阶段目录变成：

```text
raw/
  originals/           # 原始证据，不随便改
    ddl/               # 业务库和数仓表结构
    sql/               # 宽表逻辑和指标 SQL
    tickets/           # 事故单、需求单、任务失败记录
    schema-changes/    # 表结构变更单
  cards/               # source card：一份原始材料的一张入口卡
wiki/                  # 由脚本编织出的长期知识
output/
  health-check/        # 字段映射健康度报告
  impact-analysis/     # 表结构变更影响分析
  diagnosis/           # 具体事故排查结论
```

## 运行

```bash
cd /Users/mac/Documents/OriginOne-Demo/OriginOne-Wiki
python3 scripts/llm_wiki_demo.py weave 04-scenario-data-dev
python3 scripts/llm_wiki_demo.py ask 04-scenario-data-dev "订单表 drop column 会影响哪些下游表和指标"
```

## 读结果

- `wiki/concept-data-warehouse-lineage.md` 会沉淀字段血缘与表结构变更知识。
- `wiki/concept-schema-change-impact.md` 会沉淀 schema change 影响分析方法。
- `output/health-check/field-mapping-health-report.md` 是本次 DDL + SQL 的字段映射健康报告。
- `output/impact-analysis/order-drop-refund-amount.md` 是本次 `drop column` 的影响分析。

新手要看到这里的边界：raw 负责保留证据，wiki 负责长期复用，output 负责本次交付。健康报告如果变成稳定规则，再从 output 回写进 wiki。
