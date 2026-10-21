# NEXT

## Next session

- [ ] MCP server: `list_tables`, `describe_table` (show only columns the app user can read)
- [ ] Guarded `run_readonly_query` + pytest malicious-query cases
      (incl. rejecting `user_uuid` in output or GROUP BY)

## Done

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
