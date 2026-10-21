-- =============================================================================
-- Read-only database user for the application (MCP server / backend).
--
-- Run as admin; the password is passed in as a psql variable, never stored in git:
--   docker exec -i nl2sql-postgres sh -c 'psql -v ON_ERROR_STOP=1
--       -v app_password="$APP_DB_PASSWORD" -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < db/app_user.sql
--
-- Safe to re-run: the user is created once; password, settings and grants are reapplied.
-- =============================================================================

-- 1. Create the login if it doesn't exist yet, then (re)set its password.
SELECT 'CREATE ROLE nl2sql_readonly LOGIN'
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nl2sql_readonly')
\gexec
ALTER ROLE nl2sql_readonly WITH LOGIN PASSWORD :'app_password' CONNECTION LIMIT 10;

-- 2. Safety settings applied to every session of this user.
ALTER ROLE nl2sql_readonly SET default_transaction_read_only = on;
ALTER ROLE nl2sql_readonly SET statement_timeout = '5s';
ALTER ROLE nl2sql_readonly SET idle_in_transaction_session_timeout = '30s';

-- 3. Only explicitly granted users may connect or use the schema.
REVOKE ALL ON DATABASE :"DBNAME" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"DBNAME" TO nl2sql_readonly;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;   -- default since Postgres 15, kept explicit
GRANT USAGE ON SCHEMA public TO nl2sql_readonly;

-- 4. Start from zero, then allow SELECT table by table (an allowlist).
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM nl2sql_readonly;
GRANT SELECT ON dim_date, dim_team, dim_application, dim_screen, dim_process,
                fact_work_daily, fact_process_daily
    TO nl2sql_readonly;

-- 5. dim_user: every column EXCEPT user_name. No names, ever.
GRANT SELECT (user_uuid, location, role, department, team_uuid) ON dim_user TO nl2sql_readonly;
