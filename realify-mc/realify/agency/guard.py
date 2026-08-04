"""Agency routes are Postgres-only (§1c-2): the tenancy/IAM/ledger tables and their RLS exist only on
Postgres. On a SQLite deployment the agency console must refuse rather than silently run without RLS.
The whole console is also feature-flagged behind AGENCY_CONSOLE (off in prod until launch)."""
import os

from fastapi import HTTPException

from .. import dbengine


def postgres_backed():
    return dbengine.dialect() == "postgresql"


def agency_console_on():
    return (os.environ.get("AGENCY_CONSOLE") or "off").strip().lower() == "on"


def require_postgres():
    """FastAPI dependency for agency routes: 503 unless the backend is Postgres (so RLS is in force)."""
    if not postgres_backed():
        raise HTTPException(status_code=503,
                            detail="Agency console requires the Postgres backend (row-level security).")
    return True


def require_agency_console():
    """Gate for every agency route: 404 (surface hidden) when AGENCY_CONSOLE is off; else require PG."""
    if not agency_console_on():
        raise HTTPException(status_code=404, detail="Not Found")
    require_postgres()
    return True
