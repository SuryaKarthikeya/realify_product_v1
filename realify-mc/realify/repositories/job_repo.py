"""Async job ledger (TaskRunner seam, #005 1e), tenant-scoped. SQL lives here per the
repository rule; the runner owns the connection/transaction and commits state transitions."""
from .. import db
from .base import BaseRepository


class JobRepository(BaseRepository):
    def create(self, tenant_id, kind, state="queued"):
        job_id = db.create_returning_id(
            self.con,
            "INSERT INTO jobs(tenant_id, kind, state, created_at, updated_at) VALUES(?,?,?,?,?)",
            (tenant_id, kind, state, db.now_iso(), db.now_iso()),
        )
        self.con.commit()
        return job_id

    def set_state(self, job_id, state, result=None, error=None):
        self.con.execute(
            "UPDATE jobs SET state=?, result=?, error=?, updated_at=? WHERE id=?",
            (state, result, error, db.now_iso(), job_id),
        )
        self.con.commit()

    def get(self, job_id):
        row = self.con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row) if row else None
