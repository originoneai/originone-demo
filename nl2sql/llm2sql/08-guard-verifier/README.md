# 08 · Guard + Verifier + 自动重试（配套 C1-07A / 07B）

SQL 落地前的最后一道防线：一道管资格的 Guard、一个管对错的 Verifier、
一条把"验票不过"变成"带病因再来一次"的自动重试闭环。

## 这套 Demo 想让你亲眼看到什么

一条 SQL 危不危险，和它对不对，是两个独立的问题：

- **Guard 管资格**：只读吗、越界吗、有边界吗。deny(写操作/多语句/越界表) · rewrite(缺LIMIT自动补) · allow。
  CTE 局部名不误判成未知表。
- **Guard 拦不住"错"**：一条 `SUM(actual_amount)`、漏了 `payment_status` 的 SQL，只读带 LIMIT 表合规，
  Guard 全放行，可它算错了。
- **Verifier 管对错**：对着证据清单（来自上一课 LLM-Wiki 的口径）验票，抓漏口径、抓扇出、抓空集。
- **自动重试**：Verifier 的结构化病因喂回模型 → 重写 → 再验，直到通过或止损。

真实闭环（`\ask 统计各地区的销售额`，实测可复现）：

```
第 1 次: SELECT region, SUM(actual_amount) ... GROUP BY region
         Guard rewrite(missing_limit) → Verify FAIL
         病因: missing payment_status / missing item_amount / risky SUM(actual_amount)
第 2 次: SELECT o.region, SUM(i.item_amount) ... JOIN ... WHERE payment_status=2 ...
         Guard rewrite → Verify PASS
最终: 华东138427.82 华北57730.16 华南62346.62 西南68356.77  合计=真值326861.37
```

## 文件

| 文件 | 作用 |
|---|---|
| `guard.py` | 带理由码的门禁：deny/rewrite/allow，CTE 感知的白名单校验 |
| `verifier.py` | 四类检查（执行/空集/语义证据/结果契约+数值量级）+ 病因转反馈 |
| `contracts.py` | 每题的必要证据清单 + 结果契约 + 真值函数（清单源自 LLM-Wiki 口径） |
| `loop.py` | 自动重试闭环 `run_with_retry`（generate_fn 可注入 mock/DeepSeek） |
| `cli.py` | 交互入口：`\guard <SQL>` `\ask <题>` `\truth <题>` |
| `test_lab.py` | 17 项确定性 + LLM 真实闭环 |

## 跑起来

```bash
pip install -r requirements.txt
python test_lab.py                        # 确定性，不联网
export DEEPSEEK_API_KEY=sk-你的key
python test_lab.py                        # 加跑真实闭环
python cli.py                             # 交互式：\guard / \ask / \truth
```

## 边界

这套 Verifier 是轻量验票员：验的是"SQL 带没带上这道题该有的证据"，靠事先写好的证据清单，
不重新推理业务 truth（新客口径该按注册还是首单这类，它答不了，留给 C3 的 MQL / C4 的 YLP）。
它补的是执行侧的窟窿，让 SQL 跑得安全、错得可纠；语义侧那个更重的窟窿，靠后面更重的语义层去填。
