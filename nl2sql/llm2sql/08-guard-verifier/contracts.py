#!/usr/bin/env python3
"""每道题的结果契约 + 必要证据清单。配套文章 C1-07A 第四节。

这份清单不是凭空写的：它正是上一课 LLM-Wiki 里那些口径和经典问法，
在这里落成了 Verifier 手里一条条可执行的验票规则（课程一层扣一层）。

字段：
  required_sql   SQL 文本里必须出现的证据（如已支付口径 payment_status = 2）
  forbidden_sql  SQL 里不该出现的高风险写法（如订单级金额扇出 SUM(actual_amount)）
  columns        结果列契约（小写、按序）；None 表示不校验列名
  expect_nonempty 这道题正常应有数据，返回空集要判失败并要求解释
  truth_fn       可选：算真值的函数名，用于数值量级校验（判扇出）
"""

CONTRACTS = {
    "region_sales": {
        "question": "统计各地区的销售额",
        "required_sql": ["payment_status", "item_amount"],
        "forbidden_sql": ["SUM(o.actual_amount)", "SUM(actual_amount)"],
        "columns": None,          # region + sales，列名由模型定，只校验证据与数值
        "expect_nonempty": True,
        "truth_fn": "region_sales_truth",
    },
    "category_sales": {
        "question": "各类目的销售额是多少",
        "required_sql": ["payment_status", "item_amount"],
        "forbidden_sql": ["SUM(o.actual_amount)", "SUM(actual_amount)"],
        "columns": None,
        "expect_nonempty": True,
        "truth_fn": "category_sales_truth",
    },
}


def region_sales_truth(run_read_sql):
    """各地区真实销售额 = 已支付未删除订单里，该地区明细金额之和。"""
    sql = """SELECT o.region, ROUND(SUM(i.item_amount), 2) AS sales
             FROM ord_order_main o
             JOIN ord_order_item i ON o.order_id = i.order_id
             WHERE o.payment_status = 2 AND o.is_deleted = 0
             GROUP BY o.region"""
    return {r[0]: r[1] for r in run_read_sql(sql)["rows"]}


def category_sales_truth(run_read_sql):
    sql = """SELECT c.category_name, ROUND(SUM(i.item_amount), 2) AS sales
             FROM ord_order_main o
             JOIN ord_order_item i ON o.order_id = i.order_id
             JOIN prod_product p ON i.product_id = p.product_id
             JOIN prod_category c ON p.category_id = c.category_id
             WHERE o.payment_status = 2 AND o.is_deleted = 0
             GROUP BY c.category_name"""
    return {r[0]: r[1] for r in run_read_sql(sql)["rows"]}


TRUTH_FNS = {"region_sales_truth": region_sales_truth,
             "category_sales_truth": category_sales_truth}
