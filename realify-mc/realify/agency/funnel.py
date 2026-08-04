"""Agency intake funnel: validation (+ honeypot), request creation, and the status state machine.

States: received -> in_review -> (approved -> provisioning -> live) | declined. The applicant status
page renders a fixed timeline (received, in-review, decision, live) with the current state marked.
"""
import secrets
import string

VALID_COUNTRIES = ("US", "IN")
STATUSES = ("received", "in_review", "approved", "declined", "provisioning", "live")
# Fixed applicant-facing timeline (screen 3): each maps to the reached-by set of internal statuses.
TIMELINE = [
    ("received", {"received", "in_review", "approved", "provisioning", "live", "declined"}),
    ("in_review", {"in_review", "approved", "provisioning", "live", "declined"}),
    ("decision", {"approved", "provisioning", "live", "declined"}),
    ("live", {"live"}),
]
_REF_ALPHABET = string.ascii_uppercase + string.digits


class IntakeError(ValueError):
    pass


class HoneypotError(IntakeError):
    """Honeypot field was filled — silently drop (never tip off bots)."""


def validate_intake(form):
    """Validate a public intake submission. Returns a cleaned dict or raises IntakeError. `form` is a
    dict of raw fields (incl. the honeypot). Honeypot filled => HoneypotError (caller drops silently)."""
    # Honeypot is `website_hp` (R5: `website` is now a REAL field — the agency's website). A bot that
    # fills the hidden decoy is dropped silently (no row, no signal).
    if (form.get("website_hp") or "").strip():
        raise HoneypotError("rejected")
    name = (form.get("agency_name") or "").strip()
    email = (form.get("contact_email") or "").strip().lower()
    country = (form.get("hq_country") or "").strip().upper()
    if not name:
        raise IntakeError("Agency name is required.")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise IntakeError("A valid contact email is required.")
    if country not in VALID_COUNTRIES:
        raise IntakeError("HQ country must be US or IN.")
    headcount = form.get("am_headcount")
    try:
        headcount = int(headcount) if headcount not in (None, "") else None
    except (TypeError, ValueError):
        raise IntakeError("Account-manager headcount must be a number.")
    if headcount is not None and headcount < 0:
        raise IntakeError("Account-manager headcount must be a number.")
    g = lambda k: ((form.get(k) or "").strip() or None)
    return {
        "agency_name": name,
        "contact_name": g("contact_name"),
        "contact_email": email,
        "hq_country": country,
        "am_headcount": headcount,
        "reporting_hours": g("reporting_hours"),
        "website": g("website"),
        "book_size": g("book_size"),
        "marketplaces": g("marketplaces"),
        "ad_platforms": g("ad_platforms"),
        "current_tool": g("current_tool"),
        "target_start": g("target_start"),
    }


def new_request_notification(ref, cleaned, ops_url):
    """R16 — the OPERATOR 'new agency request' notification: (subject, text_body, html_body). Sent to
    mailcfg.ops_recipient() on real intake with the agency details + a link to the admin review queue.
    HTML is branded (warm system, inline styles for email clients); text is the accessible fallback."""
    import html as _h
    book = cleaned.get("am_headcount")
    book_line = f"{book} account manager(s)" if book is not None else "not provided"
    contact = f"{cleaned.get('contact_name') or '—'} <{cleaned['contact_email']}>"
    subject = f"New agency request: {cleaned['agency_name']} ({ref})"
    body = (
        "A new Realify for Agencies request was submitted.\n\n"
        f"Agency:     {cleaned['agency_name']}\n"
        f"Book size:  {book_line}\n"
        f"HQ country: {cleaned['hq_country']}\n"
        f"Contact:    {contact}\n"
        f"Reference:  {ref}\n\n"
        f"Review & provision: {ops_url}\n")
    rows = "".join(
        f"<tr><td style='padding:4px 14px 4px 0;color:#6E675C'>{k}</td>"
        f"<td style='padding:4px 0;color:#1A1A1A;font-weight:600'>{_h.escape(str(v))}</td></tr>"
        for k, v in (("Agency", cleaned["agency_name"]), ("Book size", book_line),
                     ("HQ country", cleaned["hq_country"]), ("Contact", contact), ("Reference", ref)))
    html_body = (
        "<div style=\"font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"
        "background:#F7F4EE;padding:28px;color:#1A1A1A\">"
        "<div style=\"max-width:520px;margin:0 auto;background:#fff;border:1px solid #E4DDD0;"
        "border-radius:14px;overflow:hidden\">"
        "<div style=\"background:#1A1A1A;color:#fff;padding:16px 22px;font-weight:700\">Realify · new agency request</div>"
        "<div style=\"padding:22px\">"
        "<p style=\"margin:0 0 14px;color:#6E675C\">A new <b style='color:#1A1A1A'>Realify for Agencies</b> "
        "application was submitted and is waiting in your review queue.</p>"
        f"<table style=\"border-collapse:collapse;font-size:14px;margin-bottom:20px\">{rows}</table>"
        f"<a href=\"{_h.escape(ops_url)}\" style=\"display:inline-block;background:#C4785B;color:#fff;"
        "text-decoration:none;padding:11px 22px;border-radius:9px;font-weight:600\">Review &amp; provision →</a>"
        "</div></div></div>")
    return subject, body, html_body


def _new_ref():
    return "AG-" + "".join(secrets.choice(_REF_ALPHABET) for _ in range(8))


def create_request(cur, cleaned):
    """Insert a validated request; returns its ref. R16 — IDEMPOTENT by contact_email while a request is
    still OPEN (received/provisioning): a duplicate submit UPDATES/reuses that row instead of spawning a
    second application (a resubmit or double-click must not create duplicates in the review queue)."""
    cur.execute("SELECT ref FROM agency_requests WHERE contact_email=%s AND status IN "
                "('received','provisioning') ORDER BY created_at DESC LIMIT 1", (cleaned["contact_email"],))
    dup = cur.fetchone()
    if dup:
        cur.execute(
            "UPDATE agency_requests SET agency_name=%s,contact_name=%s,hq_country=%s,am_headcount=%s,"
            "reporting_hours=%s,website=%s,book_size=%s,marketplaces=%s,ad_platforms=%s,current_tool=%s,"
            "target_start=%s,updated_at=now() WHERE ref=%s",
            (cleaned["agency_name"], cleaned["contact_name"], cleaned["hq_country"], cleaned["am_headcount"],
             cleaned["reporting_hours"], cleaned.get("website"), cleaned.get("book_size"),
             cleaned.get("marketplaces"), cleaned.get("ad_platforms"), cleaned.get("current_tool"),
             cleaned.get("target_start"), dup[0]))
        return dup[0]
    ref = _new_ref()
    cur.execute(
        "INSERT INTO agency_requests(ref,agency_name,contact_name,contact_email,hq_country,"
        "am_headcount,reporting_hours,website,book_size,marketplaces,ad_platforms,current_tool,"
        "target_start,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'received') RETURNING ref",
        (ref, cleaned["agency_name"], cleaned["contact_name"], cleaned["contact_email"],
         cleaned["hq_country"], cleaned["am_headcount"], cleaned["reporting_hours"],
         cleaned.get("website"), cleaned.get("book_size"), cleaned.get("marketplaces"),
         cleaned.get("ad_platforms"), cleaned.get("current_tool"), cleaned.get("target_start")))
    return cur.fetchone()[0]


def get_request(cur, ref):
    cur.execute(
        "SELECT id,ref,agency_name,contact_name,contact_email,hq_country,am_headcount,reporting_hours,"
        "status,agency_id,decline_reason FROM agency_requests WHERE ref=%s", (ref,))
    row = cur.fetchone()
    if not row:
        return None
    cols = ["id", "ref", "agency_name", "contact_name", "contact_email", "hq_country",
            "am_headcount", "reporting_hours", "status", "agency_id", "decline_reason"]
    return dict(zip(cols, row))


def set_status(cur, request_id, status):
    if status not in STATUSES:
        raise ValueError(f"invalid status {status!r}")
    cur.execute("UPDATE agency_requests SET status=%s, updated_at=now() WHERE id=%s", (status, request_id))


def timeline(status):
    """The applicant timeline for a request status: [{step, state}] where state is done|current|pending,
    and a declined request marks the decision step 'declined'."""
    out = []
    for step, reached_by in TIMELINE:
        if status == "declined" and step == "decision":
            out.append({"step": step, "state": "declined"})
        elif status == "declined" and step == "live":
            out.append({"step": step, "state": "pending"})
        elif status in reached_by:
            out.append({"step": step, "state": "done" if step != _current_step(status) else "current"})
        else:
            out.append({"step": step, "state": "pending"})
    return out


def _current_step(status):
    return {"received": "received", "in_review": "in_review", "approved": "decision",
            "provisioning": "decision", "live": "live", "declined": "decision"}.get(status)
