#!/usr/bin/env python3
"""本课时（编排 vs Harness）的本地测试。运行：python test_lab.py

- 确定性部分：固定节点顺序、guard 一定在 execute 之前、guard 拦截会就地终止（mock LLM，不联网，必过）。
- LLM 部分：设置 DEEPSEEK_API_KEY 才会真调 DeepSeek，验证编排能跑出数据、并和 Harness 对比出差别。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
from flow import FIXED_TABLE, NODES, run_flow
from harness import run_loop

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
failures = []


def check(name, cond):
    print(f"[{PASS if cond else FAIL}] {name}")
    if not cond:
        failures.append(name)


def mock_llm(good_sql=True):
    """假 LLM：sql 节点吐一条固定 SQL，answer 节点吐一句话。"""
    sql = ("SELECT COUNT(*) AS n FROM ord_order_main WHERE payment_status=2 AND is_deleted=0"
           if good_sql else "DELETE FROM ord_order_main")

    def llm_fn(purpose, prompt):
        if purpose == "sql":
            return json.dumps({"sql": sql})
        return "已支付订单数已查出。"

    return llm_fn


def main():
    build_dataset.build()

    # 1) 编排的节点顺序是写死的，且 guard 一定排在 execute 之前
    check("节点图固定为 7 步", len(NODES) == 7)
    check("guard 节点排在 execute 之前",
          NODES.index("guard") < NODES.index("execute_query"))
    check("describe 的表名写死为 ord_order_main", FIXED_TABLE == "ord_order_main")

    # 2) mock 跑通整条流水线（不联网）
    out = run_flow("最近有多少已支付订单？", llm_fn=mock_llm(good_sql=True))
    check("编排按写死顺序跑完 7 个节点", out["nodes"] == NODES)
    check("编排以模型回答收尾", out["stopped"] == "answered" and out["answer"])
    check("编排查出了数据", out["result"]["rows"][0][0] > 0)

    # 3) guard 拦截会就地终止，execute 节点根本不会被走到
    out2 = run_flow("删库", llm_fn=mock_llm(good_sql=False))
    check("模型写了写操作时 guard 拦下", out2["stopped"].startswith("guard_reject"))
    check("被拦下时 execute 节点没有执行", "execute_query" not in out2["nodes"])

    # 4) LLM 真实链路：编排能跑出数据；和 Harness 对比出"固定 vs 自主"的差别
    if os.environ.get("DEEPSEEK_API_KEY"):
        key = os.environ["DEEPSEEK_API_KEY"]
        try:
            q = "最近 30 天每天的支付订单数和支付金额是多少？"
            fo = run_flow(q, api_key=key)
            check("真实链路：编排跑完全部节点", fo["nodes"] == NODES)
            check("真实链路：编排查出了数据",
                  fo["result"] is not None and len(fo["result"]["rows"]) > 0)

            ho = run_loop(q, api_key=key, max_steps=8)
            steps_h = [s["tool"] for s in ho["steps"]]
            check("真实链路：Harness 也查出了数据",
                  ho["final_result"] is not None and len(ho["final_result"]["rows"]) > 0)
            # 核心对比：编排步数恒定（=节点数），Harness 步数由模型自定
            check("真实链路：编排步数恒定=7，Harness 步数由模型临场决定",
                  len(fo["nodes"]) == 7 and len(steps_h) >= 1)
        except Exception as e:  # noqa
            check(f"LLM 链路无异常（{type(e).__name__}: {e}）", False)
    else:
        print("[skip] 未设置 DEEPSEEK_API_KEY，跳过 LLM 真实链路测试")

    print()
    if failures:
        print(f"共 {len(failures)} 项失败：{failures}")
        sys.exit(1)
    print("全部通过 ✅")
    sys.exit(0)


if __name__ == "__main__":
    main()
