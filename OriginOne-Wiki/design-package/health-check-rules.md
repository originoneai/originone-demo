# Health Check Rules

## triggers

- 每次新增 raw 后。
- 每次运行 weave 后。
- 每次 output 准备作为长期知识回写前。
- 每次 smoke test 运行后。

## P0

- raw 目录为空。
- stage 缺少 raw/wiki/output 任一目录。
- ask 没有保存 output。
- `smoke_test.sh` 运行失败。
- prompt 协议缺失，导致 LLM Agent 不知道如何 weave 或 ask。
- `.env.example` 缺失，导致运行者不知道 Key 应该放在哪里。
- manual 模式无法生成自包含 prompt，导致没有 Code Agent CLI 的读者无法继续。
- API runner 无法 dry-run，导致有 DeepSeek/OpenAI-compatible Key 的读者无法确认请求边界。
- API runner 允许写 `raw/` 或 stage 外文件。

## P1

- wiki 没有 index.md。
- source summary 没有 source_ref。
- output 里没有引用来源。
- data-dev 或 personal 场景没有独立 README。
- 04/05 的 `raw/originals` 有材料但 `weave` 没有生成对应 source summary。
- source card 缺少 `status`、`trust` 或 `source_ref`。

## P2

- README 只讲概念，没有运行命令。
- README 术语太密，没有解释 raw/wiki/output。
- README 没有解释没有 Code Agent CLI 时怎么运行。
- README 没有解释 DeepSeek/OpenAI-compatible API runner 的适用条件和安全边界。
- README 或脚本 help 没有给出三层 ask/weave 使用示例。
- output 回写 wiki 的边界没有讲清楚。
- 04 没有解释 DDL/SQL/schema change 怎么进入影响分析。
- 05 没有解释 originals/cards/wiki/output 的职责差异。

## auto_detectable

- 目录是否存在。
- 文件是否存在。
- 脚本是否能运行。
- prompt 是否能生成。
- manual prompt 是否包含 stage 文件内容。
- API runner dry-run 是否能生成。
- API runner prompt 是否包含 JSON schema 和路径白名单。
- runtime 检查脚本是否能说明当前 Agent 和 Key 状态。
- smoke test 是否通过。
- design-package 是否通过 validator。

## agent_review_required

- README 是否适合第一次搭建的人。
- 场景是否贴近日常工作。
- 是否把 output 和 wiki 混在一起。
- 是否解释了由取倒推存。

## owner_approval_required

- 是否要接真实 LLM API。
- 是否要单独制作课程材料。
- 是否加入更多场景。

## fix_queue

- 缺目录：补目录和 README。
- smoke test 失败：按失败步骤修复脚本、目录或设计包。
- LLM Agent 运行失败：先用 `prompt` 命令打印任务，检查 stage、question 和权限边界；没有 Code Agent CLI 时改用 `manual`。
- API runner 运行失败：先用 `dry-run` 检查 base_url、model、bundled_files 和 allowed_writes，再检查 `.env` 中的 Key。
- Key 泄露风险：确认 `.env` 没有被 git 跟踪，文档只提交 `.env.example`。
- 检索效果不清楚：补 raw 材料或 wiki 说明。
- 04 场景过轻：补 DDL、宽表 SQL、schema change、health-check、impact-analysis。
- 05 场景过轻：补 project brief、source card、rules、semantic layer、requirements output。
- 第一次搭建的人读不懂：降低术语密度，补操作步骤。
