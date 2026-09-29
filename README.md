# SyncFit Database

Persistence schema and models for SyncFit Edge. **PostgreSQL** in production,
**SQLite** for local development and tests, via SQLAlchemy 2.0. This package is
the single definition of the schema shared by the backend and any other service.

## Why PostgreSQL

- Relational integrity for accounts, profiles, sessions and routines.
- JSON columns for flexible structures (sets, localized descriptions).
- Mature migrations (Alembic) and easy hosting; a good fit for biomedical data.
- A path to TimescaleDB later for the high-frequency telemetry timeline.

## Schema

| Table | Purpose |
|-------|---------|
| `users` | Accounts (email, password hash, display name). |
| `profiles` | Anthropometrics, objective, modality, cycle/gestation tracking. |
| `exercise_loads` | Baseline weight per exercise for each profile. |
| `energy_checkins` | Subjective energy reported before training. |
| `cycle_logs` | Daily cycle/gestation timeline (cycle day, phase, week). |
| `sessions` | Training sessions with the deterministic decision. |
| `telemetry_samples` | Telemetry associated to a session. |
| `routines` / `routine_exercises` | Generated routines and their exercises, in order. |
| `supplement_intakes` | Daily supplement intake tracking per user. |
| `share_links` | Read-only share tokens with roles/permissions. |
| `gyms` / `gym_machines` | Gyms and the machines added by their admin. |
| `gym_memberships` | Join table: one row per (profile, gym) pair the athlete joined. |

## Data structures

The persistence layer is built on indexed, set-like relations:

| Structure | Where | How it is implemented | Purpose |
|-----------|-------|-----------------------|---------|
| **B-tree index (composite)** | `gym_memberships` | `UniqueConstraint("profile_id", "gym_id", name="uq_gym_membership")` | Keeps joins idempotent and turns "which gyms did this profile join?" into an O(log n) index scan. |
| **Set semantics** | `gym_memberships` | one row per pair, no duplicates | A membership is a member of a set of `(profile, gym)` pairs. |
| **Foreign-key indexes** | `gym_memberships.profile_id`, `gym_memberships.gym_id` | `index=True` on both columns | O(log n) lookups in either direction (profile → gyms, gym → members). |
| **Cascade collection** | `Profile.memberships` | `relationship(..., cascade="all, delete-orphan")` | Deleting a profile removes its memberships atomically. |
| **Localized JSON** | `gym_machines.name` / `purpose` | `JSON` columns holding `{"en","es","zh"}` | Machine text typed in any language is translated and shown per locale. |
| **JSON array index** | `gym_machines.exercise_ids` | `JSON` list of catalog exercise ids | Lets the backend prefer gym machines when building a routine. |

> `create_all` (via `Database.init_db()`) creates missing tables on startup. Because
> `create_all` never *alters* existing tables, `init_db()` first runs a light
> **additive schema reconcile**: missing columns are added with
> `ALTER TABLE ADD COLUMN` (nullable, no data loss) plus an index when the column
> is indexed/unique (e.g. `users.document_id`). This self-heals a stale dev
> database without dropping data. Production must use Alembic instead.

## Usage

```bash
# Start PostgreSQL
docker compose up -d          # postgres:16 on localhost:5432

# Install
pip install -e ".[postgres,dev]"

# Point the backend at it (defaults to sqlite:///./syncfit.db otherwise)
export SYNCFIT_DATABASE_URL="postgresql+psycopg://syncfit:syncfit@localhost:5432/syncfit"
```

```python
from syncfit_database import Database

db = Database()          # reads SYNCFIT_DATABASE_URL / DATABASE_URL
db.init_db()             # dev convenience; use Alembic migrations in production

with db.session_scope() as session:
    ...
```

## Migrations

`alembic/` is provided for versioned migrations:

```bash
pip install -e ".[migrations]"
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## Tests

```bash
pytest        # uses a temporary SQLite database
```

## Helper scripts

```bash
./scripts/up.sh      # start PostgreSQL (localhost:5432, syncfit/syncfit/syncfit)
./scripts/down.sh    # stop it
```

## Context for a new session

**What it is.** Persistence schema (shared by backend). **PostgreSQL** in prod,
**SQLite** for dev/tests, SQLAlchemy 2.0.

**Layout.** `syncfit_database/models.py` (tables), `database.py` (`Database`,
session_scope), `alembic/`, `docker-compose.yml`, `scripts/up.sh`/`down.sh`.

**Tables.** `users`, `profiles` (language, height/weight, body_fat_pct,
daily_calories, objective, goal_phase, modality, last_period_date,
cycle_length_days, gestation_week, available_machines, current_supplements,
supplement_macros, symptoms, weekly_training_goal, rest_days_allowance,
weight_unit, photo_url), `exercise_loads`, `energy_checkins`, `cycle_logs`,
`sessions`, `telemetry_samples`, `routines`, `routine_exercises` (sets, how_to,
tips), `supplement_intakes`, `share_links`.

**Env.** `SYNCFIT_DATABASE_URL` (default `postgresql+psycopg://syncfit:syncfit@localhost:5432/syncfit`).

**Run DB.** `./scripts/up.sh` (uses docker compose or `docker run`). Migrations:
`alembic revision --autogenerate -m ...` then `alembic upgrade head` (dev uses
`create_all`). When adding columns to a running DB, apply an idempotent
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.

**Run tests.** `pytest` (SQLite).


## Roles and gyms

- `users.role`: `ATHLETE` (default) | `GYM_ADMIN` | `SUPER_ADMIN`.
- Tables `gyms` (name, code, owner_user_id) and `gym_machines` (name, purpose,
  image_url, weight_factor). `profiles.active_gym_id` links an athlete to a gym.
- Adding columns to a running DB: `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...`.
