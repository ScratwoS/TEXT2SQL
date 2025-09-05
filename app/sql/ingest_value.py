# ingest_value.py
import psycopg2
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer
import tqdm

# 1. Kết nối Postgres gốc (DB quang)
SRC_CONN = psycopg2.connect(
    host="localhost", port=5432,
    dbname="quang", user="postgres", password="123456"
)

# 2. Kết nối container pgvector (đã bật extension vector)
DST_CONN = psycopg2.connect(
    host="localhost", port=5000,
    dbname="postgres", user="postgres", password="postgres"
)

# 3. Model embedding
model = SentenceTransformer("BAAI/bge-m3")

# 4. Tạo bảng để lưu embedding (nếu chưa có)
def init_table():
    cur = DST_CONN.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS value_embeddings (
        id SERIAL PRIMARY KEY,
        table_name TEXT,
        column_name TEXT,
        value TEXT,
        embedding vector(1024)
    );
    """)
    DST_CONN.commit()
    cur.close()

# 5. Lấy danh sách tất cả bảng + cột trong DB gốc
def get_columns():
    cur = SRC_CONN.cursor()
    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
    """)
    cols = cur.fetchall()
    cur.close()
    return cols

# 6. Lấy các giá trị DISTINCT của một cột
def fetch_distinct(table, column):
    cur = SRC_CONN.cursor()
    sql = f'SELECT DISTINCT "{column}" FROM "{table}" WHERE "{column}" IS NOT NULL;'
    cur.execute(sql)
    vals = [str(r[0]) for r in cur.fetchall() if r[0] is not None]
    cur.close()
    return vals

# 7. Ingest toàn bộ
def ingest_all():
    init_table()
    columns = get_columns()
    dst_cur = DST_CONN.cursor()

    for table, column, dtype in columns:
        print(f"🔎 Ingesting {table}.{column} ({dtype})...")
        values = fetch_distinct(table, column)
        if not values:
            continue

        data = []
        for val in tqdm.tqdm(values):
            emb = model.encode(val, normalize_embeddings=True).tolist()
            data.append((table, column, val, emb))

        execute_values(dst_cur,
            """
            INSERT INTO value_embeddings (table_name, column_name, value, embedding)
            VALUES %s
            """,
            data
        )
        DST_CONN.commit()
        print(f"✅ Done {table}.{column}: {len(values)} values")

    dst_cur.close()

if __name__ == "__main__":
    ingest_all()
    print("🎉 All values ingested into pgvector")
