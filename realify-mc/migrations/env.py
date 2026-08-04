"""Alembic environment (#005 1c). The URL comes from realify.dbengine (sqlite by default;
Postgres when DATABASE_URL is set), so migrations target whatever the app targets."""
import os
import sys
from alembic import context

# repo root on path so `realify` imports work when alembic runs from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from realify import dbengine  # noqa: E402

config = context.config
config.set_main_option("sqlalchemy.url", dbengine.url())


def run_migrations_offline():
    context.configure(url=dbengine.url(), literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = dbengine.engine()
    with connectable.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
