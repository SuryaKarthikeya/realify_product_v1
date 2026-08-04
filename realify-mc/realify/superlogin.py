"""Superlogin hardening (agency-plan P7 item 5) — replaces the P0.9 tourniquet on the same /superlogin
route. Access requires: a valid admin key (ADMIN_KEY_HASH, P0.9) + an @realify.ai staff email + an
emailed OTP. Success mints a SEPARATE 8-hour signed session cookie (never the app session) and LEDGERS
the session (who/when/IP) in superlogin_sessions. Three failures lock the email out and alert. Works on
both engines (uses the main db layer)."""
import datetime
import hashlib
import secrets

from itsdangerous import URLSafeTimedSerializer

from . import config, mail
from .routers.deps import admin_key_hash_ok, is_staff_email

SESSION_TTL_SECONDS = 8 * 3600
MAX_FAILS = 3
LOCKOUT_SECONDS = 15 * 60
_SALT = "superlogin-session-v1"
_ALERT = "notifications@realifyai.app"


class SuperloginError(Exception):
    pass


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt):
    return dt.replace(microsecond=0).isoformat()


def _ser():
    return URLSafeTimedSerializer(config.SESSION_SECRET, salt=_SALT)


def issue_otp(con, email):
    email = email.lower().strip()
    code = f"{secrets.randbelow(1_000_000):06d}"
    con.execute("INSERT INTO superlogin_otp(email,code_hash,expires_at,used) VALUES(?,?,?,0)",
                (email, hashlib.sha256(code.encode()).hexdigest(),
                 _iso(_now() + datetime.timedelta(minutes=10))))
    con.commit()
    mail.send(email, "Your Realify superlogin code", f"Code: {code} — expires in 10 minutes.")
    return code


def _verify_otp(con, email, code):
    row = con.execute("SELECT id FROM superlogin_otp WHERE email=? AND code_hash=? AND used=0 "
                      "AND expires_at > ? ORDER BY id DESC LIMIT 1",
                      (email.lower().strip(), hashlib.sha256((code or "").encode()).hexdigest(),
                       _iso(_now()))).fetchone()
    if not row:
        return False
    con.execute("UPDATE superlogin_otp SET used=1 WHERE id=?", (row[0],))
    con.commit()
    return True


def is_locked(con, email):
    row = con.execute("SELECT locked_until FROM superlogin_lockout WHERE email=?",
                      (email.lower().strip(),)).fetchone()
    lu = row[0] if row else None
    return bool(lu and lu > _iso(_now()))


def _record_fail(con, email):
    email = email.lower().strip()
    row = con.execute("SELECT fails FROM superlogin_lockout WHERE email=?", (email,)).fetchone()
    fails = (row[0] if row else 0) + 1
    locked_until = _iso(_now() + datetime.timedelta(seconds=LOCKOUT_SECONDS)) if fails >= MAX_FAILS else None
    if row:
        con.execute("UPDATE superlogin_lockout SET fails=?, locked_until=? WHERE email=?",
                    (fails, locked_until, email))
    else:
        con.execute("INSERT INTO superlogin_lockout(email,fails,locked_until) VALUES(?,?,?)",
                    (email, fails, locked_until))
    con.commit()
    if locked_until:
        mail.send(_ALERT, "Superlogin lockout", f"{email} locked out after {fails} failed attempts.")
    return fails, locked_until


def _clear_fails(con, email):
    con.execute("DELETE FROM superlogin_lockout WHERE email=?", (email.lower().strip(),))
    con.commit()


def create_session(con, email, ip):
    email = email.lower().strip()
    exp = _now() + datetime.timedelta(seconds=SESSION_TTL_SECONDS)
    con.execute("INSERT INTO superlogin_sessions(email,ip,created_at,expires_at) VALUES(?,?,?,?)",
                (email, ip, _iso(_now()), _iso(exp)))          # ledger: who / when / IP
    con.commit()
    return _ser().dumps({"email": email}), _iso(exp)


def verify_session(token, max_age=SESSION_TTL_SECONDS):
    """Return the email if the signed session cookie is valid + unexpired; else None. This is NOT the
    app session — it authenticates ONLY the superlogin surface."""
    try:
        return _ser().loads(token, max_age=max_age).get("email")
    except Exception:
        return None


def authenticate(con, admin_key, email, otp_code, ip):
    """Full hardened flow. Returns {session, expires_at} or raises SuperloginError."""
    email = (email or "").lower().strip()
    if is_locked(con, email):
        raise SuperloginError("account temporarily locked")
    if admin_key_hash_ok(admin_key) and is_staff_email(email) and _verify_otp(con, email, otp_code):
        _clear_fails(con, email)
        token, exp = create_session(con, email, ip)
        return {"session": token, "expires_at": exp}
    fails, locked = _record_fail(con, email)
    raise SuperloginError(f"denied (fails={fails}{'; LOCKED' if locked else ''})")
