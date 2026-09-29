"""SyncFit Edge database: SQLAlchemy models and session management.

PostgreSQL in production, SQLite for development and tests. This package is the
single definition of the persistence schema shared by the backend and any other
service.
"""

from .base import Base
from .database import Database, get_database
from .models import (
    CycleLog,
    EnergyCheckIn,
    ExerciseLoad,
    Gym,
    GymMachine,
    GymMembership,
    Profile,
    Routine,
    RoutineExercise,
    SessionRecord,
    ShareLink,
    SupplementIntake,
    TelemetrySample,
    User,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Base",
    "Database",
    "get_database",
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
    "Gym",
    "GymMachine",
    "GymMembership",
]
