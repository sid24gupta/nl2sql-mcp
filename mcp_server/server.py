"""MCP server exposing read-only tools over the analytics database.

Run (stdio transport, started by an MCP client):
    uv run --env-file .env python -m mcp_server.server
"""

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from mcp_server.db import connect

server = MCPServer(
    "nl2sql",
    instructions=(
        "Tools for exploring a PostgreSQL star schema of daily work activity. "
        "Call list_tables first, then describe_table for the tables you need. "
        "Table and column descriptions contain rules you must follow when writing SQL."
    ),
)


@server.tool()
def list_tables() -> list[dict]:
    """List the tables you can query, with a description of each (including usage rules)."""
    with connect() as conn:
        return conn.execute("""
            SELECT c.relname                            AS table_name,
                   obj_description(c.oid, 'pg_class')   AS description
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
              AND c.relkind IN ('r', 'v')                       -- tables and views
              AND has_any_column_privilege(c.oid, 'SELECT')     -- only what we may read
            ORDER BY c.relname
        """).fetchall()


@server.tool()
def describe_table(table_name: str) -> dict:
    """Describe one table: its columns (name, type, description), primary key and foreign keys.

    Only columns you are allowed to read are listed.
    """
    with connect() as conn:
        table = conn.execute("""
            SELECT c.oid, obj_description(c.oid, 'pg_class') AS description
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = %s
              AND c.relkind IN ('r', 'v')
              AND has_any_column_privilege(c.oid, 'SELECT')
        """, (table_name,)).fetchone()
        if table is None:
            # Same message for "does not exist" and "not allowed", so nothing leaks.
            # ToolError (not ValueError): the SDK passes its message to the LLM; other exceptions
            # are treated as crashes and the LLM only sees a generic error.
            raise ToolError(f"Unknown table {table_name!r}. Call list_tables to see available tables.")

        columns = conn.execute("""
            SELECT a.attname                             AS name,
                   format_type(a.atttypid, a.atttypmod)  AS type,
                   NOT a.attnotnull                      AS nullable,
                   col_description(a.attrelid, a.attnum) AS description
            FROM pg_attribute a
            WHERE a.attrelid = %s AND a.attnum > 0 AND NOT a.attisdropped
              AND has_column_privilege(a.attrelid, a.attnum, 'SELECT')   -- hides user_name
            ORDER BY a.attnum
        """, (table["oid"],)).fetchall()

        primary_key = conn.execute("""
            SELECT a.attname AS name
            FROM pg_constraint k
            CROSS JOIN LATERAL unnest(k.conkey) WITH ORDINALITY AS u(attnum, pos)
            JOIN pg_attribute a ON a.attrelid = k.conrelid AND a.attnum = u.attnum
            WHERE k.conrelid = %s AND k.contype = 'p'
            ORDER BY u.pos
        """, (table["oid"],)).fetchall()

        foreign_keys = conn.execute("""
            SELECT a.attname AS column, rt.relname AS references_table, ra.attname AS references_column
            FROM pg_constraint k
            CROSS JOIN LATERAL unnest(k.conkey, k.confkey) AS u(attnum, ref_attnum)
            JOIN pg_attribute a  ON a.attrelid = k.conrelid  AND a.attnum = u.attnum
            JOIN pg_class rt     ON rt.oid = k.confrelid
            JOIN pg_attribute ra ON ra.attrelid = k.confrelid AND ra.attnum = u.ref_attnum
            WHERE k.conrelid = %s AND k.contype = 'f'
            ORDER BY a.attnum
        """, (table["oid"],)).fetchall()

    return {
        "table_name": table_name,
        "description": table["description"],
        "columns": columns,
        "primary_key": [row["name"] for row in primary_key],
        "foreign_keys": foreign_keys,
    }


if __name__ == "__main__":
    server.run()   # stdio transport by default
