# Wiki Product Brief

## users

- AI 新手读者：不熟悉 Obsidian、向量库、RAG 或复杂知识库，只想先跑通一个能看懂的案例。
- 内容作者 / 课程讲师：需要把 LLM-Wiki 讲成可操作的 0-1 教程。
- 后续进阶学习者：看完终端 demo 后，可以继续迁移到 Web App、数据库或 SaaS。

## problem

新手第一次学 LLM-Wiki 容易被工具和目录吓住：一上来就问用什么软件、建哪些文件夹、要不要向量库，却没有先理解 raw、wiki、output 的区别，也不知道为什么要从“取什么结果”倒推“存什么材料”。

## inputs

- 手写 Markdown 原始材料。
- 两个演示场景：数据开发、个人知识库。
- 终端命令输出。
- 生成的 wiki 页面、ask output 和截图素材。

## processing

先用 deterministic Python 脚本模拟 LLM-Wiki 的最小动作：读取 raw、生成 source summary、合并 concept wiki、更新 index、按 wiki-first 顺序检索并保存 output。后续文章再解释真实 LLM 可以替换摘要和编织步骤，但目录合同不变。

## outputs

- 可运行 demo 目录。
- 每个阶段的 README。
- 公众号/教程文章草稿。
- 终端截图 PNG。
- raw/wiki/output 三层示例。
- 两个场景化演进案例。

## non_goals

- 不使用 Obsidian 作为运行环境。
- 不接外部模型 API。
- 不做多用户权限、数据库、向量库或 Web UI。
- 不把 output 自动当作长期 wiki。
- 不把这个新手 demo 伪装成生产级 OriginOne Wiki。

## success_criteria

- 新手能运行 `python3 scripts/llm_wiki_demo.py map` 理解三目录。
- 新手能运行 `weave` 看到 raw 生成 wiki 文件。
- 新手能运行 `ask` 看到检索顺序和命中来源。
- 每个阶段都有 README、raw/wiki/output 目录。
- 至少生成 5 张终端截图素材。
- 文章能从最小目录讲到两个场景演进。

## constraints

- 目标根目录固定为 `/Users/mac/Documents/OriginOne-Demo/OriginOne-Wiki`。
- 默认只用 macOS 终端、Python3、Markdown。
- 内容必须面向新手，减少术语密度。
- 示例材料必须可公开展示，不放私密聊天或真实客户数据。
