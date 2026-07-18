#!/usr/bin/env python3
"""Guard：管资格的服务端门禁。配套文章 C1-07A 第二节。

从最早 MCP execute_query 那道最小只读线，长成一张带理由码的判定表。
一条 SQL 依次问四句话，返回结构化结果（decision/reason/sql），能进 Trace：
  1. 只读吗？    首词不在 select/with/show/explain/pragma → deny(write_or_admin_operation)
  2. 单语句吗？  分号后还有内容 → deny(multi_statement)
  3. 表都在白名单吗？（CTE 局部名先剔除，别把临时块误判成未知表）→ deny(unknown_table)
  4. 有边界吗？  缺 LIMIT → rewrite(missing_limit)，自动补 LIMIT 200 再放行
否则 allow。deny/rewrite/allow 三档；真实项目还该有 needs_review 一档留给"拿不准"。

门禁必须焊在服务端不可绕过的链路上，不赌"模型愿不愿意调用某个检查工具"。
"""
import re

READ_ONLY_HEAD = ("select", "with", "show", "explain", "pragma")
WHITELIST = {"prod_category", "prod_product", "ord_order_main", "ord_order_item"}


def _cte_names(sql: str):
    """抓出 WITH x AS (...), y AS (...) 里的局部名 x、y，它们不是真表。"""
    names = set()
    m = re.search(r"\bwith\b(.*?)\bselect\b", sql, re.IGNORECASE | re.DOTALL)
    if not m:
        return names
    head = m.group(1)
    for cm in re.finditer(r"([A-Za-z_][\w]*)\s+as\s*\(", head, re.IGNORECASE):
        names.add(cm.group(1).lower())
    return names


def _referenced_tables(sql: str):
    """抓 FROM / JOIN 后面的表名（忽略别名、忽略子查询左括号）。"""
    tabs = set()
    for tm in re.finditer(r"\b(?:from|join)\s+([A-Za-z_][\w]*)", sql, re.IGNORECASE):
        tabs.add(tm.group(1).lower())
    return tabs


def _has_limit(sql: str) -> bool:
    return re.search(r"\blimit\b", sql, re.IGNORECASE) is not None


def tables_outside_whitelist(sql: str, whitelist=WHITELIST):
    cte = _cte_names(sql)
    refs = _referenced_tables(sql)
    return sorted(t for t in refs if t not in whitelist and t not in cte)


def guard(sql: str, whitelist=WHITELIST, default_limit: int = 200) -> dict:
    s = sql.strip().rstrip(";").strip()
    if not s:
        return {"decision": "deny", "reason": "empty_sql", "sql": sql}
    if ";" in s:
        return {"decision": "deny", "reason": "multi_statement", "sql": sql}
    head = s.split(None, 1)[0].lower()
    if head not in READ_ONLY_HEAD:
        return {"decision": "deny", "reason": "write_or_admin_operation", "sql": sql}
    unknown = tables_outside_whitelist(s, whitelist)
    if unknown:
        return {"decision": "deny", "reason": f"unknown_table:{','.join(unknown)}", "sql": sql}
    if not _has_limit(s):
        return {"decision": "rewrite", "reason": "missing_limit",
                "sql": f"{s}\nLIMIT {default_limit}"}
    return {"decision": "allow", "reason": "ok", "sql": s}


if __name__ == "__main__":
    samples = [
        "SELECT region, COUNT(*) FROM ord_order_main GROUP BY region",
        "DELETE FROM ord_order_main WHERE payment_status = 0",
        "SELECT * FROM ord_order_main; DROP TABLE ord_order_main",
        "SELECT user_id, mobile FROM usr_user LIMIT 10",
        "WITH paid AS (SELECT * FROM ord_order_main WHERE payment_status=2) "
        "SELECT region, COUNT(*) FROM paid GROUP BY region LIMIT 50",
    ]
    for q in samples:
        g = guard(q)
        print(f"[{g['decision']:7}] {g['reason']:30} <= {q[:55]}")
