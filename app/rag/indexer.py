import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()

# ===== Config =====
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB = os.getenv("PG_DB", "quang")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "123456")

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://minhquang:scratwos2004@cluster0.qcxysmi.mongodb.net/")
MONGO_DB = os.getenv("MONGO_DB", "rag")
MONGO_COLLECTION_SCHEMA = os.getenv("MONGO_COLLECTION_SCHEMA", "schema")
MONGO_COLLECTION_VALUE = os.getenv("MONGO_COLLECTION_VALUE", "values")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")


# ===== Embedding model =====
embedder = SentenceTransformer(EMBEDDING_MODEL)


def fetch_schema():
    """Lấy schema từ Postgres"""
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT,
        dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT table_schema, table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position;
            """)
            return cur.fetchall()
    finally:
        conn.close()


def fetch_distinct_values(table, column, limit=5000):
    """Lấy giá trị distinct từ 1 cột trong Postgres"""
    conn = psycopg2.connect(
        host=PG_HOST, port=PG_PORT,
        dbname=PG_DB, user=PG_USER, password=PG_PASSWORD
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f'SELECT DISTINCT "{column}" FROM "{table}" LIMIT {limit};')
            rows = [r[0] for r in cur.fetchall() if r[0] is not None]
            return rows
    except Exception as e:
        print(f"⚠️ Lỗi khi lấy distinct {table}.{column}: {e}")
        return []
    finally:
        conn.close()


def ingest_schema():
    """Ingest schema + value vào Mongo"""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    coll_schema = db[MONGO_COLLECTION_SCHEMA]
    coll_value = db[MONGO_COLLECTION_VALUE]

    coll_schema.drop()
    coll_value.drop()

    schema_rows = fetch_schema()
    print(f"📥 Found {len(schema_rows)} columns in schema")

    for row in tqdm(schema_rows, desc="Ingesting schema"):
        schema = row["table_schema"]
        table = row["table_name"]
        column = row["column_name"]
        dtype = row["data_type"]

        text = f"schema={schema} table={table} column={column} type={dtype}"
        emb = embedder.encode(text, normalize_embeddings=True).astype(np.float32).tolist()

        doc = {
            "schema": schema,
            "table": table,
            "column": column,
            "dtype": dtype,
            "text": text,
            "embedding": emb
        }
        coll_schema.insert_one(doc)

        # Nếu là string column → lấy value để RAG cho entity
        if dtype in ("character varying", "text", "varchar"):
            values = fetch_distinct_values(table, column)
            for v in values:
                v_text = str(v)
                v_emb = embedder.encode(v_text, normalize_embeddings=True).astype(np.float32).tolist()
                coll_value.insert_one({
                    "table": table,
                    "column": column,
                    "value": v_text,
                    "embedding": v_emb
                })

    print("✅ Done ingesting schema + values to Mongo")
    client.close()


if __name__ == "__main__":
    ingest_schema()
