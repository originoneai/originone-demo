# 05 场景二：个人/项目知识库 LLM-Wiki

这一阶段演示的不是“收藏读书笔记”，而是一个更接近真实诉求的项目知识库：开发者希望把一个全栈项目的业务目标、接口草稿、规则、语义层说明都沉淀下来，以后能自动生成需求、拆任务、维护规则。

它仍然只用终端和 Markdown，但目录开始从三层结构演进：

```text
raw/
  originals/    # 原件区，不改写，方便溯源
  cards/        # source card，一份原件一张入口卡
wiki/           # 项目、概念、规则、语义层的长期页面
output/
  requirements/ # 本次生成的需求
  rules/        # 规则维护清单
  diagnosis/    # 任务问题诊断
```

## 目录怎么倒推

未来我们要取：

- “这个项目到底要做什么”，能从项目 brief 和会议记录里取。
- “某个功能要怎么拆”，能从接口草稿、历史决策、规则里取。
- “规则和语义层怎么维护”，能从稳定 wiki 里取，并输出本次维护清单。
- “有新需求时怎么自动生成”，能把 raw 里的业务目标转成 output 里的需求草案。

所以本阶段用 `raw/originals` 保留原文，用 `raw/cards` 记录 metadata、摘要、可信度、处理状态。暂时不处理的材料可以标记为 `unprocessed`，以后再编织进 wiki。

## 运行

```bash
git clone https://github.com/originoneai/originone-demo.git
cd originone-demo/OriginOne-Wiki
bash scripts/llm_wiki_agent.sh weave 05-scenario-personal-kb
bash scripts/llm_wiki_agent.sh ask 05-scenario-personal-kb "全栈项目知识库怎么自动生成需求并维护规则"
```

## 读结果

- `wiki/concept-project-wiki.md` 会沉淀项目知识库的长期结构。
- `wiki/concept-semantic-layer-rules.md` 会沉淀规则和语义层维护方法。
- `output/requirements/generated-requirements.md` 是一次需求生成结果。
- `output/rules/rules-maintenance-checklist.md` 是规则维护清单。

跑到这里，先记住这个边界：原件不能为了“变整齐”而改掉，source card 是入口，wiki 是稳定知识，output 是这次生成的需求或诊断。
