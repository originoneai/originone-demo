# Ingest Contracts

| source | trigger | raw_format | preprocessing | metadata | authority | quality_gate |
|---|---|---|---|---|---|---|
| 入门概念材料 | 手动写入 | Markdown | 提取标题、digest、concept key | stage, filename | demo raw evidence | weave 生成 source summary |
| 数据开发材料 | 手动写入 | DDL / SQL / incident ticket / schema change / source card | 识别字段映射、指标口径、血缘、变更类型、任务诊断点 | scenario=data-dev, source_ref, status, trust | demo raw evidence | ask 命中 data-quality / lineage / schema-change wiki |
| 个人/项目知识库材料 | 手动写入 | project brief / meeting note / API sketch / rule doc / source card | 识别项目目标、接口、规则、语义层、需求生成约束 | scenario=personal-kb, source_ref, status, trust | demo raw evidence | ask 命中 project-wiki / semantic-layer-rules wiki |
| LLM Agent 任务 prompt | 运行 `prompt/weave/ask` | Markdown prompt | 交给 Agent 读取 raw 并写 wiki/output | action, stage, question | execution contract | prompt 能生成且包含 stage contract |
| Manual prompt bundle | 运行 `manual` | Markdown prompt + stage 文件内容 | 给普通 LLM 对话窗口使用，不自动写文件 | action, stage, question, bundled_files | fallback contract | prompt 包含 Manual Chat Mode 和 Bundled Stage Files |
| API runner request | 运行 `llm_wiki_api_runner.sh dry-run/ask/weave` | Markdown prompt + stage 文件内容 + JSON schema | 给 OpenAI-compatible API 使用，返回文件级 JSON 后安全落盘 | base_url, model, action, stage, question, bundled_files | API runner contract | dry-run 能显示 allowed_writes，真实运行只写 wiki/output |

## Notes

raw 文件在 demo 里保持人工可读，不自动删除或覆盖。`weave` 由 LLM runtime 执行，可以重复运行，便于观察“同一份 raw 如何变成长期知识”。没有 Code Agent CLI 时，manual 模式只生成包含材料的 prompt，不直接写 `wiki/` 或 `output/`。API runner 可以自动写文件，但只接受模型返回的文件级 JSON，并拒绝写入 `raw/`。
