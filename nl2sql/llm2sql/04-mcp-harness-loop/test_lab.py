#!/usr/bin/env python3
"""本课时（MCP 工具循环 / Harness）的本地测试。运行：python test_lab.py

- 确定性部分：工具 schema、dispatch、以及用 mock 模型跑通整条循环（不联网，必过）。
- LLM 部分：设置 DEEPSEEK_API_KEY 才会真调 DeepSeek，验证模型确实先探索工具再执行。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
import harness
from harness import TOOL_SCHEMAS, dispatch, run_loop

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
failures = []


def check(name, cond):
    print(f"[{PASS if cond else FAIL}] {name}")
    if not cond:
        failures.append(name)


def _tc(cid, name, args):
    return {"id": cid, "type": "function",
            "function": {"name": name, "arguments": json.dumps(args)}}


def make_mock():
    """一个按脚本走查库四步的假模型：list → describe → execute → 收尾回答。"""
    script = [
        {"role": "assistant", "content": None,
         "tool_calls": [_tc("c1", "list_tables", {})]},
        {"role": "assistant", "content": None,
         "tool_calls": [_tc("c2", "describe_table", {"table": "ord_order_main"})]},
        {"role": "assistant", "content": None,
         "tool_calls": [_tc("c3", "execute_query",
                            {"sql": "SELECT COUNT(*) AS n FROM ord_order_main "
                                    "WHERE payment_status=2 AND is_deleted=0"})]},
        {"role": "assistant", "content": "已支付且未删除的订单数已查出。", "tool_calls": None},
    ]
    state = {"i": 0}

    def chat_fn(messages, tools):
        msg = script[state["i"]]
        state["i"] += 1
        return msg

    return chat_fn


def main():
    build_dataset.build()

    # 1) 工具 schema 与 dispatch
    check("交给模型的工具 schema 是四个", len(TOOL_SCHEMAS) == 4)
    names = {t["function"]["name"] for t in TOOL_SCHEMAS}
    check("四个工具名齐全",
          names == {"list_tables", "describe_table", "sample_values", "execute_query"})
    check("dispatch 能调 list_tables", "tables" in dispatch("list_tables", {}))
    check("dispatch 拦截未知工具", "error" in dispatch("no_such_tool", {}))

    # 2) 用 mock 模型跑通整条循环（不联网）
    out = run_loop("最近有多少已支付订单？", chat_fn=make_mock())
    tools_used = [s["tool"] for s in out["steps"]]
    check("mock 循环按 list→describe→execute 走",
          tools_used == ["list_tables", "describe_table", "execute_query"])
    check("mock 循环拿到 final_sql", out["final_sql"] is not None)
    check("mock 循环 execute 结果非空", out["final_result"]["rows"][0][0] > 0)
    check("mock 循环以模型回答收尾", out["stopped"] == "answered" and out["answer"])

    # 3) 循环止损：给一个永远只调工具、不收尾的模型，应在 max_steps 停下
    def never_stop(messages, tools):
        return {"role": "assistant", "content": None,
                "tool_calls": [_tc("x", "list_tables", {})]}
    out2 = run_loop("绕圈", chat_fn=never_stop, max_steps=3)
    check("到达 max_steps 能止损", out2["stopped"] == "max_steps" and len(out2["steps"]) == 3)

    # 4) LLM 真实链路：模型必须先探索工具，再执行
    if os.environ.get("DEEPSEEK_API_KEY"):
        try:
            out3 = run_loop("最近 30 天每天的支付订单数和支付金额是多少？",
                            api_key=os.environ["DEEPSEEK_API_KEY"], max_steps=8)
            used = [s["tool"] for s in out3["steps"]]
            check("真实链路：调用了 execute_query", "execute_query" in used)
            first_exec = used.index("execute_query") if "execute_query" in used else -1
            explored_first = first_exec > 0 and (
                "list_tables" in used[:first_exec] or "describe_table" in used[:first_exec])
            check("真实链路：先探索(list/describe)再执行，没有凭空写 SQL", explored_first)
            check("真实链路：最终查出了数据",
                  out3["final_result"] is not None and len(out3["final_result"]["rows"]) > 0)
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
