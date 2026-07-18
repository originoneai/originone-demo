#!/usr/bin/env python3
"""本课时（Guard + Verifier + 自动重试）的本地测试。运行：python test_lab.py

- 确定性部分（不联网）：Guard 四类判定 + CTE 不误判、Verifier 抓漏口径/扇出/空集、
  重试闭环用 mock（第一次错→喂病因→第二次对）跑通。
- LLM 部分（设 DEEPSEEK_API_KEY 才跑）：真实模型走完整闭环，最终通过校验、结果≈真值。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
import contracts as C
from db import run_read_sql
from guard import guard, tables_outside_whitelist
from loop import run_with_retry
from verifier import verify

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
failures = []


def check(name, cond):
    print(f"[{PASS if cond else FAIL}] {name}")
    if not cond:
        failures.append(name)


def main():
    build_dataset.build()

    # 1) Guard 四类判定
    check("Guard: 写操作 deny",
          guard("DELETE FROM ord_order_main")["reason"] == "write_or_admin_operation")
    check("Guard: 多语句 deny",
          guard("SELECT 1; DROP TABLE ord_order_main")["reason"] == "multi_statement")
    g_unknown = guard("SELECT user_id FROM usr_user LIMIT 10")
    check("Guard: 越界表 deny", g_unknown["decision"] == "deny"
          and "unknown_table" in g_unknown["reason"])
    g_rw = guard("SELECT region, COUNT(*) FROM ord_order_main GROUP BY region")
    check("Guard: 缺 LIMIT rewrite 并补上", g_rw["decision"] == "rewrite"
          and "LIMIT 200" in g_rw["sql"])
    check("Guard: 合规查询 allow",
          guard("SELECT region FROM ord_order_main LIMIT 5")["decision"] == "allow")

    # 2) CTE 不被误判成未知表
    cte_sql = ("WITH paid AS (SELECT * FROM ord_order_main WHERE payment_status=2) "
               "SELECT region, COUNT(*) FROM paid GROUP BY region LIMIT 50")
    check("Guard: CTE 局部名不误判越界", tables_outside_whitelist(cte_sql) == [])
    check("Guard: CTE 查询整体 allow", guard(cte_sql)["decision"] == "allow")

    # 3) Verifier 抓错
    contract = C.CONTRACTS["region_sales"]
    truth = C.region_sales_truth(run_read_sql)
    truth_total = round(sum(truth.values()), 2)

    bad_sql = ("SELECT o.region, SUM(o.actual_amount) AS sales FROM ord_order_main o "
               "JOIN ord_order_item i ON o.order_id=i.order_id GROUP BY o.region")
    bad_res = run_read_sql(bad_sql + " LIMIT 200")
    v_bad = verify("统计各地区的销售额", bad_sql, bad_res, contract, truth_total=truth_total)
    check("Verifier: 漏 payment_status 被抓", any("missing_evidence:payment_status" in f
                                                  for f in v_bad["fails"]))
    check("Verifier: 扇出 SUM(actual_amount) 被抓", any("risky_evidence" in f
                                                       for f in v_bad["fails"]))
    check("Verifier: 数值超真值→fanout_suspected", any("fanout_suspected" in f
                                                       for f in v_bad["fails"]))
    check("Verifier: 坏 SQL 判 fail", v_bad["status"] == "fail")

    good_sql = ("SELECT o.region, ROUND(SUM(i.item_amount),2) AS sales FROM ord_order_main o "
                "JOIN ord_order_item i ON o.order_id=i.order_id "
                "WHERE o.payment_status=2 AND o.is_deleted=0 GROUP BY o.region")
    good_res = run_read_sql(good_sql + " LIMIT 200")
    v_good = verify("统计各地区的销售额", good_sql, good_res, contract, truth_total=truth_total)
    check("Verifier: 正确 SQL 判 pass", v_good["status"] == "pass")

    # 4) 空集被抓
    empty_res = run_read_sql("SELECT region, 0 FROM ord_order_main WHERE 1=0")
    v_empty = verify("统计各地区的销售额",
                     "SELECT region, SUM(item_amount) FROM ... WHERE payment_status=2 AND item_amount>0",
                     empty_res, contract, truth_total=truth_total)
    check("Verifier: 不该空却空集→unexpected_empty", "unexpected_empty" in v_empty["fails"])

    # 5) 重试闭环：第一次坏、喂病因、第二次好（mock，不联网）
    calls = {"n": 0}

    def mock_gen(question, feedback):
        calls["n"] += 1
        if calls["n"] == 1:
            return bad_sql            # 第一次：扇出+漏口径
        assert feedback, "第二次应带上失败反馈"
        return good_sql               # 第二次：照病因改对

    out = run_with_retry("统计各地区的销售额", contract, mock_gen,
                         max_retries=2, truth_total=truth_total)
    check("重试闭环：最终通过", out["ok"] is True)
    check("重试闭环：恰好第 2 次通过（attempt=1）", out["attempt"] == 1)
    check("重试闭环：轨迹含 2 步且第 1 步 fail", len(out["trace"]) == 2
          and out["trace"][0]["verify"] == "fail")

    # 6) 重试也救不回时如实止损（mock 一直给坏 SQL）
    out_fail = run_with_retry("统计各地区的销售额", contract,
                              lambda q, fb: bad_sql, max_retries=1, truth_total=truth_total)
    check("重试闭环：救不回时 ok=False 并带 last_fails",
          out_fail["ok"] is False and out_fail.get("last_fails"))

    # 7) LLM 真实闭环
    if os.environ.get("DEEPSEEK_API_KEY"):
        from loop import make_deepseek_generator
        try:
            gen = make_deepseek_generator()
            real = run_with_retry("统计各地区的销售额", contract, gen,
                                  max_retries=2, truth_total=truth_total)
            check("真实闭环：最终通过校验", real["ok"] is True)
            if real["ok"]:
                got = run_read_sql(real["sql"])
                tot = 0.0
                for r in got["rows"]:
                    for v in reversed(r):
                        if isinstance(v, (int, float)):
                            tot += v
                            break
                check("真实闭环：结果≈真值（没扇出）", tot <= truth_total * 1.3)
        except Exception as e:  # noqa
            check(f"LLM 闭环无异常（{type(e).__name__}: {e}）", False)
    else:
        print("[skip] 未设置 DEEPSEEK_API_KEY，跳过 LLM 真实闭环测试")

    print()
    if failures:
        print(f"共 {len(failures)} 项失败：{failures}")
        sys.exit(1)
    print("全部通过 ✅")
    sys.exit(0)


if __name__ == "__main__":
    main()
