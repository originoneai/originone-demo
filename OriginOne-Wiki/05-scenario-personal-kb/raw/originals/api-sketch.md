# 接口草稿：项目材料与需求生成

## POST /projects/{project_id}/sources

导入一份原始材料。

请求字段：

- `source_type`: meeting_note / api_doc / rule_doc / decision
- `title`
- `body`
- `trust_level`
- `process_mode`: now / later

## POST /projects/{project_id}/requirements:generate

根据当前 wiki 和 source cards 生成需求草案。

输出字段：

- `requirement_title`
- `user_story`
- `acceptance_checks`
- `source_refs`
- `open_questions`

## PATCH /projects/{project_id}/rules

维护项目规则和语义层说明。

约束：

- 不能直接覆盖旧规则。
- 必须记录变更原因。
- 如果规则来自 output，必须先经过人工确认。
