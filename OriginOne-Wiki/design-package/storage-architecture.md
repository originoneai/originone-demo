# Storage Architecture

| layer | purpose | stores | serves_contracts | mvp_status | owner |
|---|---|---|---|---|---|
| Raw Evidence | 保存原始材料 | `*/raw/*.md`, `*/raw/originals/**`, `*/raw/cards/**` | ingest contracts | MVP | author |
| Compiled Wiki | 保存编织后的长期知识 | `*/wiki/index.md`, `source-summary-*`, `concept-*` | retrieval contracts | MVP | script + author |
| Operational State | 保存运行过程 | 终端 transcript、生成日志 | screenshot and validation | MVP | script |
| Retrieval Package | 支持检索和文章展示 | `wiki/index.md`, `output/ask-*.md`, screenshots | ask and article | MVP | script |
| Release Share | 对外展示文章和截图 | `article/`, `assets/screenshots/` | writing output | MVP | author |
| Governance | 新手安全边界 | README、检查清单、health rules | quality gate | MVP | author |

## Deferred Layers

- 数据库、对象存储、向量库、权限系统、审批流、Web UI。
- 外部 LLM API 真实摘要。
- 自动发布到远端。
