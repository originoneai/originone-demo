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

## 三层使用示例

### 第一层：manual，只有普通 LLM 对话窗口

适合没有 Codex CLI、Claude Code、Gemini CLI，也没有 API Key 的读者。它只生成 prompt，不调用模型，不改仓库。

```bash
cd originone-demo/OriginOne-Wiki

# ask：把 stage 文件和问题打包成 prompt
bash scripts/llm_wiki_agent.sh manual ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么" > /tmp/originone-wiki-manual-ask.md

# weave：把 raw/wiki/output 一起打包给普通 LLM，让它返回应更新的 wiki 文件内容
bash scripts/llm_wiki_agent.sh manual weave 02-ingest-and-weave > /tmp/originone-wiki-manual-weave.md
```

接下来，把 `/tmp/originone-wiki-manual-ask.md` 或 `/tmp/originone-wiki-manual-weave.md` 的内容复制到普通 LLM 对话窗口。模型会返回建议新增或更新的文件路径和完整内容，你再手动放回对应目录。

### 第二层：API runner，有 DeepSeek/OpenAI-compatible Key

适合没有 Code Agent CLI，但有 DeepSeek、OpenAI 或其他 OpenAI-compatible API Key 的读者。它会调用模型，并由脚本安全写文件。

```bash
cd originone-demo/OriginOne-Wiki
cp .env.example .env
```

在 `.env` 里填写：

```bash
LLM_WIKI_API_BASE_URL=https://api.deepseek.com
LLM_WIKI_API_MODEL=deepseek-v4-flash
DEEPSEEK_API_KEY=你的_deepseek_key
```

先 dry run，不调用模型，只看请求边界：

```bash
bash scripts/llm_wiki_api_runner.sh dry-run ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
```

再真实调用：

```bash
# ask 只允许写 output/*.md
bash scripts/llm_wiki_api_runner.sh ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"

# weave 只允许写 wiki/*.md
bash scripts/llm_wiki_api_runner.sh weave 02-ingest-and-weave
```

API runner 的关键边界：模型只能返回 JSON，脚本负责落盘；`raw/` 永远不允许被改。

### 第三层：Code Agent CLI，有 Codex/Claude/Gemini

适合已经安装 Codex CLI、Claude Code、Gemini CLI，或其他能读 stdin 并编辑仓库的 Agent 的读者。

```bash
cd originone-demo/OriginOne-Wiki
bash scripts/check_llm_runtime.sh

# 默认优先使用本机 codex
bash scripts/llm_wiki_agent.sh weave 02-ingest-and-weave
bash scripts/llm_wiki_agent.sh ask 02-ingest-and-weave "LLM-Wiki 怎么把 raw 编织成 wiki"
```

如果不用默认 Codex CLI，可以在 `.env` 里配置：

```bash
LLM_WIKI_AGENT=claude -p --permission-mode acceptEdits
```

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
