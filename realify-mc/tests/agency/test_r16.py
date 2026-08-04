"""R16 (Postgres/agency) — the REAL agency application → admin review queue → approve/provision chain,
asserted on the ENDPOINTS the marketing form + admin console actually hit, the OUTBOX, and the RENDERED
admin HTML (never an isolated helper). This is the guardrail against the exact gap that shipped: a real
applicant hit a dead end (no ops notification reached a person, no reviewable queue in the console).
"""
import time
from realify.mail import dev

_APP = {"agency_name": "Northwind Co", "contact_email": "ceo@northwind.co", "hq_country": "US",
        "am_headcount": "5", "reporting_hours": "10"}


def _fresh(owner_conn):
    owner_conn.rollback()                                    # fresh read-committed snapshot of the job's commits
    return owner_conn.cursor()


def test_real_submit_creates_pending_and_notifies_ops_and_applicant(agency_client, owner_conn):
    client, _H = agency_client
    dev.clear()
    r = client.post("/api/agencies/intake", data=_APP)       # PUBLIC path — no admin header (flag-gated only)
    assert r.status_code == 200 and r.json()["ref"].startswith("AG-")
    ref = r.json()["ref"]
    # Part A — exactly one pending request row with the submitted fields
    cur = _fresh(owner_conn)
    cur.execute("SELECT status, agency_name, contact_email FROM agency_requests WHERE ref=%s", (ref,))
    row = cur.fetchone()
    assert row and row[0] == "received" and row[1] == "Northwind Co" and row[2] == "ceo@northwind.co"
    box = dev.inbox()
    # Part B — ONE ops notification to shiva, from the SES-verified sender, branded HTML, review-queue link
    ops = [m for m in box if m["to"] == "shiva@realify.ai"]
    assert len(ops) == 1, [m["to"] for m in box]
    o = ops[0]
    assert "Northwind Co" in o["subject"]
    assert (o["headers"].get("from_addr") or "").endswith("@realifyai.app")   # verified sender domain
    html = o["headers"].get("html") or ""
    assert "<" in html and "Northwind Co" in html                            # branded HTML, not a plain stub
    assert "/ops/agency/admin" in (html + o["body"])                         # link to the review queue
    # applicant auto-reply NOT regressed
    appl = [m for m in box if m["to"] == "ceo@northwind.co"]
    assert appl and "received your" in appl[0]["subject"].lower()


def test_submit_is_idempotent_for_the_same_open_email(agency_client, owner_conn):
    client, _H = agency_client
    d = {"agency_name": "Dup Co", "contact_email": "dup@x.co", "hq_country": "US",
         "am_headcount": "3", "reporting_hours": "8"}
    r1 = client.post("/api/agencies/intake", data=d)
    r2 = client.post("/api/agencies/intake", data={**d, "agency_name": "Dup Co Renamed"})
    assert r1.json()["ref"] == r2.json()["ref"]              # same open request reused
    cur = _fresh(owner_conn)
    cur.execute("SELECT count(*), max(agency_name) FROM agency_requests WHERE contact_email=%s AND status='received'",
                ("dup@x.co",))
    n, nm = cur.fetchone()
    assert n == 1 and nm == "Dup Co Renamed"                 # ONE row, updated in place — no duplicates


def test_sandbox_world_creates_no_real_application_or_ops_email(agency_client, owner_conn):
    client, H = agency_client
    dev.clear()
    cur = _fresh(owner_conn); cur.execute("SELECT count(*) FROM agency_requests"); before = cur.fetchone()[0]
    wk = "gen-r16-sbx"
    assert client.post("/api/ops/sandbox/generate", headers=H, json={
        "country": "US", "seed": "r16-sbx", "brands_per_agency": 2, "direct_brands": 0,
        "sku_count": 30, "agency_name": ""}).json().get("started")
    for _ in range(60):
        if client.get(f"/api/ops/sandbox/job?world_key={wk}", headers=H).json().get("done"):
            break
        time.sleep(1)
    cur = _fresh(owner_conn); cur.execute("SELECT count(*) FROM agency_requests")
    assert cur.fetchone()[0] == before                       # sandbox creates NO real application row
    assert not [m for m in dev.inbox() if m["to"] == "shiva@realify.ai"]   # ...and NO ops email


def test_admin_queue_renders_pending_and_is_admin_gated(agency_client, owner_conn):
    client, H = agency_client
    ref = client.post("/api/agencies/intake", data={"agency_name": "Queue Co", "contact_email": "q@x.co",
                      "hq_country": "US", "am_headcount": "2", "reporting_hours": "5"}).json()["ref"]
    page = client.get("/ops/agency/admin", headers=H).text   # admin-gated render
    assert "Pending agency requests" in page and "Queue Co" in page
    assert f"'{ref}'" in page and "data-approve" in page      # actionable approve control for this ref
    # require_admin gate — no admin header ⇒ refused
    assert client.get("/ops/agency/admin").status_code == 403


def test_e2e_submit_to_provision(agency_client, owner_conn):
    client, H = agency_client
    dev.clear()
    r = client.post("/api/agencies/intake", data={"agency_name": "E2E Retail", "contact_email": "founder@e2e.co",
                    "hq_country": "US", "am_headcount": "6", "reporting_hours": "12"})
    ref = r.json()["ref"]
    box = dev.inbox()
    assert any(m["to"] == "shiva@realify.ai" for m in box)        # (3) ops notified
    assert any(m["to"] == "founder@e2e.co" for m in box)          # (2) applicant auto-reply
    cur = _fresh(owner_conn); cur.execute("SELECT status FROM agency_requests WHERE ref=%s", (ref,))
    assert cur.fetchone()[0] == "received"                        # (1) pending
    # approve → provision (synchronous, admin-gated)
    dev.clear()
    a = client.post(f"/api/ops/agencies/{ref}/approve", headers=H)
    assert a.status_code == 200 and a.json()["ok"]
    cur = _fresh(owner_conn)
    cur.execute("SELECT status, agency_id FROM agency_requests WHERE ref=%s", (ref,))
    st, aid = cur.fetchone()
    assert st == "live" and aid                                   # (6) provisioned
    cur.execute("SELECT name FROM agencies WHERE id=%s", (aid,))
    assert cur.fetchone()[0] == "E2E Retail"                      # (4) agency tenant created with the name
    assert any(m["to"] == "founder@e2e.co" and "ready" in m["subject"].lower() for m in dev.inbox())  # (5) approved email
    assert "E2E Retail" in client.get("/ops/agency/admin?internal=1", headers=H).text                  # shows in fleet


def test_reject_transitions_and_drops_from_queue(agency_client, owner_conn):
    client, H = agency_client
    ref = client.post("/api/agencies/intake", data={"agency_name": "Nope Co", "contact_email": "n@x.co",
                      "hq_country": "US", "am_headcount": "1", "reporting_hours": "2"}).json()["ref"]
    assert client.post(f"/api/ops/agencies/{ref}/decline", headers=H, json={"reason": "not a fit"}).status_code == 200
    cur = _fresh(owner_conn)
    cur.execute("SELECT status, decline_reason FROM agency_requests WHERE ref=%s", (ref,))
    st, reason = cur.fetchone()
    assert st == "declined" and reason == "not a fit"
    page = client.get("/ops/agency/admin", headers=H).text
    assert "Nope Co" not in page.split("Provisioned agencies")[0]   # gone from the PENDING section


def test_admin_actions_require_admin(agency_client, owner_conn):
    client, H = agency_client
    ref = client.post("/api/agencies/intake", data={"agency_name": "Gate Co", "contact_email": "g@x.co",
                      "hq_country": "US", "am_headcount": "1", "reporting_hours": "2"}).json()["ref"]
    assert client.post(f"/api/ops/agencies/{ref}/approve").status_code == 403          # no admin header
    assert client.post(f"/api/ops/agencies/{ref}/decline", json={"reason": "x"}).status_code == 403
