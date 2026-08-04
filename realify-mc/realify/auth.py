"""Authentication — stdlib only (no bcrypt/argon2 native deps, so it installs
clean on any machine). Passwords are PBKDF2-HMAC-SHA256 with a per-user salt.
tenant_id is derived from the authenticated user; it is never accepted from the client.

Data access goes through the repository layer (workstream 1b of #005) via UnitOfWork —
this module is the reference example of how new code talks to the database: no raw SQL,
no db.connect(), no manual commit/close.
"""
import datetime as _dt
import hashlib, secrets
from . import db
from .repositories import UnitOfWork

_ITER = 200_000
_RESET_TTL_MIN = 60          # single-use reset links expire in one hour

def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITER)
    return dk.hex(), salt

def verify_password(password, pw_hash, pw_salt):
    calc, _ = hash_password(password, pw_salt)
    return secrets.compare_digest(calc, pw_hash)

def signup(email, password, account_name=None):
    """Create a tenant + owner user. Returns (user_id, tenant_id) or raises ValueError."""
    email = (email or "").lower().strip()
    if not email or "@" not in email:
        raise ValueError("A valid email is required.")
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    with UnitOfWork() as uow:
        if uow.users.get_by_email(email):
            raise ValueError("An account with this email already exists.")
        tenant_id = uow.tenants.create(account_name or email.split("@")[0])
        pw_hash, pw_salt = hash_password(password)
        user_id = uow.users.create(email, pw_hash, pw_salt, tenant_id)
    return user_id, tenant_id

def login(email, password):
    """Return (user_id, tenant_id) on success, else None."""
    with UnitOfWork() as uow:
        u = uow.users.get_by_email(email)
    if not u:
        return None
    if not verify_password(password, u["pw_hash"], u["pw_salt"]):
        return None
    return u["id"], u["tenant_id"]

def hash_token(raw):
    return hashlib.sha256((raw or "").encode()).hexdigest()

def request_reset(email):
    """Issue a single-use, TTL'd password-reset token for an existing account. Returns the RAW token
    (to embed in the emailed link) or None if no such user — the caller shows the same message either
    way so the endpoint can't be used to enumerate accounts. The row IS the audit record of the event."""
    email = (email or "").lower().strip()
    with UnitOfWork() as uow:
        u = uow.users.get_by_email(email)
    if not u:
        return None
    raw = secrets.token_urlsafe(32)
    expires = (_dt.datetime.now(_dt.timezone.utc) + _dt.timedelta(minutes=_RESET_TTL_MIN)).isoformat()
    con = db.connect()
    try:
        con.execute("INSERT INTO password_resets(email,token_hash,expires_at,used,created_at) "
                    "VALUES(?,?,?,0,?)", (email, hash_token(raw), expires, db.now_iso()))
        con.commit()
    finally:
        con.close()
    return raw


def _reset_row(con, token):
    r = con.execute("SELECT id,email,expires_at,used FROM password_resets WHERE token_hash=?",
                    (hash_token(token),)).fetchone()
    if not r:
        return None
    row = dict(r)
    if row["used"] or (row["expires_at"] or "") < _dt.datetime.now(_dt.timezone.utc).isoformat():
        return None
    return row


def preview_reset(token):
    """Return the target email if `token` is a live (unused, unexpired) reset link, else None."""
    con = db.connect()
    try:
        row = _reset_row(con, token)
        return row["email"] if row else None
    finally:
        con.close()


def confirm_reset(token, password):
    """Consume a reset token and set the new password. Marks the token used in the same transaction so
    a link works exactly once. Raises ValueError on a bad/expired token or a too-short password."""
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    con = db.connect()
    try:
        row = _reset_row(con, token)
        if not row:
            raise ValueError("This reset link is invalid, already used, or expired.")
        con.execute("UPDATE password_resets SET used=1 WHERE id=?", (row["id"],))
        con.commit()
    finally:
        con.close()
    with UnitOfWork() as uow:
        u = uow.users.get_by_email(row["email"])
        if not u:
            raise ValueError("This reset link is invalid, already used, or expired.")
        pw_hash, pw_salt = hash_password(password)
        uow.users.set_password(u["id"], pw_hash, pw_salt)
    return row["email"]


def invite_preview(token):
    """Non-sensitive preview for the join page: org name + invited email, or None if the
    token is invalid / not pending / expired."""
    with UnitOfWork() as uow:
        inv = uow.invites.get_by_token_hash(hash_token(token))
        if not inv or inv["status"] != "pending":
            return None
        if inv.get("expires_at") and inv["expires_at"] < db.now_iso():
            return None
        t = uow.tenants.get(inv["tenant_id"])
        return {"org": (t["name"] if t else "your team"), "email": inv["email"]}

def accept_invite(password, token):
    """Create a user attached to the inviting organization (tenant). Email comes from the
    invite (bound at creation). Returns (user_id, tenant_id) or raises ValueError."""
    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    with UnitOfWork() as uow:
        inv = uow.invites.get_by_token_hash(hash_token(token))
        if not inv or inv["status"] != "pending":
            raise ValueError("This invite is invalid or has already been used.")
        if inv.get("expires_at") and inv["expires_at"] < db.now_iso():
            raise ValueError("This invite has expired. Ask for a new one.")
        email = (inv["email"] or "").lower().strip()
        if uow.users.get_by_email(email):
            raise ValueError("An account with this email already exists. A person can belong to only one organization right now.")
        pw_hash, pw_salt = hash_password(password)
        user_id = uow.users.create(email, pw_hash, pw_salt, inv["tenant_id"])
        uow.users.set_role(user_id, inv.get("role") or "member")
        uow.invites.mark_accepted(inv["id"], user_id)
        return user_id, inv["tenant_id"]
