"""Seed the analytics database with synthetic data.

Run from the repo root:
    uv run --env-file .env python db/seed.py

Every run starts fresh: all seeded tables are truncated first (dim_date is left alone,
it is loaded by db/dim_date.sql). Faker and random are seeded, so every run produces
the same names and the same activity pattern.
"""

import os
import random
from datetime import date, timedelta

import psycopg
from faker import Faker

SEED = 42
NUM_USERS = 40
NUM_INACTIVE_USERS = 4   # assigned to a team in dim_user, but no activity at all
NUM_LATE_JOINERS = 3     # activity starts partway through the date range

FACT_START = date(2025, 10, 1)
FACT_END = date(2026, 10, 20)  # last day with activity (inclusive)

# Team name -> department. Department is derived from the team so the data stays consistent.
TEAMS = {
    "Team Alpha": "Engineering",
    "Team Beta": "Engineering",
    "Team Gamma": "Operations",
    "Team Delta": "Finance",
    "Team Omega": "Support",
}

ROLES_BY_DEPARTMENT = {
    "Engineering": ["Software Engineer", "Senior Software Engineer", "QA Engineer", "Engineering Manager"],
    "Operations": ["Operations Analyst", "Operations Manager"],
    "Finance": ["Accountant", "Financial Analyst", "Finance Manager"],
    "Support": ["Support Specialist", "Support Lead"],
}

# A few office locations (not random Faker cities) so grouping by location is meaningful.
LOCATIONS = ["Bangalore", "Pune", "London", "New York", "Berlin"]

APPLICATIONS = {
    "VS Code": "Development",
    "IntelliJ IDEA": "Development",
    "GitHub": "Development",
    "Slack": "Communication",
    "Microsoft Teams": "Communication",
    "Outlook": "Communication",
    "Jira": "Project Management",
    "Confluence": "Documentation",
    "Excel": "Spreadsheet",
    "Google Chrome": "Browser",
}

SCREENS = [
    "Editor", "Terminal", "Debugger", "Pull Request", "Code Search",
    "Inbox", "Calendar", "Chat", "Video Call",
    "Board", "Backlog", "Ticket Detail", "Dashboard",
    "Page Editor", "Page View",
    "Worksheet", "Pivot Table",
    "Web Page", "Search Results", "Settings",
]

# Which screens are used in which application. A screen can appear in several applications.
APP_SCREENS = {
    "VS Code": ["Editor", "Terminal", "Debugger", "Code Search", "Settings"],
    "IntelliJ IDEA": ["Editor", "Terminal", "Debugger"],
    "GitHub": ["Pull Request", "Code Search"],
    "Slack": ["Chat", "Video Call", "Settings"],
    "Microsoft Teams": ["Chat", "Video Call", "Calendar"],
    "Outlook": ["Inbox", "Calendar"],
    "Jira": ["Board", "Backlog", "Ticket Detail", "Dashboard"],
    "Confluence": ["Page Editor", "Page View"],
    "Excel": ["Worksheet", "Pivot Table"],
    "Google Chrome": ["Web Page", "Search Results", "Dashboard"],
}

# How much each department uses each application (relative weights; missing = never).
APP_WEIGHTS_BY_DEPARTMENT = {
    "Engineering": {"VS Code": 8, "IntelliJ IDEA": 4, "GitHub": 5, "Slack": 4, "Microsoft Teams": 2,
                    "Outlook": 2, "Jira": 4, "Confluence": 2, "Excel": 0.5, "Google Chrome": 3},
    "Operations": {"Slack": 3, "Microsoft Teams": 4, "Outlook": 4, "Jira": 3, "Confluence": 2,
                   "Excel": 6, "Google Chrome": 4},
    "Finance": {"Slack": 2, "Microsoft Teams": 3, "Outlook": 5, "Jira": 1, "Confluence": 1,
                "Excel": 9, "Google Chrome": 3},
    "Support": {"Slack": 6, "Microsoft Teams": 3, "Outlook": 4, "Jira": 8, "Confluence": 3,
                "Excel": 1, "Google Chrome": 4},
}

# Process name -> owning team.
PROCESSES = {
    "Code Review": "Team Alpha",
    "Feature Development": "Team Alpha",
    "Release Deployment": "Team Alpha",
    "Bug Fixing": "Team Beta",
    "Incident Triage": "Team Beta",
    "Sprint Planning": "Team Beta",
    "Vendor Onboarding": "Team Gamma",
    "Inventory Reconciliation": "Team Gamma",
    "Invoice Approval": "Team Delta",
    "Expense Reporting": "Team Delta",
    "Month-End Close": "Team Delta",
    "Customer Ticket Resolution": "Team Omega",
}

WORK_COLUMNS = ["activity_date", "user_uuid", "team_uuid", "application_uuid", "screen_uuid",
                "effort_in_sec"]
PROCESS_COLUMNS = ["activity_date", "user_uuid", "team_uuid", "application_uuid", "screen_uuid",
                   "process_uuid", "effort_in_sec"]


def connect() -> psycopg.Connection:
    """Connect as the admin user. Values come from environment variables (see .env)."""
    return psycopg.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=int(os.environ.get("POSTGRES_PORT", "5432")),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


def truncate_seeded_tables(cur: psycopg.Cursor) -> None:
    # One TRUNCATE for all tables, so foreign keys between them don't block it.
    # Tables are listed explicitly (no CASCADE) so we never wipe a table by surprise.
    cur.execute("""
        TRUNCATE fact_process_daily, fact_work_daily,
                 dim_process, dim_user, dim_screen, dim_application, dim_team
    """)


def seed_dimensions(cur: psycopg.Cursor, fake: Faker) -> dict:
    """Insert all dimension rows. Returns the generated UUIDs for seeding the facts."""
    team_ids = {}
    for team_name in TEAMS:
        cur.execute(
            "INSERT INTO dim_team (team_name) VALUES (%s) RETURNING team_uuid",
            (team_name,),
        )
        team_ids[team_name] = cur.fetchone()[0]

    users = []  # (user_uuid, team_name)
    for _ in range(NUM_USERS):
        team_name = random.choice(list(TEAMS))
        department = TEAMS[team_name]
        cur.execute(
            """
            INSERT INTO dim_user (user_name, location, role, department, team_uuid)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_uuid
            """,
            (
                # first + last name only: fake.name() sometimes adds titles like "Dr." or "Jr.".
                # unique first names also make every full name unique.
                f"{fake.unique.first_name()} {fake.last_name()}",
                random.choice(LOCATIONS),
                random.choice(ROLES_BY_DEPARTMENT[department]),
                department,
                team_ids[team_name],
            ),
        )
        users.append((cur.fetchone()[0], team_name))

    app_ids = {}
    for app_name, category in APPLICATIONS.items():
        cur.execute(
            "INSERT INTO dim_application (application_name, app_category) VALUES (%s, %s) "
            "RETURNING application_uuid",
            (app_name, category),
        )
        app_ids[app_name] = cur.fetchone()[0]

    screen_ids = {}
    for screen_name in SCREENS:
        cur.execute(
            "INSERT INTO dim_screen (screen_name) VALUES (%s) RETURNING screen_uuid",
            (screen_name,),
        )
        screen_ids[screen_name] = cur.fetchone()[0]

    process_ids = {}
    for process_name, owner_team in PROCESSES.items():
        cur.execute(
            "INSERT INTO dim_process (process_name, team_uuid) VALUES (%s, %s) RETURNING process_uuid",
            (process_name, team_ids[owner_team]),
        )
        process_ids[process_name] = cur.fetchone()[0]

    return {
        "teams": team_ids,
        "users": users,
        "apps": app_ids,
        "screens": screen_ids,
        "processes": process_ids,
    }


def weighted_sample(items: list, weights: list, k: int) -> list:
    """Pick k distinct items; items with a higher weight are more likely to be picked."""
    items, weights = list(items), list(weights)
    picked = []
    for _ in range(min(k, len(items))):
        i = random.choices(range(len(items)), weights=weights)[0]
        picked.append(items.pop(i))
        weights.pop(i)
    return picked


def activity_start_dates(users: list) -> dict:
    """Decide from which date each user is active. None means never active."""
    shuffled = random.sample(users, len(users))
    starts = {}
    for i, (user_uuid, _team_name) in enumerate(shuffled):
        if i < NUM_INACTIVE_USERS:
            starts[user_uuid] = None
        elif i < NUM_INACTIVE_USERS + NUM_LATE_JOINERS:
            starts[user_uuid] = date(2026, 2, 1) + timedelta(days=random.randint(0, 90))
        else:
            starts[user_uuid] = FACT_START
    return starts


def daily_effort_sec(day: date) -> int:
    """Total seconds a user works on a given day (0 = did not work)."""
    if day.weekday() >= 5:  # Saturday or Sunday: occasionally a short shift
        return random.randint(1 * 3600, 3 * 3600) if random.random() < 0.05 else 0
    if random.random() < 0.05:  # leave day
        return 0
    hours = min(max(random.gauss(7.5, 0.8), 5.0), 10.0)
    return int(hours * 3600)


def process_slices(effort: int, app: str, process_names: list, process_weights: list) -> list:
    """Split part of one work row's effort across 0-2 processes. Returns [(process_name, seconds)].

    The slices add up to at most `effort`, so process effort can never exceed work effort.
    """
    chance = 0.3 if APPLICATIONS[app] == "Communication" else 0.7
    if random.random() >= chance:
        return []
    processes = weighted_sample(process_names, process_weights, 1 if random.random() < 0.75 else 2)
    per_process = int(effort * random.uniform(0.4, 1.0) / len(processes))
    if per_process == 0:
        return []
    return [(process, per_process) for process in processes]


def generate_facts(ids: dict) -> tuple[list, list]:
    """Build all fact rows in memory. Returns (work_rows, process_rows)."""
    starts = activity_start_dates(ids["users"])
    process_names = list(PROCESSES)
    work_rows, process_rows = [], []

    for user_uuid, team_name in ids["users"]:
        start = starts[user_uuid]
        if start is None:
            continue
        team_uuid = ids["teams"][team_name]

        # Every (application, screen) pair this user's department works in, weighted by app usage.
        app_weights = APP_WEIGHTS_BY_DEPARTMENT[TEAMS[team_name]]
        pairs = [(app, screen) for app in app_weights for screen in APP_SCREENS[app]]
        pair_weights = [app_weights[app] / len(APP_SCREENS[app]) for app, _ in pairs]

        # Own team's processes are far more likely, but users sometimes help with other teams' processes.
        process_weights = [6.0 if PROCESSES[p] == team_name else 0.15 for p in process_names]

        day = start
        while day <= FACT_END:
            total = daily_effort_sec(day)
            if total:
                day_pairs = weighted_sample(pairs, pair_weights, random.randint(4, 7))
                shares = [random.uniform(0.2, 1.0) for _ in day_pairs]
                for (app, screen), share in zip(day_pairs, shares):
                    effort = int(total * share / sum(shares))
                    key = (day, user_uuid, team_uuid, ids["apps"][app], ids["screens"][screen])
                    work_rows.append((*key, effort))
                    for process, seconds in process_slices(effort, app, process_names, process_weights):
                        process_rows.append((*key, ids["processes"][process], seconds))
            day += timedelta(days=1)

    return work_rows, process_rows


def copy_rows(cur: psycopg.Cursor, table: str, columns: list, rows: list) -> None:
    """Bulk-load rows with COPY: one streamed command instead of one INSERT per row."""
    with cur.copy(f"COPY {table} ({', '.join(columns)}) FROM STDIN") as copy:
        for row in rows:
            copy.write_row(row)


def check_facts(cur: psycopg.Cursor) -> None:
    """Raise (which rolls back the whole seed) if the fact data breaks the schema's rules."""
    # Rule: per user/day/app/screen, process effort <= work effort, and every process row has a work row.
    cur.execute("""
        SELECT count(*)
        FROM (
            SELECT activity_date, user_uuid, application_uuid, screen_uuid,
                   SUM(effort_in_sec) AS process_sec
            FROM fact_process_daily
            GROUP BY activity_date, user_uuid, application_uuid, screen_uuid
        ) p
        LEFT JOIN fact_work_daily w
               USING (activity_date, user_uuid, application_uuid, screen_uuid)
        WHERE w.effort_in_sec IS NULL OR p.process_sec > w.effort_in_sec
    """)
    bad = cur.fetchone()[0]
    if bad:
        raise RuntimeError(f"{bad} process groups exceed (or have no) matching work effort")

    # Rule: the team on a fact row is always the user's team.
    cur.execute("""
        SELECT count(*) FROM (
            SELECT user_uuid, team_uuid FROM fact_work_daily
            UNION ALL
            SELECT user_uuid, team_uuid FROM fact_process_daily
        ) f
        JOIN dim_user u USING (user_uuid)
        WHERE f.team_uuid <> u.team_uuid
    """)
    bad = cur.fetchone()[0]
    if bad:
        raise RuntimeError(f"{bad} fact rows have a team different from the user's team")


def print_counts(cur: psycopg.Cursor) -> None:
    for table in ["dim_team", "dim_user", "dim_application", "dim_screen", "dim_process",
                  "fact_work_daily", "fact_process_daily"]:
        cur.execute(f"SELECT count(*) FROM {table}")
        print(f"{table:<20} {cur.fetchone()[0]:>6} rows")


def main() -> None:
    random.seed(SEED)
    Faker.seed(SEED)
    fake = Faker(["en_IN", "en_GB", "en_US"])

    # `with connect()` runs everything in ONE transaction: it commits if the block finishes,
    # and rolls back if any error is raised, so a failed run never leaves half-seeded tables.
    with connect() as conn, conn.cursor() as cur:
        truncate_seeded_tables(cur)
        ids = seed_dimensions(cur, fake)
        work_rows, process_rows = generate_facts(ids)
        copy_rows(cur, "fact_work_daily", WORK_COLUMNS, work_rows)
        copy_rows(cur, "fact_process_daily", PROCESS_COLUMNS, process_rows)
        check_facts(cur)
        print_counts(cur)


if __name__ == "__main__":
    main()
