"""R17 follow-up — the /ops agency-review ACTION endpoints must authorize via the superlogin COOKIE, not
just the admin-key header. Operators reach /ops/agency/admin with the 8h superlogin cookie; the browser's
Approve/Reject fetch sends that cookie (no key header). The endpoints were key-only → 403 → the buttons
silently did nothing. This exercises the exact cookie path the UI takes (the R16 tests used the header, so
they missed it — the R15.2 rule: assert on the path the UI actually posts to).
"""
from realify import superlogin, db


def test_review_reject_authorizes_via_superlogin_cookie(agency_client, owner_conn):
    client, _H = agency_client
    ref = client.post("/api/agencies/intake", data={"agency_name": "CookieCo", "contact_name": "C",
                      "contact_email": "cookie@x.co", "hq_country": "US", "am_headcount": "3",
                      "reporting_hours": "5"}).json()["ref"]
    # authenticate the way the BROWSER does: a valid superlogin session cookie, NO admin-key header
    tok = superlogin.create_session(db.connect(), "boss@realify.ai", "1.2.3.4")[0]
    client.cookies.set("superlogin_session", tok)
    r = client.post(f"/api/ops/agencies/{ref}/decline", json={"reason": "not now"})   # was 403 before the fix
    assert r.status_code == 200 and r.json()["ok"]
    owner_conn.rollback()
    cur = owner_conn.cursor()
    cur.execute("SELECT status FROM agency_requests WHERE ref=%s", (ref,))
    assert cur.fetchone()[0] == "declined"
    # ...and it drops out of the pending section on the cookie-rendered admin page
    page = client.get("/ops/agency/admin").text
    assert "CookieCo" not in page.split("Provisioned agencies")[0]


def test_review_approve_authorizes_via_superlogin_cookie(agency_client, owner_conn):
    client, _H = agency_client
    ref = client.post("/api/agencies/intake", data={"agency_name": "CookieApproveCo", "contact_name": "C",
                      "contact_email": "capprove@x.co", "hq_country": "US", "am_headcount": "2",
                      "reporting_hours": "4"}).json()["ref"]
    tok = superlogin.create_session(db.connect(), "boss@realify.ai", "1.2.3.4")[0]
    client.cookies.set("superlogin_session", tok)
    r = client.post(f"/api/ops/agencies/{ref}/approve")     # provision via cookie only — was 403 before the fix
    assert r.status_code == 200 and r.json()["ok"]
    owner_conn.rollback()
    cur = owner_conn.cursor()
    cur.execute("SELECT status FROM agency_requests WHERE ref=%s", (ref,))
    assert cur.fetchone()[0] in ("live", "provisioning")    # advanced past 'received' — the button did something
