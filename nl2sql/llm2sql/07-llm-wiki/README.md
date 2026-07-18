# 07 · LLM-Wiki 基座（配套 C1-06A / 06B）

把焊不进表结构的语义，切成一条条人能维护、模型能查的条目，做成一间可检索的语义库房。
再用"先检索、再生成"两步固定链路，让模型带着口径写 SQL，而不是凭常识瞎猜。

## 这套 Demo 想让你亲眼看到什么

同一道"各类目的销售额是多少"：

- **无 wiki 一路**：只给很薄的 schema（只有表名字段名，没口径）。模型只能猜。真实一次运行里，
  它凭空编了 `order_status = 'completed'`（本库 order_status 是整数 0-5，没这个值），
  语法没错、不报错，安安静静返回 0 行。错得毫无破绽。
- **有 wiki 一路**：先检索到 `term.sales_amount`（销售额口径 + 扇出警告）、`alias.category`、
  `golden.category_sales`，拼进 Prompt。模型用对 `payment_status = 2`、用明细金额汇总，
  结果与真值分毫不差。

区别不在模型变聪明，在它终于拿到了本该有的那份资料。

## 文件

| 文件 | 作用 |
|---|---|
| `wiki.py` | LLM-Wiki 库房：10 条语义，四类 term/alias/golden/pitfall，全长在真实 4 表数据集上 |
| `retriever.py` | 最朴素的字面检索器（别名整词 + 标题二元组），零依赖离线可跑，附覆盖率报告 |
| `rag.py` | 很薄的 schema + 先检索再生成两步固定链路；`answer(use_wiki=...)` 可对照 |
| `cli.py` | 交互入口：`\wiki` `\search` `\bare` `\ask` `\ab` `\truth` |
| `test_lab.py` | 本地测试：19 项确定性 + LLM 真实链路 |
| `build_dataset.py` `db.py` `guard.py` | 复用前几课的数据集、连接层、只读门禁 |

## 跑起来

```bash
pip install -r requirements.txt          # sqlalchemy + requests
python test_lab.py                        # 确定性测试，不联网

export DEEPSEEK_API_KEY=sk-你的key
python test_lab.py                        # 加跑无 wiki/有 wiki 真实对照
python cli.py                             # 交互式
```

CLI 里试：

```text
\wiki                       列出库房 10 条
\search 各类目的销售额是多少？   只看检索：召回哪几条 + 覆盖率报告（离线）
\ab 各类目的销售额是多少？       无 wiki vs 有 wiki 对照跑，和真值比（需 key）
\truth                      各类目真实销售额（基准）
```

## 换库 / 换模型

- 换库：设 `DB_URL`（如 `mysql+pymysql://...`），四表结构一致即可，wiki 内容随你的库口径改。
- 向量检索是可选实现细节：本课默认字面匹配（可解释、可定位）。要上向量，只需替换 `retriever.retrieve`，
  库房 `wiki.py` 一条不用动。这正是 06A 的主张：决定上限的是库房质量，不是检索用什么技术。

## 边界

字面检索接不住"字面对不上但意思相近"的长尾（用户说"卖了多少钱"而别名只挂了"销售额"），
这类召回缺口，是向量检索该来补的地方，也是 06B 要讲的"库房要长期养"的一部分。
