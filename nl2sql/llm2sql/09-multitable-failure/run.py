#!/usr/bin/env python3
"""把一道多表难题跑过 C1 链路（生成→门禁→执行→分类）。配套文章 C1-08。

只给一份很薄的 schema，让模型自己扛多表 join 和粒度。生成的 SQL 过 guard，
执行，再用 classify 对着真值和证据契约归因失败。llm_fn 可注入 mock/DeepSeek。
"""
import json
import os

import requests

from classify import classify
from db import run_read_sql
from guard import ensure_limit, guard_sql
from questions import QUESTIONS

LEAN_SCHEMA = """ord_order_main(order_id, user_id, region, total_amount, actual_amount, order_status, payment_status, order_time, payment_time, is_deleted)
ord_order_item(item_id, order_id, product_id, quantity, item_amount)
prod_product(product_id, product_name, category_id)
prod_category(category_id, category_name)"""

SQL_SYSTEM = f"""你是一个 SQL 生成器。只用下面的表为用户问题写一条 SQLite 只读 SELECT。
{LEAN_SCHEMA}
只输出 JSON：{{"sql": "SELECT ..."}}，不要解释。"""


def call_deepseek(question, api_key, model="deepseek-chat"):
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "temperature": 0,
              "response_format": {"type": "json_object"},
              "messages": [{"role": "system", "content": SQL_SYSTEM},
                           {"role": "user", "content": f"用户问题：{question}"}]},
        timeout=90,
    )
    resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(raw).get("sql", "").strip()
    except json.JSONDecodeError:
        return raw.strip()


def run_question(qid, api_key=None, llm_fn=None, model="deepseek-chat"):
    spec = QUESTIONS[qid]
    truth = spec["truth_fn"](run_read_sql)
    if llm_fn is not None:
        sql = llm_fn(spec["question"])
    else:
        key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise SystemExit("未设置 DEEPSEEK_API_KEY")
        sql = call_deepseek(spec["question"], key, model)

    ok, reason = guard_sql(sql)
    if not ok:
        return {"qid": qid, "sql": sql, "guard": f"deny:{reason}",
                "classify": {"status": "fail", "failure_types": ["execution_risk"],
                             "detail": reason}, "truth": truth}
    try:
        result = run_read_sql(ensure_limit(sql))
    except Exception as e:  # noqa
        result = None
        exec_err = f"{type(e).__name__}: {e}"
    else:
        exec_err = None
    c = classify(spec, sql, result, truth)
    return {"qid": qid, "sql": sql, "guard": "allow", "exec_error": exec_err,
            "result": result, "classify": c, "truth": truth}


def run_all(api_key=None, llm_fn=None):
    return {qid: run_question(qid, api_key=api_key, llm_fn=llm_fn) for qid in QUESTIONS}
