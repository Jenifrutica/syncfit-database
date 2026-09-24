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
