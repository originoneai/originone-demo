# Directory Blueprint

## Tree

    OriginOne-Wiki/
    ├── .env.example
    ├── README.md
    ├── prompts/
    │   ├── llm-wiki-system.md
    │   └── actions/{weave,ask,health-check}.md
    ├── scripts/
    │   ├── llm_wiki_agent.sh
    │   ├── llm_wiki_api_runner.sh
    │   ├── check_llm_runtime.sh
    │   ├── lib/{load_env.sh,llm_wiki_api_runner.mjs}
    │   ├── smoke_test.sh
    │   └── validate_design_package.sh
    ├── design-package/
    ├── 00-minimal-raw-wiki-output/
    │   ├── raw/
    │   ├── wiki/
    │   ├── output/
    │   └── README.md
    ├── 01-retrieve-first/
    ├── 02-ingest-and-weave/
    ├── 03-output-and-reuse/
    ├── 04-scenario-data-dev/
    │   ├── raw/originals/{ddl,sql,tickets,schema-changes}/
    │   ├── raw/cards/
    │   └── output/{health-check,impact-analysis,diagnosis}/
    └── 05-scenario-personal-kb/
        ├── raw/originals/
        ├── raw/cards/
        └── output/{requirements,rules,diagnosis}/

## Mapping

| path | serves_contract | owner | required | notes |
|---|---|---|---|---|
| README.md | Product Brief | author | MVP | demo 总入口 |
| .env.example | Runtime Config | author | MVP | 本地 LLM Agent 与 API Key 配置模板，不保存真实 Key |
| prompts/ | LLM Agent Contract | author | MVP | 定义 weave、ask、health-check 的 Agent 任务协议 |
| scripts/ | Operational State | shell harness | MVP | Agent 调用、API runner、prompt/manual 打包、runtime 检查、smoke test 和设计包校验 |
| design-package/ | Governance | author | MVP | 设计合同与验收 |
| 00-minimal-raw-wiki-output/ | Retrieval Contract: basic explanation | author | MVP | 最小三目录 |
| 01-retrieve-first/ | Retrieval Contract: retrieve-first | author | MVP | 由取倒推存 |
| 02-ingest-and-weave/ | Ingest Contract: weave raw to wiki | script | MVP | 编织演示 |
| 03-output-and-reuse/ | Retrieval Contract: output reuse | author | MVP | output 边界 |
| 04-scenario-data-dev/ | Retrieval Contract: data-dev scenario | author | MVP | 数仓场景，覆盖 DDL、宽表 SQL、schema change、健康报告、影响分析 |
| 05-scenario-personal-kb/ | Retrieval Contract: personal/project scenario | author | MVP | 个人/项目知识库，覆盖 originals、source cards、规则、语义层、需求生成 |
| raw/originals/ | Ingest Contract: immutable raw originals | author | MVP | 04/05 的嵌套原件层，保留 DDL、SQL、会议记录、接口草稿等证据 |
| raw/cards/ | Ingest Contract: source cards | author | MVP | 04/05 的来源卡片层，记录 source_ref、status、trust、owner |
| output/{requirements,rules,diagnosis}/ | Retrieval Contract: project output package | author | MVP | 05 的需求生成、规则维护和任务诊断产物 |

## Deferred Directories

- `db/`：暂不需要数据库。
- `frontend/`：暂不做 Web UI。
- `private/`：本 demo 不放真实私有资料。
- `vector/`：入门阶段不引入向量库。
