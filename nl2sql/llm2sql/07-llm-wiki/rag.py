#!/usr/bin/env python3
"""先检索再生成，两步固定链路。配套文章 C1-06A 第五、六节。

关键设计（对应文章）：
  - LEAN_SCHEMA 故意很薄：只有表名、字段名，几乎没有业务注释。口径这些要命的东西
    全靠 wiki 补进来。这更贴近真实项目：真实 DDL 注释往往就是这么潦草。
  - 链路写死两步：retrieve（检索）在前，generate（生成）在后。中间不给模型
    “要不要检索、检索几次”的自由裁量。为的是每条 SQL 都能一条条复盘出它凭哪些证据生成。
  - 这一步是往 01B “推还是拉”那杆秤的“推”那头加一层可控证据：在模型动手前，
    我们先替它把最该看的几条推到眼前（区别于 03 的 Harness 让模型自己去拉）。
  - llm_fn 可注入：默认调 DeepSeek；测试传 mock，不联网。
"""
import json
import os

import requests

from db import get_engine, run_read_sql  # noqa: F401 (get_engine 供 cli 用)
from guard import ensure_limit, guard_sql
from retriever import retrieve, retrieval_report

# 很薄的 schema：只有表名和字段名，没有业务口径。口径全靠 wiki 补。
LEAN_SCHEMA = """ord_order_main(order_id, order_no, user_id, region, total_amount, actual_amount, order_status, payment_status, order_time, payment_time, is_deleted)
ord_order_item(item_id, order_id, product_id, quantity, item_amount)
prod_product(product_id, product_name, category_id)
prod_category(category_id, category_name)"""

SQL_SYSTEM = """你是一个 SQL 生成器。为用户问题写一条 SQLite 只读 SELECT。
只输出 JSON：{"sql": "SELECT ..."}，不要任何解释。"""


def build_prompt(question: str, retrieved) -> str:
    """把很薄的 schema + 检索到的 wiki 条目，拼成给模型的上下文。"""
    lines = ["你可以使用下面这些表（SQLite，只给了表名和字段名）：", LEAN_SCHEMA, ""]
    if retrieved:
        lines.append("下面是从业务知识库检索到的相关口径、术语和参考解法，请严格依据它们写 SQL：")
        for e in retrieved:
            lines.append(f"[{e['type']}] {e['title']}")
            lines.append(e["content"])
            if e.get("sql"):
                lines.append("参考 SQL：\n" + e["sql"])
            lines.append("")
    lines.append(f"用户问题：{question}")
    return "\n".join(lines)


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


def answer(question, use_wiki=True, api_key=None, model="deepseek-chat", llm_fn=None):
    """两步固定链路：先检索（可关掉做对照），再生成→门禁→执行。返回对照所需的一切。"""
    retrieved = retrieve(question) if use_wiki else []
    report = retrieval_report(question, retrieved) if use_wiki else None
    prompt = build_prompt(question, retrieved)

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

    out = {"use_wiki": use_wiki, "retrieved_ids": [e["id"] for e in retrieved],
           "report": report, "prompt_chars": len(prompt), "sql": sql,
           "result": None, "error": None}
    ok, reason = guard_sql(sql)
    if not ok:
        out["error"] = f"guard_reject:{reason}"
        return out
    try:
        out["result"] = run_read_sql(ensure_limit(sql))
    except Exception as e:  # noqa
        out["error"] = f"{type(e).__name__}: {e}"
    return out


def category_sales_truth():
    """基准：各类目真实销售额 = 已支付未删除订单里该类目明细金额之和。判扇出双算用。"""
    sql = """SELECT c.category_name, ROUND(SUM(i.item_amount), 2) AS sales
             FROM ord_order_main o
             JOIN ord_order_item i ON o.order_id = i.order_id
             JOIN prod_product p ON i.product_id = p.product_id
             JOIN prod_category c ON p.category_id = c.category_id
             WHERE o.payment_status = 2 AND o.is_deleted = 0
             GROUP BY c.category_name"""
    return {r[0]: r[1] for r in run_read_sql(sql)["rows"]}
