"""Tests for the MCP tools, run against the real seeded database as the read-only user.

Run from the repo root (Docker must be running):
    uv run --env-file .env pytest -v
"""

import pytest
from mcp import Client

from mcp_server.server import server

# Run every async test in this file with anyio's pytest plugin (anyio comes with the mcp package).
pytestmark = pytest.mark.anyio

EXPECTED_TABLES = {
    "dim_application", "dim_date", "dim_process", "dim_screen", "dim_team", "dim_user",
    "fact_process_daily", "fact_work_daily",
}


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """An MCP client connected to our server in-process (no subprocess, no stdio)."""
    async with Client(server) as mcp_client:
        yield mcp_client


async def test_lists_all_tools(client):
    tools = await client.list_tools()
    assert {tool.name for tool in tools.tools} == {"list_tables", "describe_table", "run_readonly_query"}


async def test_list_tables_returns_all_tables_with_descriptions(client):
    result = await client.call_tool("list_tables", {})

    assert not result.is_error
    tables = result.structured_content["result"]
    assert {table["table_name"] for table in tables} == EXPECTED_TABLES
    assert all(table["description"] for table in tables)


async def test_describe_table_hides_user_name(client):
    result = await client.call_tool("describe_table", {"table_name": "dim_user"})

    assert not result.is_error
    columns = [column["name"] for column in result.structured_content["columns"]]
    assert columns == ["user_uuid", "location", "role", "department", "team_uuid"]


async def test_describe_table_returns_keys(client):
    result = await client.call_tool("describe_table", {"table_name": "fact_work_daily"})

    assert not result.is_error
    table = result.structured_content
    assert table["primary_key"] == ["activity_date", "user_uuid", "application_uuid", "screen_uuid"]
    assert {
        "column": "team_uuid", "references_table": "dim_team", "references_column": "team_uuid",
    } in table["foreign_keys"]


@pytest.mark.parametrize("table_name", ["pg_shadow", "does_not_exist", "dim_user; DROP TABLE dim_team"])
async def test_describe_table_rejects_unknown_or_forbidden(client, table_name):
    result = await client.call_tool("describe_table", {"table_name": table_name})

    assert result.is_error
    assert "Unknown table" in result.content[0].text


async def test_run_readonly_query_returns_rows(client):
    sql = (
        "SELECT t.team_name, ROUND(SUM(f.effort_in_sec) / 3600.0, 1) AS hours "
        "FROM fact_work_daily f JOIN dim_team t ON t.team_uuid = f.team_uuid "
        "GROUP BY t.team_name ORDER BY t.team_name"
    )
    result = await client.call_tool("run_readonly_query", {"sql": sql})

    assert not result.is_error
    output = result.structured_content
    assert output["columns"] == ["team_name", "hours"]
    assert output["row_count"] == 5
    assert output["rows"][0]["team_name"] == "Team Alpha"
    assert output["sql"].endswith("LIMIT 1000")


async def test_run_readonly_query_rejects_unsafe_sql(client):
    result = await client.call_tool("run_readonly_query", {"sql": "DROP TABLE dim_team"})

    assert result.is_error
    assert "Query rejected" in result.content[0].text


async def test_run_readonly_query_reports_database_errors(client):
    result = await client.call_tool("run_readonly_query", {"sql": "SELECT nonexistent_column FROM dim_team"})

    assert result.is_error
    assert "Database error" in result.content[0].text


async def test_user_name_is_blocked_by_the_database(client):
    # The guardrail allows this (no user_uuid), but the read-only user has no access to user_name:
    # the second layer of defence catches it.
    sql = "SELECT location, COUNT(user_name) FROM dim_user GROUP BY location"
    result = await client.call_tool("run_readonly_query", {"sql": sql})

    assert result.is_error
    assert "permission denied" in result.content[0].text
