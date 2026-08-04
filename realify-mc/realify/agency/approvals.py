"""Propose -> approve (maker-checker) -> co-sign -> execute (agency-plan P5). Maker-checker threshold
is per-engagement; when the proposed impact meets it, a DISTINCT checker must approve. Where the
envelope requires brand co-sign, approval enters a 5-day co-sign window that NEVER auto-executes — an
expiry cancels and notifies the agency (silence never executes). Nudges are Realify-delivered, hard
cap 2 per request. Every state change is ledgered. Brand-scoped: caller sets the brand scope."""
import datetime
import hashlib
import json
import secrets

from itsdangerous import URLSafeTimedSerializer

from . import ledger, tenancy
from .. import mail, config

NUDGE_CAP = 2
COSIGN_TTL_DAYS = 5
DEEPLINK_TTL_DAYS = 7
TERMINAL = ("expired", "rejected", "executed", "canceled")   # approval no longer actionable
_OTP_SKIP_TTL = 30 * 24 * 3600
_OTP_SKIP_SALT = "agency-otp-skip"


class ApprovalError(Exception):
    """Illegal approval transition / policy violation (route -> 409)."""


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def _threshold(cur, engagement_id):
    cur.execute("SELECT maker_checker_threshold_usd_minor FROM engagements WHERE id=%s", (engagement_id,))
    row = cur.fetchone()
    return int(row[0]) if row else 0


_COSIGN_LENSES = ("pricing",)      # price changes are high-stakes -> always brand-cosigned


def cosign_required(cur, engagement_id, lens, kind, impact_usd_minor):
    """Derive brand co-sign from the engagement's rules (R2 — replaces the hardcoded True): co-sign iff
    a pricing-lens change, OR the amount meets the engagement's brand_cosign_threshold (0 = disabled)."""
    if lens in _COSIGN_LENSES:
        return True
    cur.execute("SELECT COALESCE(brand_cosign_threshold_usd_minor,0) FROM engagements WHERE id=%s",
                (engagement_id,))
    row = cur.fetchone()
    thr = int(row[0]) if row else 0
    return thr > 0 and int(impact_usd_minor) >= thr


def propose(cur, tenant_id, engagement_id, maker_user, lens, kind, signal, impact_usd_minor,
            requires_cosign=False, envelope_version=None, context=None):
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute(
        "INSERT INTO approvals(tenant_id,engagement_id,lens,kind,signal,impact_usd_minor,maker_user,"
        "requires_cosign,envelope_version,context,status) "
        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,'proposed') RETURNING id",
        (tenant_id, engagement_id, lens, kind, signal, int(impact_usd_minor), maker_user,
         bool(requires_cosign), envelope_version, json.dumps(context or {})))
    aid = cur.fetchone()[0]
    ledger.append(cur, tenant_id, maker_user, "approval.propose", payload={"approval_id": aid, "lens": lens},
                  engagement_id=engagement_id, envelope_version=envelope_version)
    return aid


def _load(cur, approval_id):
    cur.execute("SELECT id,tenant_id,engagement_id,impact_usd_minor,maker_user,checker_user,"
                "requires_cosign,status,cosign_expires_at,nudge_count,context,envelope_version "
                "FROM approvals WHERE id=%s", (approval_id,))
    row = cur.fetchone()
    if not row:
        raise ApprovalError("no such approval")
    cols = ["id", "tenant_id", "engagement_id", "impact_usd_minor", "maker_user", "checker_user",
            "requires_cosign", "status", "cosign_expires_at", "nudge_count", "context", "envelope_version"]
    return dict(zip(cols, row))


def approve(cur, approval_id, checker_user):
    """Maker-checker: at/above the engagement threshold a DISTINCT checker is required. Moves to
    'approved', or 'cosign_pending' (5-day TTL) when brand co-sign is required."""
    a = _load(cur, approval_id)
    if a["status"] != "proposed":
        raise ApprovalError(f"cannot approve from {a['status']}")
    if a["impact_usd_minor"] >= _threshold(cur, a["engagement_id"]) and checker_user == a["maker_user"]:
        raise ApprovalError("maker-checker: a different user must approve at/above the threshold")
    if a["requires_cosign"]:
        exp = _now() + datetime.timedelta(days=COSIGN_TTL_DAYS)
        cur.execute("UPDATE approvals SET status='cosign_pending', checker_user=%s, cosign_expires_at=%s,"
                    " updated_at=now() WHERE id=%s", (checker_user, exp, approval_id))
        status = "cosign_pending"
    else:
        cur.execute("UPDATE approvals SET status='approved', checker_user=%s, updated_at=now() WHERE id=%s",
                    (checker_user, approval_id))
        status = "approved"
    ledger.append(cur, a["tenant_id"], checker_user, "approval.approve",
                  payload={"approval_id": approval_id, "status": status}, engagement_id=a["engagement_id"])
    return {"status": status}


def cosign(cur, approval_id, brand_user=None):
    a = _load(cur, approval_id)
    if a["status"] != "cosign_pending":
        raise ApprovalError(f"cannot co-sign from {a['status']}")
    cur.execute("UPDATE approvals SET status='approved', updated_at=now() WHERE id=%s", (approval_id,))
    ledger.append(cur, a["tenant_id"], brand_user, "approval.cosign", payload={"approval_id": approval_id},
                  engagement_id=a["engagement_id"])
    return {"status": "approved"}


def expire_cosigns(cur, allowed_tenant_ids, agency_email="agency@example.com"):
    """Job: co-sign windows past TTL are CANCELED (never executed) and the agency is notified. Returns
    the number expired. Re-requests reuse the preserved context (approvals.context)."""
    tenancy.set_brand_scope(cur, allowed_tenant_ids)
    cur.execute("SELECT id, tenant_id, engagement_id FROM approvals "
                "WHERE status='cosign_pending' AND cosign_expires_at < now()")
    rows = cur.fetchall()
    for aid, tid, eng in rows:
        cur.execute("UPDATE approvals SET status='expired', updated_at=now() WHERE id=%s", (aid,))
        ledger.append(cur, tid, None, "approval.cosign_expired", payload={"approval_id": aid},
                      engagement_id=eng)
        mail.send(agency_email, "A brand co-sign request expired",
                  f"Approval {aid} expired without brand co-sign and was NOT executed. Re-request to "
                  f"try again (prior context is preserved).", reply_to="notifications@realifyai.app")
    return len(rows)


def nudge(cur, approval_id):
    """Realify-delivered nudge; hard cap NUDGE_CAP per request (3rd rejected)."""
    a = _load(cur, approval_id)
    if a["nudge_count"] >= NUDGE_CAP:
        raise ApprovalError(f"nudge cap ({NUDGE_CAP}) reached")
    cur.execute("UPDATE approvals SET nudge_count=nudge_count+1, updated_at=now() WHERE id=%s", (approval_id,))
    ledger.append(cur, a["tenant_id"], None, "approval.nudge",
                  payload={"approval_id": approval_id, "n": a["nudge_count"] + 1}, engagement_id=a["engagement_id"])
    return {"nudge_count": a["nudge_count"] + 1}


def escalate(cur, approval_id):
    a = _load(cur, approval_id)
    cur.execute("UPDATE approvals SET escalated=true, updated_at=now() WHERE id=%s", (approval_id,))
    ledger.append(cur, a["tenant_id"], None, "approval.escalate", payload={"approval_id": approval_id},
                  engagement_id=a["engagement_id"])
    return {"escalated": True}


# ---- hardened mobile approval deep-link + signed OTP-skip cookie (agency-plan P6 item 8) ----
def create_deeplink(cur, approval_id, user_id):
    """Issue a 256-bit deep-link token bound to (approval, user), expiring with the approval. Stored
    only as a SHA-256 hash. Returns the raw token."""
    a = _load(cur, approval_id)
    token = secrets.token_urlsafe(32)               # 256-bit >= 128-bit requirement
    exp = a["cosign_expires_at"] or (_now() + datetime.timedelta(days=DEEPLINK_TTL_DAYS))
    cur.execute("UPDATE approvals SET deeplink_token_hash=%s, deeplink_user_id=%s, deeplink_expires_at=%s "
                "WHERE id=%s", (hashlib.sha256(token.encode()).hexdigest(), user_id, exp, approval_id))
    return token


def resolve_deeplink(cur, approval_id, token):
    """Return the bound user_id iff `token` matches the issued (approval,user) deep-link AND the approval
    is still live; else None. Identity comes from the signed token binding, not from the client — so the
    approver is whoever the deep link was issued to. Constant-time hash comparison against the stored hash
    (never a non-empty check)."""
    a = _load(cur, approval_id)
    if a["status"] in TERMINAL:
        return None
    cur.execute("SELECT deeplink_token_hash, deeplink_user_id, deeplink_expires_at FROM approvals WHERE id=%s",
                (approval_id,))
    row = cur.fetchone()
    if not row:
        return None
    h, uid, exp = row
    if not h or uid is None or not token:
        return None
    if exp is not None and exp <= _now():
        return None
    if not secrets.compare_digest(h, hashlib.sha256(token.encode()).hexdigest()):
        return None
    return uid


def validate_deeplink(cur, approval_id, user_id, token):
    """True iff the token matches, is for THIS user, and the approval is still live (expires WITH it)."""
    a = _load(cur, approval_id)
    if a["status"] in TERMINAL:
        return False
    cur.execute("SELECT deeplink_token_hash, deeplink_user_id, deeplink_expires_at FROM approvals WHERE id=%s",
                (approval_id,))
    h, uid, exp = cur.fetchone()
    if not h or uid != user_id:
        return False
    if exp is not None and exp <= _now():
        return False
    return secrets.compare_digest(h, hashlib.sha256((token or "").encode()).hexdigest())


def _otp_skip_serializer():
    return URLSafeTimedSerializer(config.SESSION_SECRET, salt=_OTP_SKIP_SALT)


def make_otp_skip_token():
    """A SIGNED device token whose ONLY meaning is 'this device recently passed OTP'. It carries no
    user identity and can never authenticate a session — identity always comes from the app session."""
    return _otp_skip_serializer().dumps({"otp_skip": True})


def verify_otp_skip_token(token, max_age=_OTP_SKIP_TTL):
    try:
        data = _otp_skip_serializer().loads(token, max_age=max_age)
        return data == {"otp_skip": True}
    except Exception:
        return False


def mark_viewed(cur, approval_id):
    """Record first view (mobile deep link / cockpit open) — the cockpit's viewed/not-viewed signal."""
    cur.execute("UPDATE approvals SET viewed_at=now() WHERE id=%s AND viewed_at IS NULL", (approval_id,))


def pending(cur, allowed_tenant_ids):
    """Cockpit: pending approvals across the book, SORTED BY EXPIRY ASC (the 5-day clock is the point;
    NULL expiry — 'proposed', pre-cosign — sorts last). Carries days-to-expiry + viewed signal."""
    if not allowed_tenant_ids:
        return []
    tenancy.set_brand_scope(cur, allowed_tenant_ids)
    cur.execute("SELECT id,tenant_id,lens,kind,impact_usd_minor,status,cosign_expires_at,nudge_count,"
                "escalated,viewed_at FROM approvals WHERE status IN ('proposed','cosign_pending') "
                "ORDER BY cosign_expires_at ASC NULLS LAST, id")
    out = []
    for aid, tid, lens, kind, impact, status, exp, nudges, esc, viewed in cur.fetchall():
        days = (exp - _now()).days if exp is not None else None
        out.append({"id": aid, "tenant_id": tid, "lens": lens, "kind": kind, "impact_usd_minor": impact,
                    "status": status, "days_to_expiry": days, "nudge_count": nudges, "escalated": esc,
                    "viewed": viewed is not None})
    return out
