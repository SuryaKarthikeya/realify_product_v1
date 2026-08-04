"""Shared request dependencies for the API routers — the identity and authorization seam.

`current()` is the SINGLE place identity is resolved. Today it reads the app session cookie. The
Kratos + Google OIDC cutover (integration guide §3G) swaps the body here — validate the Kratos
session, map the verified identity to (uid, tid) — without touching any of the ~80 route handlers,
which only ever call `require_tenant()` / `current()`. It is written to be transport-agnostic so a
WebSocket handshake (guide §3H) can reuse the same resolution as an HTTP request.

Invariant: tenant_id is resolved server-side from a verified identity and is NEVER taken from a
client-supplied value. Keep it that way through any identity-provider change.
"""
import hashlib
import os
import secrets
from fastapi import HTTPException


def current(request):
    # The identity seam. Swap this body for Kratos `whoami` validation at cutover; everything
    # downstream that calls require_tenant()/current() stays unchanged.
    #
    # Service-to-service path (local integration): a trusted backend (e.g. the Realify bot)
    # presents a shared service key + an explicit tenant id in headers, instead of a browser
    # session cookie. Env-gated — inactive unless REALIFY_SERVICE_KEY is set to a strong value,
    # so it cannot be reached in an unconfigured/prod deploy. The tenant id still never comes
    # from an *unauthenticated* client; it is only honored once the service key matches.
    svc_key = (os.environ.get("REALIFY_SERVICE_KEY") or "").strip()
    if svc_key and svc_key not in _WEAK_ADMIN_KEYS and request.headers.get("x-realify-service") == svc_key:
        tid = request.headers.get("x-realify-tenant")
        if tid:
            return "service", (int(tid) if str(tid).isdigit() else tid)
    return request.session.get("uid"), request.session.get("tid")


def require_tenant(request):
    uid, tid = current(request)
    if not tid:
        raise HTTPException(status_code=401, detail="auth required")
    return tid


_WEAK_ADMIN_KEYS = {"", "dingbats2027", "changeme", "change-me", "admin", "password",
                    "secret", "realify", "test", "dev"}


def effective_admin_key():
    """The configured admin key, or "" if it is unset OR a known-weak/exposed value. A weak key is
    treated as unconfigured, so a leaked prototype default cannot be used — the operator must set a
    fresh strong key. When this returns "", all admin access is denied (fail closed)."""
    k = (os.environ.get("REALIFY_ADMIN_KEY") or "").strip()
    return "" if k.lower() in _WEAK_ADMIN_KEYS else k


def require_admin(request):
    """Admin gate: the shared admin key in the x-realify-admin header. Key-only — no tenant
    session required, so the operator console is reachable with just the key. A weak/unset key
    disables admin entirely (fail closed)."""
    admin_key = effective_admin_key()
    if not admin_key or request.headers.get("x-realify-admin") != admin_key:
        raise HTTPException(status_code=403, detail="admin required")
    return True


def _admin_key_ok(k):
    admin_key = effective_admin_key()
    return bool(admin_key) and k == admin_key


# ---- P0.9 /superlogin tourniquet ------------------------------------------
# The operator back door (/superlogin -> POST /api/signup) used to be public and minted PAID accounts
# for anyone. It is now gated behind a hashed admin key (env ADMIN_KEY_HASH, PBKDF2-HMAC-SHA256 to
# match realify.auth; argon2 waived per plan §1c) AND a @realify.ai staff-email allowlist. Fail closed:
# with ADMIN_KEY_HASH unset the back door does not exist. This is a stop-gap — full P7 hardening (staff
# OTP, short-lived separate session, ledgered logins, lockout) replaces it later.

_STAFF_EMAIL_DOMAIN = "@realify.ai"
_ADMIN_HASH_ITER = 200_000


def _pbkdf2(key, salt):
    return hashlib.pbkdf2_hmac("sha256", (key or "").encode(), (salt or "").encode(), _ADMIN_HASH_ITER).hex()


def admin_key_hash(key, salt=None):
    """Produce an ADMIN_KEY_HASH env value ('salt$hexhash') for a plaintext admin key. Run once to set
    the env var; the plaintext key itself is never stored."""
    salt = salt or secrets.token_hex(16)
    return f"{salt}${_pbkdf2(key, salt)}"


def admin_key_hash_ok(key):
    """Constant-time PBKDF2 check of a presented key against ADMIN_KEY_HASH ('salt$hexhash'). Fail
    closed: unset/malformed hash or empty key -> False (back door disabled)."""
    stored = (os.environ.get("ADMIN_KEY_HASH") or "").strip()
    if not stored or "$" not in stored or not key:
        return False
    salt, expected = stored.split("$", 1)
    return secrets.compare_digest(_pbkdf2(key, salt), expected)


def is_staff_email(email):
    """True only for @realify.ai addresses — the back-door signup allowlist."""
    return (email or "").strip().lower().endswith(_STAFF_EMAIL_DOMAIN)


def superlogin_key_ok(request, body_key=None):
    """A valid admin key presented via the x-realify-admin header OR a request body field. Any one
    suffices; all are PBKDF2-checked. The admin key is NEVER read from the URL (?key=) — a key in the
    query string leaks into access logs, browser history, and the Referer header (R10.1 hardening)."""
    presented = (request.headers.get("x-realify-admin")
                 or body_key or "")
    return admin_key_hash_ok(presented)
