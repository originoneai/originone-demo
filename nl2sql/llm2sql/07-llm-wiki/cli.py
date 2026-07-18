#!/usr/bin/env python3
"""交互式 CLI：亲手把 LLM-Wiki 跑一遍。配套文章 C1-06A。

先建库、建视图不需要，直接用 4 张源表。命令：
  \\wiki                列出库房里所有条目
  \\search <问题>       只看检索：这道题会召回哪几条 + 覆盖率报告（不联网）
  \\bare <问题>         无 wiki 一路：只给很薄的 schema，让模型猜（需要 DEEPSEEK_API_KEY）
  \\ask <问题>          有 wiki 一路：先检索再生成（需要 DEEPSEEK_API_KEY）
  \\ab <问题>           无 wiki vs 有 wiki 对照跑，并和真值比（需要 DEEPSEEK_API_KEY）
  \\truth               打印各类目真实销售额（基准）
  \\q                   退出

不设 DEEPSEEK_API_KEY 也能用 \\wiki / \\search / \\truth，它们纯离线。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
from rag import answer, category_sales_truth
from retriever import retrieve, retrieval_report
from wiki import WIKI_ENTRIES


def _sum_numeric(result):
    total = 0.0
    for r in result["rows"]:
        for v in reversed(r):
            if isinstance(v, (int, float)):
                total += v
                break
    return round(total, 2)


def show_wiki():
    from collections import Counter
    c = Counter(e["type"] for e in WIKI_ENTRIES)
    print(f"LLM-Wiki 共 {len(WIKI_ENTRIES)} 条 {dict(c)}：")
    for e in WIKI_ENTRIES:
        print(f"  [{e['type']:8}] {e['id']:24} {e['title']}")


def show_search(q):
    r = retrieve(q)
    print(f"检索到 {len(r)} 条：")
    for e in r:
        print(f"  [{e['type']:8}] {e['id']:24} {e['title']}")
    print("覆盖率报告：", json.dumps(retrieval_report(q, r), ensure_ascii=False, indent=2))


def show_answer(q, use_wiki):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        print("未设置 DEEPSEEK_API_KEY，无法调用模型。可先用 \\search 看检索。")
        return None
    out = answer(q, use_wiki=use_wiki, api_key=key)
    tag = "有 wiki" if use_wiki else "无 wiki"
    print(f"[{tag}] prompt {out['prompt_chars']} 字 | 召回 {out['retrieved_ids']}")
    print("SQL:\n" + out["sql"])
    if out["error"]:
        print("执行:", out["error"])
    else:
        print(f"结果 {out['result']['row_count']} 行，数值合计 = {_sum_numeric(out['result'])}")
    return out


def show_ab(q):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        print("未设置 DEEPSEEK_API_KEY，无法对照跑。")
        return
    truth = category_sales_truth()
    truth_total = round(sum(truth.values()), 2)
    print(f"真值：各类目销售额合计 = {truth_total}\n")
    bare = show_answer(q, use_wiki=False)
    print()
    wiki = show_answer(q, use_wiki=True)
    print(f"\n真值合计 {truth_total}")
    for tag, out in [("无 wiki", bare), ("有 wiki", wiki)]:
        if out and out["result"]:
            got = _sum_numeric(out["result"])
            flag = "≈真值" if got <= truth_total * 1.3 else "偏离真值（疑似扇出/口径错）"
            print(f"  {tag}: 合计 {got}  {flag}")


def show_truth():
    truth = category_sales_truth()
    for k, v in truth.items():
        print(f"  {k}: {v}")
    print(f"  合计: {round(sum(truth.values()), 2)}")


def main():
    build_dataset.build()
    print(__doc__)
    while True:
        try:
            line = input("wiki> ").strip()
        except EOFError:
            break
        if not line:
            continue
        if line in ("\\q", "\\quit", "exit"):
            break
        if line == "\\wiki":
            show_wiki()
        elif line == "\\truth":
            show_truth()
        elif line.startswith("\\search "):
            show_search(line[len("\\search "):].strip())
        elif line.startswith("\\bare "):
            show_answer(line[len("\\bare "):].strip(), use_wiki=False)
        elif line.startswith("\\ask "):
            show_answer(line[len("\\ask "):].strip(), use_wiki=True)
        elif line.startswith("\\ab "):
            show_ab(line[len("\\ab "):].strip())
        else:
            print("未知命令。可用：\\wiki \\search \\bare \\ask \\ab \\truth \\q")


if __name__ == "__main__":
    main()
