# 10 · C1 交付包（配套 C1-09，C1 收官）

把这一路（01~09）搭的所有零件，串成一条不可绕过的固定链路，配上一份可回归的
验收报告。这就是一个企业敢接、敢用、敢往生产上推的交付包该有的样子。

## 固定链路（交付骨架）

```
用户问题 → LLM-Wiki 检索(07) → LLM 生成 → 服务端 Guard(08,不可绕过)
        → 执行 → Verifier(08) → 验不过则病因喂回重试 → 每步落 trace
```

三个不能交给模型自由决定的点：Guard 固定在服务端、Trace 覆盖每次问数、复杂题有升级出口。

## 验收回归报告（交付里最值钱的资产）

`evaluate.py` 把一组分档 Golden Questions（D1 简单 / D2 轻量多表 / D3 复杂多表）
跑过完整链路，出报告：整体通过率 + 分档通过 + 每题成败/重试次数 + 失败归因。

**实测（真实 DeepSeek，完整链路）：6/6 通过。** 尤其是两道 D3 难题：
在上一课（09-multitable-failure）裸奔生成时两道全军覆没（0/2），
接上 LLM-Wiki 口径供给 + Verifier 加重试的纠错闭环后，都被救了回来
（客单价那道靠重试第 2 次通过）。这就是"把零件装配成系统"的价值。

> 报告好看不等于没有边界：真正撞穿这条链路的，是要在 6~10 个业务对象间做关系推理的题，
> 那种复杂度超出这个 4 表演示，也正是 C1 该向 C3/C4 交棒的地方。

## 文件与跑法

| 文件 | 作用 |
|---|---|
| `pipeline.py` | 完整链路 `answer()`：检索→生成→Guard→执行→Verifier→重试 |
| `golden.py` | 分档 Golden Questions + 契约 + 真值 |
| `evaluate.py` | 验收回归：跑 Golden 出交付报告 |
| `cli.py` | `\list` `\ask <题>` `\eval` |
| `test_lab.py` | 11 项确定性 + LLM 真实验收报告 |
| 复用 | `wiki.py`/`retriever.py`(07) · `guard.py`/`verifier.py`(08) · `build_dataset.py`/`db.py` |

```bash
pip install -r requirements.txt
python test_lab.py                     # 确定性，不联网
export DEEPSEEK_API_KEY=sk-你的key
python test_lab.py                     # 加跑真实验收报告
python cli.py                          # \eval 直接出交付验收报告
```

## C1 全套 lab 索引（交付清单）

| lab | 配套文章 | 交付了什么 |
|---|---|---|
| 01-prompt-only | C1-01A | Prompt 直出 SQL，先跑通再翻车 |
| 02-context-engineering | C1-01B | 上下文消融实验台 |
| 03-mcp-server-min | C1-02A/02B | 最小只读 MCP Server（4 工具 + 白名单） |
| 04-mcp-harness-loop | C1-03A/03B | 模型自驱的工具循环 Harness |
| 05-dify-vs-harness | C1-04A/04B | 编排 vs Harness |
| 06-wide-table | C1-05A/05B | 宽表/指标表/三查询面 |
| 07-llm-wiki | C1-06A/06B | LLM-Wiki 语义基座 |
| 08-guard-verifier | C1-07A/07B | Guard + Verifier + 自动重试 |
| 09-multitable-failure | C1-08 | 多表失败复盘 + 分类学 |
| **10-delivery** | **C1-09** | **全链路装配 + 验收回归（收官）** |
