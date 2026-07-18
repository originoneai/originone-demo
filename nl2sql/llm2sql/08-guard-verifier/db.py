#!/usr/bin/env python3
"""连接层：用 SQLAlchemy 抹平各家数据库差异。

换库只换连接串（环境变量 DB_URL），四个工具的代码一行不用动：
  SQLite   ：sqlite:////abs/path/ecommerce.db          （默认，零成本）
  Doris/MySQL/StarRocks（走 MySQL 协议）：mysql+pymysql://user:***@127.0.0.1:9030/ecommerce
  PostgreSQL：postgresql+psycopg://user:***@127.0.0.1:5432/shop
  ClickHouse：clickhouse+native://user:***@127.0.0.1:9000/shop
"""
import os

from sqlalchemy import create_engine, text

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = f"sqlite:///{os.path.join(HERE, 'ecommerce.db')}"

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        url = os.environ.get("DB_URL", DEFAULT_DB)
        _engine = create_engine(url, future=True)
    return _engine


def run_read_sql(sql: str, max_rows: int = 200) -> dict:
    """执行一条（已被门禁放行的）只读 SQL，返回列名 + 行。"""
    eng = get_engine()
    with eng.connect() as conn:
        result = conn.execute(text(sql))
        cols = list(result.keys())
        rows = [list(r) for r in result.fetchmany(max_rows)]
    return {"columns": cols, "rows": rows, "row_count": len(rows)}
