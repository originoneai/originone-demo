#!/usr/bin/env python3
"""本课时（上下文消融）的本地测试。运行：python test_lab.py

- 确定性部分（建库、干扰表、门禁、旋钮如何改写 Prompt）：无需联网，必过。
- LLM 部分：设置了 DEEPSEEK_API_KEY 才会真调 DeepSeek，验证"干净基线"能答对。
"""
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
import context_lab
from context_lab import CLEAN, Knobs, build_prompt, build_schema_block, run_once, strip_comments
from guard import ensure_limit, guard_sql

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
failures = []


def check(name, cond):
    print(f"[{PASS if cond else FAIL}] {name}")
    if not cond:
        failures.append(name)


def teacher_total(db):
    conn = sqlite3.connect(db)
    v = conn.execute(
        "SELECT COALESCE(SUM(actual_amount),0) FROM ord_order_main "
        "WHERE payment_status=2 AND is_deleted=0 AND payment_time >= date('now','-30 day')"
    ).fetchone()[0]
    conn.close()
    return round(v, 2)


def main():
    # 1) 建库 + 干扰表
    db = build_dataset.build()
    check("建库成功且文件存在", os.path.exists(db))
    conn = sqlite3.connect(db)
    ddl_map = context_lab.get_ddl_map(conn)
    check("六张表齐全（含两张撞脸干扰表）",
          {"ord_order_main", "ord_refund", "stat_order_daily"}.issubset(ddl_map.keys()))
    n_stat = conn.execute("SELECT COUNT(*) FROM stat_order_daily").fetchone()[0]
    check("预聚合干扰表非空", n_stat > 0)

    # 2) 门禁（底线不因上下文变化而变）
    check("门禁放行 SELECT", guard_sql("SELECT 1")[0] is True)
    check("门禁拦截 DELETE", guard_sql("DELETE FROM t")[1] == "write_or_admin_operation")
    check("门禁拦截多语句", guard_sql("SELECT 1; DROP TABLE t")[1] == "multi_statement_forbidden")
    check("门禁自动补 LIMIT", "LIMIT" in ensure_limit("SELECT * FROM t").upper())

    # 3) scope 旋钮：single 只给相关表，full 掺入干扰表，none 不给列
    single = build_schema_block(conn, Knobs(scope="single"))
    full = build_schema_block(conn, Knobs(scope="full"))
    none = build_schema_block(conn, Knobs(scope="none"))
    check("scope=single 只含 ord_order_main",
          "ord_order_main" in single and "ord_refund" not in single)
    check("scope=full 掺入撞脸干扰表",
          "ord_refund" in full and "stat_order_daily" in full)
    check("scope=none 只给表名、不给 CREATE 列定义",
          "ord_order_main" in none and "CREATE TABLE" not in none)

    # 4) comments 旋钮：off 后注释被剥掉
    with_c = build_schema_block(conn, Knobs(scope="single", comments=True))
    no_c = build_schema_block(conn, Knobs(scope="single", comments=False))
    check("comments=on 带字段注释", "实付金额" in with_c)
    check("comments=off 注释被剥掉", "实付金额" not in no_c and "actual_amount" in no_c)
    check("strip_comments 去掉 -- 行内注释", "--" not in strip_comments(with_c))

    # 5) 其余旋钮：确实在改写 Prompt
    q = "最近 30 天每天的支付订单数和支付金额是多少？"
    p_map_on = build_prompt(conn, q, Knobs(business_map=True))
    p_map_off = build_prompt(conn, q, Knobs(business_map=False))
    check("map=on 注入口径映射", "支付成功" in p_map_on)
    check("map=off 不注入口径映射", "支付成功" not in p_map_off)
    check("fewshot=on 注入示例", "参考示例" in build_prompt(conn, q, Knobs(fewshot=True)))
    check("fewshot=off 不注入示例", "参考示例" not in build_prompt(conn, q, Knobs(fewshot=False)))
    check("values=on 注入值域", "取值范围" in build_prompt(conn, q, Knobs(value_domain=True)))
    check("values=off 不注入值域", "取值范围" not in build_prompt(conn, q, Knobs(value_domain=False)))
    conn.close()

    t_total = teacher_total(db)
    check("最近30天支付金额基准 > 0", t_total > 0)

    # 6) LLM 真实链路：干净基线（single + 全开）应答对
    if os.environ.get("DEEPSEEK_API_KEY"):
        key = os.environ["DEEPSEEK_API_KEY"]
        conn = sqlite3.connect(db)
        try:
            res = run_once(conn, q, CLEAN, key)
            check("干净基线：链路跑通", res["status"] == "ok")
            check("干净基线：SQL 过门禁", res.get("guard_ok") is True)
            # 稳健校验：结果里某个数值列求和 ≈ 教师基准支付总额
            matched = False
            cols, rows = res.get("columns", []), res.get("rows", [])
            for ci in range(len(cols)):
                try:
                    s = round(sum(float(r[ci]) for r in rows if r[ci] is not None), 2)
                except (TypeError, ValueError):
                    continue
                if abs(s - t_total) <= max(1.0, t_total * 0.01):
                    matched = True
                    break
            check("干净基线：结果口径与教师基准一致", matched)

            # 消融对照：把口径映射+值域+示例都关掉，链路仍应能跑（对错不做硬断言，避免抖动）
            bare = Knobs(scope="full", comments=False, business_map=False,
                         fewshot=False, value_domain=False)
            res2 = run_once(conn, q, bare, key)
            check("全消融：链路能返回结果（内容对错留给学员现场观察）",
                  res2["status"] in ("ok", "exec_error", "guard_rejected"))
        except Exception as e:  # noqa
            check(f"LLM 链路无异常（{type(e).__name__}: {e}）", False)
        finally:
            conn.close()
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
