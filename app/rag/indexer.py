from typing import List, Dict
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import numpy as np
from ..config import settings

def _ensure_vector_index(coll):
    # Vector index cho MongoDB 7.0+ ($vectorSearch)
    # Tạo nếu chưa tồn tại (idempotent).
    try:
        coll.database.command({
            "createIndexes": coll.name,
            "indexes": [{
                "name": "embedding_idx",
                "key": {"embedding": "columnvector"},
                "weights": {},
                "default_language": "english"
            }]
        })
    except Exception:
        pass  # nếu đã tồn tại

def upsert_schema_docs(docs: List[Dict]):
    client = MongoClient(settings.MONGODB_URI)
    db = client[settings.MONGODB_DB]
    coll = db[settings.MONGODB_COLL_SCHEMA]

    _ensure_vector_index(coll)

    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    texts = [d["text"] for d in docs]
    embs = model.encode(texts, normalize_embeddings=True)
    for d, e in zip(docs, embs):
        d["embedding"] = np.array(e, dtype=np.float32).tolist()
        coll.update_one(
            {"schema": d["schema"], "table": d["table"], "column": d["column"]},
            {"$set": d},
            upsert=True
        )
    client.close()
