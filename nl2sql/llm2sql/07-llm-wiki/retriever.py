#!/usr/bin/env python3
"""最朴素的检索器：先别碰向量。配套文章 C1-06A 第四、七节。

逻辑一句话：把用户问题跟每条的别名、标题比一比，命中越多分越高，
按分排序取前几条。二十来行、零依赖、离线可跑。

为什么先做字面匹配而不是向量：
  1. 完全可解释。为什么召回销售额口径？因为问题里出现了“销售额”这个别名。
     命中在哪、为什么命中，一目了然，出问题能立刻定位。向量召回靠一串读不懂的
     相似度分数，哪天召错了想查为什么，得钻进 embedding 空间。
  2. 检索的成败八成不在字面还是向量，而在库房条目本身建得好不好、别名挂得全不全。
     向量是在有了好库房之后，去补“字面对不上但意思相近”的长尾，是锦上添花，不是地基。

检索完还出一份 retrieval_report：这道题必要的表召全了吗、必要的业务词命中了吗。
这是判断“能不能放心让模型往下写”的依据（第七节）。
"""
from wiki import WIKI_ENTRIES


def _bigrams(s: str):
    s = "".join(ch for ch in s if ch not in "（）“”/ 、，。：")
    return {s[i:i + 2] for i in range(len(s) - 1)}


def _score(question: str, entry: dict) -> int:
    """别名整词命中权重最高；标题按二元组重合算弱证据（避免单字如“的/各”乱命中）。"""
    score = 0
    for a in entry["aliases"]:
        if a and a in question:
            score += 2
    q2 = _bigrams(question)
    score += len(_bigrams(entry["title"]) & q2)  # 标题二元组命中，每个 +1
    return score


def retrieve(question: str, entries=WIKI_ENTRIES, top_k: int = 6):
    """返回按相关性排序的前 top_k 条命中条目。"""
    hits = [(_score(question, e), e) for e in entries]
    hits = [(s, e) for s, e in hits if s > 0]
    hits.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in hits[:top_k]]


# 一道题“必要证据”的期望清单，用来给检索打分（覆盖率报告）。
# 现实里这份期望来自 Golden Questions 的语义要求，这里给两道演示题手工标注。
EXPECTED = {
    "各类目销售额": {"terms": ["销售额", "类目"], "pitfalls": ["扇出"]},
    "各地区订单数": {"terms": ["地区", "订单数"], "pitfalls": []},
}


def retrieval_report(question: str, retrieved) -> dict:
    """检索覆盖率报告：命中/漏召的业务词、召回条目 id、是否覆盖必要证据。"""
    hit_aliases = set()
    for e in retrieved:
        for a in e["aliases"]:
            if a in question:
                hit_aliases.add(a)

    # 找到与问题最匹配的期望标注（按别名重合度）
    expected_terms = []
    for key, spec in EXPECTED.items():
        if any(t in question for t in spec["terms"]):
            expected_terms = spec["terms"]
            break

    covered = [t for t in expected_terms if any(t in a or a in t for a in hit_aliases)]
    missing = [t for t in expected_terms if t not in covered]
    return {
        "question": question,
        "retrieved_ids": [e["id"] for e in retrieved],
        "hit_aliases": sorted(hit_aliases),
        "expected_terms": expected_terms,
        "covered_terms": covered,
        "missing_terms": missing,
        "status": "pass" if expected_terms and not missing else
                  ("no_expectation" if not expected_terms else "gap"),
    }


if __name__ == "__main__":
    import json
    for q in ["各类目的销售额是多少？", "各地区订单数排名", "用户手机号是多少"]:
        r = retrieve(q)
        print(f"\n问题：{q}")
        for e in r:
            print(f"  [{e['type']:8}] {e['id']}")
        print("  报告：", json.dumps(retrieval_report(q, r), ensure_ascii=False))
