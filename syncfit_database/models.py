"""Persistence models.

Covers accounts, athlete profiles (with baseline loads), energy check-ins, the
cycle/gestation timeline, sessions, telemetry samples and generated routines.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    profile: Mapped["Profile"] = relationship(back_populates="user", uselist=False)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    language: Mapped[str] = mapped_column(String(8), default="EN")
    is_guest: Mapped[bool] = mapped_column(default=False)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    body_fat_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    daily_calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    objective: Mapped[str | None] = mapped_column(String(40), nullable=True)
    goal_phase: Mapped[str | None] = mapped_column(String(30), nullable=True)
    modality: Mapped[str | None] = mapped_column(String(20), nullable=True)
    available_machines: Mapped[list] = mapped_column(JSON, default=list)
    current_supplements: Mapped[list] = mapped_column(JSON, default=list)
    supplement_macros: Mapped[list] = mapped_column(JSON, default=list)
    weight_unit: Mapped[str | None] = mapped_column(String(4), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    weekly_training_goal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rest_days_allowance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_period_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cycle_length_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gestation_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    user: Mapped[User] = relationship(back_populates="profile")
    loads: Mapped[list["ExerciseLoad"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class ExerciseLoad(Base):
    __tablename__ = "exercise_loads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"), index=True)
    exercise_id: Mapped[str] = mapped_column(String(80))
    weight_kg: Mapped[float] = mapped_column(Float, default=0.0)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="loads")


class EnergyCheckIn(Base):
    __tablename__ = "energy_checkins"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    energy_level: Mapped[str] = mapped_column(String(20))
    modality: Mapped[str] = mapped_column(String(20))
    day_or_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CycleLog(Base):
    """Daily cycle/gestation tracking entry."""

    __tablename__ = "cycle_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    modality: Mapped[str] = mapped_column(String(20))
    cycle_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phase: Mapped[str | None] = mapped_column(String(20), nullable=True)
    gestation_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class SessionRecord(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    modality: Mapped[str] = mapped_column(String(20))
    day_or_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phase_inferred: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fatigue_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    k_load: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(20), default="simulated")

    samples: Mapped[list["TelemetrySample"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class TelemetrySample(Base):
    __tablename__ = "telemetry_samples"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("sessions.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    delta_temperature_c: Mapped[float] = mapped_column(Float)
    rmssd_hrv_ms: Mapped[float] = mapped_column(Float)
    isometric_force_loss_pct: Mapped[float] = mapped_column(Float)

    session: Mapped[SessionRecord] = relationship(back_populates="samples")


class Routine(Base):
    __tablename__ = "routines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("sessions.id"), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="EN")
    muscle_groups: Mapped[list] = mapped_column(JSON, default=list)
    total_estimated_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    phase_inferred: Mapped[str | None] = mapped_column(String(20), nullable=True)
    k_load: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    items: Mapped[list["RoutineExercise"]] = relationship(
        back_populates="routine", cascade="all, delete-orphan", order_by="RoutineExercise.order_index"
    )


class RoutineExercise(Base):
    __tablename__ = "routine_exercises"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    routine_id: Mapped[str] = mapped_column(ForeignKey("routines.id"), index=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    exercise_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    blocked: Mapped[bool] = mapped_column(default=False)
    block_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    substitute: Mapped[str | None] = mapped_column(String(160), nullable=True)
    series: Mapped[int] = mapped_column(Integer, default=3)
    reps: Mapped[int] = mapped_column(Integer, default=10)
    weight_suggested_kg: Mapped[float] = mapped_column(Float, default=0.0)
    rest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sets: Mapped[list] = mapped_column(JSON, default=list)
    description: Mapped[dict] = mapped_column(JSON, default=dict)
    how_to: Mapped[dict] = mapped_column(JSON, default=dict)
    tips: Mapped[list] = mapped_column(JSON, default=list)

    routine: Mapped[Routine] = relationship(back_populates="items")


__all__ = [
    "User",
    "Profile",
    "ExerciseLoad",
    "EnergyCheckIn",
    "CycleLog",
    "SessionRecord",
    "TelemetrySample",
    "Routine",
    "RoutineExercise",
    "SupplementIntake",
    "ShareLink",
]

class SupplementIntake(Base):
    __tablename__ = "supplement_intakes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    supplement_id: Mapped[str] = mapped_column(String(80))
    date: Mapped[date] = mapped_column(Date, index=True)
    taken: Mapped[bool] = mapped_column(default=False)

class ShareLink(Base):
    __tablename__ = "share_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    token: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    permissions: Mapped[list] = mapped_column(JSON, default=list)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

