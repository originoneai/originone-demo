# 回答：raw wiki output 区别是什么

## 问题

raw wiki output 区别是什么

## 检索路径

### Wiki hits

1. `wiki/index.md`
   - 作为本阶段长期知识入口，指向 `concept-llm-wiki.md` 和来源摘要。
2. `wiki/concept-llm-wiki.md`
   - 说明 wiki 不是 raw 原文，也不是某一次回答，而是从原始材料整理出来的长期知识页。
3. `wiki/source-summary-001-llm-wiki-basics-md.md`
   - 摘要说明：LLM-Wiki 先把材料留在 raw，再把稳定理解编织进 wiki，最后把某一次任务结果保存在 output。
4. `wiki/README.md`
   - 说明 `source-summary-*`、`concept-*`、`index.md` 在 wiki 中的作用。

### Raw evidence

1. `raw/001-llm-wiki-basics.md`
   - 用来确认 raw、wiki、output 三个目录的原始定义。

## 简短回答

raw、wiki、output 是 LLM-Wiki 里的三层不同材料：

| 层级 | 存什么 | 作用 | 不能混淆的点 |
| --- | --- | --- | --- |
| `raw/` | 原始材料，比如聊天、链接、PDF 摘录、会议纪要 | 保留证据，不急着改写 | raw 是证据底座，不应该被随手重写或删除 |
| `wiki/` | 从 raw 里整理出来的长期知识，比如概念、事实、关系、判断 | 以后提问时优先检索和复用 | wiki 不是复制 raw，也不是把一次回答直接当真理 |
| `output/` | 某一次任务的结果，比如回答、清单、草稿、诊断 | 交付当前问题的结果 | output 可以被检查和复用，但不能自动等于长期知识 |

简单说：`raw` 是原始证据，`wiki` 是沉淀后的长期知识，`output` 是这一次任务的交付结果。

这个顺序也很重要：先保留 raw，再把稳定理解写进 wiki，最后根据具体问题生成 output。以后如果发现某个 output 里有长期有用的内容，需要经过人工检查后再回织进 wiki。

## 来源引用

- `00-minimal-raw-wiki-output/wiki/index.md`
- `00-minimal-raw-wiki-output/wiki/concept-llm-wiki.md`
- `00-minimal-raw-wiki-output/wiki/source-summary-001-llm-wiki-basics-md.md`
- `00-minimal-raw-wiki-output/wiki/README.md`
- `00-minimal-raw-wiki-output/raw/001-llm-wiki-basics.md`

## 人要检查什么

- 这个三栏解释是否符合你想教学的口径。
- `output` 的边界是否讲清楚：它可以沉淀进 wiki，但不能自动变成长期知识。
- 如果后续面向第一次接触的人，可以检查是否需要补一个更生活化的例子。

## 是否建议回织进 wiki

暂时不必须回织。当前 wiki 已经有 raw、wiki、output 的基本定义。

如果这个问题会反复出现，建议后续把上面的三栏对照表精简后补进 `wiki/concept-llm-wiki.md`，作为长期知识里的“目录分工”小节。
