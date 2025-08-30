from typing import List, Dict
import json

def build_schema_docs(rows: List[Dict]) -> List[Dict]:
    """
    Convert rows -> list of RAG documents.
    Mỗi document là 1 cột, kèm text mô tả giàu ngữ nghĩa để embed.
    """
    docs = []
    for r in rows:
        schema = r.get("table_schema", "public")
        table = r.get("table_name")
        col = r.get("column_name")
        dtype = r.get("data_type")
        comment = r.get("column_comment") or ""
        text = (
            f"schema={schema}\n"
            f"table={table}\n"
            f"column={col}\n"
            f"type={dtype}\n"
            f"description={comment}"
        )
        docs.append({
            "schema": schema,
            "table": table,
            "column": col,
            "dtype": dtype,
            "comment": comment,
            "text": text
        })
    return docs
