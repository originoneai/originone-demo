# OriginOne Wiki 新手终端 Demo

这是一个给新手看的 LLM-Wiki 0-1 构建案例。它不依赖 Obsidian，不需要数据库，不需要外部模型 API；先用终端和 Markdown 跑通最小闭环：

```text
raw/    原始材料，先留住事实
wiki/   编织后的长期知识，给检索和复用用
output/ 本次任务产物，比如回答、清单、文章草稿
```

## 为什么先不用 Obsidian

这套案例的目标是先把 LLM-Wiki 的基本动作讲清楚。新手最容易一开始就卡在工具、插件、同步和主题配置上，反而忘了最重要的事：

- raw 保存什么事实
- wiki 怎么从 raw 里编织出来
- output 为什么不能直接当长期知识
- 检索时为什么先读 wiki，再回 raw 查证据
- 目录为什么要从“我要取什么结果”倒推，而不是先建一堆文件夹

等这套最小流程跑通，再换成 Obsidian、Web App、数据库或 SaaS 都不迟。

## 阶段目录

| 阶段 | 目录 | 目标 |
| --- | --- | --- |
| 00 | `00-minimal-raw-wiki-output/` | 认识 raw、wiki、output 三个基础目录 |
| 01 | `01-retrieve-first/` | 从“我要取什么”倒推“要存什么” |
| 02 | `02-ingest-and-weave/` | 把 raw 编织成 source summary 和长期 wiki |
| 03 | `03-output-and-reuse/` | 看 output 保存什么，以及如何回流为 wiki |
| 04 | `04-scenario-data-dev/` | 数仓工作场景：DDL、宽表 SQL、schema change、健康报告、影响分析 |
| 05 | `05-scenario-personal-kb/` | 个人/项目知识库：originals、source cards、规则、语义层、需求生成 |

## 快速运行

```bash
cd /Users/mac/Documents/OriginOne-Demo/OriginOne-Wiki
python3 scripts/llm_wiki_demo.py map
python3 scripts/llm_wiki_demo.py ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
python3 scripts/llm_wiki_demo.py weave 02-ingest-and-weave
python3 scripts/llm_wiki_demo.py ask 02-ingest-and-weave "LLM-Wiki 怎么把 raw 编织成 wiki"
python3 scripts/llm_wiki_demo.py demo-all
```

如果要重新生成文章截图，使用这条命令：

```bash
/Users/mac/miniconda3/bin/python3 scripts/make_terminal_screenshots.py assets/screenshots/*.txt
```

## 文章草稿

完整文章草稿在：

```text
article/LLM-Wiki-0-1-新手终端案例.md
```

截图素材会生成在：

```text
assets/screenshots/
```

## 新手记住这句话

LLM-Wiki 不是先建目录，也不是先买工具。它的第一步是问清楚：以后我要从这里取出什么结果。

取的结果清楚了，才知道 raw 要留什么，wiki 要怎么编，output 要保存什么。
