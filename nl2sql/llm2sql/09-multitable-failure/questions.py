#!/usr/bin/env python3
"""多表难题集 + 每题真值 + 证据契约。配套文章 C1-08 多表失败复盘。

这些题在真实 4 表电商数据集上，专门用来把 C1 拉到它露马脚的地方：
  avg_order_value  客单价：订单粒度指标，一 join 明细就分子分母双双扇出
  cat_sales_orders 类目销售额 + 订单数：两指标正确粒度打架（销售额明细级、订单数订单级）
                   模型爱一路 join 到底 + COUNT(*)，销售额对、订单数被放大 → 半对半错
真值函数是判对错的地面真相；证据契约配合 classify 把失败归到标准类型。
"""


def avg_order_value_truth(run_read_sql):
    """各地区客单价 = 已支付未删除订单的实付金额之和 / 订单数（订单粒度，不碰明细）。"""
    sql = """SELECT region,
                    ROUND(SUM(actual_amount) / COUNT(DISTINCT order_id), 2) AS aov
             FROM ord_order_main
             WHERE payment_status = 2 AND is_deleted = 0
             GROUP BY region"""
    return {r[0]: {"aov": r[1]} for r in run_read_sql(sql)["rows"]}


def cat_sales_orders_truth(run_read_sql):
    """各类目：销售额（明细金额之和）+ 订单数（去重订单数）。"""
    sql = """SELECT c.category_name,
                    ROUND(SUM(i.item_amount), 2) AS sales,
                    COUNT(DISTINCT o.order_id) AS orders
             FROM ord_order_main o
             JOIN ord_order_item i ON o.order_id = i.order_id
             JOIN prod_product p ON i.product_id = p.product_id
             JOIN prod_category c ON p.category_id = c.category_id
             WHERE o.payment_status = 2 AND o.is_deleted = 0
             GROUP BY c.category_name"""
    return {r[0]: {"sales": r[1], "orders": r[2]} for r in run_read_sql(sql)["rows"]}


QUESTIONS = {
    "avg_order_value": {
        "question": "统计每个地区的客单价（已支付订单的实付金额总和除以订单数）",
        "grain": "order",
        "truth_fn": avg_order_value_truth,
        "required_sql": ["payment_status"],
        # 客单价是订单粒度指标，join 明细表就会扇出分子分母
        "forbidden_sql": ["ord_order_item", "JOIN i", "join ord_order_item"],
        "metrics": ["aov"],
    },
    "cat_sales_orders": {
        "question": "统计每个类目的销售额，以及该类目的订单数",
        "grain": "mixed",
        "truth_fn": cat_sales_orders_truth,
        "required_sql": ["payment_status", "item_amount"],
        "forbidden_sql": [],
        # join 明细后数订单必须去重，缺 COUNT(DISTINCT) 会被商品件数放大（归 grain_fanout）
        # 本数据集多数订单仅 1 件，放大幅度温和，量级检查抓不住，正靠这条构件级证据兜底
        "distinct_order_required": True,
        "metrics": ["sales", "orders"],
    },
}
