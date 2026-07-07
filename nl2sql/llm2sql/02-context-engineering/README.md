# 02 · 上下文消融实验台（配套 C1-LLM-01B）

对应课程文章：《你以为你在调 Prompt，其实一直在做上下文工程》。

不换模型、不换题，只动**喂给模型的上下文**。你一个个开关下面这几个旋钮，同一道题、
同一个模型，会当场生成不一样的 SQL——这就是"上下文工程"四个字最朴素的样子。

## 五个旋钮

| 旋钮 | 命令 | 作用 |
|---|---|---|
| 给哪些表 | `\scope single\|full\|none` | single 单表(干净) / full 全库(掺入撞脸干扰表) / none 只给表名不给列 |
| 字段注释 | `\comments on\|off` | DDL 带不带业务含义注释 |
| 口径映射 | `\map on\|off` | 要不要告诉它"支付成功=2、金额用 actual_amount" |
| few-shot | `\fewshot on\|off` | 给不给"这类问法→这样的 SQL"样板 |
| 值域枚举 | `\values on\|off` | 给不给 payment_status/region 的取值范围 |

为了让"全库比单表更容易选错"这件事真实可复现，本课的样例库特意多放了两张**撞脸干扰表**：
`ord_refund`（有 `refund_amount` / `refund_time`）和 `stat_order_daily`（有 `pay_amount`）。
一旦 `\scope full`，这些和 `actual_amount` / `payment_time` 名字相近、口径不同的字段就会挤在
一起，模型在相似字段里选错手的概率明显上升。

## 快速开始：玩交互终端

```bash
pip install -r requirements.txt
export DEEPSEEK_API_KEY=你的key
python cli.py
```

进去后先敲一道题（例如「最近 30 天每天的支付订单数和支付金额是多少？」）看它答对，
然后一个个拧旋钮，看它怎么开始翻车：

```
\map off          # 关掉口径映射，看它是否漏掉 payment_status = 2
\comments off     # 剥掉字段注释，看它开始猜字段含义
\scope full       # 换成全库，看它在 actual_amount / refund_amount / pay_amount 里选错
\reset            # 一键回到干净基线
\ab 最近30天华东地区的支付金额是多少？   # 同一题：干净基线 vs 当前旋钮，两段 SQL 对照
```

`\knobs` 看当前旋钮，`\schema` 看全库表结构，`\q` 退出。

## 其它用法

```bash
# 只建库看看数据
python build_dataset.py

# 跑测试（不带 key 只跑确定性部分；带 key 连 LLM 一起测干净基线能否答对）
python test_lab.py
DEEPSEEK_API_KEY=你的key python test_lab.py
```

## 数据集

六张表：`prod_category` / `prod_product` / `ord_order_main` / `ord_order_item` /
`ord_refund` / `stat_order_daily`。订单 `payment_time` 覆盖最近 40 天，保证"最近 30 天"窗口
有数据；`stat_order_daily` 按教师口径（`payment_status=2` 且未删除）预聚合，因此干净基线的
结果可与它交叉印证。

> 不要把 API Key 写进代码或提交进仓库，一律用环境变量 `DEEPSEEK_API_KEY`。
