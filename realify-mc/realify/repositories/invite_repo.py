"""Organization invites: hashed single-use tokens (see #003). SQL moved verbatim from db.py (1b)."""
from .. import db
from .base import BaseRepository


class InviteRepository(BaseRepository):
    def create(self, tenant_id, email, role, token_hash, expires_at, created_by):
        new_id = db.create_returning_id(
            self.con,
            """INSERT INTO invites(tenant_id,email,role,token_hash,status,created_at,expires_at,created_by)
               VALUES(?,?,?,?,'pending',?,?,?)""",
            (tenant_id, (email or "").lower().strip(), role or "member", token_hash,
             db.now_iso(), expires_at, created_by))
        self.con.commit()
        return new_id

    def get_by_token_hash(self, token_hash):
        r = self.con.execute(
            "SELECT * FROM invites WHERE token_hash=?", (token_hash,)
        ).fetchone()
        return dict(r) if r else None

    def list(self, tenant_id):
        rows = self.con.execute(
            "SELECT id,email,role,status,created_at,expires_at FROM invites "
            "WHERE tenant_id=? ORDER BY created_at DESC",
            (tenant_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def revoke(self, tenant_id, invite_id):
        cur = self.con.execute(
            "UPDATE invites SET status='revoked' WHERE id=? AND tenant_id=? AND status='pending'",
            (invite_id, tenant_id),
        )
        self.con.commit()
        return cur.rowcount > 0

    def mark_accepted(self, invite_id, user_id):
        self.con.execute(
            "UPDATE invites SET status='accepted', accepted_by=?, accepted_at=? WHERE id=?",
            (user_id, db.now_iso(), invite_id),
        )
        self.con.commit()
