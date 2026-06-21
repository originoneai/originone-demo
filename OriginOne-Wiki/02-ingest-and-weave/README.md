# 02 入库与编织

这一阶段开始演示 LLM-Wiki 最核心的动作：把 raw 编织成 wiki。

## 这里的“编织”是什么意思

编织不是复制粘贴。它分两步：

1. 一份 raw 先变成一份 source summary。
2. 多份 source summary 再合并到长期 wiki，比如 concept、entity、synthesis。

这就是最小版的：

```text
raw -> source_summary -> long-term wiki
```

## 运行

```bash
git clone https://github.com/originoneai/originone-demo.git
cd originone-demo/OriginOne-Wiki
bash scripts/llm_wiki_agent.sh weave 02-ingest-and-weave
bash scripts/llm_wiki_agent.sh ask 02-ingest-and-weave "LLM-Wiki 怎么把 raw 编织成 wiki"
```

## 看什么

- `wiki/source-summary-*`：一源一页。
- `wiki/concept-*`：长期知识页。
- `wiki/index.md`：以后检索先读这里。

这个阶段最适合观察编织过程：LLM Agent 会读取 raw，并把生成或更新的 wiki 页面写回目录。
