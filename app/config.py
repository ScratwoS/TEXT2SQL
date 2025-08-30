import os
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()
class Settings:
# ───────────────────────────────
    PG_HOST = os.getenv("PG_HOST", "localhost")
    PG_PORT = int(os.getenv("PG_PORT", "5432"))
    PG_DB = os.getenv("PG_DB", "quang")
    PG_USER = os.getenv("PG_USER", "postgres")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "123456")

    # MongoDB (Schema & RAG storage)
    # ───────────────────────────────
    MONGO_URI = os.getenv(
        "MONGO_URI",
        "mongodb+srv://minhquang:scratwos2004@cluster0.qcxysmi.mongodb.net/"
    )
    MONGO_DB = os.getenv("MONGO_DB", "rag")
    MONGO_COLLECTION_SCHEMA = os.getenv("MONGO_COLLECTION_SCHEMA", "schema")
    MONGO_COLLECTION_RULE = os.getenv("MONGO_COLLECTION_RULE", "rule")  # cho policy docs nếu cần

    # ───────────────────────────────
    # LLM / LM Studio (Text2SQL + NLG)
    # ───────────────────────────────
    OPENAI_API_KEY = os.getenv("LMSTUDIO_API_KEY", "not-needed")
    OPENAI_API_BASE = os.getenv("LMSTUDIO_API_BASE", "http://127.0.0.1:1234/v1")
    OPENAI_MODEL = os.getenv("LMSTUDIO_MODEL", "openai/gpt-oss-20b")
    # ───────────────────────────────

    # ───────────────────────────────
    # Embedding model (dùng cho schema RAG)
    # ───────────────────────────────
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    TOP_K = int(os.getenv("TOP_K", "6"))  # số schema chunk retrieve
    MAX_REPAIR_ROUNDS = int(os.getenv("MAX_REPAIR_ROUNDS", "2"))

    # ───────────────────────────────
    # Guardrails (SQL safety)
    # ───────────────────────────────
    SQL_MAX_LIMIT = int(os.getenv("SQL_MAX_LIMIT", "100"))  # LIMIT mặc định cho query
settings = Settings()

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB = os.getenv("PG_DB", "quang")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "123456")

# MongoDB (Schema & RAG storage)
# ───────────────────────────────
MONGO_URI = os.getenv(
        "MONGO_URI",
        "mongodb+srv://minhquang:scratwos2004@cluster0.qcxysmi.mongodb.net/"
    )
MONGO_DB = os.getenv("MONGO_DB", "rag")
MONGO_COLLECTION_SCHEMA = os.getenv("MONGO_COLLECTION_SCHEMA", "schema")
MONGO_COLLECTION_RULE = os.getenv("MONGO_COLLECTION_RULE", "rule")  # cho policy docs nếu cần

    # ───────────────────────────────
    # LLM / LM Studio (Text2SQL + NLG)
    # ───────────────────────────────
OPENAI_API_KEY = os.getenv("LMSTUDIO_API_KEY", "not-needed")
OPENAI_API_BASE = os.getenv("LMSTUDIO_API_BASE", "http://127.0.0.1:1234/v1")
OPENAI_MODEL = os.getenv("LMSTUDIO_MODEL", "openai/gpt-oss-20b")
    # ───────────────────────────────

    # ───────────────────────────────
    # Embedding model (dùng cho schema RAG)
    # ───────────────────────────────
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
TOP_K = int(os.getenv("TOP_K", "6"))  # số schema chunk retrieve
MAX_REPAIR_ROUNDS = int(os.getenv("MAX_REPAIR_ROUNDS", "2"))

    # ───────────────────────────────
    # Guardrails (SQL safety)
    # ───────────────────────────────
SQL_MAX_LIMIT = int(os.getenv("SQL_MAX_LIMIT", "100"))  # LIMIT mặc định cho query