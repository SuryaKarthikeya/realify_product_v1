"""baseline schema (#005 1c)

Builds the full schema from `db.SCHEMA`, per dialect: SQLite runs the DDL as-is; Postgres runs the
translated DDL (`dbengine.schema_to_postgres`). Statements are applied one-by-one through the
migration connection (not `executescript`) so Alembic owns the transaction on both engines. The DDL
is `CREATE TABLE/INDEX IF NOT EXISTS`, so this is idempotent and safely ADOPTS an existing
pre-Alembic SQLite database.

Revision ID: 0001_baseline
Revises:
"""
from alembic import op

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def _statements(ddl):
    # strip line comments FIRST so a ';' inside a comment can't split a statement
    no_comments = "\n".join(line.split("--", 1)[0] for line in ddl.splitlines())
    for chunk in no_comments.split(";"):
        if chunk.strip():
            yield chunk.strip()


def upgrade():
    from realify import db, dbengine
    is_sqlite = op.get_bind().dialect.name == "sqlite"
    ddl = db.SCHEMA if is_sqlite else dbengine.schema_to_postgres(db.SCHEMA)
    for stmt in _statements(ddl):
        op.execute(stmt)


def downgrade():
    raise NotImplementedError("baseline migration is not reversible")
