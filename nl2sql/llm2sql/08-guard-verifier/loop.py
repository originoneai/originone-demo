#!/usr/bin/env python3
"""自动重试闭环：把"验票不过"变成"带着病因再来一次"。配套文章 C1-07A 第五节。

  生成 SQL -> Guard -> 执行 -> Verifier
    pass  -> 交答案
    fail  -> 把 Verifier 的结构化病因喂回模型 -> 重新生成 -> 再走一遍
  直到 pass，或到达 max_retries 止损，把最后情况连同诊断如实交出。

这套"生成、自我检查、拿反馈再生成"就是 self-correction（下一篇 07B 讲）。
generate_fn(question, feedback) 可注入：默认调 DeepSeek；测试传 mock 不联网。
"""
import json
import os

import requests

from db import run_read_sql
from guard import guard
from verifier import feedback_from_fails, verify

SQL_SYSTEM = """你是一个 SQL 生成器。只用下面的表为用户问题写一条 SQLite 只读 SELECT。
表（只给表名和字段名）：
  ord_order_main(order_id, user_id, region, actual_amount, order_status, payment_status, payment_time, is_deleted)
  ord_order_item(item_id, order_id, product_id, quantity, item_amount)
  prod_product(product_id, product_name, category_id)
  prod_category(category_id, category_name)
只输出 JSON：{"sql": "SELECT ..."}，不要解释。"""


def call_deepseek(question, feedback, api_key, model="deepseek-chat"):
    user = f"用户问题：{question}"
    if feedback:
        user += f"\n\n{feedback}"
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "temperature": 0,
              "response_format": {"type": "json_object"},
              "messages": [{"role": "system", "content": SQL_SYSTEM},
                           {"role": "user", "content": user}]},
        timeout=90,
    )
    resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(raw).get("sql", "").strip()
    except json.JSONDecodeError:
        return raw.strip()


def run_with_retry(question, contract, generate_fn, max_retries=2, truth_total=None):
    """generate_fn(question, feedback)->sql。返回完整轨迹（每次尝试的 SQL/判定/校验）。"""
    feedback = ""
    trace = []
    last = None
    for attempt in range(max_retries + 1):
        sql = generate_fn(question, feedback)
        g = guard(sql)
        step = {"attempt": attempt, "sql": sql, "guard": g["decision"], "guard_reason": g["reason"]}
        if g["decision"] == "deny":
            step["verify"] = "skipped_denied"
            trace.append(step)
            feedback = f"上一条被门禁拒绝：{g['reason']}。请换一条只读、不越界的 SQL。"
            last = {"ok": False, "sql": sql, "fails": [f"guard_deny:{g['reason']}"]}
            continue
        try:
            result = run_read_sql(g["sql"])
        except Exception as e:  # noqa
            result = None
            step["exec_error"] = f"{type(e).__name__}: {e}"
        v = verify(question, g["sql"], result, contract, truth_total=truth_total)
        step["verify"] = v["status"]
        step["fails"] = v["fails"]
        step["exec_sql"] = g["sql"]
        trace.append(step)
        if v["status"] == "pass":
            return {"ok": True, "attempt": attempt, "sql": g["sql"],
                    "result": result, "trace": trace}
        feedback = feedback_from_fails(v["fails"])
        last = {"ok": False, "sql": g["sql"], "fails": v["fails"]}
    return {"ok": False, "attempt": max_retries, "sql": last["sql"],
            "last_fails": last["fails"], "trace": trace}


def make_deepseek_generator(api_key=None, model="deepseek-chat"):
    key = api_key or os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise SystemExit("未设置 DEEPSEEK_API_KEY")
    return lambda q, fb: call_deepseek(q, fb, key, model)
