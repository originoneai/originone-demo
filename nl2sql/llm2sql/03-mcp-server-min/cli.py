#!/usr/bin/env python3
"""交互终端（主入口）：亲手调这台 MCP Server 的四个只读工具。

这一课先不接大模型——你自己扮演那个"查陌生库的人"，一步步把四个工具敲一遍，
体会它们合起来是怎么把"一次性塞全库"换成"用到哪、取到哪"的。下一课（04）再让
模型自己来敲这几个工具。

  python cli.py

命令：
  tables                  列出所有表（list_tables）
  desc  <表>              看表结构 + 口径注释（describe_table）
  sample <表> <字段>      捞该字段的实际取值（sample_values）
  sql   <SELECT...>       执行只读 SQL（execute_query，过门禁）
  \\q                     退出
"""
import json
import os
import sys

import build_dataset
import mcp_server
from db import DEFAULT_DB

DB_FILE = DEFAULT_DB.replace("sqlite:///", "")


def show(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def main():
    # 默认 SQLite；若未指定 DB_URL 且库文件不存在，则现建
    if "DB_URL" not in os.environ and not os.path.exists(DB_FILE):
        print("首次启动，正在生成 SQLite 样例库 ...")
        build_dataset.build()

    print("=" * 64)
    print(" 最小只读 MCP Server · 手动工具探索台")
    print("=" * 64)
    print(" 你来扮演查库的人，把四个工具挨个敲一遍。可用命令：")
    print("   tables            列出所有表")
    print("   desc <表>         看表结构 + 口径注释")
    print("   sample <表> <字段> 捞字段实际取值")
    print("   sql <SELECT...>   执行只读 SQL（过门禁）")
    print("   \\q                退出")
    print(" 试试这条查库四步：tables → desc ord_order_main")
    print("                → sample ord_order_main payment_status → sql SELECT ...")
    print("=" * 64)

    while True:
        try:
            line = input("\nmcp> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break
        if not line:
            continue
        if line in ("\\q", "quit", "exit"):
            print("再见。")
            break

        parts = line.split(None, 2)
        cmd = parts[0].lower()
        try:
            if cmd == "tables":
                show(mcp_server.list_tables())
            elif cmd == "desc" and len(parts) >= 2:
                show(mcp_server.describe_table(parts[1]))
            elif cmd == "sample" and len(parts) >= 3:
                show(mcp_server.sample_values(parts[1], parts[2]))
            elif cmd == "sql" and len(parts) >= 2:
                show(mcp_server.execute_query(line[len("sql"):].strip()))
            else:
                print("  用法：tables | desc <表> | sample <表> <字段> | sql <SELECT...> | \\q")
        except Exception as e:  # noqa
            print(f"  工具执行出错：{type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
