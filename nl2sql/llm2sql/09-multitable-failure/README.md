# 09 · 多表复杂题失败复盘（配套 C1-08）

不搭新东西，把 C1 拉到多表难题上压一压，看它在哪儿露马脚，并把失败归类。

## 两道专门用来压垮 C1 的难题

| id | 题 | 埋的坑 | 正确写法 |
|---|---|---|---|
| `avg_order_value` | 各地区客单价 | 订单粒度指标，一 join 明细，分子分母双双扇出 | 订单粒度 `SUM(actual_amount)/COUNT(DISTINCT order_id)`，不碰明细 |
| `cat_sales_orders` | 各类目销售额+订单数 | 两指标粒度打架：销售额明细级、订单数订单级；`COUNT(*)` 放大订单数 | `SUM(item_amount)` + `COUNT(DISTINCT order_id)` |

## 实测：真实模型两道全军覆没（0/2）

```
avg_order_value : payment_status 猜成字符串 'paid'(实为整数2) → 空表         → 失败
cat_sales_orders: 用对了 COUNT(DISTINCT) 却漏了 payment_status → 销售额虚高    → metric_definition_error
```

多表题上模型翻车花样层出不穷（状态值错/漏过滤/join 路径错/粒度扇出），你没法预判，
只能织一张够密的证据网把它接住。这正是 C1 边界的真实写照。

## 失败分类学（别只说"答错了"）

`classify.py` 把失败归到标准类型，好让错误变成可指派的改进任务：

| 类型 | 触发 |
|---|---|
| `execution_error` | SQL 跑挂 |
| `metric_definition_error` | 漏关键口径（如 payment_status） |
| `grain_fanout_error` | 粒度扇出：join 明细后金额/计数被放大；或缺 `COUNT(DISTINCT)` 构件 |
| `join_or_grain_error` | 数值对不上真值、形态不明（兜底） |

注：本数据集多数订单仅 1 件商品，`COUNT(*)` 放大幅度温和，量级检查抓不住，
靠"必须出现 `COUNT(DISTINCT`"这条构件级证据规则兜底（见 classify.py）。

## 文件与跑法

| 文件 | 作用 |
|---|---|
| `questions.py` | 两道难题 + 真值函数 + 证据契约 |
| `classify.py` | 失败分类器（真值比对 + 证据规则 + 构件级规则） |
| `run.py` | 生成→门禁→执行→分类；`run_all` |
| `cli.py` | `\list` `\truth <id>` `\ask <id>` `\all` |
| `test_lab.py` | 12 项确定性 + LLM 真实跑批 |

```bash
pip install -r requirements.txt
python test_lab.py                     # 确定性，不联网
export DEEPSEEK_API_KEY=sk-你的key
python test_lab.py                     # 加跑真实模型（看它 0/2 翻车）
python cli.py                          # 交互：\all 一次跑完出报告
```

## 边界

这两道题的失败，C1 其实补得回（加口径规则 + Verifier 证据 + 重试）。真正补不回的，是复杂度
高到你必须为每道题单独手工兜底的场景，那是撞到 C1 天花板、该上 C3 指标层 / C4 本体层的信号。
