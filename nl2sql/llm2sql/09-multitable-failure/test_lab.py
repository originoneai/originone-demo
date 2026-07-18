#!/usr/bin/env python3
"""本课时（多表失败复盘）的本地测试。运行：python test_lab.py

- 确定性部分（不联网）：真值自洽、手写正确 SQL 判 pass、手写翻车 SQL 被正确归类
  （客单价 join 明细扇出、类目订单数 COUNT(*) 放大），分类器认得失败类型。
- LLM 部分（设 DEEPSEEK_API_KEY 才跑）：真实模型跑两道难题，报告 pass/fail 与失败类型。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
from classify import classify
from db import run_read_sql
from guard import ensure_limit
from questions import QUESTIONS
from run import run_all, run_question

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
failures = []


def check(name, cond):
    print(f"[{PASS if cond else FAIL}] {name}")
    if not cond:
        failures.append(name)


def _run(sql):
    return run_read_sql(ensure_limit(sql))


def main():
    build_dataset.build()

    # ---- 客单价题：订单粒度 ----
    aov = QUESTIONS["avg_order_value"]
    aov_truth = aov["truth_fn"](run_read_sql)
    check("客单价真值有数据", len(aov_truth) > 0 and all("aov" in v for v in aov_truth.values()))

    aov_good = ("SELECT region, ROUND(SUM(actual_amount)/COUNT(DISTINCT order_id),2) AS aov "
                "FROM ord_order_main WHERE payment_status=2 AND is_deleted=0 GROUP BY region")
    c_good = classify(aov, aov_good, _run(aov_good), aov_truth)
    check("客单价：正确订单粒度 SQL 判 pass", c_good["status"] == "pass")

    # 翻车：join 明细 → 分子 SUM(actual_amount) 扇出，客单价虚高
    aov_bad = ("SELECT o.region, ROUND(SUM(o.actual_amount)/COUNT(DISTINCT o.order_id),2) AS aov "
               "FROM ord_order_main o JOIN ord_order_item i ON o.order_id=i.order_id "
               "WHERE o.payment_status=2 AND o.is_deleted=0 GROUP BY o.region")
    c_bad = classify(aov, aov_bad, _run(aov_bad), aov_truth)
    check("客单价：join 明细扇出 SQL 判 fail", c_bad["status"] == "fail")
    check("客单价：归到 grain_fanout_error", "grain_fanout_error" in c_bad["failure_types"])

    # 漏 payment_status → metric_definition_error
    aov_nopay = ("SELECT region, ROUND(SUM(actual_amount)/COUNT(DISTINCT order_id),2) AS aov "
                 "FROM ord_order_main WHERE is_deleted=0 GROUP BY region")
    c_nopay = classify(aov, aov_nopay, _run(aov_nopay), aov_truth)
    check("客单价：漏 payment_status 归到 metric_definition_error",
          "metric_definition_error" in c_nopay["failure_types"])

    # ---- 类目销售额+订单数题：粒度打架 ----
    cso = QUESTIONS["cat_sales_orders"]
    cso_truth = cso["truth_fn"](run_read_sql)
    check("类目销售额+订单数真值有数据",
          len(cso_truth) > 0 and all({"sales", "orders"} <= set(v) for v in cso_truth.values()))

    cso_good = ("SELECT c.category_name, ROUND(SUM(i.item_amount),2) AS sales, "
                "COUNT(DISTINCT o.order_id) AS orders "
                "FROM ord_order_main o JOIN ord_order_item i ON o.order_id=i.order_id "
                "JOIN prod_product p ON i.product_id=p.product_id "
                "JOIN prod_category c ON p.category_id=c.category_id "
                "WHERE o.payment_status=2 AND o.is_deleted=0 GROUP BY c.category_name")
    c_cso_good = classify(cso, cso_good, _run(cso_good), cso_truth)
    check("类目题：正确(COUNT DISTINCT)判 pass", c_cso_good["status"] == "pass")

    # 翻车：COUNT(*) 数订单 → 被商品件数放大（销售额对、订单数错，半对半错）
    cso_bad = ("SELECT c.category_name, ROUND(SUM(i.item_amount),2) AS sales, "
               "COUNT(*) AS orders "
               "FROM ord_order_main o JOIN ord_order_item i ON o.order_id=i.order_id "
               "JOIN prod_product p ON i.product_id=p.product_id "
               "JOIN prod_category c ON p.category_id=c.category_id "
               "WHERE o.payment_status=2 AND o.is_deleted=0 GROUP BY c.category_name")
    res_bad = _run(cso_bad)
    c_cso_bad = classify(cso, cso_bad, res_bad, cso_truth)
    check("类目题：COUNT(*) 订单数被放大，判 fail", c_cso_bad["status"] == "fail")
    check("类目题：归到 grain_fanout_error", "grain_fanout_error" in c_cso_bad["failure_types"])
    # 确认确实是订单数被放大（半对半错）：销售额列仍与真值一致
    got_sales = {r[0]: r[1] for r in res_bad["rows"]}
    sales_ok = all(abs(got_sales[k] - v["sales"]) < 0.01 for k, v in cso_truth.items())
    check("类目题：销售额列仍对（印证半对半错）", sales_ok)

    # mock 跑通 run_question（不联网）
    out = run_question("avg_order_value", llm_fn=lambda q: aov_good)
    check("run_question 正确 SQL → pass", out["classify"]["status"] == "pass")
    out2 = run_question("avg_order_value", llm_fn=lambda q: aov_bad)
    check("run_question 扇出 SQL → grain_fanout_error",
          "grain_fanout_error" in out2["classify"]["failure_types"])

    # ---- LLM 真实跑批 ----
    if os.environ.get("DEEPSEEK_API_KEY"):
        try:
            outs = run_all()
            check("真实跑批：两道题都产出了判定",
                  all("status" in o["classify"] for o in outs.values()))
            npass = sum(1 for o in outs.values() if o["classify"]["status"] == "pass")
            print(f"    [info] 真实模型多表难题通过 {npass}/{len(outs)}：",
                  {q: o["classify"]["failure_types"] for q, o in outs.items()})
        except Exception as e:  # noqa
            check(f"LLM 跑批无异常（{type(e).__name__}: {e}）", False)
    else:
        print("[skip] 未设置 DEEPSEEK_API_KEY，跳过 LLM 真实跑批")

    print()
    if failures:
        print(f"共 {len(failures)} 项失败：{failures}")
        sys.exit(1)
    print("全部通过 ✅")
    sys.exit(0)


if __name__ == "__main__":
    main()
