# Storage Architecture

| layer | purpose | stores | serves_contracts | mvp_status | owner |
|---|---|---|---|---|---|
| Raw Evidence | 保存原始材料 | `*/raw/*.md`, `*/raw/originals/**`, `*/raw/cards/**` | ingest contracts | MVP | author |
| Compiled Wiki | 保存编织后的长期知识 | `*/wiki/index.md`, `source-summary-*`, `concept-*` | retrieval contracts | MVP | script + author |
| Operational State | 保存运行过程 | Agent prompt、API runner prompt、终端输出、生成日志、smoke test | validation | MVP | shell harness |
| Retrieval Package | 支持检索和运行验证 | `wiki/index.md`, `output/ask-*.md`, `prompts/**`, `scripts/smoke_test.sh`, manual prompt bundle, API runner dry-run | ask and validation | MVP | LLM runtime + shell harness |
| Governance | 入门安全边界 | README、检查清单、health rules | quality gate | MVP | author |

manual prompt bundle 属于 Retrieval Package 的降级形态，用来服务没有 Code Agent CLI 的读者。

## Deferred Layers

- 数据库、对象存储、向量库、权限系统、审批流、Web UI。
- 多模型路由、批量调度和自动重试。
- 自动化发布与同步策略。
