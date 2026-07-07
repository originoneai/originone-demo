#!/usr/bin/env python3
"""交互终端（主入口）：同一道题，换三种查询面，看 Prompt 怎么缩、SQL 怎么变、坑怎么躲。

  export DEEPSEEK_API_KEY=你的key
  python cli.py

默认在【宽表面】上问。你也可以：
  \\physical / \\wide / \\metric   切换当前查询面（物理表 / 宽表 / 指标表）
  \\ab <问题>                       同一题在【物理表】和【宽表】上各跑一遍，并排比 Prompt 大小和结果
  \\truth                          打印各类目真实销售额（基准答案，用来抓扇出双算）
  \\q                              退出

这一课要你亲手感受一件事：宽表不是魔法，它是数据工程提前替你把上下文喂到位——
join 和类目上卷它替你做了，但明细粒度的扇出坑，得靠它把口径写进注释、靠你查询时回收粒度。
"""
import os
import sys
import unicodedata

import build_dataset
import views
from db import DEFAULT_DB
from surfaces import SURFACES, category_sales_truth, run_on_surface

DB_FILE = DEFAULT_DB.replace("sqlite:///", "")

EXAMPLES = [
    "每个类目的销售额是多少？（宽表上小心：SUM 订单级金额会扇出翻倍）",
    "最近 30 天每天的支付订单数和支付金额？（指标面几乎白给）",
    "华东地区有多少笔已支付订单？",
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


def show_run(out):
    print(f"    Prompt 上下文：{out['prompt_chars']} 字")
    print(f"    生成 SQL：\n      " + out["sql"].replace("\n", "\n      "))
    if out["error"]:
        print(f"    ✗ {out['error']}")
    elif out["result"]:
        print("    结果：")
        print_table(out["result"]["columns"], out["result"]["rows"])


def numeric_total(result):
    """把结果里最后一个数值列加总——用于和基准答案对表，抓扇出。"""
    if not result or not result["rows"]:
        return None
    total = 0.0
    got = False
    for r in result["rows"]:
        for v in reversed(r):
            if isinstance(v, (int, float)):
                total += v
                got = True
                break
    return total if got else None


def run_ab(q, api_key, model):
    print(f"\n—— 同一题，两种查询面并排跑：{q} ——")
    print("\n【物理表面】模型要自己选表、自己 join、自己扛粒度：")
    op = run_on_surface(q, "physical", api_key=api_key, model=model)
    show_run(op)
    print("\n【宽表面】join 和类目已接好，只剩粒度口径要看注释：")
    ow = run_on_surface(q, "wide", api_key=api_key, model=model)
    show_run(ow)

    print("\n  ── 并排看差别 ──")
    if op["prompt_chars"]:
        ratio = ow["prompt_chars"] / op["prompt_chars"]
        print(f"    Prompt：物理 {op['prompt_chars']} 字 → 宽表 {ow['prompt_chars']} 字"
              f"（压到 {ratio:.0%}），搜索空间实打实变小了。")
    # 扇出对表：类目销售额的真值
    truth = category_sales_truth()
    truth_total = round(sum(truth.values()), 2)
    print(f"    基准：各类目真实销售额合计 = {truth_total}（\\truth 看明细）")
    for tag, out in (("物理", op), ("宽表", ow)):
        t = numeric_total(out["result"])
        if t is not None:
            flag = "  ← 疑似扇出双算！" if t > truth_total * 1.5 else ""
            print(f"    {tag}面结果合计 ≈ {round(t, 2)}{flag}")


def main():
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("请先设置环境变量 DEEPSEEK_API_KEY，再启动。")
        sys.exit(1)
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    if "DB_URL" not in os.environ and not os.path.exists(DB_FILE):
        print("首次启动，正在生成 SQLite 样例库 ...")
        build_dataset.build()
    print("正在（幂等地）建宽表 / 指标表视图 ...")
    views.build_views()

    surface = "wide"
    print("=" * 70)
    print(" 宽表 vs 物理表 vs 指标表 · 交互终端（用数据工程提前把上下文喂到位）")
    print("=" * 70)
    print(f" 当前查询面：{SURFACES[surface]['title']}")
    print(" \\physical / \\wide / \\metric 切面 ；\\ab <题> 物理vs宽表并排 ；\\truth 基准答案")
    print(" 想不到问什么，可以试试：")
    for q in EXAMPLES:
        print(f"   · {q}")
    print(" \\q 退出")
    print("=" * 70)

    while True:
        try:
            line = input(f"\n[{surface}]问> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break
        if not line:
            continue
        if line in ("\\q", "quit", "exit"):
            print("再见。")
            break
        if line in ("\\physical", "\\wide", "\\metric"):
            surface = line.lstrip("\\")
            print(f"  已切到：{SURFACES[surface]['title']}")
            continue
        if line == "\\truth":
            truth = category_sales_truth()
            for k, v in truth.items():
                print(f"    {k}: {round(v, 2)}")
            print(f"    合计: {round(sum(truth.values()), 2)}")
            continue

        try:
            if line.startswith("\\ab"):
                q = line[len("\\ab"):].strip()
                if q:
                    run_ab(q, api_key, model)
            else:
                print(f"\n—— 在【{SURFACES[surface]['title']}】上 ——")
                show_run(run_on_surface(line, surface, api_key=api_key, model=model))
        except Exception as e:  # noqa
            print(f"  出错：{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
