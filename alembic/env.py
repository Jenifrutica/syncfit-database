from __future__ import annotations

from alembic import context

from syncfit_database import Base
from syncfit_database.database import Database

config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=Database().url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = Database().engine
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
