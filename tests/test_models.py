from datetime import date, datetime, timezone

from syncfit_database import (
    CycleLog,
    Database,
    EnergyCheckIn,
    ExerciseLoad,
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
