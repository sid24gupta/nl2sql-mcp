# Decisions

One line per design decision: date, what we chose, and why.

- 2026-10-20: Use `psycopg[binary]` (bundled libpq) instead of plain `psycopg`, for zero-setup installs on Windows and in Docker.
- 2026-10-21: Map the Docker Postgres to host port 5433 to avoid clashing with a local Windows Postgres on 5432.
