import re
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI
from config import (
    OPENAI_MODEL, OPENAI_API_KEY, OPENAI_API_BASE, SQL_MAX_LIMIT,
    PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD
)
from .sql_prompt import SQL_SYS
from rag.search import normalize_values
# Init LLM client
llm_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)

def sanitize_sql(raw_sql: str) -> str:
    """Lọc output từ LLM, chỉ giữ lại câu SELECT cuối cùng hợp lệ"""
    sql = raw_sql.strip()

    # Nếu có cụm "Use limit 100." thì bỏ toàn bộ phần trước đó
    m = re.search(r'Use limit 100\.\s*(SELECT.+)', sql, flags=re.I|re.S)
    if m:
        sql = m.group(1).strip()

# Nếu có cụm "Add limit 100." thì bỏ toàn bộ phần trước đó
    m = re.search(r'Add limit 100\.\s*(SELECT.+)', sql, flags=re.I|re.S)
    if m:
        sql = m.group(1).strip() 

    m = re.search(r'Use alias\.\s*(SELECT.+)', sql, flags=re.I|re.S)
    if m:
        sql = m.group(1).strip() 

    m = re.search(r'Use row_number\.\s*(SELECT.+)', sql, flags=re.I|re.S)
    if m:
        sql = m.group(1).strip() 
    # Lấy tất cả SELECT ... ;
    matches = re.findall(r'(?is)(select\s+.+?;)', sql)
    if not matches:
        # fallback: tìm từ SELECT đầu tiên
        idx = sql.lower().find("select")
        if idx != -1:
            candidate = sql[idx:].strip()
            if not candidate.endswith(";"):
                candidate += ";"
            matches = [candidate]
        else:
            raise ValueError(f"❌ Không tìm thấy SQL hợp lệ:\n{raw_sql}")

    # ✅ chỉ lấy câu SELECT cuối cùng
    sql = matches[-1].strip()

    # Fix double SELECT (vd: SELECT SELECT *)
    sql = re.sub(r'(?is)\bselect\s+(?:select\s+)+', 'SELECT ', sql)

    # Đảm bảo LIMIT tồn tại
    if not re.search(r'(?is)\blimit\b\s+\d+', sql):
        sql = sql.rstrip(";") + f"\nLIMIT {SQL_MAX_LIMIT};"

    return sql


def build_sql(user_query: str, schema_rows):
    """Sinh câu SQL từ user query + schema context (schema_rows lấy từ RAG)"""
    if not schema_rows:
        schema_text = "⚠️ Không có schema context"
    else:
        schema_text = "\n".join(
            f'TABLE "{row["table"]}" COLUMN "{row["column"]}" ({row.get("dtype","")})'
            for row in schema_rows
        )

    msgs = [
        {"role": "system", "content": SQL_SYS},
        {
            "role": "user",
            "content": f"User query: {user_query}\nSchema:\n{schema_text}\n\nSQL:"
        },
    ]

    resp = llm_client.chat.completions.create(
        model=OPENAI_MODEL, messages=msgs, temperature=0
    )
    raw_sql = resp.choices[0].message.content.strip()
    return sanitize_sql(raw_sql)

def run_select(sql: str):
    """Thực thi SQL trên Postgres chính"""
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT,
        dbname=PG_DB, user=PG_USER, password=PG_PASSWORD,
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = cur.fetchall()
            cols = [desc.name for desc in cur.description]
            return cols, rows
    finally:
        conn.close()
