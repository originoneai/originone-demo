# 01 · Prompt-only NL2SQL（配套 C1-LLM-01A）

对应课程文章：《第一条 SQL 让模型裸奔：单表能过，多表就露馅》。

让大模型裸奔一次——不接工具、不上 RAG，一段手写 Prompt 直接生成 SQL，过一道只读门禁，在 **SQLite** 上执行。小规模零成本，`git clone` 下来就能跑。

## 文件

| 文件 | 作用 |
|---|---|
| `cli.py` | **交互终端（主入口）**：敲中文问题，当场把 Prompt→SQL→门禁→结果跑给你看 |
| `build_dataset.py` | 生成 SQLite 电商样例库 `ecommerce.db`（固定随机种子，可复现） |
| `guard.py` | 只读门禁：拦写操作/多语句，缺 LIMIT 自动补 |
| `prompt_only.py` | 一次性 runner：教师基准 / 单次调用，出 Trace/Summary |
| `test_lab.py` | 本地测试：建库、教师基准、门禁、扇出演示、LLM 真实链路 |

## 快速开始：先玩交互终端

不预制题目，启动后你想问什么问什么，亲眼看它答对，也亲眼看它翻车：

```bash
pip install -r requirements.txt
export DEEPSEEK_API_KEY=你的key
python cli.py
```

启动后直接敲中文，例如「最近 30 天每天的支付订单数和支付金额是多少？」或
「华东地区各类目的支付金额是多少？」。终端会一步步显示：模型生成的 SQL、它的假设与风险、
门禁判定、以及 SQLite 里跑出来的结果。`\schema` 看表结构，`\q` 退出。

## 其它用法

```bash
# 教师基准（离线，不调 LLM，验证链路本身）
python prompt_only.py --teacher

# 单次调用 + 完整 Trace
DEEPSEEK_API_KEY=你的key python prompt_only.py --trace

# 跑测试（不带 key 只跑确定性部分；带 key 连 LLM 一起测）
python test_lab.py
DEEPSEEK_API_KEY=你的key python test_lab.py
```

## 数据集

`ecommerce.db` 四张表：`prod_category` / `prod_product` / `ord_order_main` / `ord_order_item`。
订单 `payment_time` 覆盖最近 40 天，保证"最近 30 天"窗口有数据；订单实付 `actual_amount` 等于其明细 `item_amount` 之和，因此跨表分摊题里，用订单级金额 join 明细会出现**扇出虚高**，用明细级金额才对——课程里的翻车演示可直接复现。

## 换成大规模 / 线上库

`prompt_only.py` 走标准 SQL，把连接从 SQLite 换成 Doris/PostgreSQL 即可（后续「自建 MCP Server」一课统一用 SQLAlchemy 抹平差异）。大规模数据集另见 `../../datasets/`。

> 不要把 API Key 写进代码或提交进仓库，一律用环境变量 `DEEPSEEK_API_KEY`。
