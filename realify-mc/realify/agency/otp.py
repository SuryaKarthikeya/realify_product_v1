"""Email-OTP for the agency console (agency-plan §1b): 6-digit codes, 10-minute TTL, single-use.
Codes are stored only as a SHA-256 hash; the plaintext goes out via realify.mail and is never
persisted. Raw psycopg cursor in/out (agency_otp is not brand-scoped, so no RLS scope needed)."""
import datetime
import hashlib
import secrets

from .. import mail

TTL_MINUTES = 10


def _hash(code):
    return hashlib.sha256(code.encode()).hexdigest()


def issue(cur, email, send=True):
    """Generate a 6-digit code, store its hash + expiry, and (by default) email it. Returns the code
    (tests read it; production only ever sends it)."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=TTL_MINUTES)
    cur.execute("INSERT INTO agency_otp(email, code_hash, expires_at) VALUES(%s,%s,%s)",
                (email.lower().strip(), _hash(code), expires))
    if send:
        mail.send(email, "Your Realify verification code",
                  f"Your code is {code}. It expires in {TTL_MINUTES} minutes and can be used once.")
    return code


def verify(cur, email, code):
    """True iff there is a matching, unexpired, unused code — which is then consumed (single-use)."""
    now = datetime.datetime.now(datetime.timezone.utc)
    cur.execute(
        "SELECT id FROM agency_otp WHERE email=%s AND code_hash=%s AND used=false AND expires_at > %s "
        "ORDER BY id DESC LIMIT 1",
        (email.lower().strip(), _hash(code), now))
    row = cur.fetchone()
    if not row:
        return False
    cur.execute("UPDATE agency_otp SET used=true WHERE id=%s", (row[0],))
    return True
