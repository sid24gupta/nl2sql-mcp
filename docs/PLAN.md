# Project Plan: NL2SQL Analytics Assistant

## Goal

Build and deploy a working v1 in about 4 weeks (Oct 19 to mid-Nov 2026), working ~1 hr on weekday
evenings and longer on weekends. Learn every layer well enough to explain it in an SDE2/SDE3
interview.

## v1 scope

- Synthetic star schema in Postgres with realistic seeded data
- MCP server with schema tools and a guarded read-only query tool
- FastAPI backend with its own LLM client (Groq) and agent loop with self-correction
- An eval set that measures accuracy
- Docker, GitHub Actions CI/CD, deployed on AWS EC2 behind Nginx with HTTPS
- Minimal frontend and a strong README

## Out of scope for v1 (planned for v2)

LangGraph rewrite, embedding-based schema retrieval, Redis caching, observability/tracing,
Terraform, user authentication, RDS.

## Week-by-week

### Week 1: Database and MCP server
- [ ] Repo, folder structure, context files
- [ ] Postgres in Docker via docker-compose
- [ ] Star schema: dimension and fact tables with comments
- [ ] Seed script with Faker (a few months of data)
- [ ] Read-only Postgres role
- [ ] MCP server: `list_tables`, `describe_table`
- [ ] Guarded `run_readonly_query` + pytest malicious-query cases

### Week 2: NL2SQL flow and containers
- [ ] Provider-agnostic LLM client (Groq first)
- [ ] FastAPI `/ask` endpoint: schema, then SQL, then execute, then summarize
- [ ] 15 to 20 question eval set + accuracy script (baseline number)
- [ ] Dockerfiles + full docker-compose stack

### Week 3: Agents and CI
- [ ] Agent loop: planner, SQL writer, self-correction retry (max 3)
- [ ] Re-run evals and compare against the baseline
- [ ] GitHub Actions CI: ruff, pytest with a Postgres service container, small eval subset

### Week 4: Deploy and polish
- [ ] EC2 setup: security groups, IAM, billing alarm
- [ ] CD: build images, push to registry, deploy to EC2
- [ ] Nginx reverse proxy + HTTPS (Let's Encrypt)
- [ ] Minimal frontend
- [ ] README with architecture diagram and demo GIF
