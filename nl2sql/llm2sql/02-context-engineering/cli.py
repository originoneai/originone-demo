#!/usr/bin/env python3
"""上下文消融 · 交互终端（主入口）。

启动后你自己敲中文问题，再用命令一个个开关上下文旋钮，亲眼看同一道题、
同一个模型，只因为上下文变了，生成的 SQL 当场怎么变。

  export DEEPSEEK_API_KEY=你的key
  python cli.py

进去之后：
  · 直接敲中文问题 → 用"当前旋钮"跑一遍，显示 生成SQL/门禁/结果
  · \\knobs                看当前旋钮状态
  · \\scope single|full|none    切换给哪些表
  · \\comments on|off      开关字段注释
  · \\map on|off           开关业务口径映射
  · \\fewshot on|off       开关示例
  · \\values on|off        开关值域枚举
  · \\reset                恢复干净基线（single + 全开）
  · \\ab <问题>            对照：同一题分别用"干净基线"和"当前旋钮"各跑一次，看差别
  · \\schema               看全库表结构   \\q 退出
"""
import os
import sqlite3
import sys
import unicodedata

import build_dataset
import context_lab
from context_lab import CLEAN, apply_toggle, get_ddl_map, run_once

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "ecommerce.db")

EXAMPLES = [
    "最近 30 天每天的支付订单数和支付金额是多少？",
    "最近 30 天华东地区的支付金额是多少？",
    "各地区的支付订单数是多少？",
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


def show_result(res):
    print(f"\n① 当前上下文旋钮：{res['knobs']}")
    print("\n② 模型生成的 SQL：")
    print("   " + res.get("sql", "").replace("\n", "\n   "))
    mo = res.get("model_out", {})
    if mo.get("used_tables"):
        print("   用到的表：" + "、".join(mo["used_tables"]))
    if mo.get("assumptions"):
        print("   假设：" + "；".join(mo["assumptions"]))
    if mo.get("risk_notes"):
        print("   风险：" + "；".join(mo["risk_notes"]))

    print(f"\n③ 只读门禁：{'放行' if res.get('guard_ok') else '拦截'}"
          f"（{res.get('guard_reason')}）")
    if res["status"] == "guard_rejected":
        print("   没过门禁，不执行。")
        return
    if res["status"] == "exec_error":
        print(f"\n④ 执行报错：{res['error']}")
        print("   —— 这也是一种结果：上下文没给对，模型写出了跑不通的 SQL。")
        return
    print(f"\n④ 在 SQLite 上执行，返回 {len(res['rows'])} 行：\n")
    print_table(res["columns"], res["rows"])


def run_ab(conn, question, cur_knobs, api_key, model):
    print("\n===== A · 干净基线（single + 全开）=====")
    show_result(run_once(conn, question, CLEAN, api_key, model))
    print("\n===== B · 当前旋钮 =====")
    show_result(run_once(conn, question, cur_knobs, api_key, model))
    print("\n对照看两段 SQL 的差别：过滤条件、选的表、选的金额字段，是不是变了？")


def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("请先设置环境变量 DEEPSEEK_API_KEY，再启动。")
        sys.exit(1)
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    if not os.path.exists(DB_PATH):
        print("首次启动，正在生成 SQLite 样例库（含撞脸干扰表）...")
        build_dataset.build()

    conn = sqlite3.connect(DB_PATH)
    knobs = CLEAN

    print("=" * 68)
    print(" 上下文消融实验台（NL2LLM2SQL · SQLite）")
    print("=" * 68)
    print(" 同一道题、同一个模型，只动喂进去的上下文，看生成的 SQL 怎么变。")
    print(f" 当前旋钮：{knobs.label()}")
    print(" 想不到问什么，可以试试：")
    for q in EXAMPLES:
        print(f"   · {q}")
    print(" 旋钮命令：\\scope single|full|none  \\comments on|off  \\map on|off")
    print("           \\fewshot on|off  \\values on|off  \\reset  \\knobs")
    print(" 对照命令：\\ab <问题>（干净基线 vs 当前旋钮）   \\schema 看表   \\q 退出")
    print("=" * 68)

    while True:
        try:
            line = input("\n问> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break
        if not line:
            continue
        if line in ("\\q", "\\quit", "exit", "quit"):
            print("再见。")
            break
        if line in ("\\knobs", "\\k"):
            print("  " + knobs.label())
            continue
        if line in ("\\reset",):
            knobs = CLEAN
            print("  已恢复干净基线：" + knobs.label())
            continue
        if line in ("\\schema", "\\s"):
            print("\n".join(get_ddl_map(conn).values()))
            continue
        if line.startswith("\\ab"):
            q = line[3:].strip()
            if not q:
                print("  用法：\\ab 你的问题")
                continue
            run_ab(conn, q, knobs, api_key, model)
            continue
        if line.startswith("\\"):
            parts = line[1:].split(None, 1)
            if len(parts) != 2:
                print("  旋钮命令格式：\\scope full   或   \\map off")
                continue
            knobs, msg = apply_toggle(knobs, parts[0], parts[1].strip())
            print("  " + msg + "    当前：" + knobs.label())
            continue

        # 普通问题：用当前旋钮跑
        print("\n正在用当前上下文旋钮把问题发给模型 ...")
        try:
            res = run_once(conn, line, knobs, api_key, model)
        except Exception as e:  # noqa
            print(f"   模型调用/解析失败：{type(e).__name__}: {e}")
            continue
        show_result(res)

    conn.close()


if __name__ == "__main__":
    main()
