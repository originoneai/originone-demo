# Health Check Rules

## triggers

- 每次新增 raw 后。
- 每次运行 weave 后。
- 每次 output 准备放入文章前。
- 每次截图生成后。

## P0

- raw 目录为空。
- stage 缺少 raw/wiki/output 任一目录。
- ask 没有保存 output。
- 文章引用的截图文件不存在。

## P1

- wiki 没有 index.md。
- source summary 没有 source_ref。
- output 里没有引用来源。
- data-dev 或 personal 场景没有独立 README。
- 04/05 的 `raw/originals` 有材料但 `weave` 没有生成对应 source summary。
- source card 缺少 `status`、`trust` 或 `source_ref`。

## P2

- README 只讲概念，没有运行命令。
- 文章术语太密，没有解释 raw/wiki/output。
- output 回写 wiki 的边界没有讲清楚。
- 04 没有解释 DDL/SQL/schema change 怎么进入影响分析。
- 05 没有解释 originals/cards/wiki/output 的职责差异。

## auto_detectable

- 目录是否存在。
- 文件是否存在。
- 脚本是否能运行。
- 截图 PNG 是否生成。
- design-package 是否通过 validator。

## agent_review_required

- 文章是否适合新手。
- 场景是否贴近日常工作。
- 是否把 output 和 wiki 混在一起。
- 是否解释了由取倒推存。

## owner_approval_required

- 是否要接真实 LLM API。
- 是否要把文章发布到公众号。
- 是否加入更多场景。

## fix_queue

- 缺目录：补目录和 README。
- 缺截图：重新运行 transcript 和截图脚本。
- 检索效果不清楚：补 raw 材料或 wiki 说明。
- 04 场景过轻：补 DDL、宽表 SQL、schema change、health-check、impact-analysis。
- 05 场景过轻：补 project brief、source card、rules、semantic layer、requirements output。
- 新手读不懂：降低术语密度，补操作步骤。
