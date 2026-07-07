#!/usr/bin/env python3
"""三种查询面：物理表 / 宽表 / 指标表。同一道题，只换给模型看的上下文。

这是 01B "上下文工程"的一次数据工程落地：你不改题、不改模型，只改"模型看到的库长什么样"。
  physical  4 张源表 DDL——模型要自己选表、自己 join、自己扛粒度，搜索空间最大。
  wide      1 张订单明细宽表——join 和类目上卷已由数据工程做完，但明细粒度的扇出坑还在。
  metric    1 张订单日指标表——预聚合到订单粒度，趋势题过滤日期即可，几乎零出错面。

每个查询面配一段"schema prompt"（模型看到的上下文），面越窄、越干净，C1 直出 SQL 越稳。
"""
import json
import os

import requests

from db import get_engine, run_read_sql
from guard import ensure_limit, guard_sql

PHYSICAL_SCHEMA = """你可以使用下面 4 张源表（SQLite）：

ord_order_main  订单主表（订单粒度）
  order_id 订单ID | user_id 用户ID | region 地区
  actual_amount 实付金额（订单级，一单一个值）
  payment_status 支付状态：0未支付/1部分支付/2已支付/3已退款
  is_deleted 是否删除：0否/1是 | payment_time 支付时间（未支付为NULL）
ord_order_item  订单明细表（明细粒度，一单可有多行）
  item_id 明细ID | order_id 所属订单ID | product_id 商品ID
  quantity 数量 | item_amount 明细金额（该行合计）
prod_product  商品表
  product_id 商品ID | product_name 商品名 | category_id 所属类目ID
prod_category  类目表
  category_id 类目ID | category_name 类目名
"""

WIDE_SCHEMA = """你可以使用下面这 1 张订单明细宽表（SQLite），join 和类目已由数据工程接好：

order_item_wide  （粒度：订单明细。一个多商品订单会占多行！）
  order_id 订单ID          -- 会在多商品订单里重复出现
  user_id 用户ID | region 地区 | pay_date 支付日期 | payment_time 支付时间
  payment_status 支付状态：2=已支付 | is_deleted 是否删除：0否/1是
  order_actual_amount 订单实付金额  -- 【订单级】多商品订单里每行都是同一个值，直接 SUM 会翻倍
  item_amount 明细金额             -- 【明细级】可安全 SUM，类目销售额用它
  quantity 数量 | product_id 商品ID | product_name 商品名 | category_name 类目名
"""

METRIC_SCHEMA = """你可以使用下面这 1 张订单日指标表（SQLite），已预聚合到订单粒度：

order_daily_metric  （粒度：天。已过滤只含已支付、未删除订单）
  metric_date 日期 | paid_order_count 支付订单数 | paid_user_count 支付用户数
  paid_amount 支付金额 | avg_paid_amount 客单价
"""

SURFACES = {
    "physical": {"title": "物理表面（4 张源表）", "schema": PHYSICAL_SCHEMA},
    "wide": {"title": "宽表面（order_item_wide）", "schema": WIDE_SCHEMA},
    "metric": {"title": "指标表面（order_daily_metric）", "schema": METRIC_SCHEMA},
}

SQL_SYSTEM = """你是一个 SQL 生成器。只用给定的表，为用户问题写一条 SQLite 只读 SELECT。
仔细看字段注释里的【粒度】说明：订单级金额在明细里会重复，不能直接 SUM；订单数在明细粒度要 COUNT(DISTINCT order_id)。
只输出 JSON：{"sql": "SELECT ..."}，不要任何解释。"""


def build_prompt(surface_key: str, question: str) -> str:
    return f"{SURFACES[surface_key]['schema']}\n用户问题：{question}"


def call_deepseek_sql(prompt, api_key, model="deepseek-chat"):
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "temperature": 0,
              "response_format": {"type": "json_object"},
              "messages": [{"role": "system", "content": SQL_SYSTEM},
                           {"role": "user", "content": prompt}]},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def run_on_surface(question, surface_key, api_key=None, model="deepseek-chat", llm_fn=None):
    """在指定查询面上跑一遍：建 prompt → 生成 SQL → 门禁 → 执行。返回对照所需的一切。"""
    prompt = build_prompt(surface_key, question)
    if llm_fn is None:
        key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise SystemExit("未设置 DEEPSEEK_API_KEY")
        raw = call_deepseek_sql(prompt, key, model)
    else:
        raw = llm_fn(prompt)
    try:
        sql = json.loads(raw).get("sql", "").strip()
    except json.JSONDecodeError:
        sql = raw.strip()

    ok, reason = guard_sql(sql)
    if not ok:
        return {"surface": surface_key, "prompt_chars": len(prompt), "sql": sql,
                "result": None, "error": f"guard_reject:{reason}"}
    try:
        result = run_read_sql(ensure_limit(sql))
        return {"surface": surface_key, "prompt_chars": len(prompt), "sql": sql,
                "result": result, "error": None}
    except Exception as e:  # noqa
        return {"surface": surface_key, "prompt_chars": len(prompt), "sql": sql,
                "result": None, "error": f"{type(e).__name__}: {e}"}


def category_sales_truth():
    """基准答案：每个类目的真实销售额 = 已支付未删除订单里，该类目明细金额之和。

    用它来判模型有没有掉进扇出双算的坑（把订单级金额在明细行上重复求和）。
    """
    sql = """SELECT c.category_name, ROUND(SUM(i.item_amount), 2) AS sales
             FROM ord_order_main o
             JOIN ord_order_item i ON o.order_id = i.order_id
             JOIN prod_product p ON i.product_id = p.product_id
             JOIN prod_category c ON p.category_id = c.category_id
             WHERE o.payment_status = 2 AND o.is_deleted = 0
             GROUP BY c.category_name"""
    out = run_read_sql(sql)
    return {row[0]: row[1] for row in out["rows"]}
