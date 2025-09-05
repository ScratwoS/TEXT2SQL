from rag.search import vector_search_schema, normalize_values
from sql.sql_builder import build_sql, run_select
from sql.sql_prompt import SQL_SYS
# ───────── Main ─────────
SQL_SYS

if __name__ == "__main__":
    question = input("💡 Nhập câu hỏi: ").strip()

    schema_hits = vector_search_schema(question, k=5)
    print("\n🔎 Schema hits:")
    if not schema_hits:
        print("⚠️ Không tìm thấy bảng/cột nào từ RAG!")
    else:
        # Gom theo bảng
        tables = {}
        for hit in schema_hits:
            tbl = hit["table"]
            col = hit["column"]   # luôn có, không fallback
            tables.setdefault(tbl, []).append(col)

        for tbl, cols in tables.items():
            unique_cols = sorted(set(cols))
            print(f'  📂 Table "{tbl}" → columns: {", ".join(unique_cols)}')

        sql = build_sql(question, schema_hits)
        sql = normalize_values(sql, schema_hits)
        print("\n📝 Generated SQL:")
        print(sql)

        cols, rows = run_select(sql)
        print("\n📊 Query Result :")
        for row in rows[:12]:
            print(dict(row))
