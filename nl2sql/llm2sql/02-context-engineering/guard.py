#!/usr/bin/env python3
"""服务端最小只读门禁：拦写操作、拦多语句、缺 LIMIT 自动补。

与 01-prompt-only 同款。上下文怎么消融，门禁这道底线都不动——
无论模型被喂了多干净或多脏的上下文，能穿过去的都只能是只读查询。
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
    for q in ["SELECT 1", "DELETE FROM t", "SELECT 1; DROP TABLE t", "select id from t"]:
        print(guard_sql(q), "|", q)
