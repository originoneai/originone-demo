# 05 · 编排 vs Harness（配套 C1-LLM-04A / 04B）

对应课程文章：《在 Dify 里搭一套能聊的 ChatBI：先把它的机制在代码里跑通》《回看：Dify 是什么、编排和 Harness 到底差在哪》。

前一课（04）你让模型**自己**一步步查库，那套模型驱动的循环叫 Harness。这一课换一种活法：
把同一条问数链路，改成一张**你提前画死的节点流水线**——这正是 Dify Chatflow 干的事。
你会亲手感受两种范式的脾气：

```
编排（flow.py = Dify Chatflow 的代码版）
  start → describe_table(表名写死) → LLM生成SQL → guard → execute → LLM收尾
  顺序是【人】画死的，模型只被允许填"生成SQL"这一个工位

Harness（harness.py，沿用 04）
  模型每一步自己决定调 list/describe/sample/execute 里的哪个
  顺序是【模型】临场走出来的
```

## 为什么先在代码里跑，而不是直接开 Dify

Dify 是个可视化产品，装起来重、截图也留不住。**这一课的目的不是教你点 Dify 的按钮，而是让你
看穿它画布底下到底是什么。** 一旦你用 `flow.py` 把那几个节点、那几条死线亲手跑通，再去看
Dify 的画布，你会发现它不过是把这段代码变成了拖拽——机制你已经懂了。想在真 Dify 里复现，
`dify-chatflow.yml` 是对着搭的蓝图（节点和 `flow.py` 一一对应）。

## 文件

| 文件 | 作用 |
|---|---|
| `cli.py` | **交互终端（主入口）**：默认走编排；`\harness <题>` 走循环；`\ab <题>` 两条路并排比 |
| `flow.py` | 固定编排引擎：把 ChatBI 链路写成一张写死的节点图（=Dify Chatflow 的代码版） |
| `dify-chatflow.yml` | Dify 蓝图（参考）：装了 Dify 就照它在画布上拖出同一张图 |
| `harness.py` | 模型驱动的工具循环（与 04 同款，vendored 一份保持本文件夹可独立跑） |
| `mcp_server.py` | 四个只读工具（与 03/04 同款） |
| `db.py` / `data_dictionary.py` / `guard.py` | 连接层 / 口径注释 / 只读门禁 |
| `build_dataset.py` | 生成 SQLite 样例库 |
| `test_lab.py` | 固定节点顺序 + guard 一定在 execute 前 + mock 跑通 + DeepSeek 真实链路对比 |

## 快速开始

```bash
pip install -r requirements.txt
export DEEPSEEK_API_KEY=你的key
python cli.py
```

先敲一句「最近 30 天每天的支付订单数和支付金额是多少？」看编排一个节点一个节点地走完；
再敲 `\ab 各类目下有多少个商品？`，你会看到编排在这道题上露出死板的短板——它的图里
`describe_table` 写死了 `ord_order_main`，根本够不到 `prod_category`；而 Harness 能自己
拐去查别的表。

## 这一课要你看见的两件事

1. **编排 = 确定性，Harness = 灵活性，这是一笔对赌。** 编排每次都走那固定几步，可控、可预测、
   Guard 铁定排在 execute 前面；代价是死板——图里没画的路它一步都不会走。Harness 反过来，
   能随机应变去补一次口径确认、去查张没预料到的表；代价是不可预测，可能绕圈、可能把 Guard
   的位置"想漏"。**没有哪个更高级，只有哪个更match你这道题的容错度。**
2. **不管走哪条路，Guard 都得画在 execute 前面。** 编排里它是一条死线，Harness 里它是收在
   execute_query 工具内部的服务端门禁。"是否校验"这件事，永远不能交给模型自觉——这是两种
   范式唯一不肯让步的共识。

## 换库 / 上真 Dify

换库只改 `DB_URL`。想上真 Dify：把 `03-mcp-server-min/mcp_server.py` 以 HTTP 起服务，
在 Dify 工作区 `Tools → MCP` 里加进来（Server ID 固定别乱改），再照 `dify-chatflow.yml`
把画布拖出来。工具契约是同一套，换的只是"图画在代码里还是画在画布上"。
