#!/usr/bin/env python3
"""本课时（LLM-Wiki 基座）的本地测试。运行：python test_lab.py

- 确定性部分（不联网）：库房结构完整、检索器对必考题命中必要证据、覆盖率报告识别缺口、
  很薄的 schema 确实不含口径、经典 SQL 自洽、扇出坑真实存在。
- LLM 部分（设 DEEPSEEK_API_KEY 才跑）：无 wiki 一路容易偏离真值，有 wiki 一路
  召回销售额口径后能贴近真值（把扇出双算躲过去）。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_dataset
from db import run_read_sql
from rag import LEAN_SCHEMA, answer, build_prompt, category_sales_truth
from retriever import retrieval_report, retrieve
from wiki import WIKI_ENTRIES, by_type

PASS, FAIL = "\033[32mPASS\033[0m", "\033[31mFAIL\033[0m"
failures = []


def check(name, cond):
    print(f"[{PASS if cond else FAIL}] {name}")
    if not cond:
        failures.append(name)


def _sum_numeric(result):
    total = 0.0
    for r in result["rows"]:
        for v in reversed(r):
            if isinstance(v, (int, float)):
                total += v
                break
    return total


def main():
    build_dataset.build()

    # 1) 库房结构完整：四类都在，每条字段齐全，id 唯一
    types = {e["type"] for e in WIKI_ENTRIES}
    check("四类语义都在（term/alias/golden/pitfall）",
          types == {"term", "alias", "golden", "pitfall"})
    check("每条都有 id/type/title/aliases/content",
          all(all(k in e for k in ("id", "type", "title", "aliases", "content"))
              for e in WIKI_ENTRIES))
    check("id 唯一", len({e["id"] for e in WIKI_ENTRIES}) == len(WIKI_ENTRIES))
    check("golden 条目都带可跑的标准 SQL",
          all(e.get("sql") for e in by_type("golden")))

    # 2) 检索器对必考题命中必要证据
    r = retrieve("各类目的销售额是多少？")
    ids = {e["id"] for e in r}
    check("销售额题召回口径条 term.sales_amount", "term.sales_amount" in ids)
    check("销售额题召回类目别名 alias.category", "alias.category" in ids)
    check("销售额题召回经典解法 golden.category_sales", "golden.category_sales" in ids)

    rep = retrieval_report("各类目的销售额是多少？", r)
    check("覆盖率报告：销售额题必要业务词全覆盖（status=pass）", rep["status"] == "pass")
    check("覆盖率报告：无漏召", rep["missing_terms"] == [])

    # 3) 覆盖率报告能识别缺口：删掉类目别名后应报 gap
    thin = [e for e in WIKI_ENTRIES if e["id"] != "alias.category"]
    r_thin = retrieve("各类目的销售额是多少？", entries=thin)
    rep_thin = retrieval_report("各类目的销售额是多少？", r_thin)
    check("库房缺类目别名时，报告能报出缺口（status=gap）", rep_thin["status"] == "gap")

    # 4) 越界题：召回越界 pitfall（不会硬编字段）
    r_oos = retrieve("用户手机号是多少")
    check("越界题召回 pitfall.out_of_scope",
          "pitfall.out_of_scope" in {e["id"] for e in r_oos})

    # 5) 很薄的 schema 确实不含口径（口径只能靠 wiki 补）
    check("薄 schema 不含‘明细金额’口径字样", "明细金额" not in LEAN_SCHEMA)
    check("薄 schema 不含 payment_status=2 口径", "已支付" not in LEAN_SCHEMA)
    # 有 wiki 的 prompt 明显比无 wiki 的长（多了证据）
    p_bare = build_prompt("各类目的销售额是多少？", [])
    p_wiki = build_prompt("各类目的销售额是多少？", r)
    check("有 wiki 的 Prompt 比无 wiki 长（多了证据）", len(p_wiki) > len(p_bare))
    check("有 wiki 的 Prompt 里带上了扇出警告", "扇出" in p_wiki and "actual_amount" in p_wiki)

    # 6) 经典 SQL 自洽 + 扇出坑真实存在
    truth = category_sales_truth()
    truth_total = round(sum(truth.values()), 2)
    direct = run_read_sql(
        "SELECT ROUND(SUM(i.item_amount),2) FROM ord_order_main o "
        "JOIN ord_order_item i ON o.order_id=i.order_id "
        "WHERE o.payment_status=2 AND o.is_deleted=0")["rows"][0][0]
    check("经典解法销售额与真值自洽", abs(truth_total - round(direct, 2)) < 0.01)
    fanout = run_read_sql(
        "SELECT ROUND(SUM(o.actual_amount),2) FROM ord_order_main o "
        "JOIN ord_order_item i ON o.order_id=i.order_id "
        "WHERE o.payment_status=2 AND o.is_deleted=0")["rows"][0][0]
    check("扇出坑成立：SUM 订单级金额 > 真实销售额（明细粒度虚高）",
          fanout > truth_total * 1.2)

    # 7) mock 生成器：有 wiki 照标准 SQL 出结果
    def mock_correct(prompt):
        return json.dumps({"sql":
            "SELECT c.category_name, ROUND(SUM(i.item_amount),2) AS sales "
            "FROM ord_order_main o JOIN ord_order_item i ON o.order_id=i.order_id "
            "JOIN prod_product p ON i.product_id=p.product_id "
            "JOIN prod_category c ON p.category_id=c.category_id "
            "WHERE o.payment_status=2 AND o.is_deleted=0 GROUP BY c.category_name"})
    out = answer("各类目的销售额是多少？", use_wiki=True, llm_fn=mock_correct)
    check("有 wiki 链路能生成→门禁→执行出结果",
          out["result"] is not None and out["error"] is None)
    if out["result"]:
        check("mock 结果≈真值（没扇出）", _sum_numeric(out["result"]) <= truth_total * 1.3)

    # 8) LLM 真实链路对照
    if os.environ.get("DEEPSEEK_API_KEY"):
        key = os.environ["DEEPSEEK_API_KEY"]
        try:
            wiki = answer("各类目的销售额是多少？", use_wiki=True, api_key=key)
            check("真实链路：有 wiki 能生成并执行出结果",
                  wiki["result"] is not None and wiki["error"] is None)
            if wiki["result"]:
                got = _sum_numeric(wiki["result"])
                check("真实链路：有 wiki 结果≈真值（口径命中、躲开扇出）",
                      got <= truth_total * 1.3)
        except Exception as e:  # noqa
            check(f"LLM 链路无异常（{type(e).__name__}: {e}）", False)
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
