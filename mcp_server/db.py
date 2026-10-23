"""Database access for the MCP server. Always connects as the read-only app user."""

import os

import psycopg
from psycopg.rows import dict_row


def connect() -> psycopg.Connection:
    """Open a connection as the read-only app user (APP_DB_USER), never the admin user."""
    conn = psycopg.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["APP_DB_USER"],
        password=os.environ["APP_DB_PASSWORD"],
        row_factory=dict_row,   # rows come back as {"column": value} dicts instead of tuples
        connect_timeout=5,      # fail fast if the database is unreachable
    )
    # Safety net for rule 1: refuse to run with a superuser, even if .env is misconfigured.
    is_superuser = conn.execute("SELECT rolsuper FROM pg_roles WHERE rolname = current_user").fetchone()
    if is_superuser["rolsuper"]:
        conn.close()
        raise RuntimeError("MCP server must not connect as a superuser; check APP_DB_USER")
    return conn
