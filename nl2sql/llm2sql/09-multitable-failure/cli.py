#!/usr/bin/env python3
"""交互式 CLI：把 C1 拉到多表难题上压一压，看它在哪儿翻车。配套文章 C1-08。

命令：
  \\list              列出难题
  \\truth <id>        打印这道题的真值（地面真相）
  \\ask <id>          让模型答这道题，跑过门禁+执行+分类（需 key）
  \\all               把所有难题跑一遍，出一张 pass/fail + 失败类型报告（需 key）
  \\q                 退出
难题 id：avg_order_value / cat_sales_orders
不设 DEEPSEEK_API_KEY 也能用 \\list / \\truth。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
from db import run_read_sql
from questions import QUESTIONS
from run import run_all, run_question


def show_list():
    for qid, spec in QUESTIONS.items():
        print(f"  {qid:18} {spec['question']}")


def show_truth(qid):
    if qid not in QUESTIONS:
        print("未知题。", list(QUESTIONS)); return
    truth = QUESTIONS[qid]["truth_fn"](run_read_sql)
    for k, v in truth.items():
        print(f"  {k}: {v}")


def _print_run(out):
    print("SQL:", out["sql"].replace("\n", " "))
    print("Guard:", out["guard"])
    c = out["classify"]
    tag = "\033[32mPASS\033[0m" if c["status"] == "pass" else "\033[31mFAIL\033[0m"
    print(f"判定: {tag}  失败类型: {c['failure_types']}  {c['detail']}")
    if out.get("result"):
        print("结果:", out["result"]["rows"])


def show_ask(qid):
    if qid not in QUESTIONS:
        print("未知题。", list(QUESTIONS)); return
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("未设置 DEEPSEEK_API_KEY。可用 \\truth 看真值。"); return
    _print_run(run_question(qid))


def show_all():
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("未设置 DEEPSEEK_API_KEY。"); return
    outs = run_all()
    npass = sum(1 for o in outs.values() if o["classify"]["status"] == "pass")
    print(f"===== 通过 {npass}/{len(outs)} =====\n")
    for qid, out in outs.items():
        print(f"--- {qid} ---")
        _print_run(out)
        print()


def main():
    build_dataset.build()
    print(__doc__)
    while True:
        try:
            line = input("mt> ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line in ("\\q", "\\quit", "exit"):
            break
        if line == "\\list":
            show_list()
        elif line == "\\all":
            show_all()
        elif line.startswith("\\truth "):
            show_truth(line[len("\\truth "):].strip())
        elif line.startswith("\\ask "):
            show_ask(line[len("\\ask "):].strip())
        else:
            print("未知命令。可用：\\list \\truth <id> \\ask <id> \\all \\q")


if __name__ == "__main__":
    main()
