"""Brand consent flow (agency-plan P3). A brand receives a single-use, 7-day, OTP-gated link and picks
an envelope template + per-lens autonomy ceilings, or counters, or declines. On grant (or the agency
accepting a counter in one click) the chosen caps are published as a P1 envelope for the engagement.

State machine: invited -> viewed -> granted | countered | declined | expired.
Every mutating action is email-OTP gated; illegal transitions raise ConsentStateError (route -> 409).
"""
import datetime
import hashlib
import json
import secrets

from . import otp, ops, tenancy, ledger
from ..pdp import ENVELOPES, LENSES

CONSENT_TTL_DAYS = 7
STATES = ("invited", "viewed", "granted", "countered", "declined", "expired")
TERMINAL = ("granted", "declined", "expired")


class ConsentStateError(Exception):
    """Illegal/invalid consent transition — the route maps this to HTTP 409."""


def _now():
    return datetime.datetime.now(datetime.timezone.utc)


def _hash(token):
    return hashlib.sha256((token or "").encode()).hexdigest()


def resolve_or_create_brand(cur, tenant_id, brand_name, email, country=None):
    """The brand tenant to invite. If a valid existing tenant_id is passed, use it (onboarding a brand
    that already has a Realify account). Otherwise CREATE a managed brand tenant — agency-direct
    onboarding by name, no internal tenant id needed.

    The new brand is created UNPROVISIONED (provisioned=0) + account_type='customer' + a stored `country`:
      • provisioned=0 — it has NO data yet, so drilling in lands the agency on the ONBOARDING WIZARD, not
        a fabricated interior (empty brands used to show sample Profit&Ads / hash-synthesized analyst /
        seeded demo categories). Provisioning flips to 'uploaded' when data is loaded through the wizard.
      • account_type='customer' — the real report-upload endpoints (/api/onboard/reports) gate on this.
      • country — so the fleet card + interior localize currency (US $ vs IN ₹); without it everything
        defaulted to USD/$.
    tenants is non-RLS; realify_app holds INSERT + sequence usage (migration 0015)."""
    if tenant_id:
        cur.execute("SELECT id FROM tenants WHERE id=%s", (int(tenant_id),))
        if cur.fetchone():
            return int(tenant_id)
    from .. import country as _country
    code = _country.normalize(country)
    name = (brand_name or "").strip() or (email.split("@")[0] if email else "New brand")
    cur.execute("INSERT INTO tenants(name,created_at,provisioned,tenant_kind,account_type) "
                "VALUES(%s,now()::text,0,'seller','customer') RETURNING id", (name,))
    tid = cur.fetchone()[0]
    cur.execute("INSERT INTO tenant_settings(tenant_id,key,value) VALUES(%s,'country',%s) "
                "ON CONFLICT (tenant_id,key) DO UPDATE SET value=EXCLUDED.value", (tid, code))
    return tid


def create_consent(cur, agency_id, tenant_id, agency_name, email, template, ceilings=None,
                   ttl_days=CONSENT_TTL_DAYS):
    token = secrets.token_urlsafe(24)
    cur.execute(
        "INSERT INTO brand_consents(agency_id,tenant_id,agency_name,email,token_hash,envelope_template,"
        "ceilings,expires_at) VALUES(%s::uuid,%s,%s,%s,%s,%s,%s::jsonb,%s) RETURNING id",
        (agency_id, tenant_id, agency_name, email, _hash(token), template,
         json.dumps(ceilings or {}), _now() + datetime.timedelta(days=ttl_days)))
    return token, cur.fetchone()[0]


def _load(cur, token):
    cur.execute("SELECT id,agency_id,tenant_id,email,status,envelope_template,ceilings,counter,expires_at "
                "FROM brand_consents WHERE token_hash=%s", (_hash(token),))
    row = cur.fetchone()
    if not row:
        return None
    cols = ["id", "agency_id", "tenant_id", "email", "status", "envelope_template", "ceilings",
            "counter", "expires_at"]
    return dict(zip(cols, row))


def page_context(cur, token):
    """Non-mutating lookup for RENDERING the consent page (no OTP). Returns display fields or None."""
    cur.execute("SELECT agency_name, email, status, envelope_template, ceilings, expires_at "
                "FROM brand_consents WHERE token_hash=%s", (_hash(token),))
    row = cur.fetchone()
    if not row:
        return None
    return {"agency_name": row[0], "email": row[1], "status": row[2], "template": row[3],
            "ceilings": row[4], "expires_at": row[5]}


def _active(cur, token):
    c = _load(cur, token)
    if c is None:
        raise ConsentStateError("invalid link")
    if c["expires_at"] <= _now():
        if c["status"] not in TERMINAL:
            cur.execute("UPDATE brand_consents SET status='expired' WHERE id=%s", (c["id"],))
        raise ConsentStateError("expired")
    if c["status"] in TERMINAL:
        raise ConsentStateError(f"link already {c['status']}")   # single-use: no acting after terminal
    return c


def _otp(cur, email, code):
    if not otp.verify(cur, email, code):
        raise ConsentStateError("otp required")


def request_otp(cur, token, send=True):
    """Issue an OTP to the consent email (identity check). Returns the code (tests read it)."""
    c = _active(cur, token)
    return otp.issue(cur, c["email"], send=send)


def _set(cur, cid, status, **fields):
    sets = ["status=%s"]
    vals = [status]
    for k, v in fields.items():
        sets.append(f"{k}=%s" + ("::jsonb" if k in ("ceilings", "counter") else ""))
        vals.append(json.dumps(v) if k in ("ceilings", "counter") else v)
    vals.append(cid)
    cur.execute(f"UPDATE brand_consents SET {', '.join(sets)} WHERE id=%s", tuple(vals))


def view(cur, token, code):
    c = _active(cur, token)
    _otp(cur, c["email"], code)
    if c["status"] == "invited":
        _set(cur, c["id"], "viewed", viewed_at=_now())
    return _load(cur, token)


def seen(cur, token):
    """Mark the consent VIEWED when the recipient OPENS the link (no OTP — merely opening it is not a
    consent action). Idempotent; a no-op once viewed/terminal. This is what progresses the state machine
    invited -> viewed: without it the page GET left the consent 'invited', and grant/counter/decline
    (which required 'viewed') 409'd for a recipient who followed the emailed link normally."""
    c = _load(cur, token)
    if c and c["status"] == "invited":
        _set(cur, c["id"], "viewed", viewed_at=_now())


def _apply_ceilings(template, ceilings):
    """Caps = template, with each lens's autonomy_ceiling lowered to the brand's requested ceiling
    (a brand may tighten but never exceed the template)."""
    caps = {lens: dict(spec) for lens, spec in ENVELOPES[template].items()}
    for lens, want in (ceilings or {}).items():
        if lens in caps:
            caps[lens]["autonomy_ceiling"] = min(int(caps[lens]["autonomy_ceiling"]), int(want))
    return caps


def _coerce_agency_id(agency_id):
    """engagements.agency_id is uuid; a request string won't implicitly cast to uuid on INSERT, so adapt
    it to a uuid.UUID (DB reads already hand us one)."""
    import uuid
    return agency_id if not isinstance(agency_id, str) else uuid.UUID(agency_id)


def _ensure_engagement(cur, agency_id, tenant_id):
    agency_id = _coerce_agency_id(agency_id)
    cur.execute("SELECT id FROM engagements WHERE agency_id=%s AND tenant_id=%s", (agency_id, tenant_id))
    row = cur.fetchone()
    if row:
        return row[0]
    return ops.create_engagement(cur, None, agency_id, tenant_id)


def ensure_engagement(cur, agency_id, tenant_id):
    """Agency-direct onboarding: put the brand in the agency's book NOW (create the engagement if absent),
    so it appears on the fleet and the agency can connect its data on the brand's behalf immediately —
    WITHOUT publishing an envelope, so nothing EXECUTES until the brand grants consent (grant publishes
    the envelope). Sets brand scope first (engagements is RLS-scoped under the runtime role)."""
    tenancy.set_brand_scope(cur, [tenant_id])
    return _ensure_engagement(cur, agency_id, tenant_id)


def _publish(cur, c, template, ceilings):
    tenancy.set_brand_scope(cur, [c["tenant_id"]])
    eid = _ensure_engagement(cur, c["agency_id"], c["tenant_id"])
    caps = _apply_ceilings(template, ceilings)
    ops.publish_envelope(cur, None, eid, c["tenant_id"], caps, ceilings or {})
    return eid


def grant(cur, token, code, template=None, ceilings=None):
    c = _active(cur, token)
    _otp(cur, c["email"], code)
    if c["status"] != "viewed":                            # opening the link marks 'viewed' (consent.seen),
        raise ConsentStateError(f"cannot grant from {c['status']}")   # so the real page flow reaches here
    template = template or c["envelope_template"]
    ceilings = ceilings if ceilings is not None else (c["ceilings"] or {})
    eid = _publish(cur, c, template, ceilings)
    _set(cur, c["id"], "granted", engagement_id=eid, envelope_template=template, ceilings=ceilings)
    return {"status": "granted", "engagement_id": str(eid)}


def impersonate_grant(cur, consent_id, actor_user=None):
    """R9 email short-circuit (SANDBOX only — the route enforces the tenant is sandbox). Complete a
    pending consent server-side EXACTLY as a real recipient click would (invited/viewed → granted,
    same envelope publish + state), but WITHOUT the emailed OTP — the recipient is being impersonated.
    Ledgered as impersonated. Returns {status, engagement_id}."""
    cur.execute("SELECT id,agency_id,tenant_id,email,status,envelope_template,ceilings,counter,expires_at "
                "FROM brand_consents WHERE id=%s", (consent_id,))
    row = cur.fetchone()
    if not row:
        raise ConsentStateError("no such consent")
    cols = ["id", "agency_id", "tenant_id", "email", "status", "envelope_template", "ceilings",
            "counter", "expires_at"]
    c = dict(zip(cols, row))
    if c["status"] in TERMINAL:
        raise ConsentStateError(f"link already {c['status']}")
    template = c["envelope_template"]
    ceilings = c["ceilings"] or {}
    eid = _publish(cur, c, template, ceilings)
    _set(cur, c["id"], "granted", engagement_id=eid, envelope_template=template, ceilings=ceilings)
    ledger.append(cur, c["tenant_id"], actor_user, "consent.grant.impersonated",
                  payload={"email": c["email"], "template": template}, engagement_id=eid)
    return {"status": "granted", "engagement_id": str(eid), "impersonated": True}


def counter(cur, token, code, ceilings):
    c = _active(cur, token)
    _otp(cur, c["email"], code)
    if c["status"] != "viewed":
        raise ConsentStateError(f"cannot counter from {c['status']}")
    _set(cur, c["id"], "countered", counter=ceilings)
    return {"status": "countered"}


def decline(cur, token, code):
    c = _active(cur, token)
    _otp(cur, c["email"], code)
    if c["status"] != "viewed":
        raise ConsentStateError(f"cannot decline from {c['status']}")
    _set(cur, c["id"], "declined")
    return {"status": "declined"}


def accept_counter(cur, consent_id):
    """Agency one-click acceptance of a brand counter -> publish the countered ceilings, grant."""
    cur.execute("SELECT id,agency_id,tenant_id,email,status,envelope_template,ceilings,counter,expires_at "
                "FROM brand_consents WHERE id=%s", (consent_id,))
    row = cur.fetchone()
    if not row:
        raise ConsentStateError("invalid consent")
    cols = ["id", "agency_id", "tenant_id", "email", "status", "envelope_template", "ceilings",
            "counter", "expires_at"]
    c = dict(zip(cols, row))
    if c["status"] != "countered":
        raise ConsentStateError(f"cannot accept from {c['status']}")
    ceilings = c["counter"] or {}
    eid = _publish(cur, c, c["envelope_template"], ceilings)
    _set(cur, c["id"], "granted", engagement_id=eid, ceilings=ceilings)
    return {"status": "granted", "engagement_id": str(eid)}
