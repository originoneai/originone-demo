#!/usr/bin/env python3
"""Golden Questions：覆盖简单到复杂的验收题集 + 真值 + 证据契约。配套文章 C1-09。

这是交付包里那份"可回归的验收资产"。每道题带证据契约（Verifier 用）和真值函数。
分三档：D1 单表简单、D2 轻量多表、D3 复杂多表（C1 大概率露马脚的地方）。
"""
from db import run_read_sql


def _sum(sql):
    r = run_read_sql(sql)
    return r["rows"][0][0] if r["rows"] and r["rows"][0][0] is not None else 0


def region_sales_total():
    return _sum("SELECT ROUND(SUM(i.item_amount),2) FROM ord_order_main o "
               "JOIN ord_order_item i ON o.order_id=i.order_id "
               "WHERE o.payment_status=2 AND o.is_deleted=0")


def category_sales_total():
    return region_sales_total()  # 同一口径：明细金额之和


GOLDEN = {
    "d1_region_orders": {
        "level": "D1",
        "question": "统计各地区的已支付订单数",
        "contract": {"required_sql": ["payment_status"], "forbidden_sql": [],
                     "columns": None, "expect_nonempty": True},
        "truth_total": None,
    },
    "d1_category_count": {
        "level": "D1",
        "question": "每个类目下有多少个商品",
        "contract": {"required_sql": [], "forbidden_sql": [],
                     "columns": None, "expect_nonempty": True},
        "truth_total": None,
    },
    "d2_region_sales": {
        "level": "D2",
        "question": "统计各地区的销售额",
        "contract": {"required_sql": ["payment_status", "item_amount"],
                     "forbidden_sql": ["SUM(o.actual_amount)", "SUM(actual_amount)"],
                     "columns": None, "expect_nonempty": True},
        "truth_total_fn": region_sales_total,
    },
    "d2_category_sales": {
        "level": "D2",
        "question": "各类目的销售额是多少",
        "contract": {"required_sql": ["payment_status", "item_amount"],
                     "forbidden_sql": ["SUM(o.actual_amount)", "SUM(actual_amount)"],
                     "columns": None, "expect_nonempty": True},
        "truth_total_fn": category_sales_total,
    },
    "d3_avg_order_value": {
        "level": "D3",
        "question": "统计每个地区的客单价（已支付实付金额总和除以订单数）",
        "contract": {"required_sql": ["payment_status", "count(distinct"],
                     "forbidden_sql": ["ord_order_item"],  # 客单价订单粒度，join 明细即错
                     "columns": None, "expect_nonempty": True},
        "truth_total": None,
    },
    "d3_category_sales_orders": {
        "level": "D3",
        "question": "统计每个类目的销售额，以及该类目的订单数",
        "contract": {"required_sql": ["payment_status", "item_amount", "count(distinct"],
                     "forbidden_sql": [], "columns": None, "expect_nonempty": True},
        "truth_total": None,
    },
}


def truth_total_for(qid):
    spec = GOLDEN[qid]
    if spec.get("truth_total_fn"):
        return spec["truth_total_fn"]()
    return spec.get("truth_total")
