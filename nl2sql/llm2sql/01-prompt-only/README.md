# 01 · Prompt-only NL2SQL（配套 C1-LLM-01A）

对应课程文章：《第一条 SQL 让模型裸奔：单表能过，多表就露馅》。

让大模型裸奔一次——不接工具、不上 RAG，一段手写 Prompt 直接生成 SQL，过一道只读门禁，在 **SQLite** 上执行。小规模零成本，`git clone` 下来就能跑。

## 文件

| 文件 | 作用 |
|---|---|
| `build_dataset.py` | 生成 SQLite 电商样例库 `ecommerce.db`（固定随机种子，可复现） |
| `guard.py` | 只读门禁：拦写操作/多语句，缺 LIMIT 自动补 |
| `prompt_only.py` | runner：手写 Prompt → LLM 出 JSON → 门禁 → SQLite 执行 → Trace/Summary |
| `test_lab.py` | 本地测试：建库、教师基准、门禁、扇出演示、LLM 真实链路 |

## 快速开始

```bash
pip install -r requirements.txt

# 1) 建库
python build_dataset.py

# 2) 教师基准（离线，不调 LLM，先验证链路本身）
python prompt_only.py --teacher

# 3) 真实 LLM 链路（DeepSeek，OpenAI 兼容）
export DEEPSEEK_API_KEY=你的key
python prompt_only.py --trace

# 4) 跑测试
python test_lab.py            # 不带 key 只跑确定性部分
DEEPSEEK_API_KEY=你的key python test_lab.py   # 带 key 连 LLM 一起测
```

## 数据集

`ecommerce.db` 四张表：`prod_category` / `prod_product` / `ord_order_main` / `ord_order_item`。
订单 `payment_time` 覆盖最近 40 天，保证"最近 30 天"窗口有数据；订单实付 `actual_amount` 等于其明细 `item_amount` 之和，因此跨表分摊题里，用订单级金额 join 明细会出现**扇出虚高**，用明细级金额才对——课程里的翻车演示可直接复现。

## 换成大规模 / 线上库

`prompt_only.py` 走标准 SQL，把连接从 SQLite 换成 Doris/PostgreSQL 即可（后续「自建 MCP Server」一课统一用 SQLAlchemy 抹平差异）。大规模数据集另见 `../../datasets/`。

> 不要把 API Key 写进代码或提交进仓库，一律用环境变量 `DEEPSEEK_API_KEY`。
