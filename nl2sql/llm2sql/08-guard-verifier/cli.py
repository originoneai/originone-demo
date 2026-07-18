#!/usr/bin/env python3
"""交互式 CLI：亲手把 Guard + Verifier + 自动重试跑一遍。配套文章 C1-07A。

命令：
  \\guard <SQL>        只过门禁：看 deny/rewrite/allow + 理由码（离线）
  \\ask <题>           走完整闭环：生成→Guard→执行→Verifier→（不过则重试）（需 key）
  \\truth <题>         打印这道题的真值（region_sales / category_sales）
  \\q                  退出

题目支持两道内置契约题：
  统计各地区的销售额     （对应契约 region_sales）
  各类目的销售额是多少   （对应契约 category_sales）
不设 DEEPSEEK_API_KEY 也能用 \\guard / \\truth。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
import contracts as C
from db import run_read_sql
from guard import guard
from loop import make_deepseek_generator, run_with_retry


def _match_contract(question):
    if "地区" in question:
        return "region_sales", C.CONTRACTS["region_sales"]
    if "类目" in question or "品类" in question:
        return "category_sales", C.CONTRACTS["category_sales"]
    return None, None


def _truth_total(key):
    fn = C.TRUTH_FNS[C.CONTRACTS[key]["truth_fn"]]
    return round(sum(fn(run_read_sql).values()), 2)


def show_guard(sql):
    g = guard(sql)
    print(json.dumps(g, ensure_ascii=False, indent=2))


def show_ask(question):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        print("未设置 DEEPSEEK_API_KEY，无法生成。可用 \\guard 试门禁。")
        return
    ckey, contract = _match_contract(question)
    if not contract:
        print("这道题暂无内置契约。内置：统计各地区的销售额 / 各类目的销售额是多少")
        return
    truth = _truth_total(ckey)
    gen = make_deepseek_generator(key)
    out = run_with_retry(question, contract, gen, max_retries=2, truth_total=truth)
    print(f"真值合计={truth}  最终={'通过' if out['ok'] else '仍未通过'}（尝试 {out['attempt']+1} 次）\n")
    for step in out["trace"]:
        print(f"--- 第 {step['attempt']+1} 次 ---")
        print("SQL:", step["sql"].replace("\n", " "))
        print(f"Guard: {step['guard']}({step['guard_reason']})  Verify: {step['verify']}")
        if step.get("fails"):
            print("病因:", step["fails"])
        print()
    if out["ok"]:
        print("最终结果：", run_read_sql(out["sql"])["rows"])


def show_truth(question):
    ckey, _ = _match_contract(question)
    if not ckey:
        print("内置：统计各地区的销售额 / 各类目的销售额是多少")
        return
    fn = C.TRUTH_FNS[C.CONTRACTS[ckey]["truth_fn"]]
    for k, v in fn(run_read_sql).items():
        print(f"  {k}: {v}")
    print(f"  合计: {_truth_total(ckey)}")


def main():
    build_dataset.build()
    print(__doc__)
    while True:
        try:
            line = input("gv> ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line in ("\\q", "\\quit", "exit"):
            break
        if line.startswith("\\guard "):
            show_guard(line[len("\\guard "):].strip())
        elif line.startswith("\\ask "):
            show_ask(line[len("\\ask "):].strip())
        elif line.startswith("\\truth "):
            show_truth(line[len("\\truth "):].strip())
        else:
            print("未知命令。可用：\\guard <SQL>  \\ask <题>  \\truth <题>  \\q")


if __name__ == "__main__":
    main()
