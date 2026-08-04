"""R17.3 — a freshly provisioned agency (no brands yet) must be able to onboard its FIRST client. The
consent-invite authz was grant-only (grants JOIN engagements), so a brand-less agency — which has no
engagements and thus no grants — was refused "not authorized for this agency" on every onboard attempt,
regardless of role (chicken-and-egg: the first brand needs an engagement onboarding a brand would create).
Fixed to authorize by agency_members MEMBERSHIP. Asserted on the endpoint the "Add a client" form posts to.
"""
import re
from realify import auth, db
from realify.mail import dev


def _fresh_agency_admin_session(client, H, email):
    """Provision an agency + accept its invite so `client` is authed as a brand-less agency admin. Returns
    the agency_id."""
    ref = client.post("/api/agencies/intake", data={"agency_name": "OnboardCo", "contact_name": "Ann",
                      "contact_email": email, "hq_country": "US", "am_headcount": "2",
                      "reporting_hours": "4"}).json()["ref"]
    assert client.post(f"/api/ops/agencies/{ref}/approve", headers=H).json()["ok"]
    body = "\n".join(m["body"] for m in dev.inbox(to=email))
    token = re.search(r"/agency/invite/([A-Za-z0-9_-]+)", body).group(1)
    assert client.post(f"/api/agency/invite/{token}/accept", json={"password": "onboardpw1"}).json()["ok"]
    with db.connect() as con:
        aid = con.execute("SELECT agency_id FROM agency_requests WHERE ref=?", (ref,)).fetchone()["agency_id"]
    return aid


def test_fresh_agency_admin_can_onboard_first_brand(agency_client, owner_conn):
    client, H = agency_client
    dev.clear()
    aid = _fresh_agency_admin_session(client, H, "ann@onboardco.co")
    # a brand tenant to invite (the client being onboarded)
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO tenants(name,created_at,provisioned,tenant_kind) "
                "VALUES('Prospect Brand',now()::text,1,'seller') RETURNING id")
    btid = cur.fetchone()[0]; owner_conn.commit()
    # onboard: the "Add a client" consent invite — must NOT be 'not authorized' now (was 403 every time)
    r = client.post("/api/agencies/consent/invite", json={"agency_id": str(aid), "tenant_id": btid,
                    "email": "owner@prospect.co", "agency_name": "OnboardCo", "template": "Advise"})
    assert r.status_code == 200 and r.json()["ok"], r.text
    # the brand owner got a consent invite email
    assert any(m["to"] == "owner@prospect.co" for m in dev.inbox())


def test_agency_home_routes_to_console_not_pricing(agency_client, owner_conn):
    """R18.6 regression: an agency member revisiting the site ROOT must land on their console, NOT the
    seller billing pay wall. Their session tenant is the agency workspace (no Stripe subscription), which
    used to trip billing.has_access() -> RedirectResponse('/pricing') and trap them (root AND /signin
    both bounce there)."""
    client, H = agency_client
    dev.clear()
    _aid = _fresh_agency_admin_session(client, H, "homeroute@onboardco.co")   # client now an agency-admin session
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (302, 303, 307), r.status_code
    assert r.headers.get("location") == "/agency/console", r.headers.get("location")


def test_fresh_admin_onboards_brand_into_wizard_after_self_approve(agency_client, owner_conn):
    """R18.7: a fresh agency admin (no per-brand grant) onboards + self-approves a brand, then must reach
    the brand's data-sources/onboarding page — NOT 'not authorized'. The authz flows through
    agency_brand_ids, which now sets the fleet scope so the engagement is visible under the runtime role
    (was invisible in prod → 403; harness owner bypassed RLS and hid the bug)."""
    client, H = agency_client
    dev.clear()
    aid = _fresh_agency_admin_session(client, H, "ds@onboardco.co")
    r = client.post("/api/agencies/consent/invite", json={"agency_id": str(aid), "brand_name": "DS Brand",
                    "email": "owner@dsbrand.co", "agency_name": "OnboardCo", "template": "Advise", "country": "US"})
    assert r.status_code == 200, r.text
    cid = r.json()["consent_id"]
    ap = client.post(f"/api/agencies/consent/{cid}/self-approve")
    assert ap.status_code == 200 and ap.json().get("tenant_id"), ap.text
    tid = ap.json()["tenant_id"]
    assert ap.json()["redirect"] == f"/agency/brand/{tid}"           # drills into the brand (onboarding wizard)
    d = client.get(f"/agency/brand/{tid}", follow_redirects=False)   # authorized (was 403) -> 303 to /
    assert d.status_code in (302, 303, 307), d.text
    home = client.get("/", follow_redirects=False).text              # unprovisioned brand -> onboarding wizard
    assert "SAMPLE-" not in home                                     # no fabricated Profit&Ads sample leaks in
    assert "window.__agencyBrand" in home                            # flagged as an agency drill-in
    assert "display:none!important" in home                          # sign-in box + tester switcher pre-hidden (no flash)
    assert "Connect your data" in home                               # the real upload wizard body is served


def test_back_to_hub_from_a_brand_returns_to_agency_home(agency_client, owner_conn):
    """R18.8: a real agency customer (no superlogin session) operating one of its brands hits 'back to
    hub' and must land on the AGENCY HOME (fleet) — NOT the tester/superlogin sandbox — with its login
    intact. Previously /api/ops/sandbox/return dropped uid+tid and sent everyone to /superlogin/hub."""
    client, H = agency_client
    dev.clear()
    aid = _fresh_agency_admin_session(client, H, "hub@onboardco.co")
    r = client.post("/api/agencies/consent/invite", json={"agency_id": str(aid), "brand_name": "Hub Brand",
                    "email": "owner@hubbrand.co", "agency_name": "OnboardCo", "template": "Advise"})
    cid = r.json()["consent_id"]
    tid = client.post(f"/api/agencies/consent/{cid}/self-approve").json()["tenant_id"]
    client.get(f"/agency/brand/{tid}", follow_redirects=False)       # drill in (sets acting_as + envelope)
    home = client.get("/", follow_redirects=False).text
    assert "Back to agency home" in home and "Back to hub" not in home   # customer bar, not the sandbox bar
    back = client.post("/api/ops/sandbox/return")
    assert back.json().get("redirect") == "/agency/console", back.text   # agency home, not /superlogin/hub
    con = client.get("/agency/console")                              # still signed in -> console renders
    assert con.status_code == 200 and "No agency in scope" not in con.text


def test_brand_with_data_opens_app_not_onboarding_wizard(agency_client, owner_conn):
    """R19.1: a brand that already has a real catalog must open the five-lens APP on drill-in, never loop
    back to the onboarding wizard — even if its provisioned flag is (wrongly) unset. (gogodolls had 1,447
    SKUs but provisioned=0, so drilling in kept sending the agency to 'upload data'.)"""
    client, H = agency_client
    dev.clear()
    aid = _fresh_agency_admin_session(client, H, "hasdata@onboardco.co")
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO tenants(name,created_at,provisioned,tenant_kind,account_type) "
                "VALUES('HasData Brand',now()::text,0,'seller','customer') RETURNING id"); bt = cur.fetchone()[0]
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status) VALUES(%s::uuid,%s,'active')", (str(aid), bt))
    cur.execute("INSERT INTO seller_skus(tenant_id,asin,internal_sku) VALUES(%s,'B00DATA','SKU1')", (bt,))  # real data
    owner_conn.commit()
    assert client.get(f"/agency/brand/{bt}", follow_redirects=False).status_code in (302, 303, 307)  # drill in
    home = client.get("/", follow_redirects=False).text
    assert "window.__agencyBrand" not in home and "Connect your data" not in home  # the APP, not the wizard


def test_non_member_cannot_onboard_for_an_agency(agency_client, owner_conn):
    client, H = agency_client
    dev.clear()
    aid = _fresh_agency_admin_session(client, H, "ann2@onboardco.co")
    # a DIFFERENT logged-in user who is NOT a member of that agency
    auth.signup("stranger@x.co", "strangerpw1", "Stranger LLC")
    client.post("/api/logout")
    client.post("/api/login", json={"email": "stranger@x.co", "password": "strangerpw1"})
    r = client.post("/api/agencies/consent/invite", json={"agency_id": str(aid), "tenant_id": 1,
                    "email": "x@y.co", "template": "Advise"})
    assert r.status_code == 403 and "not authorized" in r.json()["error"]
