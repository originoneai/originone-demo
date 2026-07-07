#!/usr/bin/env python3
"""构建本课时（上下文消融）用的 SQLite 电商样例库 ecommerce.db。

在 01-prompt-only 那套四张表的基础上，特意多加了两张"长得像"的干扰表：
  - ord_refund：退款表，也有金额字段（refund_amount）、也有时间字段（refund_time）
  - stat_order_daily：按天预聚合表，字段叫 pay_amount，和订单表的 actual_amount 撞脸

这两张表本身没错，但它们是用来演示"上下文精确率"的：当你把全库结构一股脑塞给模型，
`actual_amount / refund_amount / pay_amount` 一堆名字相近、口径不同的金额字段挤在一起，
模型就容易在相似字段里选错手——这正是本课要你亲手复现的现象。

零依赖、可复现：固定随机种子，任何机器上生成的数据一致。
"""
import os
import random
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecommerce.db")

SCHEMA = """
DROP TABLE IF EXISTS ord_order_item;
DROP TABLE IF EXISTS ord_order_main;
DROP TABLE IF EXISTS ord_refund;
DROP TABLE IF EXISTS stat_order_daily;
DROP TABLE IF EXISTS prod_product;
DROP TABLE IF EXISTS prod_category;

CREATE TABLE prod_category (
  category_id   INTEGER PRIMARY KEY,
  category_name TEXT NOT NULL          -- 类目名称
);

CREATE TABLE prod_product (
  product_id   INTEGER PRIMARY KEY,
  product_name TEXT NOT NULL,          -- 商品名称
  category_id  INTEGER NOT NULL        -- 所属类目
);

CREATE TABLE ord_order_main (
  order_id       INTEGER PRIMARY KEY,
  order_no       TEXT    NOT NULL,
  user_id        INTEGER NOT NULL,
  region         TEXT    NOT NULL,     -- 地区：华东/华北/华南/西南
  total_amount   REAL    NOT NULL,     -- 订单总金额（含运费）
  actual_amount  REAL    NOT NULL,     -- 实付金额（订单级，不含运费）
  order_status   INTEGER NOT NULL,     -- 0待支付/1已支付/2待发货/3已发货/4已完成/5已取消
  payment_status INTEGER NOT NULL,     -- 0未支付/1部分支付/2已支付/3已退款
  order_time     TEXT    NOT NULL,     -- 下单时间
  payment_time   TEXT,                 -- 支付时间，未支付为 NULL
  is_deleted     INTEGER NOT NULL      -- 0未删除/1已删除
);

CREATE TABLE ord_order_item (
  item_id     INTEGER PRIMARY KEY,
  order_id    INTEGER NOT NULL,        -- 所属订单
  product_id  INTEGER NOT NULL,        -- 商品
  quantity    INTEGER NOT NULL,        -- 数量
  item_amount REAL    NOT NULL         -- 明细金额（该行合计，明细级）
);

CREATE TABLE ord_refund (
  refund_id     INTEGER PRIMARY KEY,
  order_id      INTEGER NOT NULL,      -- 关联订单
  refund_amount REAL    NOT NULL,      -- 退款金额（易与 actual_amount 混淆）
  refund_status INTEGER NOT NULL,      -- 0处理中/1已退款
  refund_time   TEXT    NOT NULL       -- 退款时间（易与 payment_time 混淆）
);

CREATE TABLE stat_order_daily (
  stat_date  TEXT    NOT NULL,         -- 统计日期
  region     TEXT    NOT NULL,         -- 地区
  order_cnt  INTEGER NOT NULL,         -- 当日支付订单数（预聚合）
  pay_amount REAL    NOT NULL          -- 当日支付金额（预聚合，易与 actual_amount 混淆）
);
"""

CATEGORIES = ["家居", "数码", "服饰", "食品", "图书"]
REGIONS = ["华东", "华东", "华东", "华北", "华南", "西南"]  # 华东加权，保证跨表题有量


def build(db_path: str = DB_PATH, n_orders: int = 400) -> str:
    random.seed(42)
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    cur = conn.cursor()

    cur.executemany(
        "INSERT INTO prod_category(category_id, category_name) VALUES (?, ?)",
        [(i + 1, name) for i, name in enumerate(CATEGORIES)],
    )
    products = []
    pid = 0
    for cid in range(1, len(CATEGORIES) + 1):
        for k in range(4):
            pid += 1
            products.append((pid, f"{CATEGORIES[cid - 1]}商品{k + 1}", cid))
    cur.executemany(
        "INSERT INTO prod_product(product_id, product_name, category_id) VALUES (?, ?, ?)",
        products,
    )

    now = datetime.now()
    item_id = 0
    refund_id = 0
    orders, items, refunds = [], [], []
    # 预聚合累加器：{(date, region): [cnt, amount]}
    daily = {}
    for oid in range(1, n_orders + 1):
        days_ago = random.randint(0, 39)  # 覆盖最近 40 天
        order_time = now - timedelta(days=days_ago, hours=random.randint(0, 23),
                                     minutes=random.randint(0, 59))
        region = random.choice(REGIONS)

        r = random.random()
        if r < 0.80:
            payment_status, order_status = 2, 4
        elif r < 0.90:
            payment_status, order_status = 0, 0
        elif r < 0.95:
            payment_status, order_status = 1, 1
        else:
            payment_status, order_status = 3, 5
        paid = payment_status in (1, 2, 3)
        pay_dt = order_time + timedelta(minutes=random.randint(1, 120)) if paid else None
        payment_time = pay_dt.strftime("%Y-%m-%d %H:%M:%S") if pay_dt else None

        n_items = random.randint(1, 3)
        chosen = random.sample(products, n_items)
        actual = 0.0
        for prod in chosen:
            item_id += 1
            qty = random.randint(1, 3)
            amt = round(random.uniform(20, 500) * qty, 2)
            actual += amt
            items.append((item_id, oid, prod[0], qty, amt))
        actual = round(actual, 2)
        total = round(actual + random.choice([0, 0, 8, 12]), 2)  # 运费

        is_deleted = 1 if random.random() < 0.05 else 0
        orders.append((
            oid, f"NO{oid:08d}", random.randint(1, 5000), region, total, actual,
            order_status, payment_status, order_time.strftime("%Y-%m-%d %H:%M:%S"),
            payment_time, is_deleted,
        ))

        # 已退款的订单，补一条退款记录（干扰表）
        if payment_status == 3:
            refund_id += 1
            refund_dt = pay_dt + timedelta(days=random.randint(1, 5))
            refunds.append((refund_id, oid, actual, 1,
                            refund_dt.strftime("%Y-%m-%d %H:%M:%S")))

        # 预聚合：只统计 payment_status=2 且未删除的（与教师口径一致）
        if payment_status == 2 and is_deleted == 0 and pay_dt is not None:
            key = (pay_dt.strftime("%Y-%m-%d"), region)
            slot = daily.setdefault(key, [0, 0.0])
            slot[0] += 1
            slot[1] += actual

    cur.executemany(
        "INSERT INTO ord_order_main(order_id, order_no, user_id, region, total_amount, "
        "actual_amount, order_status, payment_status, order_time, payment_time, is_deleted) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", orders)
    cur.executemany(
        "INSERT INTO ord_order_item(item_id, order_id, product_id, quantity, item_amount) "
        "VALUES (?, ?, ?, ?, ?)", items)
    cur.executemany(
        "INSERT INTO ord_refund(refund_id, order_id, refund_amount, refund_status, refund_time) "
        "VALUES (?, ?, ?, ?, ?)", refunds)
    cur.executemany(
        "INSERT INTO stat_order_daily(stat_date, region, order_cnt, pay_amount) "
        "VALUES (?, ?, ?, ?)",
        [(d, reg, c[0], round(c[1], 2)) for (d, reg), c in daily.items()])
    conn.commit()
    conn.close()
    return db_path


if __name__ == "__main__":
    path = build()
    conn = sqlite3.connect(path)
    n_orders = conn.execute("SELECT COUNT(*) FROM ord_order_main").fetchone()[0]
    n_refund = conn.execute("SELECT COUNT(*) FROM ord_refund").fetchone()[0]
    n_stat = conn.execute("SELECT COUNT(*) FROM stat_order_daily").fetchone()[0]
    conn.close()
    print(f"已生成 {path}")
    print(f"  订单 {n_orders} 条，退款 {n_refund} 条，预聚合 {n_stat} 行")
    print("  干扰表 ord_refund / stat_order_daily 已就位（金额字段与订单表撞脸）")
