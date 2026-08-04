"""Base repository — the single place a bounded context's SQL lives.

This is workstream 1b of #005. Today every repository wraps a SQLite connection
(``realify.db.connect``). In Phase 1c/1d this is where the Postgres engine, connection
pooling, and the per-transaction RLS tenant context (``SET LOCAL app.tenant_id``) will be
applied — repository *method signatures and call sites do not change* when that happens.

Rules for repositories (see docs/EXTENDING.md):
- A repository owns the SQL for ONE bounded context (tenancy, identity, invites, ...).
- Tenant-scoped methods take ``tenant_id`` explicitly today; under Postgres RLS (1d) the
  database will additionally enforce it, so a forgotten ``WHERE tenant_id=`` cannot leak.
- Repositories never open their own connection — they receive one (from a UnitOfWork or a
  caller-managed ``con``). This keeps transaction control in one place.
"""


class BaseRepository:
    """Holds a live DB connection shared with its UnitOfWork / caller."""

    def __init__(self, con):
        self.con = con
