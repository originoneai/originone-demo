#!/usr/bin/env python3
"""Tiny terminal demo for a beginner-friendly LLM-Wiki.

The script intentionally avoids external LLM calls. It simulates the core
operations with deterministic rules so readers can run the demo anywhere:

- map: explain raw/wiki/output.
- weave <stage>: compile raw notes into source summaries and concept pages.
- ask <stage> <question>: search wiki first, then raw, and save an answer.
- demo-all: run a compact end-to-end flow for all stages.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import textwrap
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGE_RE = re.compile(r"^\d{2}-")


STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from", "into", "what",
    "怎么", "什么", "一个", "为什么", "以及", "如何", "区别", "作用", "可以",
    "我们", "这个", "就是", "不是", "因为", "所以", "进行", "里的", "中的",
}


CONCEPT_RULES = [
    ("llm-wiki", ["llm-wiki", "LLM-Wiki", "raw", "wiki", "output", "编织"]),
    ("retrieve-first", ["取", "倒推", "检索", "问题", "输出形式"]),
    ("source-summary", ["source summary", "摘要", "来源摘要", "source_snapshot"]),
    ("data-quality", ["数据质量", "指标", "SQL", "口径", "宽表", "延迟", "健康度"]),
    ("data-warehouse-lineage", ["DDL", "血缘", "dwd", "ads", "ods", "dim", "lineage", "宽表"]),
    ("schema-change-impact", ["drop column", "modify column", "add column", "表结构", "影响分析", "schema change", "changed_field"]),
    ("data-requirement-dev", ["数据需求", "任务诊断", "需求开发", "验收清单", "需求生成", "自动生成需求"]),
    ("semantic-layer-rules", ["语义层", "规则", "指标口径", "semantic", "rules"]),
    ("project-wiki", ["全栈", "项目", "project", "前端", "后端", "接口", "需求生成"]),
    ("source-card", ["source card", "来源卡片", "unprocessed", "metadata", "可信度"]),
    ("personal-learning", ["个人", "学习", "读书", "复盘", "笔记"]),
]


SAMPLE_QUESTIONS = {
    "00-minimal-raw-wiki-output": "raw wiki output 区别是什么",
    "01-retrieve-first": "为什么要由取倒推存",
    "02-ingest-and-weave": "LLM-Wiki 怎么把 raw 编织成 wiki",
    "03-output-and-reuse": "output 保存什么 为什么不能直接当 wiki",
    "04-scenario-data-dev": "订单表 drop column 会影响哪些下游表和指标",
    "05-scenario-personal-kb": "全栈项目知识库怎么自动生成需求并维护规则",
}


def iter_stages() -> list[Path]:
    return sorted([p for p in ROOT.iterdir() if p.is_dir() and STAGE_RE.match(p.name)])


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    return text.strip("-")[:60] or "note"


def tokens(text: str) -> list[str]:
    parts: list[str] = []
    for match in re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]+", text.lower()):
        if re.fullmatch(r"[\u4e00-\u9fff]+", match):
            parts.append(match)
            parts.extend(match[i:i + 2] for i in range(max(0, len(match) - 1)))
        else:
            parts.append(match)
    return [p for p in parts if p not in STOPWORDS]


def title_from(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:40]
    return fallback


def digest_from(text: str) -> str:
    markers = ["核心观点", "摘要", "结论", "问题", "做法"]
    for marker in markers:
        idx = text.find(marker)
        if idx >= 0:
            snippet = re.sub(r"\s+", " ", text[idx:idx + 180]).strip()
            return snippet[:120]
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned[:120]


def concept_keys(text: str) -> list[str]:
    hits = []
    for key, words in CONCEPT_RULES:
        if any(w.lower() in text.lower() for w in words):
            hits.append(key)
    return hits or ["llm-wiki"]


def map_command() -> None:
    print("LLM-Wiki 最小地图")
    print("=" * 40)
    print("raw/    : 原始材料。先保留事实，不急着改写。")
    print("wiki/   : 长期知识。把多份 raw 编织成能复用的页面。")
    print("output/ : 本次任务产物。回答、清单、报告草稿、复盘结果。")
    print()
    print("检索顺序：先读 wiki，wiki 不够再回 raw 查证据。")
    print("设计顺序：先问以后要取什么，再决定 raw/wiki/output 怎么放。")


def stage_path(name: str) -> Path:
    path = ROOT / name
    if not path.exists():
        raise SystemExit(f"找不到阶段目录: {name}")
    return path


def raw_files(stage: Path) -> list[Path]:
    return sorted([p for p in (stage / "raw").rglob("*") if p.is_file()])


def wiki_files(stage: Path) -> list[Path]:
    return sorted([p for p in (stage / "wiki").glob("*.md") if p.is_file()])


def weave(stage_name: str) -> None:
    stage = stage_path(stage_name)
    raws = raw_files(stage)
    if not raws:
        raise SystemExit(f"{stage_name}/raw 没有材料")

    source_refs_by_concept: dict[str, list[str]] = {}
    print(f"开始编织: {stage_name}")
    print(f"raw 文件数: {len(raws)}")

    for raw in raws:
        text = read_text(raw)
        title = title_from(text, raw.stem)
        digest = digest_from(text)
        keys = concept_keys(text)
        source_ref = raw.relative_to(stage / "raw").as_posix()
        summary_name = f"source-summary-{slugify(source_ref)}.md"
        summary_path = stage / "wiki" / summary_name
        summary = f"""---
wiki_kind: source_summary
source_ref: ../raw/{source_ref}
confidence: medium
---

# 来源摘要：{title}

## 一句话摘要

{digest}

## 这份 raw 适合回织到哪里

{chr(10).join(f"- {key}" for key in keys)}

## 人要检查什么

- 原文有没有被误读。
- 这个摘要是否足够支持后面的长期 wiki。
- 如果要公开使用，是否需要脱敏或审批。
"""
        write_text(summary_path, summary)
        print(f"+ wiki/{summary_name}")

        for key in keys:
            source_refs_by_concept.setdefault(key, []).append(source_ref)

    for key, source_ids in source_refs_by_concept.items():
        concept_path = stage / "wiki" / f"concept-{key}.md"
        title = {
            "llm-wiki": "LLM-Wiki 最小知识结构",
            "retrieve-first": "由取倒推存",
            "source-summary": "Source Summary 来源摘要",
            "data-quality": "数据开发里的指标口径与质量排查",
            "data-warehouse-lineage": "数仓字段血缘与表结构变更",
            "schema-change-impact": "业务库表结构变更影响分析",
            "data-requirement-dev": "数据需求开发与任务诊断",
            "semantic-layer-rules": "语义层规则与指标口径维护",
            "project-wiki": "个人项目知识库与全栈开发",
            "source-card": "Source Card 来源卡片",
            "personal-learning": "个人知识库里的学习复盘",
        }.get(key, key)
        body = f"""---
wiki_kind: concept
source_refs:
{chr(10).join(f"  - ../raw/{sid}" for sid in source_ids)}
---

# {title}

## 稳定理解

这一页不是 raw 原文，也不是某一次回答。它是从 {len(source_ids)} 份原始材料里整理出来的长期知识页。

## 为什么要放在 wiki

- 以后提问时可以先读这一页，而不是每次重新翻 raw。
- 多份材料可以在这里合并、去重、补充。
- 如果出现冲突，可以在这里标记“待确认”，而不是偷偷改成事实。

## 证据来源

{chr(10).join(f"- {sid}" for sid in source_ids)}
"""
        write_text(concept_path, body)
        print(f"+ wiki/{concept_path.name}")

    update_index(stage)
    print("编织完成。建议下一步运行 ask 命令看看检索效果。")


def update_index(stage: Path) -> None:
    pages = [p.name for p in wiki_files(stage) if p.name != "index.md"]
    content = ["# Wiki Index", "", "这里是本阶段的长期知识入口。检索时先看这里，再进入具体页面。", ""]
    for page in pages:
        title = title_from(read_text(stage / "wiki" / page), page)
        content.append(f"- [{title}]({page})")
    write_text(stage / "wiki" / "index.md", "\n".join(content))


def score_doc(query: str, text: str) -> int:
    q = Counter(tokens(query))
    d = Counter(tokens(text))
    return sum(min(q[t], d[t]) for t in q)


def ask(stage_name: str, question: str) -> None:
    stage = stage_path(stage_name)
    if not wiki_files(stage):
        print("wiki 还没有内容，先运行 weave。")
        weave(stage_name)

    candidates = []
    for p in wiki_files(stage):
        text = read_text(p)
        candidates.append(("wiki", p, score_doc(question, text), text))
    for p in raw_files(stage):
        text = read_text(p)
        candidates.append(("raw", p, max(0, score_doc(question, text) - 1), text))

    ranked = sorted(candidates, key=lambda x: x[2], reverse=True)
    wiki_hits = [
        r for r in ranked
        if r[0] == "wiki" and r[1].name != "index.md" and r[2] > 0
    ][:2]
    if len(wiki_hits) < 2:
        wiki_hits.extend([
            r for r in ranked
            if r[0] == "wiki" and r[1].name == "index.md" and r[2] > 0
        ][:2 - len(wiki_hits)])
    raw_hits = [r for r in ranked if r[0] == "raw" and r[2] > 0][:1]
    selected = wiki_hits + raw_hits
    if not selected:
        selected = ranked[:2]

    print(f"问题: {question}")
    print("检索顺序: wiki -> raw")
    print("命中的材料:")
    for kind, path, score, _ in selected:
        rel = path.relative_to(stage)
        print(f"- [{kind}] {rel} score={score}")

    answer_lines = [
        f"# 回答：{question}",
        "",
        "## 简短回答",
        "",
        build_answer(question, selected),
        "",
        "## 引用来源",
        "",
    ]
    for idx, (kind, path, score, text) in enumerate(selected, 1):
        rel = path.relative_to(stage)
        answer_lines.append(f"{idx}. `{kind}` `{rel}`，score={score}")
    answer_lines.extend([
        "",
        "## 人要检查",
        "",
        "- 这次回答是否真的被引用来源支持。",
        "- 如果 output 里出现了长期有用的判断，要回写到 wiki，而不是只留在 output。",
    ])
    output_name = f"ask-{slugify(question)}.md"
    output_path = stage / "output" / output_name
    write_text(output_path, "\n".join(answer_lines))
    print()
    print(textwrap.fill(build_answer(question, selected), width=72))
    print()
    print(f"已保存 output/{output_name}")


def build_answer(question: str, selected: list[tuple[str, Path, int, str]]) -> str:
    joined = "\n".join(text for _, _, _, text in selected)
    q = question.lower()
    if "raw" in q and "wiki" in q and "output" in q:
        return "raw 保存原始材料，wiki 保存从材料里编织出来的长期知识，output 保存某一次任务的结果。新手先把这三层分清，后面才不会把一次回答误当成长期知识。"
    if "取" in question or "倒推" in question:
        return "由取倒推存，就是先想以后要问什么、要拿到什么结果，再决定 raw 留哪些材料、wiki 编哪些页面、output 保存哪些产物。这样目录会服务真实检索，而不是变成好看的空文件夹。"
    if "编织" in question or "weave" in q:
        return "编织就是把 raw 先整理成一源一页的 source summary，再把多份 summary 合并到 concept、entity、synthesis 等长期 wiki 页里。raw 不改，wiki 才负责复用和合并。"
    if "output" in q:
        return "output 保存本次任务结果，比如一段回答、一个检查清单、一份报告草稿。它的作用是交付当下任务；只有反复会用、经检查可靠的部分，才应该回写到 wiki。"
    if "drop" in q or "column" in q or "表结构" in question or "影响" in question:
        return "表结构变更要先查 wiki 里的字段血缘、指标口径和同步任务规则，再回到 raw 的 DDL、宽表 SQL、变更单核对证据。output 里应该保存影响表清单、风险等级和改动方案，而不是只给一句“可能有影响”。"
    if "健康" in question or "映射" in question:
        return "字段映射健康度报告要回答三件事：字段类型是否匹配、下游宽表是否还引用旧字段、指标口径是否需要同步更新。报告属于 output，稳定规则再回写到 wiki。"
    if "需求" in question or "任务" in question or "全栈" in question or "规则" in question or "语义层" in question:
        return "项目知识库可以把业务目标、接口草稿、规则说明和历史决策先放 raw，再编成 project、workflow、semantic rules 等 wiki 页面。output 保存本次生成的需求、任务拆分和验收清单，稳定规则再回写 wiki。"
    if "数据" in question or "指标" in question or "sql" in q:
        return "数据开发场景里，raw 可以放需求、SQL、报错和口径讨论；wiki 编成指标定义、排查步骤和质量规则；output 保存本次排查结论或上线检查清单。"
    if "个人" in question or "读书" in question or "复盘" in question:
        return "个人知识库场景里，raw 放读书摘录和日常笔记；wiki 编成稳定主题、方法和行动原则；output 保存本周计划、复盘问题和下一步行动。"

    digest = digest_from(joined)
    return f"根据当前 wiki 和 raw，最相关的结论是：{digest}"


def demo_all() -> None:
    map_command()
    print("\n" + "=" * 60 + "\n")
    for stage in iter_stages():
        question = SAMPLE_QUESTIONS.get(stage.name, "这个阶段讲什么")
        print(f"## {stage.name}")
        weave(stage.name)
        ask(stage.name, question)
        print("\n" + "=" * 60 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="OriginOne Wiki beginner terminal demo")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("map")
    weave_parser = sub.add_parser("weave")
    weave_parser.add_argument("stage")
    ask_parser = sub.add_parser("ask")
    ask_parser.add_argument("stage")
    ask_parser.add_argument("question")
    sub.add_parser("demo-all")
    args = parser.parse_args()

    if args.command == "map":
        map_command()
    elif args.command == "weave":
        weave(args.stage)
    elif args.command == "ask":
        ask(args.stage, args.question)
    elif args.command == "demo-all":
        demo_all()


if __name__ == "__main__":
    main()
