# Learning Checklist

Concepts this project should teach. When a task touches one of these for the first time, explain it
briefly (what it is, why we use it here). Tick an item only when I can explain it out loud and point
to where it lives in the code.

## Database (PostgreSQL)
- [ ] Schema design: primary/foreign keys, normalization
- [ ] Star schema: fact vs dimension tables, grain
- [ ] Slowly Changing Dimensions (why team_uuid lives on the fact table)
- [ ] SQL: joins, GROUP BY, aggregations, window functions, CTEs, date filtering
- [ ] Indexes and EXPLAIN / EXPLAIN ANALYZE
- [ ] information_schema and pg_catalog metadata
- [ ] Roles and permissions (GRANT / REVOKE), read-only user
- [ ] Transactions: READ ONLY, statement_timeout
- [ ] Connection pooling
- [ ] Seeding fake data (Faker) and migrations (Alembic)

## Backend (Python)
- [ ] FastAPI: routes, request/response models, dependency injection
- [ ] Pydantic validation
- [ ] Async Python: async / await
- [ ] Postgres drivers: asyncpg or psycopg
- [ ] Config and secrets: .env, settings classes
- [ ] Error handling and structured logging
- [ ] Rate limiting
- [ ] pytest: fixtures, test database
- [ ] ruff, type hints
- [ ] uv, lock files

## LLM fundamentals and prompting
- [ ] Tokens and the context window
- [ ] Temperature and sampling
- [ ] System / user / assistant messages
- [ ] OpenAI-compatible API format
- [ ] Hallucination and grounding
- [ ] Latency and cost per request
- [ ] System prompts, zero-shot vs few-shot, chain-of-thought
- [ ] Structured output / JSON mode
- [ ] Prompt templates
- [ ] Prompt injection and defenses

## Tool calling, MCP and RAG
- [ ] Function / tool calling and JSON Schema
- [ ] MCP: server, client, host; tools, resources, prompts
- [ ] JSON-RPC
- [ ] Transports: stdio vs streamable HTTP
- [ ] MCP Inspector
- [ ] Embeddings, vector similarity search, pgvector
- [ ] RAG for schema retrieval

## AI agents
- [ ] Agent loop and the ReAct pattern
- [ ] Planning
- [ ] Self-correction / reflection
- [ ] Multi-agent orchestration
- [ ] State management and memory (short vs long term)
- [ ] Human-in-the-loop clarification
- [ ] Stopping conditions and max retries
- [ ] Hand-rolled loop vs LangChain vs LangGraph

## Evals, observability, guardrails
- [ ] Eval sets, execution accuracy vs exact SQL match
- [ ] Regression testing for prompt changes
- [ ] Tracing (Phoenix or LangSmith)
- [ ] LLM-as-judge
- [ ] AST parsing with sqlglot
- [ ] Defense in depth, least privilege

## Frontend
- [ ] HTML / CSS / JS basics, fetch
- [ ] Streaming responses (SSE)
- [ ] Rendering tables and charts
- [ ] CORS

## Docker
- [ ] Images vs containers
- [ ] Dockerfile layers, caching, multi-stage builds
- [ ] docker-compose, container networking, volumes
- [ ] Env vars and secrets in containers
- [ ] Health checks
- [ ] Registries: GHCR / ECR

## Git, GitHub, CI/CD
- [ ] Branches, PRs, Conventional Commits
- [ ] Line endings and .gitattributes
- [ ] Branch protection
- [ ] GitHub Actions: workflows, jobs, steps, runners, triggers
- [ ] Service containers, secrets, caching
- [ ] Build and push images from CI
- [ ] Quality gates (tests + eval score)
- [ ] Deployment strategies: rolling, rollback, blue-green

## AWS, Linux, networking
- [ ] EC2, security groups, key pairs, SSH
- [ ] IAM and least privilege
- [ ] Elastic IP, SSM Parameter Store
- [ ] Billing alarms
- [ ] Nginx reverse proxy, DNS, HTTPS (Let's Encrypt)
- [ ] Linux basics: permissions, systemd, logs
- [ ] RDS, Terraform (stretch)

## System design
- [ ] Separation of concerns
- [ ] Caching strategy
- [ ] Scalability: stateless services, queues, load balancers
- [ ] Reliability: retries, timeouts, circuit breakers
- [ ] Trade-off reasoning (see DECISIONS.md)
