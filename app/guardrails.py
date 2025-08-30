import re

FORBIDDEN = [
    r"(?is)\b(drop|delete|update|insert|alter|truncate)\b",
    r"(?is)\bpg_catalog\b",
]

def validate_sql(sql: str):
    if not re.match(r"(?is)^\s*select\b", sql or ""):
        raise ValueError("Only SELECT is allowed.")
    for pat in FORBIDDEN:
        if re.search(pat, sql):
            raise ValueError("Forbidden statement detected.")
    if ";" in sql.strip():
        # chặn multi-statement
        if not sql.strip().endswith(";"):
            raise ValueError("Multiple statements are not allowed.")
