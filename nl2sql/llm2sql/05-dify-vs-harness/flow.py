#!/usr/bin/env python3
"""固定编排引擎：把一条 ChatBI 链路写成"人画死的节点图"（配套 C1-LLM-04A/04B）。

这就是 Dify Chatflow 在代码里的样子。和 04 的 Harness 最大的区别只有一句话：
    这里每个节点该干什么、下一步走哪，全是你（人）提前画死的；模型只负责被点到的
    那两个节点（写 SQL、总结结果），它无权决定"先查哪张表、要不要再确认一下口径"。

节点图（顺序写死，不由模型决定）：
    start(拿到问题)
      → list_tables         [工具节点] 列表（本例其实用不上，保留是为了和 Dify 蓝图对齐）
      → describe_table       [工具节点] 表名写死 = ord_order_main（对应 Dify 的 Fixed 参数）
      → llm_generate_sql     [LLM 节点] 给它问题 + 表结构，只让它吐一条 SQL
      → guard                [代码节点] 只读门禁：拦下就地终止，exec 根本没机会跑
      → execute_query        [工具节点] 执行门禁放行后的 SQL
      → llm_answer           [LLM 节点] 把结果行数用一句话讲给用户

对比 04 的 harness.py：那里模型每一步都在自己决定调哪个工具；这里模型只是流水线上
被固定工位调用的两个零件。可控性和灵活性的取舍，全藏在这个差别里——这正是 04B 要讲的
"编排 vs Harness"。
"""
import json
import os

import requests

import mcp_server
from guard import ensure_limit, guard_sql

# 整张图就这几步，顺序写死。模型无权改动这个列表——这正是"编排"的定义。
NODES = ["start", "list_tables", "describe_table",
         "llm_generate_sql", "guard", "execute_query", "llm_answer"]

# 对应 Dify 里把 table 参数设成 Fixed：这条流水线只认这张表。
FIXED_TABLE = "ord_order_main"

SQL_SYSTEM = """你是一个 SQL 生成器，是一条固定流水线上的一个工位。
上游已经把用户问题和目标表的完整结构交给你。你只做一件事：为这个问题写一条 SQLite 只读 SELECT。
硬性要求：
1. 只能用给你的这张表，不要 join 别的表，不要猜别的表名。
2. 只输出 JSON：{"sql": "SELECT ..."}，不要任何解释。
3. status 类字段的口径以表结构里的注释为准（比如已支付看 payment_status）。"""

ANSWER_SYSTEM = "你是流水线的收尾工位。根据用户问题和查询返回的数据，用一句中文把结论说清楚，不要复述 SQL。"


def _schema_block(describe_result: dict) -> str:
    lines = [f"表 {describe_result['table']} 的字段："]
    for c in describe_result.get("columns", []):
        note = f"  -- {c['comment']}" if c.get("comment") else ""
        lines.append(f"  {c['name']} {c['type']}{note}")
    return "\n".join(lines)


def call_deepseek(messages, api_key, model="deepseek-chat", json_mode=False):
    body = {"model": model, "temperature": 0, "messages": messages}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=body, timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def run_flow(question, api_key=None, model="deepseek-chat", on_event=None, llm_fn=None):
    """按写死的节点图跑一遍。返回 {answer, sql, result, nodes, stopped}。

    on_event(node_name, payload)：cli 用它把每个节点实时打出来。
    llm_fn(purpose, prompt) -> str：可注入（测试用 mock）。purpose ∈ {"sql","answer"}。
        默认走 DeepSeek：sql 节点用 json 模式，answer 节点用普通文本。
    """
    if llm_fn is None:
        key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise SystemExit("未设置 DEEPSEEK_API_KEY")

        def llm_fn(purpose, prompt):  # noqa
            if purpose == "sql":
                return call_deepseek(
                    [{"role": "system", "content": SQL_SYSTEM},
                     {"role": "user", "content": prompt}], key, model, json_mode=True)
            return call_deepseek(
                [{"role": "system", "content": ANSWER_SYSTEM},
                 {"role": "user", "content": prompt}], key, model)

    def emit(node, payload):
        if on_event:
            on_event(node, payload)

    ran = []

    # ---- 节点：start ----
    ran.append("start")
    emit("start", {"question": question})

    # ---- 节点：list_tables（工具，固定）----
    ran.append("list_tables")
    tables = mcp_server.list_tables()
    emit("list_tables", {"result": tables})

    # ---- 节点：describe_table（工具，表名写死）----
    ran.append("describe_table")
    schema = mcp_server.describe_table(FIXED_TABLE)
    emit("describe_table", {"table": FIXED_TABLE, "result": schema})

    # ---- 节点：llm_generate_sql（LLM，模型只被允许干这个）----
    ran.append("llm_generate_sql")
    prompt = f"用户问题：{question}\n\n{_schema_block(schema)}"
    raw = llm_fn("sql", prompt)
    try:
        sql = json.loads(raw).get("sql", "").strip()
    except json.JSONDecodeError:
        sql = raw.strip()
    emit("llm_generate_sql", {"sql": sql})

    # ---- 节点：guard（代码，拦下就终止；exec 永远排在它后面）----
    ran.append("guard")
    ok, reason = guard_sql(sql)
    if not ok:
        emit("guard", {"decision": "reject", "reason": reason})
        return {"answer": None, "sql": sql, "result": None,
                "nodes": ran, "stopped": f"guard_reject:{reason}"}
    safe_sql = ensure_limit(sql)
    emit("guard", {"decision": "allow", "sql": safe_sql})

    # ---- 节点：execute_query（工具，跑门禁放行后的 SQL）----
    ran.append("execute_query")
    result = mcp_server.execute_query(safe_sql)
    emit("execute_query", {"result": result})
    if result.get("guard") != "allow" or "rows" not in result:
        return {"answer": None, "sql": safe_sql, "result": result,
                "nodes": ran, "stopped": "execute_error"}

    # ---- 节点：llm_answer（LLM，收尾）----
    ran.append("llm_answer")
    ans_prompt = (f"用户问题：{question}\n查询返回 {result['row_count']} 行，"
                  f"列={result['columns']}，前几行={result['rows'][:5]}")
    answer = llm_fn("answer", ans_prompt)
    emit("llm_answer", {"answer": answer})

    return {"answer": answer, "sql": safe_sql, "result": result,
            "nodes": ran, "stopped": "answered"}
