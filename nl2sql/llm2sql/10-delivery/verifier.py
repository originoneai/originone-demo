#!/usr/bin/env python3
"""Verifier：管对错的验票员。配套文章 C1-07A 第四节。

站在 SQL 执行之后，对着 SQL 文本和结果，逐项验票，四类检查由浅入深：
  1. 执行有没有出岔子（result is None → execution_error）
  2. 结果空不空得蹊跷（该有数据却空集 → unexpected_empty）
  3. 必要语义证据在不在（required_sql 缺 → missing_evidence；forbidden_sql 现 → risky_evidence）
  4. 结果契约对不对（列名、数值量级；数值远超真值 → fanout_suspected）

它是轻量验票员：只验"这条 SQL 有没有带上这道题该有的证据"，靠事先写好的
证据清单（来自 LLM-Wiki），不重新推理业务 truth（那是 C3/C4 的事）。
返回结构化失败原因，喂给重试环——fail 只说"错了"，病因才说"往哪改"。
"""


def _sum_numeric(result):
    total = 0.0
    for row in result["rows"]:
        for v in reversed(row):
            if isinstance(v, (int, float)):
                total += v
                break
    return total


def verify(question, sql, result, contract, truth_total=None) -> dict:
    fails = []

    # 1. 执行出岔子
    if result is None:
        return {"status": "fail", "fails": ["execution_error"]}

    # 2. 空集蹊跷
    if result["row_count"] == 0 and contract.get("expect_nonempty"):
        fails.append("unexpected_empty")

    # 3. 必要语义证据（大小写不敏感比对 SQL 文本）
    low = sql.lower()
    for token in contract.get("required_sql", []):
        if token.lower() not in low:
            fails.append(f"missing_evidence:{token}")
    for token in contract.get("forbidden_sql", []):
        if token.lower() in low:
            fails.append(f"risky_evidence:{token}")

    # 4. 结果契约：列名
    cols = contract.get("columns")
    if cols and [c.lower() for c in result["columns"]] != [c.lower() for c in cols]:
        fails.append("column_contract_mismatch")

    # 4. 结果契约：数值量级（扇出会让合计远超真值）
    if truth_total is not None and result["rows"]:
        got = _sum_numeric(result)
        if got > truth_total * 1.3:
            fails.append(f"fanout_suspected:got={round(got, 2)}>truth={round(truth_total, 2)}")

    return {"status": "pass" if not fails else "fail", "fails": fails}


def feedback_from_fails(fails) -> str:
    """把结构化失败原因翻成给模型的、可订正的自然语言反馈。"""
    hints = []
    for f in fails:
        if f.startswith("missing_evidence:payment_status"):
            hints.append("漏了已支付过滤，请加 WHERE payment_status = 2（可再带 is_deleted = 0）")
        elif f.startswith("missing_evidence:item_amount"):
            hints.append("销售额要用明细金额 SUM(item_amount)，请改用订单明细表 ord_order_item")
        elif f.startswith("risky_evidence"):
            hints.append("不要 SUM 订单级金额 actual_amount，多商品订单会扇出翻倍，改用明细金额 item_amount")
        elif f.startswith("fanout_suspected"):
            hints.append("结果金额明显偏高，疑似扇出双算，请对明细金额 item_amount 求和而非订单级金额")
        elif f == "unexpected_empty":
            hints.append("结果为空，检查过滤条件是否过严、状态值是否取错")
        elif f == "column_contract_mismatch":
            hints.append("输出列不符合要求，请对齐约定的结果列")
        elif f == "execution_error":
            hints.append("SQL 执行报错，检查字段名和表名是否存在")
        else:
            hints.append(f)
    return "上一条 SQL 没通过校验：" + "；".join(hints) + "。请针对这些问题重写。"
