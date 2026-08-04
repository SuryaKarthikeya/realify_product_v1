"""R1 RENDERED-UI conformance tests (new test class): the HTTP response for each customer-facing page
must contain the named elements, states, and EXACT semantic copy from the mockup annotations. Behavior
tests alone are insufficient here. Screens: 12 consent, 2 confirmation, 18 console, 19 queue, 22 cockpit."""
import datetime
import re
import secrets

from realify import auth as core_auth
from realify.agency import consent, funnel, ops, fx, connections, tenancy
from realify.pdp import ENVELOPES
from realify.mail import dev

UTC = datetime.timezone.utc


def _login(client, email=None):
    email = email or f"amr1-{secrets.token_hex(4)}@x.com"
    uid, _tid = core_auth.signup(email, "password1", "AM Org")
    r = client.post("/api/login", json={"email": email, "password": "password1"})
    assert r.status_code == 200, r.text
    return uid


def _brand(cur, ag, currency="USD"):
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('BR',now()::text,1) RETURNING id")
    t = cur.fetchone()[0]
    cur.execute("INSERT INTO engagements(agency_id,tenant_id,status) VALUES(%s,%s,'active') RETURNING id",
                (ag, t))
    return t, cur.fetchone()[0]


# ---- screen 12: consent page (rendered) ----
def test_consent_page_rendered(agency_client, owner_conn):
    client, _ = agency_client
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('Acme') RETURNING id"); ag = cur.fetchone()[0]
    cur.execute("INSERT INTO tenants(name,created_at,provisioned) VALUES('B',now()::text,1) RETURNING id")
    t = cur.fetchone()[0]
    owner_conn.commit()
    token, _cid = consent.create_consent(cur, str(ag), t, "Acme", "brand@x.com", "Ads Only", {})
    owner_conn.commit()
    body = client.get(f"/consent/{token}").text
    for card in ("Full Operate", "Operate ex-Pricing", "Ads Only", "Advise Only", "Read-Report Only"):
        assert card in body                                              # 5 envelope template cards
    assert "EXECUTE" in body and "autonomy ceiling" in body             # per-lens read/execute + dials
    assert "Counter-offer" in body and "Decline" in body               # counter + decline
    assert "Who is Realify" in body                                     # who-is-Realify panel
    # the AGENCY connects channels on the brand's behalf — the consent page does NOT ask the brand to
    # connect (that was the wrong actor); it explains the agency will do it, no buttons for the brand.
    assert "connects your sales channels for" in body
    assert "Connect amazon" not in body
    assert "/agency/console" in body                                     # post-grant forward link (no dead-end)
    assert "You can narrow or revoke this access at any time" in body   # EXACT copy
    assert "Acme pays for Realify. You will never receive an invoice from us." in body  # EXACT copy
    assert "brand@x.com" in body and "single-use" in body              # verification banner: email + single-use + expiry
    assert re.search(r"expires on <b>\d{4}-\d{2}-\d{2}</b>", body)


# ---- screen 2: applicant confirmation page + email ----
def test_confirmation_page_rendered(agency_client, owner_conn):
    client, _ = agency_client
    cur = owner_conn.cursor()
    ref = funnel.create_request(cur, {"agency_name": "Conf", "contact_name": None,
                                      "contact_email": "c@x.com", "hq_country": "US",
                                      "am_headcount": 1, "reporting_hours": None})
    owner_conn.commit()
    body = client.get(f"/agencies/status/{ref}").text
    assert ref in body                                                  # reference ID
    for state in ("received", "in-review", "decision", "live"):
        assert state in body                                            # timeline states
    assert "within 2 business days" in body and "A human reads this" in body   # EXACT copy


def test_confirmation_email_sent(agency_client, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path)); monkeypatch.setenv("MAIL_DRIVER", "dev"); dev.clear()
    client, _ = agency_client
    r = client.post("/api/agencies/intake", data={"agency_name": "MailCo", "contact_email": "app@x.com",
                                                  "hq_country": "US", "am_headcount": "2"})
    ref = r.json()["ref"]
    box = dev.inbox(to="app@x.com")
    assert box, "applicant confirmation email not sent"
    b = box[-1]["body"]
    assert "within 2 business days" in b and f"/agencies/status/{ref}" in b and "A human reads this" in b


# ---- screen 18: portfolio console EMPTY state ----
def test_console_empty_state_rendered(agency_client):
    client, _ = agency_client
    _login(client)
    # R11: /agency/console is the FLEET GRID (h7). A session with no agency context (no grant/brand)
    # renders the design-system'd no-agency state, not a bare table. (Fleet-with-brands + Add-client
    # coverage lives in test_queue_items_rendered, which has an agency context.)
    body = client.get("/agency/console").text
    assert "No agency in scope" in body and "class=sc" in body


# ---- screen 19: work queue (rendered) ----
def test_queue_items_rendered(agency_client, owner_conn):
    client, _ = agency_client
    uid = _login(client)
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('QAg') RETURNING id"); ag = cur.fetchone()[0]
    # brand A: suggest-only (Advise), INR (non-USD) decision
    tA, engA = _brand(cur, ag, "INR")
    ops.grant_role(cur, uid, engA, tA, uid, "account_manager")
    ops.publish_envelope(cur, uid, engA, tA, ENVELOPES["Advise"], {})
    fx_id, _ = fx.lock_rate(cur, datetime.date(2026, 7, 14), "INR", 83_000_000)
    cur.execute("INSERT INTO decisions(tenant_id,lens,kind,impact_minor,impact_currency,fx_rate_id,"
                "impact_usd_minor,confidence,signal,status) "
                "VALUES(%s,'ads','bid',131000,'INR',%s,158000,82,'hero_undercut','open')", (tA, fx_id))
    # brand B: execute envelope (Full Operate) -> shows Approve
    tB, engB = _brand(cur, ag, "USD")
    ops.grant_role(cur, uid, engB, tB, uid, "account_manager")
    ops.publish_envelope(cur, uid, engB, tB, ENVELOPES["Full Operate"], {})
    cur.execute("INSERT INTO decisions(tenant_id,lens,kind,impact_minor,impact_currency,fx_rate_id,"
                "impact_usd_minor,confidence,signal,status) "
                "VALUES(%s,'ads','bid',5000,'USD',NULL,5000,90,'restock','open')", (tB,))
    # brand C: paused (expired connection) + a decision
    tC, engC = _brand(cur, ag, "USD")
    ops.grant_role(cur, uid, engC, tC, uid, "account_manager")
    tenancy.set_brand_scope(cur, [tC])
    connections.upsert_connection(cur, tC, "shopify", "expired",
                                  datetime.datetime.now(UTC) - datetime.timedelta(days=1))
    cur.execute("INSERT INTO decisions(tenant_id,lens,kind,impact_minor,impact_currency,fx_rate_id,"
                "impact_usd_minor,confidence,signal,status) "
                "VALUES(%s,'ads','bid',9000,'USD',NULL,9000,70,'stockout','open')", (tC,))
    owner_conn.commit()

    # R11: the cross-brand queue is retired — per-brand decisions surface in the DRILL-IN (h8), where
    # the agency now acts. The fleet grid lists the brands; drilling in shows envelope-aware acts.
    fleet = client.get("/agency/console").text
    assert "Fleet" in fleet and "at stake" in fleet                    # fleet grid renders, $-at-stake per brand
    assert "Add a client" in fleet and "/api/agencies/consent/invite" in fleet   # Add-client wired
    # R15 Part 0 — decisions live INSIDE the real five-lens app now (not a bespoke wrapper). Drilling in
    # scope-switches to it; the brand's envelope (per /api/scope) drives in-lens Approve vs Propose.
    # brand A: suggest-only (Advise) -> ads lens is NOT executable (propose-only) in the real app
    assert client.get(f"/agency/brand/{tA}", follow_redirects=False).status_code == 303
    ca = client.get("/api/scope").json()["agency_scope"]["caps"]
    assert ca.get("ads") != "execute"                                # suggest-only envelope -> propose, never approve
    # brand B: execute envelope (Full Operate) -> ads executable (Approve)
    assert client.get(f"/agency/brand/{tB}", follow_redirects=False).status_code == 303
    cb = client.get("/api/scope").json()["agency_scope"]["caps"]
    assert cb.get("ads") == "execute"
    # brand C: paused (expired connection) -> drill-in still scope-switches into the real app
    assert client.get(f"/agency/brand/{tC}", follow_redirects=False).status_code == 303


# ---- screen 22: approvals cockpit (rendered) ----
def test_cockpit_expiry_sort_rendered(agency_client, owner_conn):
    client, _ = agency_client
    uid = _login(client)
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name) VALUES('CAg') RETURNING id"); ag = cur.fetchone()[0]
    t, eng = _brand(cur, ag, "USD")
    ops.grant_role(cur, uid, eng, t, uid, "account_manager")
    tenancy.set_brand_scope(cur, [t])
    now = datetime.datetime.now(UTC)
    # two cosign_pending approvals: 'soon' expires before 'later' -> must sort first (unique impacts)
    for sig, days, impact in [("later", 6, 20000), ("soon", 2, 10000)]:
        cur.execute("INSERT INTO approvals(tenant_id,engagement_id,lens,kind,signal,impact_usd_minor,"
                    "requires_cosign,status,cosign_expires_at) VALUES(%s,%s,'ads','bid',%s,%s,true,"
                    "'cosign_pending',%s)", (t, eng, sig, impact, now + datetime.timedelta(days=days)))
    owner_conn.commit()
    body = client.get("/agency/cockpit").text
    assert "/mo blocked" in body                                       # $-blocked total in header
    assert "Expired = not executed, ever." in body                    # EXACT copy
    assert "d to expiry" in body                                       # days-to-expiry chips
    assert "not viewed" in body                                        # per-row viewed/not-viewed signal
    # sorted by expiry ascending: 'soon' ($100) row appears before 'later' ($200)
    assert body.index("$100") < body.index("$200")
