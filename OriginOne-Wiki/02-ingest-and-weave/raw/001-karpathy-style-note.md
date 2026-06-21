# Karpathy 风格 LLM-Wiki 笔记

核心观点：LLM-Wiki 不只是每次问答时临时检索 raw。它会把原始材料持续编译成 wiki，让长期知识越来越稳定。

raw 是事实来源，不应该被覆盖。

wiki 是编译后的知识，应该有 source_refs，能回到原始材料。

output 是一次任务产物，可以是回答或草稿。output 里有长期价值的部分，可以再回写成 synthesis。

编织流程：读 raw，提炼 source summary，抽取概念和实体，合并到长期 wiki，更新 index 和 log。
