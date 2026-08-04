"""Identity: users (members of a tenant/org). SQL moved verbatim from db.py (1b).

Note for Phase 1 auth refactor (#005): when sign-in OAuth lands, identity moves to a
separate ``user_identities`` table (provider, provider_subject, email_verified) and this
repository gains the lookups for it. The password fields stay for the LocalPassword provider.
"""
from .. import db
from .base import BaseRepository


class UserRepository(BaseRepository):
    def get_by_email(self, email):
        r = self.con.execute(
            "SELECT * FROM users WHERE email=?", (email.lower().strip(),)
        ).fetchone()
        return dict(r) if r else None

    def get_by_id(self, user_id):
        r = self.con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(r) if r else None

    def count_members(self, tenant_id):
        return self.con.execute(
            "SELECT COUNT(*) c FROM users WHERE tenant_id=?", (tenant_id,)
        ).fetchone()["c"]

    def create(self, email, pw_hash, pw_salt, tenant_id):
        new_id = db.create_returning_id(
            self.con,
            "INSERT INTO users(tenant_id,email,pw_hash,pw_salt,created_at) VALUES(?,?,?,?,?)",
            (tenant_id, email.lower().strip(), pw_hash, pw_salt, db.now_iso()))
        self.con.commit()
        return new_id

    def set_role(self, user_id, role):
        self.con.execute("UPDATE users SET role=? WHERE id=?", (role, user_id))
        self.con.commit()

    def set_avatar(self, user_id, avatar):
        self.con.execute("UPDATE users SET avatar=? WHERE id=?", (avatar, user_id))

    def set_password(self, user_id, pw_hash, pw_salt):
        self.con.execute("UPDATE users SET pw_hash=?, pw_salt=? WHERE id=?", (pw_hash, pw_salt, user_id))
        self.con.commit()

    def delete(self, user_id):
        """Remove a single user (leave-organization). Org + data survive."""
        self.con.execute("DELETE FROM users WHERE id=?", (user_id,))
        self.con.commit()

    def list_members(self, tenant_id):
        rows = self.con.execute(
            "SELECT id,email,role,created_at FROM users WHERE tenant_id=? ORDER BY created_at",
            (tenant_id,),
        ).fetchall()
        return [dict(r) for r in rows]
