# 00 最小三目录：raw / wiki / output

这一阶段只做一件事：让新手先把三个目录分清楚。

## 先从“取”开始

假设你以后想问：

> LLM-Wiki 里 raw、wiki、output 到底有什么区别？

为了回答这个问题，最小目录只需要三层：

```text
raw/     保存原始材料
wiki/    保存长期知识
output/  保存本次回答
```

## 运行

```bash
cd /Users/mac/Documents/OriginOne-Demo/OriginOne-Wiki
python3 scripts/llm_wiki_demo.py map
python3 scripts/llm_wiki_demo.py ask 00-minimal-raw-wiki-output "raw wiki output 区别是什么"
```

## 看什么

- `raw/001-llm-wiki-basics.md` 是原始材料。
- `wiki/` 里会生成 source summary 和 concept 页面。
- `output/` 里会保存这次问答结果。

新手先记住：output 不等于 wiki。一次回答只是一次任务结果，只有反复会用、经过检查的内容才适合回写到 wiki。
