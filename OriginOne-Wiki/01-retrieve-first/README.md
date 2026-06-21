# 01 由取倒推存

这一阶段讲一个关键动作：不要先问“我要建哪些目录”，先问“以后我要从这里取出什么”。

## 这次要取什么

我们假设以后要取这三类结果：

1. 我想快速回答：LLM-Wiki 怎么开始搭？
2. 我想知道：哪些材料还没有被整理进 wiki？
3. 我想拿到：一份可以直接照着做的入门步骤。

这些取法决定了目录：

- raw 要保留原始需求和材料。
- wiki 要沉淀稳定方法。
- output 要保存步骤清单和问答结果。

## 运行

```bash
git clone https://github.com/originoneai/originone-demo.git
cd originone-demo/OriginOne-Wiki
python3 scripts/llm_wiki_demo.py weave 01-retrieve-first
python3 scripts/llm_wiki_demo.py ask 01-retrieve-first "为什么要由取倒推存"
```

## 看什么

看 `wiki/index.md`，它就是最小版的检索入口。新手先不需要向量库，也不用复杂搜索，先学会让 wiki 有一个清楚入口。
