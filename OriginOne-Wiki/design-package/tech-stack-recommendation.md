# Tech Stack Recommendation

## requirements_summary

- user_count：单人作者 + 新手读者本地运行。
- collaboration_intensity：低。
- privacy_boundary：public-safe demo。
- automation_frequency：手动运行。
- source_volume：小。
- retrieval_complexity：简单关键词检索，重点是展示流程。
- sharing_requirement：可运行目录包。
- audit_requirement：轻量，可用 output 和 smoke test 说明。
- maintenance_capacity：低。

## recommendation

使用 Markdown + Python 脚本。

原因：

- 新手不用先安装复杂工具。
- 文件结构透明，能直接看到 raw/wiki/output。
- Python 脚本能真实生成 wiki 和 output。
- 运行结果能直接在终端查看。

## rejected_options

- Obsidian：会让新手先卡在工具配置，不适合作为第一篇 0-1 案例。
- 向量库：会把注意力从“目录合同和知识生命周期”转移到检索技术。
- Web App：展示效果更好，但会增加前端、服务和端口复杂度。
- 真实 LLM API：更接近生产，但新手复现成本高，也可能受网络和 key 影响。

## migration_path

1. 当前终端 demo。
2. 接入真实 LLM 做摘要和 wiki 编织。
3. 增加 health check 和 log。
4. 转成 Web UI 或 SaaS。
5. 再考虑向量检索、权限和多用户。

## operational_cost

本地运行几乎无成本。唯一要求是 Python3。
