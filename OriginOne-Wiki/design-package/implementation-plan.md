# Implementation Plan

## MVP

- 创建 `OriginOne-Wiki` 根目录。
- 每个阶段创建 `raw/wiki/output/README.md`。
- 写入可公开演示的 raw 材料。
- 在 04/05 增加 nested raw：`raw/originals` 和 `raw/cards`。
- 在 04 增加数据开发 output：字段映射健康报告、schema change 影响分析、事故诊断。
- 在 05 增加项目知识库 output：需求草案、规则维护清单、任务诊断。
- 提供 `prompts/`，把 `weave`、`ask`、`health-check` 定义成 LLM Agent 可执行的任务协议。
- 提供 `.env.example`，说明本地 LLM Agent 和 API Key 怎么配置，真实 `.env` 不进仓库。
- 提供 `llm_wiki_agent.sh`，支持 `map`、`prompt`、`manual`、`weave`、`ask`、`health-check`、`demo-all`。
- 提供 `llm_wiki_api_runner.sh`，支持 OpenAI-compatible API 的 `prompt`、`dry-run`、`ask`、`weave`。
- API runner 使用文件级 JSON 和路径白名单：`ask` 只写 `output/*.md`，`weave` 只写 `wiki/*.md`，拒绝写 `raw/`。
- 提供 `check_llm_runtime.sh`，检查本机 Agent CLI 和 API Key 环境变量。
- 提供 `smoke_test.sh`，clone 后可以验证目录、prompt 和设计包，不消耗模型。
- 提供 manual prompt fallback，让没有 Code Agent CLI 的读者也能把 stage 文件打包给普通 LLM 对话窗口。
- 提供 `validate_design_package.sh`，让设计包校验不依赖本机私有路径。
- 运行每个阶段并保存可检查 output。

## vNext

- 增加模型路由、运行日志和成本记录。
- 增加 `wiki/log.md`。
- 扩展 health check：缺 source_ref、output 未回写、wiki 无证据。
- 增加更多场景：销售拜访、会议纪要、课程学习。
- 给 04 增加真实字段血缘 parser，给 05 增加 source card 审批状态流转。

## Deferred

- Obsidian vault。
- Web App。
- 多用户权限。
- 数据库和向量库。
- 自动化同步与发布策略。

## validation_commands

```bash
git clone https://github.com/originoneai/originone-demo.git
cd originone-demo/OriginOne-Wiki
bash scripts/llm_wiki_agent.sh map
bash scripts/check_llm_runtime.sh --soft
bash scripts/llm_wiki_agent.sh prompt weave 02-ingest-and-weave
bash scripts/llm_wiki_agent.sh prompt ask 02-ingest-and-weave "LLM-Wiki 怎么把 raw 编织成 wiki"
bash scripts/llm_wiki_agent.sh manual ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
bash scripts/llm_wiki_api_runner.sh dry-run ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
bash scripts/llm_wiki_api_runner.sh prompt ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
bash scripts/smoke_test.sh
bash scripts/validate_design_package.sh design-package
```

## acceptance_checklist

- [ ] 每个阶段都有 raw/wiki/output。
- [ ] 04/05 的 nested raw 能被 `weave` 递归读取。
- [ ] 04 能展示 health-check 和 impact-analysis。
- [ ] 05 能展示 requirements、rules、diagnosis。
- [ ] `weave` 由 LLM Agent 生成 source summary 和 concept。
- [ ] `ask` 由 LLM Agent 保存 output。
- [ ] `manual` 能生成包含 stage 文件内容的自包含 prompt。
- [ ] API runner `dry-run` 能显示 base_url、model、bundled_files、allowed_writes。
- [ ] API runner prompt 包含 Required JSON schema 和 Bundled Stage Files。
- [ ] API runner 安全策略拒绝写 `raw/` 和 stage 外文件。
- [ ] `.env.example` 说明 Key 放在本地 `.env`，真实 Key 不进仓库。
- [ ] `check_llm_runtime.sh` 能显示当前可用的 Agent/runtime。
- [ ] `smoke_test.sh` 能从 clean clone 后运行。
- [ ] README 的一键命令能复制粘贴执行。
- [ ] 设计包通过 validator。
