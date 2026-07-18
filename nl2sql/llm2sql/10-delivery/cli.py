#!/usr/bin/env python3
"""C1 交付包交互入口：完整链路问数 + 验收回归。配套文章 C1-09（C1 收官）。

命令：
  \\list           列出 Golden Questions
  \\ask <题>       走完整链路答一道题（检索→生成→Guard→执行→Verifier→重试），需 key
  \\eval           把整套 Golden Questions 跑一遍，出交付验收报告，需 key
  \\q              退出
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
from evaluate import evaluate, print_report
from golden import GOLDEN, truth_total_for
from pipeline import answer


def show_list():
    for qid, spec in GOLDEN.items():
        print(f"  [{spec['level']}] {qid:26} {spec['question']}")


def show_ask(question):
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("未设置 DEEPSEEK_API_KEY。"); return
    # 找匹配的契约，找不到就用一个宽松契约
    spec = next((s for s in GOLDEN.values() if s["question"] == question), None)
    contract = spec["contract"] if spec else {"required_sql": [], "forbidden_sql": [],
                                              "columns": None, "expect_nonempty": True}
    tt = truth_total_for(next(k for k, s in GOLDEN.items() if s is spec)) if spec else None
    out = answer(question, contract, max_retries=2, truth_total=tt)
    print(f"最终：{'通过' if out['ok'] else '未通过'}（尝试 {out['attempt']+1} 次）  召回 {out['retrieved']}")
    for step in out["trace"]:
        print(f"  第{step['attempt']+1}次 Guard={step['guard']} Verify={step.get('verify')}"
              f" {step.get('fails','')}")
    print("SQL:", out["sql"].replace("\n", " "))


def main():
    build_dataset.build()
    print(__doc__)
    while True:
        try:
            line = input("c1> ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line in ("\\q", "\\quit", "exit"):
            break
        if line == "\\list":
            show_list()
        elif line == "\\eval":
            if not os.environ.get("DEEPSEEK_API_KEY"):
                print("未设置 DEEPSEEK_API_KEY。"); continue
            print_report(evaluate())
        elif line.startswith("\\ask "):
            show_ask(line[len("\\ask "):].strip())
        else:
            print("未知命令。可用：\\list \\ask <题> \\eval \\q")


if __name__ == "__main__":
    main()
