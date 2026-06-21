# Implementation Plan

## MVP

- 创建 `OriginOne-Wiki` 根目录。
- 每个阶段创建 `raw/wiki/output/README.md`。
- 写入可公开演示的 raw 材料。
- 在 04/05 增加 nested raw：`raw/originals` 和 `raw/cards`。
- 在 04 增加数据开发 output：字段映射健康报告、schema change 影响分析、事故诊断。
- 在 05 增加项目知识库 output：需求草案、规则维护清单、任务诊断。
- 提供 `llm_wiki_demo.py`，支持 `map`、`weave`、`ask`、`demo-all`。
- 提供 `smoke_test.sh`，让读者 clone 后一键验证。
- 提供 `validate_design_package.py`，让设计包校验不依赖本机私有路径。
- 运行每个阶段并保存可检查 output。

## vNext

- 把规则编织替换为真实 LLM。
- 增加 `wiki/log.md`。
- 增加 health check：缺 source_ref、output 未回写、wiki 无证据。
- 增加更多场景：销售拜访、会议纪要、课程学习。
- 给 04 增加真实字段血缘 parser，给 05 增加 source card 审批状态流转。

## Deferred

- Obsidian vault。
- Web App。
- 多用户权限。
- 数据库和向量库。
- 自动同步和远端发布。

## validation_commands

```bash
git clone https://github.com/originoneai/originone-demo.git
cd originone-demo/OriginOne-Wiki
python3 -m py_compile scripts/llm_wiki_demo.py scripts/validate_design_package.py
python3 scripts/llm_wiki_demo.py map
python3 scripts/llm_wiki_demo.py demo-all
bash scripts/smoke_test.sh
python3 scripts/validate_design_package.py design-package
```

## acceptance_checklist

- [ ] 每个阶段都有 raw/wiki/output。
- [ ] 04/05 的 nested raw 能被 `weave` 递归读取。
- [ ] 04 能展示 health-check 和 impact-analysis。
- [ ] 05 能展示 requirements、rules、diagnosis。
- [ ] `weave` 能生成 source summary 和 concept。
- [ ] `ask` 能保存 output。
- [ ] `smoke_test.sh` 能从 clean clone 后运行。
- [ ] README 的一键命令能复制粘贴执行。
- [ ] 设计包通过 validator。
