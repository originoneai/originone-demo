#!/usr/bin/env python3
"""上下文消融实验台（配套 C1-LLM-01B《你以为你在调 Prompt，其实一直在做上下文工程》）。

这一课不换模型、不换题，只动一样东西——喂给模型的上下文。你可以一个个开关这几个旋钮：

  scope        给哪些表：single 单表(干净) / full 全库(掺入撞脸的干扰表) / none 只给表名不给列
  comments     DDL 里的字段注释：on 带业务含义 / off 只剩光秃秃的字段名
  business_map 业务口径映射：on 明确告诉它"支付成功=2、金额用 actual_amount" / off 让它自己猜
  fewshot      示例：on 给一个"这类问法→这样的 SQL"样板 / off 不给
  value_domain 值域枚举：on 告诉它 payment_status/region 有哪些取值 / off 不给

每拧一个旋钮，同一道题，模型生成的 SQL 就可能当场变样——这就是"上下文工程"四个字最朴素的样子。
"""
import json
import os
import sqlite3
from dataclasses import dataclass, replace

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "ecommerce.db")

RELEVANT_TABLE = "ord_order_main"  # 支付趋势题真正该用的表
SCOPES = ("single", "full", "none")


@dataclass(frozen=True)
class Knobs:
    scope: str = "single"        # single | full | none
    comments: bool = True        # DDL 是否带字段注释
    business_map: bool = True     # 是否给业务口径映射
    fewshot: bool = True          # 是否给 few-shot 示例
    value_domain: bool = True     # 是否给值域枚举

    def label(self) -> str:
        return (f"scope={self.scope} | comments={'on' if self.comments else 'off'} | "
                f"map={'on' if self.business_map else 'off'} | "
                f"fewshot={'on' if self.fewshot else 'off'} | "
                f"values={'on' if self.value_domain else 'off'}")


# 全上下文的"干净基线"：单表 + 注释 + 口径 + 示例 + 值域
CLEAN = Knobs()


BUSINESS_MAP = """业务口径映射：
- "支付成功" = payment_status = 2；"未删除" = is_deleted = 0
- 金额一律用 actual_amount（订单级实付），不要用 total_amount / refund_amount / pay_amount
- 时间锚点：支付相关用 payment_time，下单相关用 order_time
- "最近 30 天" = payment_time >= date('now','-30 day')"""

VALUE_DOMAIN = """字段取值范围：
- payment_status：0未支付 / 1部分支付 / 2已支付 / 3已退款
- order_status：0待支付 / 1已支付 / 2待发货 / 3已发货 / 4已完成 / 5已取消
- region：华东 / 华北 / 华南 / 西南
- is_deleted：0未删除 / 1已删除"""

FEWSHOT = """参考示例（同类问法应照此口径与格式）：
问：最近 30 天每天的支付订单数是多少？
SQL：SELECT date(payment_time) AS pay_date, COUNT(*) AS paid_order_count
     FROM ord_order_main
     WHERE payment_status = 2 AND is_deleted = 0
       AND payment_time >= date('now','-30 day')
     GROUP BY date(payment_time)
     ORDER BY pay_date DESC"""


def get_ddl_map(conn) -> dict:
    rows = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    return {name: sql for name, sql in rows if sql}


def strip_comments(ddl: str) -> str:
    """去掉 DDL 里的 -- 行内注释，只留光秃秃的字段名。"""
    out = []
    for line in ddl.splitlines():
        idx = line.find("--")
        out.append(line[:idx].rstrip() if idx >= 0 else line)
    return "\n".join(l for l in out if l.strip())


def build_schema_block(conn, knobs: Knobs) -> str:
    ddl_map = get_ddl_map(conn)
    if knobs.scope == "none":
        return "可用的表（只给表名，字段需你自行推断）：\n" + "、".join(ddl_map.keys())
    if knobs.scope == "single":
        chosen = {RELEVANT_TABLE: ddl_map[RELEVANT_TABLE]}
    else:  # full：把全库都给它，包含撞脸的干扰表
        chosen = ddl_map
    ddls = [(d if knobs.comments else strip_comments(d)) for d in chosen.values()]
    return "\n\n".join(ddls)


def build_prompt(conn, question: str, knobs: Knobs) -> str:
    parts = ["你是一个只写 SQLite SQL 的助手。只能使用下面给出的表：",
             build_schema_block(conn, knobs)]
    if knobs.business_map:
        parts.append(BUSINESS_MAP)
    if knobs.value_domain:
        parts.append(VALUE_DOMAIN)
    if knobs.fewshot:
        parts.append(FEWSHOT)
    parts.append("目标数据库是 SQLite，请使用 SQLite 语法（如 date('now','-30 day')）。")
    parts.append(f"用户问题：{question}")
    parts.append(
        "只输出一个 JSON 对象（不要多余文字、不要 markdown 代码块）：\n"
        '{"sql": "一条 SELECT 语句", "used_tables": [], "used_columns": [], '
        '"assumptions": [], "risk_notes": []}')
    return "\n\n".join(parts)


def call_deepseek(prompt, api_key, model="deepseek-chat"):
    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "你是严谨的 Text-to-SQL 助手，只输出 JSON 对象。"},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def parse_model_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()
    return json.loads(text)


def run_once(conn, question: str, knobs: Knobs, api_key: str, model="deepseek-chat") -> dict:
    """跑一遍完整链路，返回结构化结果供 CLI / 测试使用。"""
    from guard import ensure_limit, guard_sql
    prompt = build_prompt(conn, question, knobs)
    out = {"knobs": knobs.label(), "prompt": prompt}
    raw = call_deepseek(prompt, api_key, model)
    model_out = parse_model_json(raw)
    sql = model_out.get("sql", "")
    out["model_out"] = model_out
    out["sql"] = sql

    ok, reason = guard_sql(sql)
    out["guard_ok"], out["guard_reason"] = ok, reason
    if not ok:
        out["status"] = "guard_rejected"
        return out

    safe_sql = ensure_limit(sql)
    out["executed_sql"] = safe_sql
    try:
        cur = conn.execute(safe_sql)
        out["columns"] = [d[0] for d in cur.description]
        out["rows"] = cur.fetchall()
        out["status"] = "ok"
    except Exception as e:  # noqa
        out["status"] = "exec_error"
        out["error"] = f"{type(e).__name__}: {e}"
    return out


def apply_toggle(knobs: Knobs, key: str, value: str):
    """把 '\\comments off' 这类命令映射成新的 Knobs。返回 (新Knobs, 提示语)。"""
    key = key.lower()
    if key == "scope":
        if value not in SCOPES:
            return knobs, f"scope 只能是 {'/'.join(SCOPES)}"
        return replace(knobs, scope=value), f"scope -> {value}"
    flags = {"comments": "comments", "map": "business_map", "business_map": "business_map",
             "fewshot": "fewshot", "values": "value_domain", "value_domain": "value_domain"}
    if key in flags:
        if value not in ("on", "off"):
            return knobs, f"{key} 只能是 on/off"
        return replace(knobs, **{flags[key]: value == "on"}), f"{key} -> {value}"
    return knobs, f"未知旋钮：{key}"
