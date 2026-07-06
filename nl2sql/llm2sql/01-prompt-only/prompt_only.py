#!/usr/bin/env python3
"""C1-LLM-01A 配套 runner：Prompt-only NL2SQL（SQLite 版）。

链路：中文问题 + 手写 Prompt（贴 DDL + 业务映射 + 输出契约）
      -> LLM 生成 JSON{sql, used_tables, ...}
      -> 只读门禁
      -> SQLite 执行
      -> Trace / Summary

默认用 DeepSeek（OpenAI 兼容），从环境变量 DEEPSEEK_API_KEY 读 key。
加 --teacher 走教师基准 SQL，不调 LLM，可离线复现。
"""
import argparse
import json
import os
import sqlite3
import sys

import requests

from guard import ensure_limit, guard_sql

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "ecommerce.db")

QUESTION = "最近 30 天每天的支付订单数和支付金额是多少？"
ALLOWED_TABLE = "ord_order_main"

BUSINESS_MAP = """业务口径：
- "支付成功" = payment_status = 2
- "未删除"   = is_deleted = 0
- 金额一律用 actual_amount
- 时间锚点用 payment_time（不是 order_time）
- "最近 30 天" 用 payment_time >= date('now','-30 day')
- 目标数据库是 SQLite，请使用 SQLite 语法（如 date()）"""

TEACHER_SQL = """SELECT date(payment_time)   AS pay_date,
       COUNT(*)             AS paid_order_count,
       SUM(actual_amount)   AS paid_amount
FROM ord_order_main
WHERE payment_status = 2
  AND is_deleted = 0
  AND payment_time >= date('now', '-30 day')
GROUP BY date(payment_time)
ORDER BY pay_date DESC
LIMIT 30"""


def get_ddl(conn, table):
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return row[0] if row else ""


def build_prompt(ddl, question):
    return f"""你是一个只写 SQLite SQL 的助手。只能使用下面这张表：

{ddl}

{BUSINESS_MAP}

用户问题：{question}

只输出一个 JSON 对象，字段如下（不要输出多余文字、不要 markdown 代码块）：
{{
  "sql": "一条 SELECT 语句",
  "used_tables": ["用到的表"],
  "used_columns": ["用到的列"],
  "assumptions": ["你做的假设"],
  "risk_notes": ["你不确定的风险点"]
}}"""


def call_deepseek(prompt, api_key, model="deepseek-chat"):
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"},
        json={
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system",
                 "content": "你是严谨的 Text-to-SQL 助手，只输出 JSON 对象。"},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def parse_model_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()
    return json.loads(text)


def execute(conn, sql):
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return cols, rows


def run(teacher=False, question=QUESTION, model="deepseek-chat"):
    if not os.path.exists(DB_PATH):
        raise SystemExit("找不到 ecommerce.db，请先运行 python build_dataset.py")

    conn = sqlite3.connect(DB_PATH)
    ddl = get_ddl(conn, ALLOWED_TABLE)
    trace = {"question": question, "mode": "teacher" if teacher else "llm"}

    if teacher:
        model_out = {"sql": TEACHER_SQL, "used_tables": [ALLOWED_TABLE],
                     "used_columns": ["payment_time", "payment_status",
                                      "is_deleted", "actual_amount"],
                     "assumptions": ["按支付时间落天，支付成功取 payment_status=2"],
                     "risk_notes": []}
    else:
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise SystemExit("未设置 DEEPSEEK_API_KEY")
        prompt = build_prompt(ddl, question)
        trace["prompt"] = prompt
        raw = call_deepseek(prompt, api_key, model)
        trace["raw_model_output"] = raw
        model_out = parse_model_json(raw)

    sql = model_out["sql"]
    trace["model_output"] = model_out

    ok, reason = guard_sql(sql)
    trace["guard"] = {"decision": "allow" if ok else "reject", "reason": reason}
    if not ok:
        conn.close()
        summary = {"status": "guard_rejected", "reason": reason, "sql": sql}
        return summary, trace

    safe_sql = ensure_limit(sql)
    trace["executed_sql"] = safe_sql
    cols, rows = execute(conn, safe_sql)
    conn.close()

    trace["result_columns"] = cols
    trace["result_row_count"] = len(rows)
    trace["result_sample"] = rows[:5]
    summary = {
        "status": "ok",
        "mode": trace["mode"],
        "guard_decision": "allow",
        "result_columns": cols,
        "result_row_count": len(rows),
    }
    return summary, trace


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teacher", action="store_true", help="用教师基准 SQL，不调 LLM")
    ap.add_argument("--question", default=QUESTION)
    ap.add_argument("--model", default="deepseek-chat")
    ap.add_argument("--trace", action="store_true", help="打印完整 trace")
    args = ap.parse_args()

    summary, trace = run(teacher=args.teacher, question=args.question, model=args.model)
    if args.trace:
        print(json.dumps(trace, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    sys.exit(0 if summary["status"] == "ok" else 1)


if __name__ == "__main__":
    main()
