from typing import Dict, Any
from .intents import detect_intent
from .rag.search import vector_search_schema
from .sqlgen import build_sql
from .guardrails import validate_sql
from .datasource.postgres import run_select
from .llm import chat_completion

ANSWER_SYS = """You are a data analyst. 
Given the SQL result (rows as JSON) and the user question, write a concise answer.
If rows are empty, say that no matching records were found.
"""

def answer_with_llm(user_query: str, columns, rows):
    # Option: synthesize a human answer
    messages = [
        {"role":"system","content": ANSWER_SYS},
        {"role":"user","content": f"Question: {user_query}\nColumns: {columns}\nRows(sample up to 5): {rows[:5]}"},
    ]
    return chat_completion(messages)

def run_pipeline(user_query: str, synthesize: bool = True) -> Dict[str, Any]:
    intent = detect_intent(user_query)
    schema_hits = vector_search_schema(user_query, k=12)
    sql = build_sql(user_query, schema_hits)
    validate_sql(sql)
    columns, rows = run_select(sql)
    out = {
        "intent": intent,
        "schema_hits": schema_hits,
        "sql": sql,
        "columns": columns,
        "rows": rows
    }
    if synthesize:
        out["answer"] = answer_with_llm(user_query, columns, rows)
    return out
