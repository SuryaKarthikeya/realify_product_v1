"""Platform policy switches for the agency console — simple key/value backed by `sandbox_settings`
(the same realify_app-granted k/v the email short-circuit uses, migration 0034). Distinct from `gates`
(which is the attestation engine with provenance/expiry); these are plain operator on/off toggles.

R18.1 — `agency_self_approve`: whether an agency may impersonate the brand's consent click (approve the
engagement on the brand's behalf, using the access the brand already handed them offline). DEFAULT ON.
When OFF, the brand must approve through the OTP consent flow. Either way the brand still gets an email —
the copy differs (FYI-we're-managing vs please-approve), see routers/agency_consent.py.
"""
SELF_APPROVE_KEY = "agency_self_approve"


def _get(cur, key, default):
    cur.execute("SELECT value FROM sandbox_settings WHERE key=%s", (key,))
    r = cur.fetchone()
    return r[0] if r and r[0] is not None else default


def _set(cur, key, value):
    cur.execute("INSERT INTO sandbox_settings(key,value) VALUES(%s,%s) "
                "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value, updated_at=now()", (key, value))


def self_approve_on(cur):
    """Agencies may impersonate brand approvals. Unset defaults to ON (the R18.1 product decision)."""
    return _get(cur, SELF_APPROVE_KEY, "on") == "on"


def set_self_approve(cur, on):
    _set(cur, SELF_APPROVE_KEY, "on" if on else "off")
    return self_approve_on(cur)
