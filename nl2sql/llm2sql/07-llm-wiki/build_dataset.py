#!/usr/bin/env python3
"""构建本课时使用的 SQLite 电商样例库 ecommerce.db。

零依赖、可复现：固定随机种子，任何机器上生成的数据一致。
覆盖两类题目所需的表：
  - 单表订单趋势题：ord_order_main
  - 跨表分摊题：ord_order_main + ord_order_item + prod_product + prod_category
"""
import os
import random
import sqlite3
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ecommerce.db")

SCHEMA = """
DROP TABLE IF EXISTS ord_order_item;
DROP TABLE IF EXISTS ord_order_main;
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
  total_amount   REAL    NOT NULL,     -- 订单总金额
  actual_amount  REAL    NOT NULL,     -- 实付金额（订单级）
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

    # 类目
    cur.executemany(
        "INSERT INTO prod_category(category_id, category_name) VALUES (?, ?)",
        [(i + 1, name) for i, name in enumerate(CATEGORIES)],
    )
    # 商品：每个类目 4 个
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
    orders, items = [], []
    for oid in range(1, n_orders + 1):
        days_ago = random.randint(0, 39)  # 覆盖最近 40 天，保证"最近 30 天"有数据
        order_time = now - timedelta(days=days_ago, hours=random.randint(0, 23),
                                     minutes=random.randint(0, 59))
        region = random.choice(REGIONS)

        # 支付状态：80% 已支付，10% 未支付，5% 部分支付，5% 已退款
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
        payment_time = (order_time + timedelta(minutes=random.randint(1, 120))
                        ).strftime("%Y-%m-%d %H:%M:%S") if paid else None

        # 明细：1~3 行，跨不同商品（用于演示扇出）
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

    cur.executemany(
        "INSERT INTO ord_order_main(order_id, order_no, user_id, region, total_amount, "
        "actual_amount, order_status, payment_status, order_time, payment_time, is_deleted) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", orders)
    cur.executemany(
        "INSERT INTO ord_order_item(item_id, order_id, product_id, quantity, item_amount) "
        "VALUES (?, ?, ?, ?, ?)", items)
    conn.commit()
    conn.close()
    return db_path


if __name__ == "__main__":
    path = build()
    conn = sqlite3.connect(path)
    n_orders = conn.execute("SELECT COUNT(*) FROM ord_order_main").fetchone()[0]
    n_items = conn.execute("SELECT COUNT(*) FROM ord_order_item").fetchone()[0]
    n_paid = conn.execute(
        "SELECT COUNT(*) FROM ord_order_main WHERE payment_status=2 AND is_deleted=0"
    ).fetchone()[0]
    conn.close()
    print(f"已生成 {path}")
    print(f"  订单 {n_orders} 条，明细 {n_items} 条，已支付未删除 {n_paid} 条")
