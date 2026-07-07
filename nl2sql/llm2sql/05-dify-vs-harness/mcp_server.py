#!/usr/bin/env python3
"""最小只读 MCP Server（配套 C1-LLM-02A《教大模型查数据库，先别急着写 Prompt》）。

只暴露四个只读工具，正好对应"人查一个陌生库"的四步：
  list_tables      这库里有哪些表        —— 先扫一眼有什么
  describe_table   这张表有哪些字段       —— 看表结构（含数据字典里的口径注释）
  sample_values    这个字段有哪些实际取值   —— 捞几个值确认口径
  execute_query    查出来到底是什么        —— 写 SQL 执行（过只读门禁）

设计要点：
  1. 模型不直连库，只能调这四个动作——执行权收在你这一侧。
  2. execute_query 是唯一会跑模型 SQL 的工具，因此它是命门，必须过 guard。
  3. 表白名单：模型只看得到你允许它看的表，敏感表/日志表根本不暴露。
  4. 连接走 SQLAlchemy（见 db.py），换库只换 DB_URL。

跑成真正的 MCP Server（stdio）：需要安装 mcp 包，然后 `python mcp_server.py`。
这四个函数本身是普通 Python 函数，可被 04-mcp-harness-loop 里的循环直接驱动，也可单测。
"""
from sqlalchemy import inspect

from data_dictionary import comment_for
from db import get_engine, run_read_sql
from guard import ensure_limit, guard_sql

# 表白名单：只有这几张表对模型可见
TABLE_WHITELIST = {"prod_category", "prod_product", "ord_order_main", "ord_order_item"}


def _check_table(table: str):
    if table not in TABLE_WHITELIST:
        return {"error": f"表 {table} 不在白名单内，不可访问", "allowed": sorted(TABLE_WHITELIST)}
    return None


def list_tables() -> dict:
    """列出当前库里模型可以访问的所有表名。查库第一步，先看有哪些表。"""
    insp = inspect(get_engine())
    names = [t for t in insp.get_table_names() if t in TABLE_WHITELIST]
    return {"tables": sorted(names)}


def describe_table(table: str) -> dict:
    """返回一张表的字段名、类型、是否主键，以及数据字典里的业务口径注释。

    参数 table：表名，必须在白名单内。查库第二步，锁定相关表后看它的结构。
    """
    err = _check_table(table)
    if err:
        return err
    insp = inspect(get_engine())
    cols = []
    for c in insp.get_columns(table):
        comment = c.get("comment") or comment_for(table, c["name"])
        cols.append({
            "name": c["name"],
            "type": str(c["type"]),
            "primary_key": bool(c.get("primary_key")),
            "comment": comment,
        })
    return {"table": table, "columns": cols}


def sample_values(table: str, column: str, limit: int = 10) -> dict:
    """捞出某个字段的若干个实际取值（去重）。查库第三步，确认像 status 这类字段的真实口径。

    参数 table/column 必须在白名单表里；limit 默认 10，最多 50。
    """
    err = _check_table(table)
    if err:
        return err
    insp = inspect(get_engine())
    valid_cols = {c["name"] for c in insp.get_columns(table)}
    if column not in valid_cols:
        return {"error": f"字段 {column} 不存在于表 {table}", "columns": sorted(valid_cols)}
    limit = max(1, min(int(limit), 50))
    prep = get_engine().dialect.identifier_preparer
    q = (f"SELECT DISTINCT {prep.quote(column)} AS v FROM {prep.quote(table)} "
         f"WHERE {prep.quote(column)} IS NOT NULL LIMIT {limit}")
    out = run_read_sql(q, max_rows=limit)
    return {"table": table, "column": column, "values": [r[0] for r in out["rows"]]}


def execute_query(sql: str) -> dict:
    """执行一条只读 SQL 并返回结果。查库第四步，也是唯一会真正跑模型 SQL 的工具。

    进来先过只读门禁：只放行 select/with/show/explain/pragma 开头、拒多语句、缺 LIMIT 自动补。
    """
    ok, reason = guard_sql(sql)
    if not ok:
        return {"guard": "reject", "reason": reason}
    safe_sql = ensure_limit(sql)
    try:
        out = run_read_sql(safe_sql)
    except Exception as e:  # noqa
        return {"guard": "allow", "error": f"{type(e).__name__}: {e}", "executed_sql": safe_sql}
    out["guard"] = "allow"
    out["executed_sql"] = safe_sql
    return out


TOOLS = [list_tables, describe_table, sample_values, execute_query]


# ---- 把这四个普通函数注册成真正的 MCP 工具（stdio）----
def build_mcp():
    """装了 mcp 包才能构建真正的 MCP Server；没装也不影响四个函数被单测/被循环调用。"""
    from mcp.server.fastmcp import FastMCP
    server = FastMCP("mini-db-mcp")
    for fn in TOOLS:
        server.tool()(fn)  # 装饰器 + docstring 就是给模型的"工具说明书"
    return server


if __name__ == "__main__":
    build_mcp().run()  # 默认 stdio：客户端把本文件当子进程拉起来
