# OriginOne Demo

可运行的 OriginOneAI 示例仓库。

## 直接运行

先复制下面这段命令检查目录、prompt 协议和设计包：

```bash
git clone https://github.com/originoneai/originone-demo.git
cd originone-demo/OriginOne-Wiki
bash scripts/smoke_test.sh
```

这条命令只是 smoke test（冒烟测试）：检查目录、prompt 模板、runtime 配置和设计包是否完整。它不会调用模型，也不会生成真正的 wiki 结果。

真正的 LLM-Wiki 运行靠 LLM runtime：

- `bash scripts/llm_wiki_agent.sh prompt ...`：只打印要交给 Agent 的任务 prompt，不调用模型。
- `bash scripts/llm_wiki_agent.sh manual ...`：把 stage 文件打包成 prompt，给普通 LLM 对话窗口用。
- `bash scripts/llm_wiki_api_runner.sh ask/weave ...`：通过 OpenAI-compatible API 调用 DeepSeek/OpenAI 等模型，模型返回文件级 JSON，脚本安全写入 `wiki/` 或 `output/`。
- `bash scripts/llm_wiki_agent.sh weave ...`：调用 Agent 读取 `raw/`，编织并更新 `wiki/`。
- `bash scripts/llm_wiki_agent.sh ask ...`：调用 Agent 先检索 `wiki/`，必要时回查 `raw/`，再把本次结果写入 `output/`。

默认 Agent 是本机 Codex CLI。也可以通过 `LLM_WIKI_AGENT` 换成 Claude Code、Gemini CLI，或其他能读 stdin 并编辑仓库的 Agent。脚本本身不硬编码知识理解逻辑，只负责打包 prompt、调用 Agent 和做基础检查。

如果你没有任何 Code Agent CLI，也可以用 manual 模式：

```bash
bash scripts/llm_wiki_agent.sh manual ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么" > /tmp/originone-wiki-manual-ask.md
```

manual 模式会把该阶段的文本文件一起打包进 prompt。你可以把这份 prompt 放进普通 LLM 对话窗口，让模型返回要新增或更新的文件内容。区别是：manual 模式不会自动改仓库，需要人把结果落回对应目录；`weave/ask` 模式才会由 Agent 自动读写文件。

如果你没有 Code Agent CLI，但有 DeepSeek 或其他 OpenAI-compatible API Key，可以走第二层 API runner：

```bash
cp .env.example .env
# 在 .env 里填写 DEEPSEEK_API_KEY，默认 base_url 是 https://api.deepseek.com，默认模型是 deepseek-v4-flash
bash scripts/llm_wiki_api_runner.sh dry-run ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
bash scripts/llm_wiki_api_runner.sh ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
```

API runner 会请求 Chat Completions-compatible 接口，但不会让模型直接碰文件系统。模型只能返回 JSON；脚本只允许 `ask` 写 `output/*.md`，只允许 `weave` 写 `wiki/*.md`，并且永远不改 `raw/`。

如果需要配置 Key，只在本机复制 `.env.example`：

```bash
cp .env.example .env
bash scripts/check_llm_runtime.sh
```

不要把 `.env` 提交到仓库。

## 当前 Demo

- `OriginOne-Wiki/`：一个终端优先、LLM runtime 驱动的 LLM-Wiki 0-1 构建案例，从 `raw/`、`wiki/`、`output/` 三个基础目录开始，逐步演进到数据开发场景和个人/项目知识库场景。

## 常用命令

```bash
cd originone-demo/OriginOne-Wiki
bash scripts/llm_wiki_agent.sh map
bash scripts/llm_wiki_agent.sh manual ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
bash scripts/llm_wiki_api_runner.sh dry-run ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
bash scripts/llm_wiki_agent.sh weave 02-ingest-and-weave
bash scripts/llm_wiki_agent.sh ask 02-ingest-and-weave "LLM-Wiki 怎么把 raw 编织成 wiki"
bash scripts/check_llm_runtime.sh
bash scripts/validate_design_package.sh design-package
```

## 内容结构

- `OriginOne-Wiki/prompts/`：LLM Agent 的任务协议。
- `OriginOne-Wiki/scripts/`：Agent 调用、API runner、prompt 打包和验证脚本。
- `OriginOne-Wiki/.env.example`：本地 LLM runtime 和 Key 配置模板。
- `OriginOne-Wiki/design-package/`：LLM-Wiki 设计契约与验收材料。
