#!/usr/bin/env python3
"""交互终端（主入口）：看模型自己驱动 MCP 工具，一步步查出答案。

和 01/02 最大的不同：你不再往 Prompt 里塞任何表结构。模型开局对这个库一无所知，
只能靠手里那四个工具，自己一步步 list_tables → describe_table → sample_values →
execute_query 地问出来。你在屏幕上能看到这条推理循环真实地发生。

  export DEEPSEEK_API_KEY=你的key
  python cli.py
"""
import json
import os
import sqlite3
import sys
import unicodedata

import build_dataset
from db import DEFAULT_DB
from harness import run_loop

DB_FILE = DEFAULT_DB.replace("sqlite:///", "")

EXAMPLES = [
    "最近 30 天每天的支付订单数和支付金额是多少？",
    "华东地区有多少笔已支付订单？",
    "payment_status 字段有哪些取值，各代表什么？",
]


def disp_width(s):
    return sum(2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in str(s))


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def pad(s, w):
    return s + " " * max(0, w - disp_width(s))


def print_table(cols, rows, max_rows=20):
    if not rows:
        print("    (无数据)")
        return
    widths = [disp_width(c) for c in cols]
    for r in rows[:max_rows]:
        for i, v in enumerate(r):
            widths[i] = max(widths[i], disp_width(fmt(v)))
    line = "    " + " | ".join(pad(c, widths[i]) for i, c in enumerate(cols))
    print(line)
    print("    " + "-" * (disp_width(line) - 4))
    for r in rows[:max_rows]:
        print("    " + " | ".join(pad(fmt(v), widths[i]) for i, v in enumerate(r)))
    if len(rows) > max_rows:
        print(f"    ... 还有 {len(rows) - max_rows} 行")


def brief(result):
    """把工具返回压成一行短摘要，避免刷屏。"""
    if "tables" in result:
        return "表：" + "、".join(result["tables"])
    if "columns" in result and "table" in result:
        return f"{result['table']} 共 {len(result['columns'])} 个字段"
    if "values" in result:
        return f"{result['column']} 取值：{result['values']}"
    if result.get("guard") == "reject":
        return f"门禁拦截（{result.get('reason')}）"
    if result.get("guard") == "allow" and "rows" in result:
        return f"执行成功，返回 {result.get('row_count', len(result['rows']))} 行"
    if "error" in result:
        return "出错：" + str(result["error"])
    return json.dumps(result, ensure_ascii=False, default=str)[:80]


STEP = {"n": 0}


def on_event(kind, payload):
    if kind == "call":
        STEP["n"] += 1
        args = payload["args"]
        argstr = ", ".join(f"{k}={v}" for k, v in args.items()) if args else ""
        print(f"\n  第{STEP['n']}步 · 模型调用工具 → {payload['tool']}({argstr})")
    elif kind == "result":
        print(f"           工具返回 ← {brief(payload['result'])}")
    elif kind == "final":
        print(f"\n  ✅ 模型的回答：{payload}")
    elif kind == "stopped":
        print("\n  ⚠️ 到达最大步数仍未收敛（这也是一种结果：模型在这个库上绕不出来）。")


def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("请先设置环境变量 DEEPSEEK_API_KEY，再启动。")
        sys.exit(1)
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    if "DB_URL" not in os.environ and not os.path.exists(DB_FILE):
        print("首次启动，正在生成 SQLite 样例库 ...")
        build_dataset.build()

    print("=" * 66)
    print(" MCP 工具循环（Harness）· 交互终端")
    print("=" * 66)
    print(" 不往 Prompt 塞任何表结构。模型开局对这库一无所知，只能靠四个工具")
    print(" 自己一步步查：list_tables → describe_table → sample_values → execute_query")
    print(" 想不到问什么，可以试试：")
    for q in EXAMPLES:
        print(f"   · {q}")
    print(" \\q 退出")
    print("=" * 66)

    while True:
        try:
            q = input("\n问> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break
        if not q:
            continue
        if q in ("\\q", "quit", "exit"):
            print("再见。")
            break

        STEP["n"] = 0
        print("\n—— 模型开始自己查库（看它一步步调工具）——")
        try:
            out = run_loop(q, api_key=api_key, model=model, on_event=on_event)
        except Exception as e:  # noqa
            print(f"  循环出错：{type(e).__name__}: {e}")
            continue

        if out.get("final_sql"):
            print(f"\n  它最终执行的 SQL：\n    {out['final_sql'].replace(chr(10), chr(10) + '    ')}")
        if out.get("final_result"):
            fr = out["final_result"]
            print("\n  查询结果：")
            print_table(fr["columns"], fr["rows"])
        print(f"\n  （本轮共 {len(out['steps'])} 次工具调用）")


if __name__ == "__main__":
    main()
