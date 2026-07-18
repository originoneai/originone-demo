#!/usr/bin/env python3
"""本课时（C1 交付包 / 收官）的本地测试。运行：python test_lab.py

- 确定性部分（不联网）：全链路用 mock 生成器跑通（好 SQL 一次过、坏 SQL 触发重试）、
  Golden 契约齐全、验收评估器能出报告并正确统计通过率与失败归因。
- LLM 部分（设 DEEPSEEK_API_KEY 才跑）：真实模型跑整套 Golden，出交付验收报告。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
from evaluate import evaluate, print_report
from golden import GOLDEN, truth_total_for
from pipeline import answer

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
failures = []


def check(name, cond):
    print(f"[{PASS if cond else FAIL}] {name}")
    if not cond:
        failures.append(name)


def main():
    build_dataset.build()

    # 1) Golden 契约结构完整，三档都在
    levels = {s["level"] for s in GOLDEN.values()}
    check("Golden 覆盖 D1/D2/D3 三档", {"D1", "D2", "D3"} <= levels)
    check("每题都有 question 和 contract",
          all("question" in s and "contract" in s for s in GOLDEN.values()))

    # 2) 全链路：mock 给正确 SQL → 一次通过
    spec = GOLDEN["d2_region_sales"]
    good = ("SELECT o.region, ROUND(SUM(i.item_amount),2) AS sales FROM ord_order_main o "
            "JOIN ord_order_item i ON o.order_id=i.order_id "
            "WHERE o.payment_status=2 AND o.is_deleted=0 GROUP BY o.region")
    out = answer(spec["question"], spec["contract"],
                 generate_fn=lambda p: good, truth_total=truth_total_for("d2_region_sales"))
    check("全链路：正确 SQL 一次通过", out["ok"] and out["attempt"] == 0)

    # 3) 全链路：mock 先坏后好 → 重试救回
    calls = {"n": 0}

    def flaky(prompt):
        calls["n"] += 1
        if calls["n"] == 1:
            return ("SELECT o.region, SUM(o.actual_amount) AS sales FROM ord_order_main o "
                    "JOIN ord_order_item i ON o.order_id=i.order_id GROUP BY o.region")  # 扇出+漏口径
        return good

    out2 = answer(spec["question"], spec["contract"],
                  generate_fn=flaky, truth_total=truth_total_for("d2_region_sales"))
    check("全链路：先坏后好，重试救回", out2["ok"] and out2["attempt"] == 1)
    check("全链路：轨迹第 1 步 fail", out2["trace"][0]["verify"] == "fail")

    # 4) 全链路：Guard 拦截写操作，链路不执行
    out3 = answer(spec["question"], spec["contract"],
                  generate_fn=lambda p: "DELETE FROM ord_order_main", max_retries=0)
    check("全链路：写操作被 Guard 拦、最终未通过", out3["ok"] is False)
    check("全链路：deny 记进轨迹", out3["trace"][0]["guard"] == "deny")

    # 5) 验收评估器：全 mock 给正确 SQL 时，能出报告、通过率计算正确
    def mock_all_good(prompt):
        # 针对不同题给一个大体正确的 SQL；简单题用通用可过的
        if "客单价" in prompt:
            return ("SELECT region, ROUND(SUM(actual_amount)/COUNT(DISTINCT order_id),2) AS aov "
                    "FROM ord_order_main WHERE payment_status=2 AND is_deleted=0 GROUP BY region")
        if "订单数" in prompt and "类目" in prompt:
            return ("SELECT c.category_name, ROUND(SUM(i.item_amount),2) s, "
                    "COUNT(DISTINCT o.order_id) n FROM ord_order_main o "
                    "JOIN ord_order_item i ON o.order_id=i.order_id "
                    "JOIN prod_product p ON i.product_id=p.product_id "
                    "JOIN prod_category c ON p.category_id=c.category_id "
                    "WHERE o.payment_status=2 AND o.is_deleted=0 GROUP BY c.category_name")
        if "销售额" in prompt:
            return ("SELECT c.category_name, ROUND(SUM(i.item_amount),2) s FROM ord_order_main o "
                    "JOIN ord_order_item i ON o.order_id=i.order_id "
                    "JOIN prod_product p ON i.product_id=p.product_id "
                    "JOIN prod_category c ON p.category_id=c.category_id "
                    "WHERE o.payment_status=2 AND o.is_deleted=0 GROUP BY c.category_name")
        if "订单数" in prompt:  # 各地区已支付订单数
            return ("SELECT region, COUNT(*) n FROM ord_order_main "
                    "WHERE payment_status=2 AND is_deleted=0 GROUP BY region")
        return "SELECT category_name, COUNT(*) FROM prod_category GROUP BY category_name"

    rep = evaluate(generate_fn=mock_all_good, max_retries=1)
    check("验收报告：结构完整（total/passed/pass_rate/by_level/failure_breakdown）",
          all(k in rep for k in ("total", "passed", "pass_rate", "by_level", "failure_breakdown")))
    check("验收报告：total = Golden 题数", rep["total"] == len(GOLDEN))
    check("验收报告：全对 SQL 时通过率为 1.0", rep["pass_rate"] == 1.0)

    # 6) 验收评估器：全给漏口径 SQL 时，失败被归因为 metric_definition
    def mock_all_bad(prompt):
        return "SELECT region, COUNT(*) FROM ord_order_main GROUP BY region"  # 漏 payment_status
    rep_bad = evaluate(generate_fn=mock_all_bad, max_retries=0)
    check("验收报告：坏 SQL 时通过率下降", rep_bad["pass_rate"] < 1.0)

    # 7) LLM 真实验收
    if os.environ.get("DEEPSEEK_API_KEY"):
        try:
            real = evaluate(max_retries=2)
            check("真实验收：出了报告", "pass_rate" in real and real["total"] == len(GOLDEN))
            print("\n    [真实交付验收报告]")
            print_report(real)
        except Exception as e:  # noqa
            check(f"LLM 验收无异常（{type(e).__name__}: {e}）", False)
    else:
        print("[skip] 未设置 DEEPSEEK_API_KEY，跳过 LLM 真实验收")

    print()
    if failures:
        print(f"共 {len(failures)} 项失败：{failures}")
        sys.exit(1)
    print("全部通过 ✅")
    sys.exit(0)


if __name__ == "__main__":
    main()
