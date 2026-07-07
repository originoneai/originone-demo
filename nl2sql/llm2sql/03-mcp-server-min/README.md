# 03 · 最小只读 MCP Server（配套 C1-LLM-02A / 02B）

对应课程文章：《教大模型查数据库，我为什么让学员先别急着写 Prompt》《MCP 到底是什么》。

在教模型写 SQL 之前，先给它一层**你说了算的、只读的、跟着你自己库走的"手"**。这台最小
MCP Server 只暴露四个只读工具，正好对应"人查一个陌生库"的四步：

| 工具 | 回答的问题 | 对应人查库的动作 |
|---|---|---|
| `list_tables` | 这库里有哪些表 | 先扫一眼有什么 |
| `describe_table` | 这张表有哪些字段、什么口径 | 看表结构 |
| `sample_values` | 这个字段有哪些实际取值 | 捞几个值确认口径 |
| `execute_query` | 查出来到底是什么 | 写 SQL 执行（过只读门禁） |

## 文件

| 文件 | 作用 |
|---|---|
| `cli.py` | **交互终端（主入口）**：你亲手把四个工具挨个敲一遍 |
| `mcp_server.py` | 四个只读工具 + 表白名单；装了 `mcp` 包即可 `python mcp_server.py` 跑成真正的 stdio MCP Server |
| `db.py` | 连接层：SQLAlchemy 抹平库差异，换库只换 `DB_URL` |
| `data_dictionary.py` | side-car 字段口径注释（SQLite 没有原生列注释，也是 LLM-Wiki 的雏形） |
| `guard.py` | 只读门禁：`execute_query` 的命门 |
| `build_dataset.py` | 生成 SQLite 样例库 |
| `test_lab.py` | 本地测试：四工具 / 白名单 / 门禁 / 注释合并 / 真实 MCP 注册 |

## 快速开始：手动把四步敲一遍

```bash
pip install -r requirements.txt
python cli.py
```

先不接大模型，你自己扮演查库的人，走一遍查库四步：

```
tables
desc ord_order_main
sample ord_order_main payment_status
sql SELECT COUNT(*) FROM ord_order_main WHERE payment_status = 2 AND is_deleted = 0
```

体会一下：这四步合起来，把"一次性把整库 DDL 塞进 Prompt"换成了"用到哪、取到哪"。
下一课 `04-mcp-harness-loop` 就让**模型自己**来敲这四个工具。

## 跑成真正的 MCP Server（stdio）

```bash
python mcp_server.py     # 以 stdio 启动，等客户端把它当子进程拉起来
```

接进 Claude Desktop / Cursor 的配置示例：

```json
{
  "mcpServers": {
    "mini-db": {
      "command": "python",
      "args": ["/abs/path/03-mcp-server-min/mcp_server.py"],
      "env": { "DB_URL": "sqlite:////abs/path/03-mcp-server-min/ecommerce.db" }
    }
  }
}
```

## 换成你自己的库

只改 `DB_URL` 一个环境变量，四个工具的代码一行不动：

```bash
export DB_URL="mysql+pymysql://readonly:***@127.0.0.1:9030/ecommerce"   # Doris/MySQL 走 9030
export DB_URL="postgresql+psycopg://readonly:***@127.0.0.1:5432/shop"    # PostgreSQL
python cli.py
```

> 生产上务必用**只读账号**连库，并把 `TABLE_WHITELIST` 收到最小——门禁再严，连接账号权限过大也白搭。
