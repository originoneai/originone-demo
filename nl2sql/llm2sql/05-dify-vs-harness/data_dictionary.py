#!/usr/bin/env python3
"""字段数据字典（side-car 注释）。

SQLite 不像 MySQL/PG/Doris 那样把列注释存进可查询的元数据里，所以这里用一份
本地字典兜底：describe_table 会优先用数据库自带的列注释，取不到时再从这里补。

这不只是为了 SQLite 演示——真实项目里，字段口径散在人脑和文档里、没落到 COMMENT
上，是常态。把它显式收拢成一份可查的字典，正是后面 LLM-Wiki 那条线要做的事的雏形。
元数据质量直接决定模型问得准不准。
"""

COLUMN_COMMENTS = {
    "prod_category.category_id": "类目ID",
    "prod_category.category_name": "类目名称",
    "prod_product.product_id": "商品ID",
    "prod_product.product_name": "商品名称",
    "prod_product.category_id": "所属类目ID",
    "ord_order_main.order_id": "订单ID",
    "ord_order_main.order_no": "订单号",
    "ord_order_main.user_id": "用户ID",
    "ord_order_main.region": "地区：华东/华北/华南/西南",
    "ord_order_main.total_amount": "订单总金额（含运费）",
    "ord_order_main.actual_amount": "实付金额（订单级，不含运费）",
    "ord_order_main.order_status": "订单状态：0待支付/1已支付/2待发货/3已发货/4已完成/5已取消",
    "ord_order_main.payment_status": "支付状态：0未支付/1部分支付/2已支付/3已退款",
    "ord_order_main.order_time": "下单时间",
    "ord_order_main.payment_time": "支付时间，未支付为 NULL",
    "ord_order_main.is_deleted": "是否删除：0未删除/1已删除",
    "ord_order_item.item_id": "明细ID",
    "ord_order_item.order_id": "所属订单ID",
    "ord_order_item.product_id": "商品ID",
    "ord_order_item.quantity": "数量",
    "ord_order_item.item_amount": "明细金额（该行合计，明细级）",
}


def comment_for(table: str, column: str) -> str:
    return COLUMN_COMMENTS.get(f"{table}.{column}", "")
