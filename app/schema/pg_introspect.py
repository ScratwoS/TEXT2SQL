import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict
from ..config import settings

def fetch_schema_from_postgres() -> List[Dict]:
    conn = psycopg2.connect(
        host=settings.PG_HOST,
        port=settings.PG_PORT,
        dbname=settings.PG_DB,
        user=settings.PG_USER,
        password=settings.PG_PASSWORD,
    )
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    c.table_schema,
                    c.table_name,
                    c.column_name,
                    c.data_type,
                    pgd.description AS column_comment
                FROM information_schema.columns c
                LEFT JOIN pg_catalog.pg_statio_all_tables st
                       ON st.relname = c.table_name
                LEFT JOIN pg_catalog.pg_description pgd
                       ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
                WHERE c.table_schema NOT IN ('pg_catalog','information_schema')
                ORDER BY c.table_schema, c.table_name, c.ordinal_position;
            """)
            rows = cur.fetchall()
    finally:
        conn.close()
    return rows
