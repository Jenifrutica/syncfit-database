from datetime import date, datetime, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from syncfit_database import (
    CycleLog,
    Database,
    EnergyCheckIn,
    ExerciseLoad,
    Gym,
    GymMachine,
    GymMembership,
    Profile,
    Routine,
    RoutineExercise,
    SessionRecord,
    TelemetrySample,
    User,
)


def make_db(tmp_path):
    db = Database(f"sqlite:///{tmp_path}/test.db")
    db.init_db()
    return db


def test_user_profile_and_loads(tmp_path):
    db = make_db(tmp_path)
    with db.session_scope() as session:
        user = User(email="ana@example.com", password_hash="x", display_name="Ana")
        profile = Profile(
            user=user,
            language="ES",
            height_cm=165,
            weight_kg=62,
            objective="HYPERTROPHY",
            modality="MENSTRUAL_CYCLE",
            last_period_date=date(2026, 9, 10),
            cycle_length_days=28,
        )
        profile.loads.append(ExerciseLoad(exercise_id="goblet-squat", weight_kg=20, reps=10))
        session.add(user)

    with db.session_scope() as session:
        stored = session.query(User).filter_by(email="ana@example.com").one()
        assert stored.profile.height_cm == 165
        assert stored.profile.loads[0].exercise_id == "goblet-squat"
        assert stored.profile.loads[0].weight_kg == 20


def test_energy_and_cycle_logs(tmp_path):
    db = make_db(tmp_path)
    with db.session_scope() as session:
        user = User(email="b@example.com", password_hash="x", display_name="B")
        session.add(user)
        session.flush()
        session.add(
            EnergyCheckIn(
                user_id=user.id,
                timestamp=datetime.now(timezone.utc),
                energy_level="NO_ENERGY",
                modality="MENSTRUAL_CYCLE",
                day_or_week=14,
            )
        )
        session.add(
            CycleLog(
                user_id=user.id,
                date=date(2026, 9, 23),
                modality="MENSTRUAL_CYCLE",
                cycle_day=14,
                phase="OVULATORY",
            )
        )
        user_id = user.id

    with db.session_scope() as session:
        energy = session.query(EnergyCheckIn).filter_by(user_id=user_id).one()
        log = session.query(CycleLog).filter_by(user_id=user_id).one()
        assert energy.energy_level == "NO_ENERGY"
        assert log.phase == "OVULATORY"


def test_session_telemetry_and_routine(tmp_path):
    db = make_db(tmp_path)
    with db.session_scope() as session:
        user = User(email="c@example.com", password_hash="x", display_name="C")
        session.add(user)
        session.flush()
        record = SessionRecord(
            user_id=user.id,
            modality="MENSTRUAL_CYCLE",
            day_or_week=14,
            phase_inferred="OVULATORY",
            k_load=0.72,
            source="simulated",
        )
        record.samples.append(
            TelemetrySample(
                delta_temperature_c=0.42, rmssd_hrv_ms=28.5, isometric_force_loss_pct=12.8
            )
        )
        routine = Routine(user_id=user.id, language="ES", muscle_groups=["GLUTES", "QUADRICEPS"])
        routine.items.append(
            RoutineExercise(
                order_index=0,
                exercise_id="goblet-squat",
                name="Sentadilla goblet",
                role="MAIN",
                sets=[{"type": "EFFECTIVE", "reps": 10, "weight_kg": 16}],
                description={"en": "Goblet squat"},
            )
        )
        session.add(record)
        session.add(routine)
        session.flush()
        user_id = user.id

    with db.session_scope() as session:
        rec = session.query(SessionRecord).filter_by(user_id=user_id).one()
        assert rec.samples[0].rmssd_hrv_ms == 28.5
        routine = session.query(Routine).filter_by(user_id=user_id).one()
        assert routine.items[0].exercise_id == "goblet-squat"
        assert routine.items[0].sets[0]["type"] == "EFFECTIVE"


def test_gym_memberships(tmp_path):
    db = make_db(tmp_path)
    with db.session_scope() as session:
        owner = User(email="admin@example.com", password_hash="x", display_name="Admin")
        gym = Gym(name="Asgard", code="A1B2C3", owner_user_id="pending")
        gym.machines.append(
            GymMachine(
                name={"en": "Hip thrust", "es": "Hip thrust"},
                purpose={"en": "Glutes"},
                exercise_ids=["hip-thrust"],
                weight_factor=1.4,
            )
        )
        athlete = User(email="d@example.com", password_hash="x", display_name="D")
        profile = Profile(user=athlete, modality="MENSTRUAL_CYCLE")
        session.add(owner)
        session.add(gym)
        session.add(profile)
        session.flush()
        gym.owner_user_id = owner.id
        profile.memberships.append(GymMembership(gym_id=gym.id))
        profile_id = profile.id
        gym_id = gym.id

    with db.session_scope() as session:
        profile = session.query(Profile).filter_by(id=profile_id).one()
        assert len(profile.memberships) == 1
        assert profile.memberships[0].gym_id == gym_id
        machine = profile.memberships[0].gym.machines[0]
        assert machine.name["en"] == "Hip thrust"
        assert machine.exercise_ids == ["hip-thrust"]

    # A duplicate (profile_id, gym_id) is rejected by the unique constraint.
    with pytest.raises(IntegrityError):
        with db.session_scope() as session:
            session.add(GymMembership(profile_id=profile_id, gym_id=gym_id))
            session.flush()


def test_init_db_adds_missing_columns_without_data_loss(tmp_path):
    from sqlalchemy import text

    db = Database(f"sqlite:///{tmp_path}/drift.db")
    # Simulate a stale table that is missing modeled columns, with a row in it.
    with db.engine.begin() as conn:
        conn.execute(text("CREATE TABLE gym_machines (id VARCHAR PRIMARY KEY, gym_id VARCHAR)"))
        conn.execute(text("INSERT INTO gym_machines (id, gym_id) VALUES ('m1', 'g1')"))
    added = db.init_db()
    assert any(name.startswith("gym_machines.") for name in added)
    # The row survives and the full schema is queryable.
    with db.session_scope() as session:
        assert session.query(GymMachine).count() == 1


def test_init_db_adds_document_id_column(tmp_path):
    from sqlalchemy import text

    db = Database(f"sqlite:///{tmp_path}/doc.db")
    with db.engine.begin() as conn:
        conn.execute(
            text("CREATE TABLE users (id VARCHAR PRIMARY KEY, email VARCHAR, password_hash VARCHAR, display_name VARCHAR, role VARCHAR)")
        )
    added = db.init_db()
    assert "users.document_id" in added
    with db.session_scope() as session:
        user = User(email="x@y.dev", password_hash="h", display_name="X", document_id="10203040")
        session.add(user)
    with db.session_scope() as session:
        assert session.query(User).filter_by(document_id="10203040").one().email == "x@y.dev"


def test_user_active_flag_and_gym_equipment(tmp_path):
    db = make_db(tmp_path)
    with db.session_scope() as session:
        user = User(email="act@example.com", password_hash="x", display_name="Act")
        session.add(user)
        gym = Gym(name="Eq", code="EQ1", owner_user_id="x")
        gym.machines.append(GymMachine(name={"en": "Flat bench"}, equipment_key="bench", equipment_type="BENCH"))
        session.add(gym)
        session.flush()
        user_id = user.id
    with db.session_scope() as session:
        assert session.query(User).filter_by(id=user_id).one().active is True
        machine = session.query(GymMachine).one()
        assert machine.equipment_key == "bench"
        assert machine.equipment_type == "BENCH"
