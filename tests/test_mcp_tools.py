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


async def test_lists_both_tools(client):
    tools = await client.list_tools()
    assert {tool.name for tool in tools.tools} == {"list_tables", "describe_table"}


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
