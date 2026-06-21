# Wiki Product Brief

## users

- 第一次搭建 LLM-Wiki 的人：不熟悉 Obsidian、向量库、RAG 或复杂知识库，只想先跑通一个能看懂的案例。
- 内容作者 / 课程讲师：需要把 LLM-Wiki 讲成可操作的 0-1 教程。
- 后续进阶学习者：看完终端 demo 后，可以继续迁移到 Web App、数据库或 SaaS。

## problem

第一次学 LLM-Wiki，容易被工具和目录吓住：一上来就问用什么软件、建哪些文件夹、要不要向量库，却没有先理解 raw、wiki、output 的区别，也不知道为什么要从“取什么结果”倒推“存什么材料”。

## inputs

- 手写 Markdown 原始材料。
- 两个演示场景：数据开发、个人知识库。
- LLM Agent 运行输出。
- OpenAI-compatible API runner 输出。
- prompt 协议文件。
- 生成的 wiki 页面和 ask output。

## processing

用 LLM runtime 执行 LLM-Wiki 的最小动作：读取 raw、生成 source summary、合并 concept wiki、更新 index、按 wiki-first 顺序检索并保存 output。第一层 manual 只打包 prompt；第二层 API runner 调用 OpenAI-compatible API 并安全写文件；第三层 LLM Agent CLI 直接在仓库里执行。shell 脚本只负责打包 prompt、调用 runtime、做安全落盘和基础健康检查，不负责理解材料。

## outputs

- 可运行 demo 目录。
- 每个阶段的 README。
- 可复现的 LLM Agent 任务 prompt。
- 可复现的 API runner prompt 和 dry-run。
- 可检查的 output 产物。
- raw/wiki/output 三层示例。
- 两个场景化演进案例。

## non_goals

- 不使用 Obsidian 作为运行环境。
- 不用硬编码规则模拟 LLM。
- 不做多用户权限、数据库、向量库或 Web UI。
- 不把 output 自动当作长期 wiki。
- 不把这个入门 demo 伪装成生产级 OriginOne Wiki。

## success_criteria

- 运行 `bash scripts/llm_wiki_agent.sh map` 后，能理解三目录。
- 运行 `weave` 后，LLM Agent 能从 raw 生成 wiki 文件。
- 运行 `ask` 后，LLM Agent 能按 wiki-first 顺序保存 output。
- 运行 `llm_wiki_api_runner.sh dry-run` 后，能看到 API runner 的模型配置、打包文件数和允许写入范围。
- 每个阶段都有 README、raw/wiki/output 目录。
- `smoke_test.sh` 能验证目录、prompt 协议和设计包。
- README 里的命令可以直接复制运行。

## constraints

- 目标根目录固定为 `originone-demo/OriginOne-Wiki`。
- 默认只用终端、Markdown、shell、Node.js 和一个 LLM runtime。
- 内容必须面向第一次搭建的人，减少术语密度。
- 示例材料必须可公开展示，不放私密聊天或真实客户数据。
