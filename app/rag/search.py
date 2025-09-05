import re
import psycopg2
from typing import List, Dict
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import numpy as np
from config import settings 
from psycopg2.extras import RealDictCursor

_model = SentenceTransformer(settings.EMBEDDING_MODEL)

def vector_search_schema(user_query: str, k: int = 6) -> List[Dict]:
    """
    Tìm schema (bảng + cột) trong MongoDB bằng $vectorSearch.
    - user_query: câu hỏi người dùng
    - k: số lượng schema top-k cần trả về
    """
    client = MongoClient(settings.MONGO_URI)
    coll = client[settings.MONGO_DB][settings.MONGO_COLLECTION_SCHEMA]

    # Encode user query thành vector
    q_emb = _model.encode(user_query, normalize_embeddings=True)
    q_emb = np.array(q_emb, dtype=np.float32).tolist()

    pipeline = [
        {
            "$vectorSearch": {
                "index": "sql_query",          # tên index bạn đã tạo
                "path": "embedding",              # field chứa vector
                "queryVector": q_emb,
                "numCandidates": max(100, k * 10),
                "limit": k,
            }
        },
        {
            "$project": {
                "_id": 0,
                "schema": 1,
                "table": 1,
                "column": 1,
                "dtype": 1,
                "comment": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]

    results = list(coll.aggregate(pipeline))
    client.close()
    return results

def vector_search_value_pgvector(user_val: str, table: str, column: str, k: int = 3):
    # Load model (có thể load 1 lần bên ngoài hàm để tối ưu)
    model = SentenceTransformer("BAAI/bge-m3")
    emb = model.encode(user_val, normalize_embeddings=True).tolist()

    # Kết nối tới Postgres container (port 5000)
    conn = psycopg2.connect(
        host="localhost",
        port=5000,
        dbname="postgres",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Truy vấn gần đúng
    cur.execute("""
        SELECT value, table_name, column_name,
               embedding <=> %s::vector AS distance
        FROM value_embeddings
        WHERE table_name = %s AND column_name = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s;
    """, (emb, table, column, emb, k))

    results = cur.fetchall()

    cur.close()
    conn.close()
    return results

def normalize_values(sql: str, schema_hits):
    # tìm các cặp ("Column", 'Literal') trong WHERE
    patterns = re.findall(r'"(\w+)"\s*=\s*\'([^\']+)\'', sql)
    if not patterns:
        return sql

    new_sql = sql
    for col, lit in patterns:
        # skip wildcard
        if "%" in lit or "_" in lit:
            print(f"⚠️ Skip normalize pattern literal: '{lit}'")
            continue

        # skip nếu là FirstName / LastName
        if col.lower() in ("firstname", "lastname"):
            print(f"⚠️ Skip normalize name literal: '{lit}'")
            continue

        # tìm đúng bảng chứa cột đó
        table = None
        for hit in schema_hits:
            if hit["column"].lower() == col.lower():
                table = hit["table"]
                break

        if not table:
            continue

        hits = vector_search_value_pgvector(lit, table, col, k=1)
        if hits:
            best_match = hits[0]["value"]
            if best_match.lower() != lit.lower():
                print(f"✨ Normalize '{lit}' → '{best_match}'")
                new_sql = new_sql.replace(f"'{lit}'", f"'{best_match}'")

    return new_sql
