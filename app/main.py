import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from openai import OpenAI
from dotenv import load_dotenv
from config import PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD, OPENAI_MODEL, OPENAI_API_KEY, OPENAI_API_BASE, SQL_MAX_LIMIT
from rag.search import vector_search_schema

# Load biến môi trường
load_dotenv()


# ───────── Init LLM client ─────────
llm_client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)


# ───────── Sinh SQL ─────────
SQL_SYS = f"""You are a Text2SQL assistant targeting PostgreSQL.
- Always prefix column names with their table name or alias to avoid ambiguity.
- Example: SELECT "Genre"."Name" not SELECT "Name".
- Use only the provided schema.
- PostgreSQL does NOT support QUALIFY.
- If you need to filter on a window function, you MUST use a subquery or CTE with ROW_NUMBER().
You MUST return exactly one valid SELECT statement only.
⚠️ Always wrap table and column names in double quotes.
⚠️ Do not pluralize or invent names.
- Add a LIMIT if missing (<= {SQL_MAX_LIMIT}).
- Output only the SQL query, nothing else.
"""

def build_sql(user_query: str, schema_rows):
    schema_text = []
    for row in schema_rows:
        schema_text.append(f'TABLE "{row["table"]}" COLUMN "{row["column"]}" ({row.get("dtype","")})')
    schema_text = "\n".join(schema_text)

    msgs = [
        {"role": "system", "content": SQL_SYS},
        {"role": "user", "content": f"User query: {user_query}\nSchema:\n{schema_text}\n\nSQL:"}
    ]

    resp = llm_client.chat.completions.create(model=OPENAI_MODEL, messages=msgs, temperature=0)
    raw_sql = resp.choices[0].message.content.strip()

    # 🛠 Lấy tất cả SELECT ... ;
    matches = re.findall(r"(?is)(select\s.+?;)", raw_sql)
    if not matches:
        raise ValueError(f"❌ LLM không trả về SQL hợp lệ:\n{raw_sql}")

    # Chỉ lấy SELECT cuối cùng
    sql = matches[-1].strip()

    # Đảm bảo LIMIT
    if not re.search(r"(?is)\blimit\b\s+\d+", sql):
        sql = sql.rstrip(";") + f"\nLIMIT {SQL_MAX_LIMIT};"

    return sql


# ───────── Thực thi SQL ─────────
def run_select(sql: str):
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

# ───────── Main ─────────

if __name__ == "__main__":
    question = input("💡 Nhập câu hỏi: ").strip()
  

    schema_hits = vector_search_schema(question, k=6)
    print("\n🔎 Schema hits:")
if not schema_hits:
    print("⚠️ Không tìm thấy bảng/cột nào từ RAG!")
else:
    # gom theo bảng
    tables = {}
    for hit in schema_hits:
        tables.setdefault(hit["table"], []).append(hit["column"])
    for tbl, cols in tables.items():
        print(f'  📂 Table "{tbl}" → columns: {", ".join(cols)}')
    sql = build_sql(question, schema_hits)

    print("\n📝 Generated SQL:")
    print(sql)

    cols, rows = run_select(sql)
    print("\n📊 Query Result :")
    for row in rows[:12]:
        print(dict(row))
