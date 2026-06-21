# Retrieval Contracts

| consumer | trigger | timing | output_form | next_action | accuracy_need | privacy_boundary |
|---|---|---|---|---|---|---|
| 第一次搭建的人 | 第一次理解 raw/wiki/output | ad hoc | 终端解释 + README + Agent prompt | 照着运行最小 demo | medium | local public-safe |
| 没有 Code Agent CLI 的读者 | 只能使用普通 LLM 对话窗口 | ad hoc | manual prompt bundle | 在普通 LLM 对话窗口里得到文件级建议 | medium | local public-safe |
| 有 DeepSeek/OpenAI-compatible Key 的读者 | 没有 Code Agent CLI 但希望脚本自动写文件 | ad hoc | API runner output | 让脚本安全写入 wiki/output | high | local public-safe |
| 第一次搭建的人 | 想知道为什么由取倒推存 | ad hoc | LLM Agent 生成的 ask output | 修改自己的目录设计 | high | local public-safe |
| 数据开发使用者 | 业务库表结构变更或指标异常 | ad hoc | 字段映射健康报告 + schema change 影响分析 | 更新同步任务、宽表 SQL、指标口径或语义层说明 | high | public demo data |
| 项目知识库使用者 | 新需求、任务诊断或规则维护 | ad hoc | 需求草案 + 验收清单 + 规则维护建议 | 人工确认后回写 project/rules/semantic wiki | high | personal demo |

## Notes

检索路径必须先看 `wiki/index.md` 和长期 wiki 页面；如果 wiki 不够，再回 raw 查证据。脚本只生成任务 prompt 和调用 runtime，判断、编织和回答由 LLM 完成。没有 Code Agent CLI 时，`manual` 会把 stage 文本文件打包进 prompt，让普通 LLM 对话窗口也能按同一套检索合同工作，但不会自动写回仓库。API runner 会调用 OpenAI-compatible API，让模型返回文件级 JSON，再由脚本按路径白名单写入 `wiki/` 或 `output/`。
