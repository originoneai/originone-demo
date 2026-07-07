#!/usr/bin/env python3
"""交互终端（主入口）：同一道题，一边走"编排"，一边走"Harness"，当场看差别。

  export DEEPSEEK_API_KEY=你的key
  python cli.py

默认（直接敲问题）走【编排】：一条你提前画死的节点流水线（flow.py），等价于 Dify Chatflow。
  \\harness <问题>   同一道题改走【Harness】：模型自己决定每一步调哪个工具（04 的循环）。
  \\ab <问题>        两条路一起跑，并排给你看：谁画的顺序、几步、灵活性差在哪。
  \\q               退出

这一课不是要你二选一，而是要你亲手感受"人画死的图"和"模型自己走"各自的脾气。
"""
import os
import sys
import unicodedata

import build_dataset
from db import DEFAULT_DB
from flow import NODES, run_flow
from harness import run_loop

DB_FILE = DEFAULT_DB.replace("sqlite:///", "")

EXAMPLES = [
    "最近 30 天每天的支付订单数和支付金额是多少？",
    "华东地区有多少笔已支付订单？",
    "各类目下有多少个商品？",  # 编排流水线只认 ord_order_main，这题会当场露出死板的短板
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


# ---------- 编排：把每个节点实时打出来 ----------
def flow_event(node, payload):
    label = {
        "start": "① start        接到问题",
        "list_tables": "② list_tables  （工具·固定）列表",
        "describe_table": "③ describe     （工具·表名写死）读 ord_order_main 结构",
        "llm_generate_sql": "④ 生成SQL      （LLM）模型只被允许干这一步",
        "guard": "⑤ guard        （代码）只读门禁",
        "execute_query": "⑥ execute      （工具）跑门禁放行的 SQL",
        "llm_answer": "⑦ answer       （LLM）一句话收尾",
    }.get(node, node)
    extra = ""
    if node == "describe_table":
        extra = f" → {len(payload['result'].get('columns', []))} 个字段"
    elif node == "llm_generate_sql":
        extra = f" → {payload['sql'][:60]}"
    elif node == "guard":
        extra = (f" → 拦下（{payload['reason']}），流水线终止" if payload["decision"] == "reject"
                 else " → 放行")
    elif node == "execute_query":
        r = payload["result"]
        extra = (f" → 返回 {r.get('row_count')} 行" if r.get("guard") == "allow"
                 else f" → {r.get('reason') or r.get('error')}")
    print(f"    {label}{extra}")


def run_flow_verbose(q, api_key, model):
    print("\n—— 走【编排】：节点顺序是你画死的，模型只填第④步 ——")
    out = run_flow(q, api_key=api_key, model=model, on_event=flow_event)
    if out.get("result") and out["result"].get("rows"):
        print("\n  查询结果：")
        print_table(out["result"]["columns"], out["result"]["rows"])
    if out.get("answer"):
        print(f"\n  ✅ 回答：{out['answer']}")
    if out["stopped"].startswith("guard_reject"):
        print("\n  ⚠️ 门禁拦下，流水线在 execute 之前就停了——这正是把 guard 画在 exec 前的意义。")
    return out


# ---------- Harness：复用 04 的逐步打印 ----------
STEP = {"n": 0}


def harness_event(kind, payload):
    if kind == "call":
        STEP["n"] += 1
        args = payload["args"]
        argstr = ", ".join(f"{k}={v}" for k, v in args.items()) if args else ""
        print(f"    第{STEP['n']}步 · 模型自己决定 → {payload['tool']}({argstr})")
    elif kind == "final":
        print(f"    ✅ 回答：{payload}")
    elif kind == "stopped":
        print("    ⚠️ 到达最大步数仍未收敛。")


def run_harness_verbose(q, api_key, model):
    print("\n—— 走【Harness】：每一步调哪个工具，都是模型自己临场决定 ——")
    STEP["n"] = 0
    out = run_loop(q, api_key=api_key, model=model, on_event=harness_event)
    if out.get("final_result") and out["final_result"].get("rows"):
        print("\n  查询结果：")
        print_table(out["final_result"]["columns"], out["final_result"]["rows"])
    return out


def run_ab(q, api_key, model):
    fo = run_flow_verbose(q, api_key, model)
    ho = run_harness_verbose(q, api_key, model)
    tools_h = [s["tool"] for s in ho["steps"]]
    print("\n  ── 并排看差别 ──")
    print(f"    编排  ：节点顺序【人画死】，固定 {len(fo['nodes'])} 步，走的是 {'→'.join(fo['nodes'])}")
    print(f"    Harness：每步【模型自定】，本轮 {len(tools_h)} 步，走的是 {'→'.join(tools_h) or '(未调工具)'}")
    used_sample = "sample_values" in tools_h
    print(f"    差别点：编排图里根本没有 sample_values 这个工位；Harness {'这轮自己去补了口径确认' if used_sample else '这轮没触发，但它随时能自己加一步去确认口径'}。")


def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("请先设置环境变量 DEEPSEEK_API_KEY，再启动。")
        sys.exit(1)
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    if "DB_URL" not in os.environ and not os.path.exists(DB_FILE):
        print("首次启动，正在生成 SQLite 样例库 ...")
        build_dataset.build()

    print("=" * 68)
    print(" 编排 vs Harness · 交互终端（Dify Chatflow 的机制，先在代码里跑通）")
    print("=" * 68)
    print(" 默认走【编排】：一条你提前画死的节点流水线（flow.py = Dify Chatflow 的代码版）")
    print(" \\harness <问题>  同一题改走【Harness】：模型自己决定每一步（04 的循环）")
    print(" \\ab <问题>       两条路一起跑，并排看差别")
    print(" 想不到问什么，可以试试：")
    for q in EXAMPLES:
        print(f"   · {q}")
    print(" \\q 退出")
    print("=" * 68)

    while True:
        try:
            line = input("\n问> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break
        if not line:
            continue
        if line in ("\\q", "quit", "exit"):
            print("再见。")
            break

        try:
            if line.startswith("\\harness"):
                q = line[len("\\harness"):].strip()
                if q:
                    run_harness_verbose(q, api_key, model)
            elif line.startswith("\\ab"):
                q = line[len("\\ab"):].strip()
                if q:
                    run_ab(q, api_key, model)
            else:
                run_flow_verbose(line, api_key, model)
        except Exception as e:  # noqa
            print(f"  出错：{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
