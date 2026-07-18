#!/usr/bin/env python3
"""失败分类器：别只说"答错了"，把错归到标准类型。配套文章 C1-08 第二节。

给一条 SQL 和它的结果，对着真值和证据契约，判 pass/fail 并归类：
  execution_error       跑挂了
  metric_definition_error 漏了关键口径（如 payment_status）
  grain_fanout_error    粒度扇出：join 明细后金额/计数被放大，数值远超真值
  join_or_grain_error   数值对不上真值但形态不明（兜底）
分类质量决定系统能不能持续改进：能归类，才能把错误变成可指派的改进任务。
"""


def _rows_to_map(result):
    """把结果行按第一列（维度）聚成 {key: [数值列...]}。"""
    out = {}
    for row in result["rows"]:
        key = row[0]
        nums = [v for v in row[1:] if isinstance(v, (int, float))]
        out[key] = nums
    return out


def classify(spec, sql, result, truth) -> dict:
    """返回 {status, failure_types, detail}。"""
    fails = []
    low = sql.lower()

    if result is None:
        return {"status": "fail", "failure_types": ["execution_error"], "detail": "SQL 执行报错"}

    # 证据：漏关键口径
    for token in spec.get("required_sql", []):
        if token.lower() not in low:
            fails.append("metric_definition_error")
            break

    # 证据：踩了禁止的写法（如客单价 join 明细）
    hit_forbidden = any(tok.lower() in low for tok in spec.get("forbidden_sql", []))

    # 构件级：join 明细数订单却没 COUNT(DISTINCT) → 粒度扇出（量级温和时靠这条兜底）
    if spec.get("distinct_order_required"):
        if "count(" in low and "count(distinct" not in low.replace(" ", ""):
            fails.append("grain_fanout_error")

    # 数值：拿真值逐维逐指标比对，抓扇出放大
    got = _rows_to_map(result)
    inflated = False
    detail_bits = []
    for key, tvals in truth.items():
        metrics = list(tvals.values())
        gnums = got.get(key)
        if not gnums:
            continue
        # 逐指标找与真值最接近的匹配，任一指标被放大 >1.3x 记为扇出
        for tv in metrics:
            if tv in (None, 0):
                continue
            # 结果里存在某个数值明显大于该真值指标（同量级放大）
            for gv in gnums:
                if gv > tv * 1.3 and gv <= tv * 6:  # 放大但不是完全不同的量纲
                    inflated = True
                    detail_bits.append(f"{key}: got~{round(gv,2)} vs truth {round(tv,2)}")
                    break

    if inflated:
        fails.append("grain_fanout_error")
    elif hit_forbidden and "grain_fanout_error" not in fails:
        # join 了明细但数值这次没明显放大，仍标注粒度风险
        fails.append("grain_fanout_error")

    # 数值对不上真值、又没归到上面任何一类 → 兜底
    if not fails:
        mismatch = _value_mismatch(spec, got, truth)
        if mismatch:
            fails.append("join_or_grain_error")
            detail_bits.append(mismatch)

    fails = list(dict.fromkeys(fails))  # 去重保序
    return {"status": "pass" if not fails else "fail",
            "failure_types": fails,
            "detail": "；".join(detail_bits) if detail_bits else "对齐真值"}


def _value_mismatch(spec, got, truth):
    """第一指标是否与真值对得上（容差 1%）。对不上返回描述，否则 None。"""
    for key, tvals in truth.items():
        tv = list(tvals.values())[0]
        gnums = got.get(key)
        if not gnums:
            return f"{key} 缺失"
        if tv and not any(abs(g - tv) <= max(0.01, abs(tv) * 0.01) for g in gnums):
            return f"{key} 首指标对不上真值({round(tv,2)})"
    return None
