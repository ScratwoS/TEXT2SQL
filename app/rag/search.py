from typing import List, Dict
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import numpy as np
from config import settings 

def vector_search_schema(user_query: str, k: int = 12) -> List[Dict]:
    client = MongoClient(settings.MONGO_URI)
    coll = client[settings.MONGO_DB][settings.MONGO_COLLECTION_SCHEMA]

    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    q = model.encode(user_query, normalize_embeddings=True)
    pipeline = [
        {"$vectorSearch": {
            "index": "sql_query",
            "path": "embedding",
            "queryVector": np.array(q, dtype=np.float32).tolist(),
            "numCandidates": max(100, k*10),
            "limit": k
        }},
        {"$project": {
            "_id": 0,
            "schema": 1, "table": 1, "column": 1, "dtype": 1, "comment": 1, "text": 1,
            "score": {"$meta": "vectorSearchScore"}
        }}
    ]
    out = list(coll.aggregate(pipeline))
    client.close()
    return out
