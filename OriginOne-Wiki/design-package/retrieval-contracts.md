# Retrieval Contracts

| consumer | trigger | timing | output_form | next_action | accuracy_need | privacy_boundary |
|---|---|---|---|---|---|---|
| 新手读者 | 第一次理解 raw/wiki/output | ad hoc | 终端解释 + README | 照着运行最小 demo | medium | local public-safe |
| 新手读者 | 想知道为什么由取倒推存 | ad hoc | 带引用的 ask output | 修改自己的目录设计 | high | local public-safe |
| 数据开发读者 | 业务库表结构变更或指标异常 | ad hoc | 字段映射健康报告 + schema change 影响分析 | 更新同步任务、宽表 SQL、指标口径或语义层说明 | high | demo-only |
| 个人/项目知识库读者 | 新需求、任务诊断或规则维护 | ad hoc | 需求草案 + 验收清单 + 规则维护建议 | 人工确认后回写 project/rules/semantic wiki | high | personal demo |

## Notes

检索路径必须先看 `wiki/index.md` 和长期 wiki 页面；如果 wiki 不够，再回 raw 查证据。这个 demo 暂时用简单关键词评分模拟检索，脚本不是模型，它只是让新手先看见流程。
