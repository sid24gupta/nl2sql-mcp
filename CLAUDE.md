# CLAUDE.md

Context for AI coding assistants working in this repo. Read this first every session, then read `NEXT.md`.

## What this project is

An NL2SQL (natural language to SQL) analytics assistant. A user asks a question in plain English
("show process execution times for Team Alpha in September"), and the system generates safe,
read-only SQL against a PostgreSQL star schema, runs it, and summarizes the result.

It is a learning and portfolio project for SDE2/SDE3 interviews. The goal is to understand every
line, not just to ship. **Always explain what code does and why before or while writing it.**

## Architecture (v1)

- **PostgreSQL** (Docker): a synthetic star schema of user activity data (dimension + fact tables).
- **MCP server** (Python, FastMCP): exposes database tools: `list_tables`, `describe_table`,
  `run_readonly_query`.
- **Backend / agent layer** (FastAPI): acts as the MCP client, calls the LLM, runs the agent loop
  (planner, SQL writer, self-correction), returns answers.
- **LLM provider**: Groq free tier via an OpenAI-compatible client. Keep the LLM layer
  provider-agnostic so it can be swapped by config.
- **Frontend**: a minimal HTML/JS page served behind Nginx.
- **Deployment**: docker-compose on AWS EC2, CI/CD with GitHub Actions.

## Tech stack

Python 3.12, uv, FastAPI, FastMCP, asyncpg or psycopg, sqlglot, Pydantic, pytest, ruff,
Docker, docker-compose, GitHub Actions, AWS EC2, Nginx.

## Folder structure

```
mcp_server/   MCP server and database tools
backend/      FastAPI app, LLM client, agent loop
db/           schema SQL, seed scripts, roles
evals/        NL2SQL evaluation questions and runner
tests/        pytest tests
docs/         PLAN.md, ARCHITECTURE.md, DATABASE.md
```

## Non-negotiable rules

1. **Database access is read-only.** The app connects as a read-only Postgres role. Never use the
   admin user in application code.
2. **Every generated SQL query goes through the guardrail** before execution: sqlglot parse,
   exactly one statement, no write/DDL nodes anywhere in the tree, blocked functions rejected,
   `statement_timeout` set, row `LIMIT` enforced.
3. **No secrets in code or git.** Use environment variables and `.env` (git-ignored). Keep
   `.env.example` up to date.
4. **Date ranges use half-open intervals:** `created_at >= start AND created_at < end + 1 day`,
   never `BETWEEN` on timestamps.
5. **Tests for every guardrail change**, including malicious-query cases.
6. **Small, focused commits** using Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).

## How to work with me (the developer)

- Explain new concepts briefly when they first appear. I am learning.
- Prefer simple, readable code over clever code.
- When there are trade-offs, give 2 options and recommend one, then let me decide.
- After a design decision, suggest a one-line entry for `DECISIONS.md`.
- At the end of a session, suggest an update to `NEXT.md`.

## Current status

Phase: Week 1, project setup and database. See `docs/PLAN.md` and `NEXT.md`.
