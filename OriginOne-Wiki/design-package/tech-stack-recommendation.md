# Tech Stack Recommendation

## requirements_summary

- user_count：单人作者 + 第一次搭建的人本地运行。
- collaboration_intensity：低。
- privacy_boundary：public-safe demo。
- automation_frequency：手动运行。
- source_volume：小。
- retrieval_complexity：LLM Agent 按 wiki-first 读取，重点是展示流程和证据边界。
- runtime_availability：部分新手没有 Codex CLI、Claude Code 或 Gemini CLI，但可能有 DeepSeek/OpenAI-compatible API Key。
- sharing_requirement：可运行目录包。
- audit_requirement：轻量，可用 output 和 smoke test 说明。
- maintenance_capacity：低。

## recommendation

使用 Markdown + manual prompt fallback + OpenAI-compatible API runner + LLM Agent + shell harness。

原因：

- 第一次运行不用先安装复杂知识库工具。
- 文件结构透明，能直接看到 raw/wiki/output。
- LLM Agent 负责理解、编织和回答，避免把规则脚本误讲成知识引擎。
- API runner 覆盖“有 DeepSeek Key 但没有 Code Agent CLI”的读者：模型返回文件级 JSON，脚本只做安全落盘。
- shell harness 能打包 prompt、调用 Agent 或 API runner、生成检查结果。
- manual 模式能把 stage 文本文件打包成自包含 prompt，让没有 Code Agent CLI 的人也能用普通 LLM 对话窗口体验流程。
- `.env.example` 提供配置模板，真实 `.env` 留在本机并被 git 忽略。

## rejected_options

- Obsidian：会让第一次运行的人先卡在工具配置，不适合作为第一篇 0-1 案例。
- 向量库：会把注意力从“目录合同和知识生命周期”转移到检索技术。
- Web App：展示效果更好，但会增加前端、服务和端口复杂度。
- 直接把 API 返回文本写文件：风险太高，容易覆盖 raw 或把半截回答写入 wiki。本案例采用文件级 JSON + 路径白名单：`ask` 只能写 `output/*.md`，`weave` 只能写 `wiki/*.md`。

## migration_path

1. 当前终端 + LLM Agent demo。
2. manual prompt fallback，覆盖没有 Code Agent CLI 的读者。
3. OpenAI-compatible API runner，覆盖有 DeepSeek/OpenAI-compatible Key 的读者。
4. 增加运行日志、成本记录和 health check。
5. 接入批量调度和多模型路由。
6. 转成 Web UI 或 SaaS。
7. 再考虑向量检索、权限和多用户。

## operational_cost

`smoke_test.sh` 不消耗模型。`prompt/manual` 和 API runner `dry-run` 只生成 prompt 或检查请求，不在脚本里调用模型。真正运行 `llm_wiki_api_runner.sh ask/weave` 会消耗所选 API provider 的额度；真正运行 `llm_wiki_agent.sh weave/ask` 会消耗所选 LLM Agent 的模型额度。manual 模式的模型消耗发生在用户选择的普通 LLM 对话窗口里。API Key 只放在本机 `.env` 或对应 CLI 的登录态里，不进入仓库。
