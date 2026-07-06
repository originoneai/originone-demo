#!/usr/bin/env python3
"""NL2LLM2SQL 交互式终端（Prompt-only）。

启动后你直接敲中文问题，它把整条链路当场跑给你看：
  你的问题 -> 手写 Prompt(贴全库 DDL) -> DeepSeek 生成 SQL(JSON)
          -> 只读门禁 -> SQLite 执行 -> 结果表 + 模型的假设/风险

没有预制题目。想问什么问什么——简单的它答得利索，复杂的（比如跨表分摊）
你能亲眼看它怎么翻车，这正是这一课要你体会的。

运行：
  export DEEPSEEK_API_KEY=你的key
  python cli.py
"""
import os
import sqlite3
import sys
import unicodedata

import build_dataset
from guard import ensure_limit, guard_sql
from prompt_only import call_deepseek, parse_model_json

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "ecommerce.db")

BUSINESS_MAP = """业务口径提示：
- "支付成功" = payment_status = 2；"未删除" = is_deleted = 0
- 金额用 actual_amount（订单级）或 item_amount（明细级，跨类目分摊时用它）
- 时间锚点：支付相关用 payment_time，下单相关用 order_time
- 目标数据库是 SQLite，请使用 SQLite 语法（如 date('now','-30 day')）"""

EXAMPLES = [
    "最近 30 天每天的支付订单数和支付金额是多少？",
    "华东地区各商品类目的支付金额是多少？",
    "支付金额最高的 5 个商品类目是哪些？",
]


def disp_width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in str(s))


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def pad(s, width):
    return s + " " * max(0, width - disp_width(s))


def print_table(cols, rows, max_rows=20):
    if not rows:
        print("  (无数据)")
        return
    widths = [disp_width(c) for c in cols]
    for r in rows[:max_rows]:
        for i, v in enumerate(r):
            widths[i] = max(widths[i], disp_width(fmt(v)))
    line = "  " + " | ".join(pad(c, widths[i]) for i, c in enumerate(cols))
    print(line)
    print("  " + "-" * (disp_width(line) - 2))
    for r in rows[:max_rows]:
        print("  " + " | ".join(pad(fmt(v), widths[i]) for i, v in enumerate(r)))
    if len(rows) > max_rows:
        print(f"  ... 还有 {len(rows) - max_rows} 行")


def get_schema_ddl(conn) -> str:
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name").fetchall()
    return "\n\n".join(r[0] for r in rows if r[0])


def list_tables(conn):
    return [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name").fetchall()]


def build_prompt(schema_ddl, question):
    return f"""你是一个只写 SQLite SQL 的助手。只能使用下面这些表：

{schema_ddl}

{BUSINESS_MAP}

用户问题：{question}

只输出一个 JSON 对象（不要多余文字、不要 markdown 代码块）：
{{"sql": "一条 SELECT 语句", "used_tables": [], "used_columns": [],
  "assumptions": [], "risk_notes": []}}"""


def answer(question, conn, api_key, model):
    schema = get_schema_ddl(conn)
    prompt = build_prompt(schema, question)

    print("\n① 正在把你的问题 + 全库结构发给模型 ...")
    try:
        raw = call_deepseek(prompt, api_key, model)
        out = parse_model_json(raw)
    except Exception as e:  # noqa
        print(f"   模型调用/解析失败：{type(e).__name__}: {e}")
        return
    sql = out.get("sql", "")

    print("\n② 模型生成的 SQL：")
    print("   " + sql.replace("\n", "\n   "))
    if out.get("assumptions"):
        print("   假设：" + "；".join(out["assumptions"]))
    if out.get("risk_notes"):
        print("   风险：" + "；".join(out["risk_notes"]))

    ok, reason = guard_sql(sql)
    print(f"\n③ 只读门禁：{'放行' if ok else '拦截'}（{reason}）")
    if not ok:
        print("   这条 SQL 没通过门禁，不执行。")
        return

    safe_sql = ensure_limit(sql)
    print("\n④ 在 SQLite 上执行 ...")
    try:
        cur = conn.execute(safe_sql)
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
    except Exception as e:  # noqa
        print(f"   执行报错：{type(e).__name__}: {e}")
        print("   —— 这也是一种结果：模型写的 SQL 跑不通。裸奔阶段很常见。")
        return
    print(f"   返回 {len(rows)} 行：\n")
    print_table(cols, rows)


def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("请先设置环境变量 DEEPSEEK_API_KEY，再启动。")
        sys.exit(1)
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    if not os.path.exists(DB_PATH):
        print("首次启动，正在生成 SQLite 样例库 ...")
        build_dataset.build()

    conn = sqlite3.connect(DB_PATH)
    tables = list_tables(conn)

    print("=" * 64)
    print(" NL2LLM2SQL 交互终端（Prompt-only · SQLite）")
    print("=" * 64)
    print(f" 可用的表：{', '.join(tables)}")
    print(" 直接敲中文问题，回车执行。想不到问什么，可以试试：")
    for q in EXAMPLES:
        print(f"   · {q}")
    print(" 命令： \\schema 看表结构   \\tables 看表名   \\q 退出")
    print("=" * 64)

    while True:
        try:
            q = input("\n问> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break
        if not q:
            continue
        if q in ("\\q", "\\quit", "exit", "quit"):
            print("再见。")
            break
        if q in ("\\tables", "\\t"):
            print("  " + ", ".join(tables))
            continue
        if q in ("\\schema", "\\s"):
            print(get_schema_ddl(conn))
            continue
        answer(q, conn, api_key, model)

    conn.close()


if __name__ == "__main__":
    main()
