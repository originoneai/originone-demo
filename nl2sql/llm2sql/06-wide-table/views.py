#!/usr/bin/env python3
"""用数据工程把上下文提前喂到位：建一张订单明细宽表 + 一张订单日指标表。

这就是"宽表路线"的核心动作——在建表阶段，把该 join 的表接好、该上卷的类目卷好、
该固化的口径写进注释。模型运行时看到的，从"四张要自己拼的源表"，变成"一张查询友好表"。
搜索空间被压小，C1 直出 SQL 的难度随之下降。

两个产物：
  order_item_wide     订单明细粒度宽表：一行一明细，把订单/商品/类目摊平在一起。
                      注意粒度——order_actual_amount 是订单级、会在多商品订单里重复；
                      item_amount 是明细级、可安全求和。这条口径写进了注释，正是宽表的价值。
  order_daily_metric  订单日指标表：预聚合好的日粒度指标，趋势题直接过滤日期即可。
"""
from sqlalchemy import text

from db import get_engine

CREATE_WIDE = """
CREATE VIEW IF NOT EXISTS order_item_wide AS
SELECT
  o.order_id,
  o.user_id,
  o.region,
  date(o.payment_time)      AS pay_date,
  o.payment_time,
  o.payment_status,
  o.is_deleted,
  o.actual_amount           AS order_actual_amount,  -- 订单级金额（多商品订单会在多行重复）
  i.item_id,
  i.product_id,
  i.quantity,
  i.item_amount,                                     -- 明细级金额（可安全求和）
  p.product_name,
  c.category_name
FROM ord_order_main o
JOIN ord_order_item i ON o.order_id = i.order_id
JOIN prod_product   p ON i.product_id = p.product_id
JOIN prod_category  c ON p.category_id = c.category_id
"""

CREATE_METRIC = """
CREATE VIEW IF NOT EXISTS order_daily_metric AS
SELECT
  date(payment_time)                        AS metric_date,
  COUNT(*)                                  AS paid_order_count,
  COUNT(DISTINCT user_id)                   AS paid_user_count,
  SUM(actual_amount)                        AS paid_amount,
  ROUND(SUM(actual_amount) / COUNT(*), 2)   AS avg_paid_amount
FROM ord_order_main
WHERE payment_status = 2 AND is_deleted = 0 AND payment_time IS NOT NULL
GROUP BY date(payment_time)
"""

VIEW_NAMES = ("order_item_wide", "order_daily_metric")


def build_views():
    """把两张视图建到当前库里（幂等）。宽表路线的'建设阶段'就浓缩在这一步。"""
    eng = get_engine()
    with eng.begin() as conn:
        for v in VIEW_NAMES:
            conn.execute(text(f"DROP VIEW IF EXISTS {v}"))
        conn.execute(text(CREATE_WIDE.strip()))
        conn.execute(text(CREATE_METRIC.strip()))
    return VIEW_NAMES


if __name__ == "__main__":
    import build_dataset
    build_dataset.build()
    build_views()
    eng = get_engine()
    with eng.connect() as conn:
        w = conn.execute(text("SELECT COUNT(*) FROM order_item_wide")).scalar()
        m = conn.execute(text("SELECT COUNT(*) FROM order_daily_metric")).scalar()
        # 扇出演示：宽表行数（明细粒度）> 订单数
        o = conn.execute(text("SELECT COUNT(*) FROM ord_order_main")).scalar()
    print(f"order_item_wide {w} 行（明细粒度，> 订单数 {o}，这就是扇出）")
    print(f"order_daily_metric {m} 行（日粒度预聚合）")
