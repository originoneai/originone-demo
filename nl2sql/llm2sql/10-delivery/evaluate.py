#!/usr/bin/env python3
"""验收回归：把 Golden Questions 跑过全链路，出一份交付验收报告。配套文章 C1-09。

报告 = 整体通过率 + 每题成败 + 失败按类型归因。这就是交给客户的"到底行到什么程度"
的诚实答卷，也是日后每次迭代的基准线。generate_fn 可注入 mock/DeepSeek。
"""
from collections import Counter

from golden import GOLDEN, truth_total_for
from pipeline import answer


def evaluate(api_key=None, generate_fn=None, max_retries=2):
    rows = []
    for qid, spec in GOLDEN.items():
        out = answer(spec["question"], spec["contract"],
                     api_key=api_key, generate_fn=generate_fn,
                     max_retries=max_retries, truth_total=truth_total_for(qid))
        fails = [] if out["ok"] else out.get("last_fails", ["unknown"])
        rows.append({"qid": qid, "level": spec["level"], "ok": out["ok"],
                     "attempts": out["attempt"] + 1, "fails": fails,
                     "sql": out["sql"]})
    npass = sum(1 for r in rows if r["ok"])
    by_level = {}
    for r in rows:
        d = by_level.setdefault(r["level"], [0, 0])
        d[1] += 1
        if r["ok"]:
            d[0] += 1
    fail_types = Counter(f.split(":")[0] for r in rows for f in r["fails"])
    return {"total": len(rows), "passed": npass,
            "pass_rate": round(npass / len(rows), 3),
            "by_level": by_level, "failure_breakdown": dict(fail_types),
            "rows": rows}


def print_report(rep):
    print(f"===== C1 交付验收报告 =====")
    print(f"整体通过率：{rep['passed']}/{rep['total']}  ({rep['pass_rate']*100:.0f}%)")
    print("分档通过：", {k: f"{v[0]}/{v[1]}" for k, v in sorted(rep["by_level"].items())})
    print("失败归因：", rep["failure_breakdown"] or "无")
    print("-" * 40)
    for r in rep["rows"]:
        tag = "PASS" if r["ok"] else "FAIL"
        extra = "" if r["ok"] else f"  失败类型={r['fails']}"
        print(f"[{r['level']}] {tag}  {r['qid']}  (尝试{r['attempts']}次){extra}")
