"""Engine and session management."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .base import Base

DEFAULT_URL = "sqlite:///./syncfit.db"
POSTGRES_URL = "postgresql+psycopg://syncfit:syncfit@localhost:5432/syncfit"


class Database:
    """Thin wrapper around a SQLAlchemy engine and session factory."""

    def __init__(self, url: str | None = None, echo: bool = False) -> None:
        self.url = url or os.environ.get("SYNCFIT_DATABASE_URL") or os.environ.get(
            "DATABASE_URL", DEFAULT_URL
        )
        connect_args = {"check_same_thread": False} if self.url.startswith("sqlite") else {}
        self.engine: Engine = create_engine(self.url, echo=echo, connect_args=connect_args)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)

    def init_db(self) -> None:
        """Create all tables (development convenience; use Alembic in production)."""
        Base.metadata.create_all(self.engine)

    def drop_db(self) -> None:
        Base.metadata.drop_all(self.engine)

    def session(self) -> Session:
        return self.session_factory()

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


_DATABASE: Database | None = None


def get_database(url: str | None = None) -> Database:
    """Return the process-wide database (created once)."""
    global _DATABASE
    if _DATABASE is None or (url is not None and url != _DATABASE.url):
        _DATABASE = Database(url)
    return _DATABASE


__all__ = ["Database", "get_database", "DEFAULT_URL", "POSTGRES_URL"]
