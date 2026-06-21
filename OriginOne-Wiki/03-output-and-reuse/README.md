# 03 output 保存什么

这一阶段讲 output。

## output 的作用

output 保存的是“这一次任务的产物”，不是长期知识本身。

例子：

- 一次问答结果。
- 一份检查清单。
- 一篇文章草稿。
- 一次项目复盘。
- 一段要发给同事的说明。

## 为什么不能把 output 直接当 wiki

因为 output 往往带着当时的任务目的。它可能语气很好，也可能很有用，但未必适合长期复用。

正确做法是：

```text
output 先保存
  -> 人检查
  -> 有长期价值的部分回写 wiki
```

## 运行

```bash
cd /Users/mac/Documents/OriginOne-Demo/OriginOne-Wiki
python3 scripts/llm_wiki_demo.py weave 03-output-and-reuse
python3 scripts/llm_wiki_demo.py ask 03-output-and-reuse "output 保存什么 为什么不能直接当 wiki"
```
