#!/usr/bin/env python3
"""本课时的本地测试。运行：python test_lab.py

- 确定性部分（建库、教师基准、门禁、扇出演示）：无需联网，必过。
- LLM 部分：设置了 DEEPSEEK_API_KEY 才会真调 DeepSeek，验证真实链路。
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
import prompt_only
from guard import ensure_limit, guard_sql

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
failures = []


def check(name, cond):
    print(f"[{PASS if cond else FAIL}] {name}")
    if not cond:
        failures.append(name)


def teacher_total(db):
    conn = sqlite3.connect(db)
    v = conn.execute(
        "SELECT COALESCE(SUM(actual_amount),0) FROM ord_order_main "
        "WHERE payment_status=2 AND is_deleted=0 AND payment_time >= date('now','-30 day')"
    ).fetchone()[0]
    conn.close()
    return round(v, 2)


def main():
    # 1) 建库
    db = build_dataset.build()
    check("建库成功且文件存在", os.path.exists(db))

    conn = sqlite3.connect(db)
    n = conn.execute("SELECT COUNT(*) FROM ord_order_main").fetchone()[0]
    conn.close()
    check("订单数据非空", n > 0)

    # 2) 门禁
    check("门禁放行 SELECT", guard_sql("SELECT 1")[0] is True)
    check("门禁拦截 DELETE", guard_sql("DELETE FROM t")[1] == "write_or_admin_operation")
    check("门禁拦截多语句", guard_sql("SELECT 1; DROP TABLE t")[1] == "multi_statement_forbidden")
    check("门禁自动补 LIMIT", "LIMIT" in ensure_limit("SELECT * FROM t").upper())

    # 3) 教师基准（离线，必过）
    summary, trace = prompt_only.run(teacher=True)
    check("教师基准执行成功", summary["status"] == "ok")
    check("教师基准返回列正确",
          summary["result_columns"] == ["pay_date", "paid_order_count", "paid_amount"])
    check("教师基准有数据", summary["result_row_count"] > 0)

    t_total = teacher_total(db)
    check("最近30天支付金额 > 0", t_total > 0)

    # 4) 扇出演示：错误写法（订单级金额 join 明细）应明显高于正确写法（明细级金额）
    conn = sqlite3.connect(db)
    wrong = conn.execute(
        "SELECT COALESCE(SUM(o.actual_amount),0) FROM ord_order_main o "
        "JOIN ord_order_item i ON i.order_id=o.order_id "
        "WHERE o.payment_status=2 AND o.is_deleted=0 "
        "AND o.payment_time >= date('now','-30 day')").fetchone()[0]
    right = conn.execute(
        "SELECT COALESCE(SUM(i.item_amount),0) FROM ord_order_main o "
        "JOIN ord_order_item i ON i.order_id=o.order_id "
        "WHERE o.payment_status=2 AND o.is_deleted=0 "
        "AND o.payment_time >= date('now','-30 day')").fetchone()[0]
    conn.close()
    check("扇出演示：错误写法金额虚高于正确写法", round(wrong, 2) > round(right, 2))
    check("扇出演示：正确写法≈订单实付总额", abs(round(right, 2) - t_total) < 0.01)

    # 5) LLM 真实链路（有 key 才跑）
    if os.environ.get("DEEPSEEK_API_KEY"):
        try:
            summary, trace = prompt_only.run(teacher=False)
            check("LLM 链路执行成功", summary["status"] == "ok")
            check("LLM 结果非空", summary.get("result_row_count", 0) > 0)
            # 稳健校验：LLM 结果里某个数值列求和 ≈ 教师基准的支付总额
            cols = trace.get("result_columns", [])
            rows = trace.get("result_sample", [])
            full_rows = _rerun_full(trace["executed_sql"], db)
            matched = False
            for ci in range(len(cols)):
                try:
                    s = round(sum(float(r[ci]) for r in full_rows if r[ci] is not None), 2)
                except (TypeError, ValueError):
                    continue
                if abs(s - t_total) <= max(1.0, t_total * 0.01):
                    matched = True
                    break
            check("LLM 生成的 SQL 结果与教师基准口径一致", matched)
        except Exception as e:  # noqa
            check(f"LLM 链路无异常（{type(e).__name__}: {e}）", False)
    else:
        print("[skip] 未设置 DEEPSEEK_API_KEY，跳过 LLM 真实链路测试")

    print()
    if failures:
        print(f"共 {len(failures)} 项失败：{failures}")
        sys.exit(1)
    print("全部通过 ✅")
    sys.exit(0)


def _rerun_full(sql, db):
    conn = sqlite3.connect(db)
    rows = conn.execute(sql).fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    main()
