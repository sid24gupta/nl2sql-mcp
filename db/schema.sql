-- =============================================================================
-- NL2SQL Analytics: star schema for daily user work activity
--
-- Two fact tables share the same dimensions:
--   fact_work_daily     total effort per user/day/app/screen (process + one-off activity)
--   fact_process_daily  the process-related SUBSET of that effort, per process
--
-- Golden rules (also written as COMMENTs so the LLM can read them):
--   1. Team is always taken from the FACT table (fact.team_uuid), never via dim_user.
--   2. Never add work_daily and process_daily effort together: process is a subset of work.
--      One-off activity effort = work_daily effort - process_daily effort.
--   3. Filter and display dates through dim_date.
-- =============================================================================

-- gen_random_uuid() is built into Postgres 13+, no extension needed.

-- -----------------------------------------------------------------------------
-- Dimensions
-- -----------------------------------------------------------------------------

CREATE TABLE dim_date (
    date_key      DATE PRIMARY KEY,
    day_of_week   SMALLINT    NOT NULL,   -- 1 = Monday ... 7 = Sunday (ISO)
    day_name      TEXT        NOT NULL,
    is_weekend    BOOLEAN     NOT NULL,
    week_of_year  SMALLINT    NOT NULL,   -- ISO week number
    month         SMALLINT    NOT NULL,
    month_name    TEXT        NOT NULL,
    quarter       SMALLINT    NOT NULL,
    year          SMALLINT    NOT NULL
);
COMMENT ON TABLE dim_date IS
    'Calendar dimension, one row per day. Every fact table joins to it on its date column. '
    'Use it for all date filtering (weekends, months, quarters) and for dates shown in results or charts.';

CREATE TABLE dim_team (
    team_uuid  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_name  TEXT NOT NULL UNIQUE
);
COMMENT ON TABLE dim_team IS
    'Teams. Join to fact tables on fact.team_uuid. Users are NOT linked to teams through dim_user for analysis.';

CREATE TABLE dim_user (
    user_uuid   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_name   TEXT NOT NULL,
    location    TEXT NOT NULL,
    role        TEXT NOT NULL,
    department  TEXT NOT NULL,
    team_uuid   UUID            -- informational only, see comment
);
COMMENT ON TABLE dim_user IS 'People whose work activity is tracked.';
COMMENT ON COLUMN dim_user.team_uuid IS
    'Current team, for reference only. Do NOT use it to group or filter effort by team. '
    'For team-level analysis always use the team_uuid on the fact table.';

CREATE TABLE dim_application (
    application_uuid  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_name  TEXT NOT NULL UNIQUE,
    app_category      TEXT NOT NULL
);
COMMENT ON TABLE dim_application IS 'Applications users work in (e.g. an IDE, chat tool, ticketing tool).';
COMMENT ON COLUMN dim_application.app_category IS 'Category such as Development, Communication, Documentation, Browser.';

CREATE TABLE dim_screen (
    screen_uuid  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    screen_name  TEXT NOT NULL
);
COMMENT ON TABLE dim_screen IS
    'Screens or views inside applications. A screen has no application of its own; '
    'which application a screen was used in is recorded only on the fact row (application_uuid + screen_uuid).';

CREATE TABLE dim_process (
    process_uuid  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    process_name  TEXT NOT NULL UNIQUE,
    team_uuid     UUID NOT NULL REFERENCES dim_team (team_uuid)
);
COMMENT ON TABLE dim_process IS 'Defined business processes (e.g. Invoice Approval, Code Review).';
COMMENT ON COLUMN dim_process.team_uuid IS
    'Team that OWNS the process. This can differ from the team of the users who performed the work '
    '(that is fact_process_daily.team_uuid).';

-- -----------------------------------------------------------------------------
-- Facts
-- -----------------------------------------------------------------------------

CREATE TABLE fact_work_daily (
    activity_date     DATE    NOT NULL REFERENCES dim_date (date_key),
    user_uuid         UUID    NOT NULL REFERENCES dim_user (user_uuid),
    team_uuid         UUID    NOT NULL REFERENCES dim_team (team_uuid),
    application_uuid  UUID    NOT NULL REFERENCES dim_application (application_uuid),
    screen_uuid       UUID    NOT NULL REFERENCES dim_screen (screen_uuid),
    effort_in_sec     INTEGER NOT NULL CHECK (effort_in_sec >= 0),
    PRIMARY KEY (activity_date, user_uuid, application_uuid, screen_uuid)
);
COMMENT ON TABLE fact_work_daily IS
    'Grain: one row per user, per day, per application, per screen. '
    'Holds TOTAL effort = process effort + one-off activity effort. '
    'team_uuid is the team the user belonged to on that day; use it for all team analysis. '
    'Do not add this table''s effort to fact_process_daily effort (that would double count).';
COMMENT ON COLUMN fact_work_daily.effort_in_sec IS 'Time spent in seconds. Divide by 3600 for hours.';

CREATE TABLE fact_process_daily (
    activity_date     DATE    NOT NULL REFERENCES dim_date (date_key),
    user_uuid         UUID    NOT NULL REFERENCES dim_user (user_uuid),
    team_uuid         UUID    NOT NULL REFERENCES dim_team (team_uuid),
    application_uuid  UUID    NOT NULL REFERENCES dim_application (application_uuid),
    screen_uuid       UUID    NOT NULL REFERENCES dim_screen (screen_uuid),
    process_uuid      UUID    NOT NULL REFERENCES dim_process (process_uuid),
    effort_in_sec     INTEGER NOT NULL CHECK (effort_in_sec >= 0),
    PRIMARY KEY (activity_date, user_uuid, application_uuid, screen_uuid, process_uuid)
);
COMMENT ON TABLE fact_process_daily IS
    'Grain: one row per user, per day, per application, per screen, per process. '
    'Process-related SUBSET of fact_work_daily effort. '
    'One-off (non-process) activity effort = fact_work_daily effort minus fact_process_daily effort. '
    'team_uuid is the team the user belonged to on that day.';
COMMENT ON COLUMN fact_process_daily.effort_in_sec IS 'Time spent in seconds. Divide by 3600 for hours.';

-- -----------------------------------------------------------------------------
-- Indexes for the most common filters (date range + team)
-- The primary keys already index queries that start with activity_date.
-- -----------------------------------------------------------------------------

CREATE INDEX idx_work_daily_team_date    ON fact_work_daily (team_uuid, activity_date);
CREATE INDEX idx_process_daily_team_date ON fact_process_daily (team_uuid, activity_date);
CREATE INDEX idx_process_daily_process   ON fact_process_daily (process_uuid, activity_date);
