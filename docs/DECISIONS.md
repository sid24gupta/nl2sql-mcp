# Decisions

One line per design decision: date, what we chose, and why.

- 2026-10-20: Use `psycopg[binary]` (bundled libpq) instead of plain `psycopg`, for zero-setup installs on Windows and in Docker.
