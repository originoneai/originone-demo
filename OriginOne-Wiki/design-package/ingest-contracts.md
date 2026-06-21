# Ingest Contracts

| source | trigger | raw_format | preprocessing | metadata | authority | quality_gate |
|---|---|---|---|---|---|---|
| 入门概念材料 | 手动写入 | Markdown | 提取标题、digest、concept key | stage, filename | demo raw evidence | weave 生成 source summary |
| 数据开发材料 | 手动写入 | DDL / SQL / incident ticket / schema change / source card | 识别字段映射、指标口径、血缘、变更类型、任务诊断点 | scenario=data-dev, source_ref, status, trust | demo raw evidence | ask 命中 data-quality / lineage / schema-change wiki |
| 个人/项目知识库材料 | 手动写入 | project brief / meeting note / API sketch / rule doc / source card | 识别项目目标、接口、规则、语义层、需求生成约束 | scenario=personal-kb, source_ref, status, trust | demo raw evidence | ask 命中 project-wiki / semantic-layer-rules wiki |
| 终端命令输出 | 运行脚本 | stdout text | 保留在终端或 output 文件中 | command, timestamp | demo evidence | smoke test 通过 |

## Notes

raw 文件在 demo 里保持人工可读，不自动删除或覆盖。`weave` 生成的 wiki 可以重复运行，便于新手观察“同一份 raw 如何变成长期知识”。
