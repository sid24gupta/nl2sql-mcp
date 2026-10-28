# NEXT

## Next session

Week 2 (see `docs/PLAN.md`):
- [ ] Provider-agnostic LLM client (Groq first, OpenAI-compatible API)
- [ ] FastAPI `/ask` endpoint: MCP client -> schema tools -> SQL -> run_readonly_query -> summary
- [ ] 15 to 20 question eval set + accuracy script (baseline number)

## Done

### Oct 28
- `mcp_server/guardrail.py` (sqlglot AST): one statement, read queries only, no write/DDL/lock nodes
  anywhere (incl. CTEs), blocked functions and system tables, no per-user results, LIMIT <= 1000
- `run_readonly_query` MCP tool: guardrail -> Postgres as `nl2sql_readonly`; rejections and DB
  errors returned as `ToolError` so the LLM can self-correct
- 47 passing tests: 36 guardrail unit tests + 11 MCP integration tests
- Known limitation: renaming `user_uuid` inside a subquery bypasses the per-user check
  (smaller-group protection deferred)

### Oct 23
- MCP server (`mcp_server/server.py`, official SDK 2.x `MCPServer`): `list_tables`, `describe_table`
  - typed structured output (TypedDict), hides columns the app user can't read (`user_name`)
  - unknown/forbidden tables return a `ToolError` with a helpful message
- `mcp_server/db.py`: connects as `nl2sql_readonly`, refuses superusers
- Tested with a stdio smoke client and the MCP Inspector
- pytest set up (dev dependency, anyio plugin): 7 passing tests in `tests/test_mcp_tools.py`
- Run tests: `uv run --env-file .env pytest -v` (Docker must be running)

### Oct 21
- `docs/DATABASE.md`: tables, grain, golden rules, seeded data, example queries
- `db/seed.py`: dimensions + ~51k work / ~36k process rows via `COPY`, with built-in rule checks
- "Active team" rule clarified in schema comments (team from facts = active users only)
- Docker Postgres moved to host port 5433 (local Windows Postgres uses 5432)
- Sanity-checked the data with 7 queries
- Read-only app user `nl2sql_readonly` (`db/app_user.sql`): SELECT allowlist, no `user_name`,
  read-only + 5 s timeout

### Oct 20
- `dim_date` populated (2025-10-01 to 2026-12-31, 457 rows) via `db/dim_date.sql`
- uv project set up with faker and psycopg[binary]
- `docs/LEARNING.md` checklist added, `docs/DECISIONS.md` started

### Oct 19
- Repo created, folder structure, context files added
- `.gitattributes` added to enforce LF line endings
- Postgres 16 running in Docker via docker-compose
- Star schema created in `db/schema.sql` (6 dimensions, 2 facts) with table comments
