#!/usr/bin/env python3
"""本课时（最小只读 MCP Server）的本地测试。运行：python test_lab.py

全部确定性、无需联网：建库、四个工具、白名单、门禁、注释合并、真正的 MCP 注册。
（这一课是"服务端"，模型驱动工具循环的真实链路在 04-mcp-harness-loop 里测。）
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
import mcp_server
from mcp_server import (describe_table, execute_query, list_tables, sample_values)

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
failures = []


def check(name, cond):
    print(f"[{PASS if cond else FAIL}] {name}")
    if not cond:
        failures.append(name)


def main():
    build_dataset.build()

    # 1) list_tables 只返回白名单里的表
    tabs = list_tables()["tables"]
    check("list_tables 返回四张业务表",
          set(tabs) == {"prod_category", "prod_product", "ord_order_main", "ord_order_item"})

    # 2) describe_table：结构 + 口径注释（注释来自 side-car 数据字典）
    d = describe_table("ord_order_main")
    names = [c["name"] for c in d["columns"]]
    check("describe_table 返回全部字段", "payment_status" in names and "actual_amount" in names)
    ps = next(c for c in d["columns"] if c["name"] == "payment_status")
    check("describe_table 合并了口径注释", "已支付" in ps["comment"])

    # 3) describe_table 白名单外的表被拒
    check("describe_table 拦截白名单外的表", "error" in describe_table("sys_secret"))

    # 4) sample_values：payment_status 的真实取值应含 2
    sv = sample_values("ord_order_main", "payment_status", limit=10)
    check("sample_values 捞到真实取值", 2 in sv["values"])
    check("sample_values 拦截不存在的字段",
          "error" in sample_values("ord_order_main", "no_such_col"))

    # 5) execute_query：只读放行 + 写操作拦截 + 缺 LIMIT 自动补
    ok = execute_query("SELECT COUNT(*) AS n FROM ord_order_main")
    check("execute_query 放行 SELECT 并返回结果", ok.get("guard") == "allow" and ok["rows"])
    check("execute_query 自动补 LIMIT", "LIMIT" in ok["executed_sql"].upper())
    bad = execute_query("DELETE FROM ord_order_main")
    check("execute_query 拦截写操作", bad.get("guard") == "reject")
    multi = execute_query("SELECT 1; DROP TABLE ord_order_main")
    check("execute_query 拦截多语句", multi.get("reason") == "multi_statement_forbidden")

    # 6) 四步链路能真正串起来（人肉版）：查出 payment_status=2 的订单数
    n = execute_query(
        "SELECT COUNT(*) AS n FROM ord_order_main WHERE payment_status = 2 AND is_deleted = 0"
    )["rows"][0][0]
    check("四步链路跑通且有数据", n > 0)

    # 7) 真正注册成 MCP Server（装了 mcp 包时）
    try:
        server = mcp_server.build_mcp()
        check("四个工具已注册进 MCP Server", server is not None)
    except ImportError:
        print("[skip] 未安装 mcp 包，跳过真实 MCP 注册校验（不影响四个工具本身）")

    print()
    if failures:
        print(f"共 {len(failures)} 项失败：{failures}")
        sys.exit(1)
    print("全部通过 ✅")
    sys.exit(0)


if __name__ == "__main__":
    main()
