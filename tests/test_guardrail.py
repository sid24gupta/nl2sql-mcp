"""Unit tests for the SQL guardrail (no database needed)."""

import pytest

from mcp_server.guardrail import MAX_ROWS, GuardrailError, check_sql

ALLOWED = [
    "SELECT t.team_name, SUM(f.effort_in_sec) FROM fact_work_daily f "
    "JOIN dim_team t ON t.team_uuid = f.team_uuid GROUP BY t.team_name",
    "SELECT location, COUNT(DISTINCT user_uuid) AS users FROM dim_user GROUP BY location",
    "WITH per_day AS (SELECT user_uuid, activity_date, SUM(effort_in_sec) AS s FROM fact_work_daily "
    "GROUP BY user_uuid, activity_date) SELECT AVG(s) FROM per_day",
    "SELECT team_name FROM dim_team UNION SELECT process_name FROM dim_process",
    "SELECT COUNT(*) FROM fact_work_daily",
    "/* comment */ sElEcT team_name FROM dim_team -- trailing comment",
]

# (sql, part of the expected error message)
REJECTED = [
    ("SELECT 1; DROP TABLE dim_team", "exactly one"),
    ("DROP TABLE dim_team", "Only read queries"),
    ("DELETE FROM fact_work_daily", "Only read queries"),
    ("UPDATE dim_team SET team_name = 'x'", "Only read queries"),
    ("INSERT INTO dim_team (team_name) VALUES ('x')", "Only read queries"),
    ("WITH x AS (DELETE FROM dim_team RETURNING team_uuid) SELECT COUNT(*) FROM x", "DELETE"),
    ("SELECT team_name INTO evil FROM dim_team", "INTO"),
    ("SELECT team_name FROM dim_team FOR UPDATE", "LOCK"),
    ("VACUUM", "Only read queries"),
    ("GRANT SELECT ON dim_user TO public", "Only read queries"),
    ("SET statement_timeout = 0", "Only read queries"),
    ("SELECT pg_sleep(10)", "pg_sleep"),
    ("SELECT PG_SLEEP(10)", "pg_sleep"),
    ("SELECT pg_read_file('/etc/passwd')", "pg_read_file"),
    ("SELECT set_config('statement_timeout', '0', false)", "set_config"),
    ("SELECT query_to_xml('SELECT user_name FROM dim_user', true, true, '')", "query_to_xml"),
    ("SELECT rolname FROM pg_catalog.pg_roles", "not allowed"),
    ("SELECT usename FROM pg_user", "not allowed"),
    ("SELECT table_name FROM information_schema.tables", "not allowed"),
    ("SELEC 1", "Could not parse"),
    ("", "exactly one"),
]

PER_USER = [
    "SELECT * FROM fact_work_daily",
    "SELECT f.* FROM fact_work_daily f",
    "SELECT user_uuid, SUM(effort_in_sec) FROM fact_work_daily GROUP BY user_uuid",
    "SELECT SUM(effort_in_sec) FROM fact_work_daily GROUP BY user_uuid",
    "SELECT f.user_uuid::text AS u FROM fact_work_daily f",
    "SELECT team_name FROM dim_team UNION SELECT user_uuid::text FROM dim_user",
]


@pytest.mark.parametrize("sql", ALLOWED)
def test_allows_safe_queries(sql):
    check_sql(sql)  # must not raise


@pytest.mark.parametrize(("sql", "message"), REJECTED)
def test_rejects_unsafe_queries(sql, message):
    with pytest.raises(GuardrailError, match=message):
        check_sql(sql)


@pytest.mark.parametrize("sql", PER_USER)
def test_rejects_per_user_results(sql):
    with pytest.raises(GuardrailError, match="per user"):
        check_sql(sql)


def test_adds_limit_when_missing():
    assert check_sql("SELECT team_name FROM dim_team").endswith(f"LIMIT {MAX_ROWS}")


def test_keeps_small_limit():
    assert check_sql("SELECT team_name FROM dim_team LIMIT 10").endswith("LIMIT 10")


def test_caps_large_limit():
    assert check_sql("SELECT team_name FROM dim_team LIMIT 5000").endswith(f"LIMIT {MAX_ROWS}")
