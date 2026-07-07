#!/usr/bin/env python3
"""Harness：让模型自己驱动 MCP 工具的推理循环（配套 C1-LLM-03A/03B）。

这就是"真 MCP 工具循环"的核心。不再由你把整库 DDL 一次性塞进 Prompt，而是把
四个只读工具交给模型，让它自己一步步问：
    list_tables → describe_table → sample_values → execute_query
每一步模型看到上一步的返回，再决定下一步调哪个工具，直到查出答案。这套
"想—调工具—看结果—再想"的循环，就是 Harness（也叫 ReAct / Tool Calling 的骨架）。

关键设计：
  - 工具就是 03-mcp-server-min 里那四个只读函数（这里 vendored 一份，保持单文件夹可跑）。
  - chat_fn 可注入：默认调 DeepSeek（OpenAI 兼容 tool calling）；测试可传入 mock，不联网。
  - max_steps 是止损阀：模型绕不出来时不至于无限调工具。
"""
import json
import os

import requests

import mcp_server

# 交给模型的"工具说明书"——OpenAI/DeepSeek 通用的 function calling schema
TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "list_tables",
        "description": "列出库里可访问的所有表名。查库第一步。",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "describe_table",
        "description": "返回一张表的字段名、类型、主键和业务口径注释。查库第二步。",
        "parameters": {"type": "object",
                       "properties": {"table": {"type": "string", "description": "表名"}},
                       "required": ["table"]},
    }},
    {"type": "function", "function": {
        "name": "sample_values",
        "description": "捞出某字段的若干去重实际取值，用于确认 status 这类字段的真实口径。查库第三步。",
        "parameters": {"type": "object",
                       "properties": {"table": {"type": "string"},
                                      "column": {"type": "string"},
                                      "limit": {"type": "integer"}},
                       "required": ["table", "column"]},
    }},
    {"type": "function", "function": {
        "name": "execute_query",
        "description": "执行一条只读 SELECT 并返回结果。查库第四步，也是唯一真正跑 SQL 的工具。",
        "parameters": {"type": "object",
                       "properties": {"sql": {"type": "string", "description": "一条 SELECT 语句"}},
                       "required": ["sql"]},
    }},
]

DISPATCH = {fn.__name__: fn for fn in mcp_server.TOOLS}

SYSTEM_PROMPT = """你是一个查数据库的助手。你看不到库的结构，只能通过调用工具去了解它。
硬性要求：
1. 不许凭空猜表名、字段名。写 SQL 之前，必须先用 list_tables、describe_table 把相关表和字段搞清楚。
2. 遇到 status、payment_status 这类含义不明的字段，先用 sample_values 看真实取值再下过滤条件。
3. 只有在弄清结构后，才用 execute_query 执行 SQL（只读，SQLite 语法，如 date('now','-30 day')）。
4. 拿到 execute_query 的结果后，用一句中文把结论说清楚，不要再调工具。"""


def dispatch(name: str, args: dict) -> dict:
    fn = DISPATCH.get(name)
    if fn is None:
        return {"error": f"未知工具 {name}"}
    return fn(**args)


def call_deepseek_chat(messages, tools, api_key, model="deepseek-chat"):
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "temperature": 0, "tools": tools,
              "tool_choice": "auto", "messages": messages},
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]


def run_loop(question, api_key=None, model="deepseek-chat", max_steps=8,
             on_event=None, chat_fn=None):
    """跑一整轮工具循环。返回 {answer, steps, final_sql, final_result, stopped}。

    on_event(kind, payload)：cli 用它把每一步实时打出来。
    chat_fn(messages, tools) -> assistant message dict：可注入，默认调 DeepSeek。
    """
    if chat_fn is None:
        key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not key:
            raise SystemExit("未设置 DEEPSEEK_API_KEY")
        chat_fn = lambda msgs, tools: call_deepseek_chat(msgs, tools, key, model)  # noqa

    def emit(kind, payload):
        if on_event:
            on_event(kind, payload)

    messages = [{"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}]
    steps, final_sql, final_result = [], None, None

    for _ in range(max_steps):
        msg = chat_fn(messages, TOOL_SCHEMAS)
        messages.append(msg)
        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            emit("final", msg.get("content", ""))
            return {"answer": msg.get("content", ""), "steps": steps,
                    "final_sql": final_sql, "final_result": final_result, "stopped": "answered"}

        for tc in tool_calls:
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            emit("call", {"tool": name, "args": args})
            result = dispatch(name, args)
            steps.append({"tool": name, "args": args, "result": result})
            emit("result", {"tool": name, "result": result})
            if name == "execute_query" and result.get("guard") == "allow" and "rows" in result:
                final_sql = result.get("executed_sql")
                final_result = result
            messages.append({"role": "tool", "tool_call_id": tc.get("id", name),
                             "content": json.dumps(result, ensure_ascii=False, default=str)})

    emit("stopped", "max_steps")
    return {"answer": None, "steps": steps, "final_sql": final_sql,
            "final_result": final_result, "stopped": "max_steps"}
