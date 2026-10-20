# NEXT

## Next session

- [ ] Write `docs/DATABASE.md` describing each table, its grain, and the golden rules
      (include the ISO week caveat: e.g. 2025-12-29 is week 1 but year 2025)
- [ ] Faker seed script for dimensions: teams, users, applications, screens, processes
- [ ] Seed both fact tables (rule: work effort >= process effort per user/day/app/screen)
- [ ] Sanity-check the data with a few manual SQL queries

## Done

### Oct 20
- `dim_date` populated (2025-10-01 to 2026-12-31, 457 rows) via `db/dim_date.sql`
- uv project set up with faker and psycopg[binary]
- `docs/LEARNING.md` checklist added, `docs/DECISIONS.md` started

### Oct 19
- Repo created, folder structure, context files added
- `.gitattributes` added to enforce LF line endings
- Postgres 16 running in Docker via docker-compose
- Star schema created in `db/schema.sql` (6 dimensions, 2 facts) with table comments
