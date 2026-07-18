#!/usr/bin/env python3
"""C1 全链路：把这一路搭的零件串成一条不可绕过的固定链路。配套文章 C1-09。

  用户问题
    -> LLM-Wiki 检索（铺语义地基，来自 07）
    -> LLM 生成 SQL 草稿
    -> 服务端 Guard（管资格，来自 08，不可绕过）
    -> 执行
    -> Verifier（管对错，来自 08）
    -> 验不过则把病因喂回重试（self-correction）
    -> 每一步落进 trace 留痕
这就是交付包的骨架。generate_fn 可注入 mock/DeepSeek。
"""
import json
import os

import requests

from db import run_read_sql
from guard import guard
from retriever import retrieve
from verifier import feedback_from_fails, verify

LEAN_SCHEMA = """ord_order_main(order_id, user_id, region, total_amount, actual_amount, order_status, payment_status, order_time, payment_time, is_deleted)
ord_order_item(item_id, order_id, product_id, quantity, item_amount)
prod_product(product_id, product_name, category_id)
prod_category(category_id, category_name)"""

SQL_SYSTEM = """你是一个 SQL 生成器。为用户问题写一条 SQLite 只读 SELECT。
只输出 JSON：{"sql": "SELECT ..."}，不要解释。"""


def build_prompt(question, retrieved, feedback=""):
    lines = ["可用表（SQLite，只给表名字段名）：", LEAN_SCHEMA, ""]
    if retrieved:
        lines.append("从业务知识库检索到的口径/术语/参考解法，请严格依据：")
        for e in retrieved:
            lines.append(f"[{e['type']}] {e['title']}\n{e['content']}")
            if e.get("sql"):
                lines.append("参考 SQL：\n" + e["sql"])
        lines.append("")
    lines.append(f"用户问题：{question}")
    if feedback:
        lines.append(feedback)
    return "\n".join(lines)


def call_deepseek(prompt, api_key, model="deepseek-chat"):
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
    raw = resp.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(raw).get("sql", "").strip()
    except json.JSONDecodeError:
        return raw.strip()


def answer(question, contract, api_key=None, generate_fn=None,
           max_retries=2, truth_total=None):
    """跑完整链路，返回 {ok, attempt, sql, result, trace}。"""
    retrieved = retrieve(question)
    feedback = ""
    trace = []
    last = {"sql": "", "fails": ["no_attempt"]}
    for attempt in range(max_retries + 1):
        prompt = build_prompt(question, retrieved, feedback)
        if generate_fn is not None:
            sql = generate_fn(prompt)
        else:
            key = api_key or os.environ.get("DEEPSEEK_API_KEY")
            if not key:
                raise SystemExit("未设置 DEEPSEEK_API_KEY")
            sql = call_deepseek(prompt, key)
        g = guard(sql)
        step = {"attempt": attempt, "sql": sql, "guard": g["decision"], "reason": g["reason"]}
        if g["decision"] == "deny":
            step["verify"] = "skipped_denied"
            trace.append(step)
            feedback = f"上一条被门禁拒绝：{g['reason']}，请换只读、不越界的 SQL。"
            last = {"sql": sql, "fails": [f"guard_deny:{g['reason']}"]}
            continue
        try:
            result = run_read_sql(g["sql"])
        except Exception as e:  # noqa
            result = None
            step["exec_error"] = f"{type(e).__name__}: {e}"
        v = verify(question, g["sql"], result, contract, truth_total=truth_total)
        step["verify"] = v["status"]
        step["fails"] = v["fails"]
        trace.append(step)
        if v["status"] == "pass":
            return {"ok": True, "attempt": attempt, "sql": g["sql"],
                    "result": result, "trace": trace, "retrieved": [e["id"] for e in retrieved]}
        feedback = feedback_from_fails(v["fails"])
        last = {"sql": g["sql"], "fails": v["fails"]}
    return {"ok": False, "attempt": max_retries, "sql": last["sql"],
            "last_fails": last["fails"], "trace": trace,
            "retrieved": [e["id"] for e in retrieved]}
