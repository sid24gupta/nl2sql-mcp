"""SQL guardrail: every query written by the LLM goes through check_sql() before it reaches Postgres.

The SQL is parsed into a syntax tree (AST) with sqlglot and the tree is inspected, instead of
searching the text, so comments, odd casing or a DELETE hidden inside a CTE are still caught.
This is the first layer of defence; the read-only database user (db/app_user.sql) is the second.
"""

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

MAX_ROWS = 1000

# Nodes that write data, change the schema, take locks or manage transactions.
# Rejected anywhere in the tree, including inside CTEs and subqueries.
FORBIDDEN_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Merge,
    exp.Create, exp.Drop, exp.Alter, exp.TruncateTable,
    exp.Grant, exp.Revoke, exp.Copy, exp.Set,
    exp.Transaction, exp.Commit, exp.Rollback,
    exp.Command,  # statements sqlglot doesn't model: VACUUM, CALL, DO, EXPLAIN ...
    exp.Into,     # SELECT ... INTO new_table creates a table
    exp.Lock,     # SELECT ... FOR UPDATE locks rows
)

# Functions that sleep, read files, change settings, reach other servers or run SQL given as a string.
BLOCKED_FUNCTION_PREFIXES = ("pg_", "dblink", "lo_")
BLOCKED_FUNCTIONS = {
    "set_config", "current_setting",
    "query_to_xml", "query_to_xmlschema", "query_to_xml_and_xmlschema", "cursor_to_xml",
    "table_to_xml", "table_to_xml_and_xmlschema", "database_to_xml",
}

# Postgres's own system tables. The LLM should only query our tables.
BLOCKED_SCHEMAS = {"pg_catalog", "information_schema"}

# Privacy rule (DECISIONS.md): results are never per user.
USER_COLUMN = "user_uuid"


class GuardrailError(ValueError):
    """The query was rejected. The message says why, so the LLM can fix its SQL."""


def check_sql(sql: str) -> str:
    """Validate one query written by the LLM.

    Returns the SQL to run (re-generated from the tree, with a LIMIT of at most MAX_ROWS),
    or raises GuardrailError.
    """
    try:
        statements = [s for s in sqlglot.parse(sql, read="postgres") if s is not None]
    except SqlglotError as e:
        raise GuardrailError(f"Could not parse the SQL: {e}") from e

    if len(statements) != 1:
        raise GuardrailError(f"Send exactly one SQL statement (got {len(statements)}).")
    tree = statements[0]

    if not isinstance(tree, exp.Query):
        raise GuardrailError("Only read queries are allowed (SELECT, or WITH ... SELECT).")

    forbidden = tree.find(*FORBIDDEN_NODES)
    if forbidden is not None:
        raise GuardrailError(f"Only read queries are allowed; found {forbidden.key.upper()}.")

    for func in tree.find_all(exp.Func):
        name = (func.name if isinstance(func, exp.Anonymous) else func.sql_name()).lower()
        if name in BLOCKED_FUNCTIONS or name.startswith(BLOCKED_FUNCTION_PREFIXES):
            raise GuardrailError(f"Function {name}() is not allowed.")

    for table in tree.find_all(exp.Table):
        if table.catalog or table.db.lower() in BLOCKED_SCHEMAS or table.name.lower().startswith("pg_"):
            raise GuardrailError(f"Table {table.sql('postgres')} is not allowed. Use list_tables to see available tables.")

    for select in _final_selects(tree):
        _check_not_per_user(select)

    return _enforce_limit(tree).sql(dialect="postgres")


def _final_selects(query: exp.Expression) -> list[exp.Select]:
    """The SELECTs whose rows are returned (both sides of a UNION), not CTEs or subqueries."""
    if isinstance(query, exp.SetOperation):
        return _final_selects(query.this) + _final_selects(query.expression)
    if isinstance(query, exp.Subquery):
        return _final_selects(query.this)
    return [query]


def _check_not_per_user(select: exp.Select) -> None:
    """Reject results with one row per user. Aggregates like COUNT(DISTINCT user_uuid) are fine."""
    for projection in select.expressions:
        for node in projection.find_all(exp.Column, exp.Star):
            if node.find_ancestor(exp.AggFunc) is not None:
                continue
            if isinstance(node, exp.Star) or node.name.lower() == USER_COLUMN:
                raise GuardrailError(
                    "Results must not be per user: select named, grouped columns (no * and no user_uuid). "
                    "To count users use COUNT(DISTINCT user_uuid)."
                )

    group = select.args.get("group")
    if group is not None and any(c.name.lower() == USER_COLUMN for c in group.find_all(exp.Column)):
        raise GuardrailError("Results must not be per user: don't GROUP BY user_uuid in the final query.")


def _enforce_limit(tree: exp.Query) -> exp.Query:
    """Keep a LIMIT of at most MAX_ROWS; add one if missing."""
    limit = tree.args.get("limit")
    value = limit.expression if limit is not None else None
    if isinstance(value, exp.Literal) and value.is_int and int(value.this) <= MAX_ROWS:
        return tree
    return tree.limit(MAX_ROWS)
