from typing import List, Dict
import sqlglot
from sqlglot import parse

def parse_schema_sql(sql_text: str) -> List[Dict]:
    """
    Trích xuất (schema, table, column, type, comment?) từ file .sql chứa CREATE TABLE ...
    Lưu ý: comment có thể không đầy đủ nếu dump không có COMMENT ON COLUMN.
    """
    result = []
    try:
        statements = parse(sql_text)
    except Exception:
        statements = sqlglot.parse_one(sql_text, error_level="ignore")
        statements = [statements] if statements else []

    for stmt in statements:
        if not stmt:
            continue
        if stmt.token_type == "CREATE":
            # Với sqlglot 20.x+, tốt hơn dùng AST class; ta fallback bằng cách đọc name/columns
            try:
                table = stmt.find("Table")
                table_name = ".".join([p for p in table.parts]) if table else None
                cols = stmt.find_all("ColumnDef")
            except Exception:
                table_name, cols = None, []

            if table_name and cols:
                schema = None
                if "." in table_name:
                    schema, table_name = table_name.split(".", 1)
                for col in cols:
                    col_name = col.name if hasattr(col, "name") else None
                    data_type = getattr(col, "kind", None)
                    result.append({
                        "table_schema": schema or "public",
                        "table_name": table_name,
                        "column_name": col_name,
                        "data_type": str(data_type) if data_type else None,
                        "column_comment": None
                    })
    return result
