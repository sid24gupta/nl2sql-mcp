# NEXT

## Next session (Oct 20)

- [ ] Write `docs/DATABASE.md` describing each table, its grain, and the golden rules
- [ ] Populate `dim_date` (Oct 2025 to Dec 2026)
- [ ] Faker seed script for dimensions: teams, users, applications, screens, processes
- [ ] Seed both fact tables (rule: work effort >= process effort per user/day/app/screen)
- [ ] Sanity-check the data with a few manual SQL queries

## Done

### Oct 19
- Repo created, folder structure, context files added
- `.gitattributes` added to enforce LF line endings
- Postgres 16 running in Docker via docker-compose
- Star schema created in `db/schema.sql` (6 dimensions, 2 facts) with table comments