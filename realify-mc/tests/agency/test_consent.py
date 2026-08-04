"""P3 brand consent (route-level): T-P3-01 single-use/expiry/OTP-gated, T-P3-02 state machine
(legal transitions + illegal ⇒ 409), T-P3-03 counter round trip."""
import re

from realify.agency import consent, tenancy
from realify.mail import dev


def _mk(cur):
    cur.execute("INSERT INTO agencies(name) VALUES('Acme') RETURNING id")
    ag = cur.fetchone()[0]
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('Brand',now()::text,1) RETURNING id")
    t = cur.fetchone()[0]
    return ag, t


def _invite(client, H, owner_conn, email, template="Advise"):
    cur = owner_conn.cursor()
    ag, t = _mk(cur)
    owner_conn.commit()
    r = client.post("/api/agencies/consent/invite", headers=H,
                    json={"agency_id": str(ag), "tenant_id": t, "agency_name": "Acme",
                          "email": email, "template": template})
    assert r.status_code == 200, r.text
    body = dev.inbox(to=email)[-1]["body"]
    token = re.search(r"/consent/([A-Za-z0-9_-]+)", body).group(1)
    # assert the via-Realify From + Reply-To + agency name leading
    hdrs = dev.inbox(to=email)[-1]["headers"]
    assert "Acme" in hdrs["from_addr"] and "realifyai.app" in hdrs["from_addr"]
    assert hdrs["reply_to"]
    return ag, t, token


def _otp(client, token, email):
    dev.clear()
    assert client.post(f"/api/consent/{token}/otp").status_code == 200
    return re.search(r"\b(\d{6})\b", dev.inbox(to=email)[-1]["body"]).group(1)


# ---- T-P3-01 ----
def test_link_is_otp_gated_single_use_and_expires(agency_client, owner_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path)); dev.clear()
    client, H = agency_client
    ag, t, token = _invite(client, H, owner_conn, "b1@x.com")

    # OTP-gated: wrong code -> 409
    assert client.post(f"/api/consent/{token}/view", json={"code": "000000"}).status_code == 409
    code = _otp(client, token, "b1@x.com")
    assert client.post(f"/api/consent/{token}/view", json={"code": code}).status_code == 200
    # decline -> terminal; link is now single-use-spent -> further use 409
    code = _otp(client, token, "b1@x.com")
    assert client.post(f"/api/consent/{token}/decline", json={"code": code}).status_code == 200
    assert client.post(f"/api/consent/{token}/otp").status_code == 409          # single-use spent

    # expiry: a fresh consent expired in the DB -> 409
    _, _, token2 = _invite(client, H, owner_conn, "b2@x.com")
    cur = owner_conn.cursor()
    cur.execute("UPDATE brand_consents SET expires_at = now() - interval '1 day' WHERE token_hash=%s",
                (consent._hash(token2),))
    owner_conn.commit()
    assert client.post(f"/api/consent/{token2}/otp").status_code == 409          # expired


# ---- T-P3-02 ----
def test_state_machine_legal_and_illegal(agency_client, owner_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path)); dev.clear()
    client, H = agency_client
    ag, t, token = _invite(client, H, owner_conn, "sm@x.com")

    # illegal: grant before view (status invited) -> 409
    code = _otp(client, token, "sm@x.com")
    assert client.post(f"/api/consent/{token}/grant", json={"code": code}).status_code == 409
    # legal: invited -> viewed
    code = _otp(client, token, "sm@x.com")
    assert client.post(f"/api/consent/{token}/view", json={"code": code}).status_code == 200
    # legal: viewed -> granted
    code = _otp(client, token, "sm@x.com")
    r = client.post(f"/api/consent/{token}/grant", json={"code": code})
    assert r.status_code == 200 and r.json()["status"] == "granted"
    # illegal from terminal (granted): any further action -> 409
    assert client.post(f"/api/consent/{token}/otp").status_code == 409


# ---- R18: opening the emailed link marks 'viewed', so a normal recipient CAN grant ----
def test_opening_link_marks_viewed_then_grant_succeeds(agency_client, owner_conn, monkeypatch, tmp_path):
    """The reported bug: recipient got the link, clicked it, but 'Grant access' 409'd — the page GET
    never transitioned invited->viewed and the page JS never called /view, so grant (which requires
    'viewed') always failed. Opening the page now marks it viewed."""
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path)); dev.clear()
    client, H = agency_client
    ag, t, token = _invite(client, H, owner_conn, "open@x.com")
    # open the page exactly as the recipient does (no explicit /view call) -> marks viewed
    assert client.get(f"/consent/{token}").status_code == 200
    cur = owner_conn.cursor()
    cur.execute("SELECT status FROM brand_consents WHERE token_hash=%s", (consent._hash(token),))
    assert cur.fetchone()[0] == "viewed"
    # now grant works straight from the page (OTP + Grant), no separate /view needed
    code = _otp(client, token, "open@x.com")
    r = client.post(f"/api/consent/{token}/grant", json={"code": code})
    assert r.status_code == 200 and r.json()["status"] == "granted", r.text


# ---- R18: agency-direct onboarding of a NET-NEW brand (no tenant_id) doesn't FK-500 ----
def test_onboard_netnew_brand_creates_tenant_and_sends_invite(agency_client, owner_conn, monkeypatch, tmp_path):
    """Onboarding a brand with no Realify account used to 500 (FK on a bogus tenant_id) so the invite
    email never sent. Now the invite CREATES a managed brand tenant + engagement and sends the email."""
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path)); dev.clear()
    client, H = agency_client
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('DirectCo') RETURNING id"); ag = cur.fetchone()[0]
    owner_conn.commit()
    r = client.post("/api/agencies/consent/invite", headers=H,
                    json={"agency_id": str(ag), "brand_name": "Acme Coffee Co.",
                          "email": "owner@acmecoffee.com", "agency_name": "DirectCo", "template": "Advise",
                          "country": "IN"})
    assert r.status_code == 200 and r.json()["ok"], r.text
    assert any(m["to"] == "owner@acmecoffee.com" for m in dev.inbox())      # invite actually sent
    # a managed brand tenant was created UNPROVISIONED (no data -> onboarding wizard, not a fake interior),
    # account_type=customer (real-upload endpoints gate on it), with the stored country (localizes currency)
    cur.execute("SELECT id,provisioned,account_type FROM tenants WHERE name='Acme Coffee Co.' AND tenant_kind='seller'")
    tid, prov, acct = cur.fetchone()
    assert prov == 0 and acct == "customer", (prov, acct)
    cur.execute("SELECT value FROM tenant_settings WHERE tenant_id=%s AND key='country'", (tid,))
    assert cur.fetchone()[0] == "IN"
    cur.execute("SELECT 1 FROM engagements WHERE agency_id=%s::uuid AND tenant_id=%s AND status<>'terminated'",
                (str(ag), tid))
    assert cur.fetchone() is not None


# ---- R18.1: agency self-approve switch (impersonate the brand's consent click, any tenant) ----
def test_self_approve_on_grants_on_behalf_with_fyi_email(agency_client, owner_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path)); dev.clear()
    client, H = agency_client
    cur = owner_conn.cursor()
    cur.execute("DELETE FROM sandbox_settings WHERE key='agency_self_approve'")   # unset => default ON
    cur.execute("INSERT INTO agencies(name) VALUES('SelfCo') RETURNING id"); ag = cur.fetchone()[0]
    owner_conn.commit()
    r = client.post("/api/agencies/consent/invite", headers=H,
                    json={"agency_id": str(ag), "brand_name": "OnBrand", "email": "o@onbrand.com",
                          "agency_name": "SelfCo", "template": "Advise"})
    assert r.status_code == 200 and r.json()["self_approve"] is True, r.text
    cid = r.json()["consent_id"]
    body = "\n".join(m["body"] for m in dev.inbox(to="o@onbrand.com"))
    assert "optimize your margin" in body                          # FYI copy, not an approval request
    # agency approves on the brand's behalf — a REAL (seller) tenant, no sandbox gate
    r2 = client.post(f"/api/agencies/consent/{cid}/self-approve", headers=H)
    assert r2.status_code == 200 and r2.json()["status"] == "granted", r2.text
    cur.execute("SELECT id FROM tenants WHERE name='OnBrand'"); t = cur.fetchone()[0]
    assert r2.json()["redirect"] == f"/agency/brand/{t}"           # drill in -> onboarding wizard (unprovisioned)
    assert r2.json()["tenant_id"] == t
    tenancy.set_brand_scope(cur, [t])
    cur.execute("SELECT count(*) FROM envelopes WHERE tenant_id=%s AND active=true", (t,))
    assert cur.fetchone()[0] == 1                                   # envelope published on the brand's behalf
    cur.execute("SELECT count(*) FROM ledger WHERE tenant_id=%s AND action='consent.grant.impersonated'", (t,))
    assert cur.fetchone()[0] >= 1                                   # ledgered as impersonated


def test_self_approve_off_refuses_and_sends_approval_email(agency_client, owner_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path)); dev.clear()
    client, H = agency_client
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO sandbox_settings(key,value) VALUES('agency_self_approve','off') "
                "ON CONFLICT (key) DO UPDATE SET value='off'")
    cur.execute("INSERT INTO agencies(name) VALUES('OffCo') RETURNING id"); ag = cur.fetchone()[0]
    owner_conn.commit()
    try:
        r = client.post("/api/agencies/consent/invite", headers=H,
                        json={"agency_id": str(ag), "brand_name": "OffBrand", "email": "o@offbrand.com",
                              "agency_name": "OffCo", "template": "Advise"})
        assert r.status_code == 200 and r.json()["self_approve"] is False, r.text
        cid = r.json()["consent_id"]
        body = "\n".join(m["body"] for m in dev.inbox(to="o@offbrand.com"))
        assert "emailed code" in body                              # approval-request copy
        # self-approve is refused while the switch is OFF — brand must approve via OTP
        r2 = client.post(f"/api/agencies/consent/{cid}/self-approve", headers=H)
        assert r2.status_code == 409 and "self-approve is off" in r2.json()["error"], r2.text
    finally:
        cur.execute("DELETE FROM sandbox_settings WHERE key='agency_self_approve'")   # restore default ON
        owner_conn.commit()


# ---- T-P3-03 ----
def test_counter_round_trip(agency_client, owner_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path)); dev.clear()
    client, H = agency_client
    ag, t, token = _invite(client, H, owner_conn, "co@x.com", template="Full Operate")

    code = _otp(client, token, "co@x.com")
    client.post(f"/api/consent/{token}/view", json={"code": code})
    code = _otp(client, token, "co@x.com")
    r = client.post(f"/api/consent/{token}/counter", json={"code": code, "ceilings": {"ads": 1}})
    assert r.status_code == 200 and r.json()["status"] == "countered"

    cur = owner_conn.cursor()
    cur.execute("SELECT id, status FROM brand_consents WHERE tenant_id=%s", (t,))
    cid, status = cur.fetchone()
    assert status == "countered"

    # agency accepts the counter in one click -> granted + envelope published with the countered ceiling
    r = client.post(f"/api/ops/consent/{cid}/accept", headers=H)
    assert r.status_code == 200 and r.json()["status"] == "granted"
    cur.execute("SELECT id FROM engagements WHERE tenant_id=%s", (t,))
    eng = cur.fetchone()
    assert eng is not None
    tenancy.set_brand_scope(cur, [t])
    cur.execute("SELECT caps->'ads'->>'autonomy_ceiling' FROM envelopes WHERE tenant_id=%s AND active=true", (t,))
    assert cur.fetchone()[0] == "1"                     # brand's countered ceiling applied
