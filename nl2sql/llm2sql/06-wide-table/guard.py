#!/usr/bin/env python3
"""服务端最小只读门禁：拦写操作、拦多语句、缺 LIMIT 自动补。

对应课程 01A 里 execute_query 的那道关。它不赌模型的自觉，
在执行入口就把能穿过去的语句限定成只读查询。
"""
import re

READ_ONLY_HEAD = ("select", "with", "show", "explain", "pragma")


def guard_sql(sql: str):
    """返回 (是否放行, 原因码)。"""
    s = sql.strip().rstrip(";").strip()
    if not s:
        return False, "empty_sql"
    if ";" in s:
        return False, "multi_statement_forbidden"
    head = s.split(None, 1)[0].lower()
    if head not in READ_ONLY_HEAD:
        return False, "write_or_admin_operation"
    return True, "ok"


def ensure_limit(sql: str, default_limit: int = 200) -> str:
    """给没有 LIMIT 的查询补一个默认上限。"""
    s = sql.strip().rstrip(";").strip()
    if re.search(r"\blimit\b", s, re.IGNORECASE):
        return s
    return f"{s}\nLIMIT {default_limit}"


if __name__ == "__main__":
    samples = [
        "SELECT 1",
        "DELETE FROM ord_order_main",
        "SELECT * FROM t; DROP TABLE t",
        "select id from t",
    ]
    for q in samples:
        print(guard_sql(q), "|", q)
