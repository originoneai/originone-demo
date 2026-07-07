#!/usr/bin/env python3
"""本课时（宽表 / 指标表 / 三查询面对照）的本地测试。运行：python test_lab.py

- 确定性部分：视图能建、扇出关系成立、三种面 Prompt 大小递减、基准答案自洽（mock，不联网）。
- LLM 部分：设置 DEEPSEEK_API_KEY 才会真调 DeepSeek，验证宽表 Prompt 更短、宽表面能躲开扇出双算。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
import views
from db import run_read_sql
from surfaces import (SURFACES, build_prompt, category_sales_truth, run_on_surface)

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
failures = []


def check(name, cond):
    print(f"[{PASS if cond else FAIL}] {name}")
    if not cond:
        failures.append(name)


def main():
    build_dataset.build()
    views.build_views()

    # 1) 视图建成，且宽表是明细粒度（行数 > 订单数）——这就是扇出
    n_orders = run_read_sql("SELECT COUNT(*) c FROM ord_order_main")["rows"][0][0]
    n_wide = run_read_sql("SELECT COUNT(*) c FROM order_item_wide")["rows"][0][0]
    check("order_item_wide 建成", n_wide > 0)
    check("宽表为明细粒度：行数 > 订单数（扇出成立）", n_wide > n_orders)
    n_metric = run_read_sql("SELECT COUNT(*) c FROM order_daily_metric")["rows"][0][0]
    check("order_daily_metric 建成且为日粒度", 0 < n_metric <= 45)

    # 2) 三种查询面 Prompt 大小递减：物理 > 宽表 > 指标
    q = "每个类目的销售额是多少？"
    sizes = {k: len(build_prompt(k, q)) for k in SURFACES}
    check("Prompt 大小：物理 > 宽表", sizes["physical"] > sizes["wide"])
    check("Prompt 大小：宽表 > 指标", sizes["wide"] > sizes["metric"])

    # 3) 基准答案自洽：类目销售额合计 == 已支付未删除订单的明细金额总和
    truth = category_sales_truth()
    truth_total = round(sum(truth.values()), 2)
    direct = run_read_sql(
        "SELECT ROUND(SUM(i.item_amount),2) FROM ord_order_main o "
        "JOIN ord_order_item i ON o.order_id=i.order_id "
        "WHERE o.payment_status=2 AND o.is_deleted=0")["rows"][0][0]
    check("基准销售额自洽", abs(truth_total - round(direct, 2)) < 0.01)

    # 4) 扇出坑真实存在：SUM(order_actual_amount) over 明细行 > 真实销售额
    fanout = run_read_sql(
        "SELECT ROUND(SUM(order_actual_amount),2) FROM order_item_wide "
        "WHERE payment_status=2 AND is_deleted=0")["rows"][0][0]
    check("扇出坑成立：直接 SUM 订单级金额 > 真实销售额", fanout > truth_total * 1.2)

    # 5) mock 生成器跑通 run_on_surface（不联网）
    def mock_wide_correct(prompt):
        return json.dumps({"sql": "SELECT category_name, ROUND(SUM(item_amount),2) AS sales "
                                  "FROM order_item_wide WHERE payment_status=2 AND is_deleted=0 "
                                  "GROUP BY category_name"})
    out = run_on_surface(q, "wide", llm_fn=mock_wide_correct)
    check("run_on_surface 能生成→执行出结果", out["result"] is not None and out["error"] is None)

    # 6) LLM 真实链路：宽表 Prompt 更短，且宽表面能算对类目销售额（不扇出）
    if os.environ.get("DEEPSEEK_API_KEY"):
        key = os.environ["DEEPSEEK_API_KEY"]
        try:
            op = run_on_surface(q, "physical", api_key=key)
            ow = run_on_surface(q, "wide", api_key=key)
            check("真实链路：宽表 Prompt 比物理表短", ow["prompt_chars"] < op["prompt_chars"])
            check("真实链路：宽表面能生成并执行出结果",
                  ow["result"] is not None and ow["error"] is None)
            # 宽表面的类目销售额，应贴近真值（说明模型看懂了注释里的粒度口径、没扇出）
            if ow["result"] and ow["result"]["rows"]:
                total = 0.0
                for r in ow["result"]["rows"]:
                    for v in reversed(r):
                        if isinstance(v, (int, float)):
                            total += v
                            break
                check("真实链路：宽表面结果≈真值（没掉进扇出双算）",
                      total <= truth_total * 1.3)
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


if __name__ == "__main__":
    main()
