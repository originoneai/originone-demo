# OriginOne Wiki：LLM-Wiki 0-1 终端实操

你可以直接克隆这个仓库，用终端跑通一个 LLM-Wiki 0-1 案例。它不依赖 Obsidian，不需要数据库，也不先接向量库；核心动力源是 LLM runtime。

这里要先说清楚几种命令的区别：

- `smoke_test.sh` 是 smoke test（冒烟测试），只检查目录、prompt 模板、runtime 配置和设计包，不调用模型，也不会生成真正的检索结果。
- `llm_wiki_agent.sh prompt ...` 只把任务 prompt 打印出来，方便你看到 Agent 将收到什么指令。
- `llm_wiki_agent.sh manual ...` 会把该阶段的文本文件一起打包进 prompt，适合没有 Code Agent CLI、只能使用普通 LLM 对话窗口的人。
- `llm_wiki_api_runner.sh ask/weave ...` 适合没有 Code Agent CLI、但有 DeepSeek/OpenAI-compatible API Key 的人：脚本调用模型，模型返回文件级 JSON，再由脚本安全写入 `wiki/` 或 `output/`。
- `llm_wiki_agent.sh weave/ask ...` 才是真正运行 LLM-Wiki：脚本把 prompt 发给 Codex CLI、Claude Code、Gemini CLI 或你配置的其他 LLM Agent，由 Agent 读取 `raw/`、更新 `wiki/`、保存 `output/`。

所以，这套 demo 不是靠脚本硬编知识，也不是靠关键词规则假装检索。脚本只负责打包 prompt、调用 runtime、做安全落盘和基础验证；理解材料、编织 wiki、回答问题和写入结果，都是 LLM 完成的。

```text
raw/    原始材料，先留住事实
wiki/   编织后的长期知识，给检索和复用用
output/ 本次任务产物，比如回答、清单、报告草稿
```

## 为什么先不用 Obsidian

第一次搭 LLM-Wiki，最容易卡在工具、插件、同步和主题配置上，反而忘了最重要的事：

- raw 保存什么事实
- wiki 怎么从 raw 里编织出来
- output 为什么不能直接当长期知识
- 检索时为什么先读 wiki，再回 raw 查证据
- 目录为什么要从“我要取什么结果”倒推，而不是先建一堆文件夹

等这套最小流程跑通，再换成 Obsidian、Web App、数据库或 SaaS 都不迟。

## 一键检查

从 GitHub 克隆后，先复制下面这段命令检查目录、prompt 协议和设计包：

```bash
git clone https://github.com/originoneai/originone-demo.git
cd originone-demo/OriginOne-Wiki
bash scripts/smoke_test.sh
```

如果已经在 `OriginOne-Wiki/` 目录内：

```bash
bash scripts/smoke_test.sh
```

`smoke_test.sh` 会做五件事：

- 检查 LLM Agent harness。
- 检查本机 LLM runtime 配置。
- 单独运行 `map`。
- 生成 Agent/manual/API runner 的任务 prompt 或 dry-run，但不调用模型。
- 校验 `design-package/` 是否包含完整设计文件。

换句话说，`smoke_test.sh` 只能证明“这套脚手架准备好了”。要看到真正的 wiki 编织、检索回答和 output 结果，需要继续运行下面的 `weave` 或 `ask`。

## 没有 Code Agent CLI 怎么办

没有 Codex CLI、Claude Code、Gemini CLI，也可以先用 manual 模式体验 LLM-Wiki 的思路：

```bash
bash scripts/llm_wiki_agent.sh manual ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么" > /tmp/originone-wiki-manual-ask.md
```

普通 LLM 网页不能直接读取你的本地目录，所以 manual 模式会把当前 stage 里的 `raw/`、`wiki/`、`output/` 文本文件一起打包进 prompt。把这份 prompt 交给 ChatGPT、Claude、Gemini、Kimi、DeepSeek 等对话窗口后，模型会返回应该新增或更新的文件路径和完整内容。

manual 模式的边界也要讲清楚：它能帮助你理解 raw、wiki、output 怎么协作，但不会自动改仓库。想让系统自动读文件、写 wiki、保存 output，需要使用 API runner 或 `weave/ask`，也就是配置一个能调用模型并安全写文件的 runtime。

## 有 DeepSeek Key 怎么办

如果你没有 Code Agent CLI，但有 DeepSeek Key，可以走第二层 API runner。它使用 OpenAI-compatible Chat Completions 协议，默认配置就是 DeepSeek：

```bash
cp .env.example .env
```

在 `.env` 里填写：

```bash
LLM_WIKI_API_BASE_URL=https://api.deepseek.com
LLM_WIKI_API_MODEL=deepseek-v4-flash
DEEPSEEK_API_KEY=你的_deepseek_key
```

先 dry run（不调用模型）：

```bash
bash scripts/llm_wiki_api_runner.sh dry-run ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
```

确认没问题后再真实调用：

```bash
bash scripts/llm_wiki_api_runner.sh ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
```

API runner 的边界是：模型只返回 JSON，脚本负责落盘。`ask` 只能写 `output/*.md`，`weave` 只能写 `wiki/*.md`，`raw/` 永远不允许被改。这样比 manual 自动，但比 Code Agent CLI 更可控。

## 配置 LLM 和 Key

仓库不会保存任何 Key。先复制一份本地配置：

```bash
cp .env.example .env
```

如果你已经登录了 Codex CLI、Claude Code 或 Gemini CLI，通常不需要在 `.env` 里写 API Key。直接检查：

```bash
bash scripts/check_llm_runtime.sh
```

如果你的运行方式需要 API Key，就只在本机 `.env` 里填写：

```bash
DEEPSEEK_API_KEY=你的_deepseek_key
OPENAI_API_KEY=你的_key
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
GOOGLE_API_KEY=
```

如果不用默认 Codex CLI，可以在 `.env` 里指定 Agent 命令：

```bash
LLM_WIKI_AGENT=claude -p --permission-mode acceptEdits
```

`.env` 已经被 `.gitignore` 忽略，不要提交真实 Key。

## 运行 LLM 驱动流程

如果本机有 Codex CLI，可以直接运行：

```bash
bash scripts/llm_wiki_agent.sh weave 02-ingest-and-weave
bash scripts/llm_wiki_agent.sh ask 02-ingest-and-weave "LLM-Wiki 怎么把 raw 编织成 wiki"
```

脚本会把任务 prompt 发给 Codex Agent。Agent 会读取 `raw/`，更新 `wiki/`，并把本次回答保存到 `output/`。这一步会消耗你所使用 Agent 的模型额度或登录态额度。

如果你使用 Claude Code、Gemini CLI 或其他 Agent，可以显式指定：

```bash
export LLM_WIKI_AGENT='claude -p --permission-mode acceptEdits'
bash scripts/llm_wiki_agent.sh weave 02-ingest-and-weave
```

只想看 prompt，不想调用模型：

```bash
bash scripts/llm_wiki_agent.sh prompt weave 02-ingest-and-weave
bash scripts/llm_wiki_agent.sh prompt ask 02-ingest-and-weave "LLM-Wiki 怎么把 raw 编织成 wiki"
bash scripts/llm_wiki_agent.sh manual ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
bash scripts/llm_wiki_api_runner.sh dry-run ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
```

## 阶段目录

| 阶段 | 目录 | 目标 |
| --- | --- | --- |
| 00 | `00-minimal-raw-wiki-output/` | 认识 raw、wiki、output 三个基础目录 |
| 01 | `01-retrieve-first/` | 从“我要取什么”倒推“要存什么” |
| 02 | `02-ingest-and-weave/` | 把 raw 编织成 source summary 和长期 wiki |
| 03 | `03-output-and-reuse/` | 看 output 保存什么，以及如何回流为 wiki |
| 04 | `04-scenario-data-dev/` | 数仓工作场景：DDL、宽表 SQL、schema change、健康报告、影响分析 |
| 05 | `05-scenario-personal-kb/` | 个人/项目知识库：originals、source cards、规则、语义层、需求生成 |

## 单独运行某一步

如果只想体验某个阶段，可以在 `OriginOne-Wiki/` 目录内执行：

```bash
bash scripts/llm_wiki_agent.sh map
bash scripts/llm_wiki_agent.sh ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
bash scripts/llm_wiki_api_runner.sh dry-run ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
bash scripts/llm_wiki_agent.sh weave 02-ingest-and-weave
bash scripts/llm_wiki_agent.sh ask 02-ingest-and-weave "LLM-Wiki 怎么把 raw 编织成 wiki"
```

如果只想校验设计包：

```bash
bash scripts/validate_design_package.sh design-package
```

## 先记住这句话

LLM-Wiki 不是先建目录，也不是先买工具。它的第一步是问清楚：以后我要从这里取出什么结果。

取的结果清楚了，才知道 raw 要留什么，wiki 要怎么编，output 要保存什么。
