# 04 · MCP 工具循环 / Harness（配套 C1-LLM-03A / 03B）

对应课程文章：《真 MCP 工具循环：让模型自己一步步把 schema 问出来》《回看：你搭的这个循环叫 Harness》。

前一课（03）你搭好了一台只暴露四个只读工具的 MCP Server。这一课，把这四个工具交给模型，
让它**自己**一步步查库——你不再往 Prompt 里塞任何表结构：

```
模型开局对库一无所知
  → list_tables       有哪些表？
  → describe_table     这张表什么结构、什么口径？
  → sample_values      payment_status 到底有哪些取值？
  → execute_query      写出 SQL，执行
  → 拿到结果，用一句话回答
```

这套"想—调工具—看结果—再想"的循环，就是 **Harness**（也就是 ReAct / Tool Calling 的骨架）。

## 文件

| 文件 | 作用 |
|---|---|
| `cli.py` | **交互终端（主入口）**：敲问题，看模型一步步调工具的循环真实发生 |
| `harness.py` | 循环核心：工具 schema、dispatch、`run_loop`（DeepSeek function calling 驱动） |
| `mcp_server.py` | 四个只读工具（与 03 同款，vendored 一份保持本文件夹可独立跑） |
| `db.py` / `data_dictionary.py` / `guard.py` | 连接层 / 口径注释 / 只读门禁 |
| `build_dataset.py` | 生成 SQLite 样例库 |
| `test_lab.py` | mock 模型跑通整条循环 + 止损 + DeepSeek 真实链路（先探索再执行） |

## 快速开始

```bash
pip install -r requirements.txt
export DEEPSEEK_API_KEY=你的key
python cli.py
```

问一句「最近 30 天每天的支付订单数和支付金额是多少？」，屏幕上会一步步打印：

```
第1步 · 模型调用工具 → list_tables()
         工具返回 ← 表：ord_order_main、ord_order_item、prod_category、prod_product
第2步 · 模型调用工具 → describe_table(table=ord_order_main)
         工具返回 ← ord_order_main 共 11 个字段
第3步 · 模型调用工具 → sample_values(table=ord_order_main, column=payment_status)
         工具返回 ← payment_status 取值：[2, 3, 1, 0]
第4步 · 模型调用工具 → execute_query(sql=SELECT ...)
         工具返回 ← 执行成功，返回 N 行
✅ 模型的回答：...
```

## 这一课要你看见的两件事

1. **"用到哪、取到哪"** —— 全程没有一次性把整库 DDL 塞进 Prompt。模型只把这道题真正需要的
   那几张表、那几个字段问了出来。这正是 01B 讲的"上下文该拉不该推"的一次落地。
2. **探索不等于正确** —— 你会看到模型有时探索得很勤，却仍写出过度约束、或口径拧巴的 SQL
   （比如把 `order_status` 和 `payment_status` 一起卡死，查出 0 行）。工具循环解决的是
   "让它够得到、看得清"，答得对不对是后面 Guard / Verifier 那一课的事。别把 Harness 当银弹。

## 和真正的 MCP 的关系

本课的循环用 DeepSeek 的 function calling 直接驱动那四个工具函数，跑起来稳、好测。若想让循环
经由**真正的 MCP Server（stdio）**来驱动，把 `03-mcp-server-min/mcp_server.py` 以 stdio 起服务、
再用 MCP 客户端桥接到这里的工具循环即可——工具契约是同一套，换的只是"工具从哪来"。

> 换库同样只改 `DB_URL`；生产上连库用只读账号、把表白名单收到最小。
