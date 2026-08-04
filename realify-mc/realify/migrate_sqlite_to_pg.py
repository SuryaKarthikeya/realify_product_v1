"""1g — one-time data migration: SQLite -> Postgres (#005 1c).

Copies every table from the SQLite source into the Postgres dest by truncating each dest table and
re-inserting the source rows (so a re-run is clean and idempotent regardless of constraints),
resets the serial sequences so new inserts won't collide with migrated ids, and verifies row counts
match. It NEVER deletes from SQLite — the source file is your instant rollback. Because it truncates
the DEST, only run it against the migration-target Postgres before cutover, never a live DB.

    DATABASE_URL=postgresql+psycopg://...:5432/realify  REALIFY_DB=/data/realify_mc.db \
    python3 run.py migrate-pg [--dry-run]

Run AFTER the Postgres schema exists; this also runs `alembic upgrade head` on the dest first to be
sure. Safe to run repeatedly.
"""
import sqlite3
from . import config, dbengine, db

SKIP = {"alembic_version"}


def source_tables(scon):
    rows = scon.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
    return [r[0] for r in rows if r[0] not in SKIP]


def columns(scon, table):
    return [r[1] for r in scon.execute(f"PRAGMA table_info({table})").fetchall()]


def copy_table(scon, dcur, table, cols, dry_run=False):
    """Replace the dest table's contents with the source rows. Truncate-then-copy makes a re-run
    clean and idempotent regardless of whether the table has a unique constraint (correct for a
    one-time load into a fresh Postgres). Never touches SQLite."""
    rows = scon.execute(f"SELECT {', '.join(cols)} FROM {table}").fetchall()
    if not dry_run:
        dcur.execute(f"TRUNCATE TABLE {table}")
        if rows:
            placeholders = "(" + ", ".join(["%s"] * len(cols)) + ")"
            dcur.executemany(
                f"INSERT INTO {table}({', '.join(cols)}) VALUES {placeholders}",
                [tuple(r) for r in rows])
    return len(rows)


def reset_sequence(dcur, table):
    """Bump each serial sequence in the table to its column MAX so new inserts won't collide with
    migrated ids. Finds serial columns from the catalog (no assumption the PK is named `id`) — so
    tables like seller_skus, keyed on (tenant_id, asin), are correctly skipped. Returns the list of
    (column, sequence) reset."""
    serial_cols = dcur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = %s AND column_default LIKE %s", (table, "nextval(%")
    ).fetchall()
    done = []
    for (col,) in serial_cols:
        seq = dcur.execute("SELECT pg_get_serial_sequence(%s, %s)", (table, col)).fetchone()[0]
        if seq:
            dcur.execute(f"SELECT setval(%s, (SELECT COALESCE(MAX({col}), 1) FROM {table}), true)", (seq,))
            done.append((col, seq))
    return done


def dest_count(dcur, table):
    return dcur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def migrate(dry_run=False, ensure_schema=True, source_path=None, dest=None):
    """Copy SQLite -> Postgres. Returns a report list of [table, source_rows, dest_rows].
    `dest` is an open DBAPI connection (defaults to the configured Postgres engine); injectable
    for tests. `dest_rows` is None in a dry run."""
    if dest is None and dbengine.dialect() != "postgresql":
        raise SystemExit("DATABASE_URL must point at Postgres before migrating. Aborting.")
    if ensure_schema and dest is None:
        db.init_db()                                   # alembic upgrade head on the Postgres dest
    scon = sqlite3.connect(source_path or config.DB_PATH)
    scon.row_factory = sqlite3.Row
    own_dest = dest is None
    draw = dest if dest is not None else dbengine.engine().raw_connection()
    try:
        dcur = draw.cursor()
        tables = source_tables(scon)
        report = [[t, copy_table(scon, dcur, t, columns(scon, t), dry_run), None] for t in tables]
        draw.commit()
        if not dry_run:
            for t in tables:
                reset_sequence(dcur, t)
            draw.commit()
            for row in report:
                row[2] = dest_count(dcur, row[0])
        return report
    finally:
        scon.close()
        if own_dest:
            draw.close()
