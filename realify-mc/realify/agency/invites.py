"""Agency admin invites: single-use, 7-day TTL. The raw token is returned once (emailed by the caller)
and stored only as a SHA-256 hash — same pattern as realify.auth org invites, but for an AGENCY."""
import datetime
import hashlib
import secrets

INVITE_TTL_DAYS = 7


def _hash(token):
    return hashlib.sha256((token or "").encode()).hexdigest()


def create_agency_invite(cur, agency_id, email, role="agency_admin", ttl_days=INVITE_TTL_DAYS):
    """Create (or reuse an existing unused, unexpired) invite for (agency, email). Returns
    (raw_token_or_None, invite_id). Reuse returns token None (the original token was shown once)."""
    now = datetime.datetime.now(datetime.timezone.utc)
    cur.execute(
        "SELECT id FROM agency_invites WHERE agency_id=%s AND lower(email)=lower(%s) "
        "AND used=false AND expires_at > %s ORDER BY id DESC LIMIT 1", (agency_id, email, now))
    row = cur.fetchone()
    if row:
        return None, row[0]
    token = secrets.token_urlsafe(24)
    expires = now + datetime.timedelta(days=ttl_days)
    cur.execute(
        "INSERT INTO agency_invites(agency_id,email,role,token_hash,expires_at) "
        "VALUES(%s,%s,%s,%s,%s) RETURNING id", (agency_id, email, role, _hash(token), expires))
    return token, cur.fetchone()[0]


def preview(cur, token):
    """Invite details if the token is valid, unused and unexpired; else None."""
    now = datetime.datetime.now(datetime.timezone.utc)
    cur.execute(
        "SELECT id, agency_id, email, role FROM agency_invites "
        "WHERE token_hash=%s AND used=false AND expires_at > %s", (_hash(token), now))
    row = cur.fetchone()
    if not row:
        return None
    return {"id": row[0], "agency_id": row[1], "email": row[2], "role": row[3]}


def accept(cur, token):
    """Consume the invite (single-use). Returns the invite dict, or None if invalid/used/expired."""
    inv = preview(cur, token)
    if not inv:
        return None
    cur.execute("UPDATE agency_invites SET used=true WHERE id=%s", (inv["id"],))
    return inv
