"""SES bounce/complaint suppression (agency-plan P6 rider). Hard bounces + complaints (from SES via
SNS / a config-set webhook) are added to suppression_list, which the mail abstraction checks before
EVERY send. Global (email-keyed), not brand-scoped."""
from .. import dbengine


def add(cur, email, reason):
    cur.execute("INSERT INTO suppression_list(email, reason) VALUES(%s,%s) ON CONFLICT (email) DO NOTHING",
                (email.lower().strip(), reason))


def is_suppressed(email):
    """True if the address is suppressed. Cheap + safe: no-op (False) when there's no Postgres backend
    (so the SQLite dev suite and the mail abstraction are unaffected)."""
    if not email or dbengine.dialect() != "postgresql":
        return False
    try:
        from .db import agency_connect
        conn = agency_connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM suppression_list WHERE email=%s", (email.lower().strip(),))
            return cur.fetchone() is not None
        finally:
            conn.close()
    except Exception:
        return False


def handle_ses_notification(cur, msg):
    """Parse an SES/SNS notification; suppress hard bounces + complaints. Returns the emails added.
    Reason is 'hard_bounce' for Permanent bounces and 'complaint' for complaints (transient/soft
    bounces are NOT suppressed)."""
    ntype = msg.get("notificationType") or msg.get("eventType")
    emails, reason = [], (ntype or "").lower()
    if ntype == "Bounce" and (msg.get("bounce", {}).get("bounceType") == "Permanent"):
        emails = [r["emailAddress"] for r in msg["bounce"].get("bouncedRecipients", [])]
        reason = "hard_bounce"
    elif ntype == "Complaint":
        emails = [r["emailAddress"] for r in msg["complaint"].get("complainedRecipients", [])]
        reason = "complaint"
    for e in emails:
        add(cur, e, reason)
    return emails
