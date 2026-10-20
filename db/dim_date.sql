-- =============================================================================
-- Populate dim_date: one row per day, 2025-10-01 through 2026-12-31.
-- Safe to re-run: existing dates are skipped (ON CONFLICT DO NOTHING).
-- =============================================================================

INSERT INTO dim_date (
    date_key, day_of_week, day_name, is_weekend,
    week_of_year, month, month_name, quarter, year
)
SELECT
    d::date                              AS date_key,
    EXTRACT(ISODOW  FROM d)::smallint    AS day_of_week,   -- 1 = Monday ... 7 = Sunday
    to_char(d, 'FMDay')                  AS day_name,      -- FM strips padding spaces
    EXTRACT(ISODOW  FROM d) IN (6, 7)    AS is_weekend,
    EXTRACT(WEEK    FROM d)::smallint    AS week_of_year,  -- ISO week number
    EXTRACT(MONTH   FROM d)::smallint    AS month,
    to_char(d, 'FMMonth')                AS month_name,
    EXTRACT(QUARTER FROM d)::smallint    AS quarter,
    EXTRACT(YEAR    FROM d)::smallint    AS year
FROM generate_series('2025-10-01'::date, '2026-12-31'::date, interval '1 day') AS d
ON CONFLICT (date_key) DO NOTHING;
