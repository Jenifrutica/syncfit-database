"""Engine and session management."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Boolean, create_engine, inspect, text
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

    def _reconcile_schema(self) -> list[str]:
        """Add columns that the models define but the database is missing.

        This is a development convenience: ``create_all`` only creates whole
        tables, so a new column (e.g. ``users.document_id``) would otherwise be
        absent and break queries. Missing columns are added with
        ``ALTER TABLE ADD COLUMN`` (nullable, no data loss) and, when the column
        is indexed/unique, a matching index is created. Production must use
        Alembic instead.
        """
        inspector = inspect(self.engine)
        existing = set(inspector.get_table_names())
        added: list[str] = []
        for table in Base.metadata.sorted_tables:
            if table.name not in existing:
                continue
            current = {column["name"] for column in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in current:
                    continue
                column_type = column.type.compile(dialect=self.engine.dialect)
                default_sql = " DEFAULT true" if isinstance(column.type, Boolean) else ""
                with self.engine.begin() as connection:
                    connection.execute(
                        text(
                            f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" '
                            f"{column_type}{default_sql}"
                        )
                    )
                    if column.unique or column.index:
                        unique = "UNIQUE " if column.unique else ""
                        index_name = f"ix_{table.name}_{column.name}"
                        connection.execute(
                            text(
                                f'CREATE {unique}INDEX IF NOT EXISTS "{index_name}" '
                                f'ON "{table.name}" ("{column.name}")'
                            )
                        )
                added.append(f"{table.name}.{column.name}")
        return added

    def init_db(self) -> list[str]:
        """Reconcile new columns, then create all tables.

        Development convenience; use Alembic in production. Returns the names of
        the columns that had to be added (``"table.column"``).
        """
        added = self._reconcile_schema()
        Base.metadata.create_all(self.engine)
        if added:
            import sys

            print(f"[syncfit-database] added missing columns: {', '.join(added)}", file=sys.stderr)
        return added

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
