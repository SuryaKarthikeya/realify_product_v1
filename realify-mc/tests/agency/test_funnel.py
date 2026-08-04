"""P2 agency funnel: T-P2-01 intake+honeypot, 02 idempotent provision, 03 fault+retry, 04 invite
single-use/expiry, 05 decline mail, 06 status state machine."""
import datetime

from realify.agency import provision as prov, invites, funnel
from realify.mail import dev


def _count(cur, sql, *a):
    cur.execute(sql, a)
    return cur.fetchone()[0]


# ---- T-P2-01 intake validation + honeypot ----
def test_intake_validation_and_honeypot(agency_client, owner_conn):
    client, _ = agency_client
    cur = owner_conn.cursor()
    base = _count(cur, "SELECT count(*) FROM agency_requests")

    ok = client.post("/api/agencies/intake", data={"agency_name": "Acme", "contact_email": "a@acme.com",
                                                   "hq_country": "US", "am_headcount": "4",
                                                   "website": "acme.co", "book_size": "6–15",
                                                   "marketplaces": "Amazon US, Walmart"})
    assert ok.status_code == 200 and ok.json()["ref"].startswith("AG-")
    # R5: `website` is a real captured field now, not the honeypot — a filled website must NOT drop the row
    ref_ok = ok.json()["ref"]
    assert _count(cur, "SELECT website FROM agency_requests WHERE ref=%s", ref_ok) == "acme.co"
    assert _count(cur, "SELECT marketplaces FROM agency_requests WHERE ref=%s", ref_ok) == "Amazon US, Walmart"
    assert client.post("/api/agencies/intake", data={"agency_name": "", "contact_email": "a@a.com",
                                                     "hq_country": "US"}).status_code == 400
    assert client.post("/api/agencies/intake", data={"agency_name": "X", "contact_email": "nope",
                                                     "hq_country": "US"}).status_code == 400
    assert client.post("/api/agencies/intake", data={"agency_name": "X", "contact_email": "a@a.com",
                                                     "hq_country": "FR"}).status_code == 400
    # honeypot (`website_hp`): returns ok but creates NO row
    hp = client.post("/api/agencies/intake", data={"agency_name": "Bot", "contact_email": "b@b.com",
                                                   "hq_country": "US", "website_hp": "http://spam"})
    assert hp.status_code == 200
    assert _count(cur, "SELECT count(*) FROM agency_requests") == base + 1   # only the one valid request


# ---- T-P2-01b intake sends a new-request notification to REPLY_TO_ADDRESS ----
def test_intake_notifies_ops_inbox(agency_client, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path))
    dev.clear()
    client, _ = agency_client
    ref = client.post("/api/agencies/intake", data={"agency_name": "BookCo", "contact_name": "Lee",
                      "contact_email": "lead@bookco.com", "hq_country": "US", "am_headcount": "7"}).json()["ref"]
    # R16 — the ops notification now goes to a MONITORED operator inbox (ops_recipient → shiva@), NOT the
    # no-reply forwarder, and links to the admin review QUEUE (/ops/agency/admin) with a branded HTML part.
    box = dev.inbox(to="shiva@realify.ai")
    assert len(box) == 1                                        # notification reached the operator
    m = box[0]
    assert "BookCo" in m["subject"] and ref in m["subject"]
    assert "BookCo" in m["body"]                                # agency name
    assert "7 account manager" in m["body"]                     # book size
    assert "/ops/agency/admin" in (m["body"] + (m["headers"].get("html") or ""))   # link to the review queue
    assert "<" in (m["headers"].get("html") or "")             # branded HTML part present
    assert m["headers"]["from_addr"].endswith("@realifyai.app")
    assert m["headers"]["reply_to"] == "lead@bookco.com"        # replies go to the applicant


# ---- R5: the application form lives on the /agencies landing; /agencies/apply 301s to #apply ----
def test_apply_redirects_to_landing_anchor(agency_client):
    client, _ = agency_client
    r = client.get("/agencies/apply", follow_redirects=False)
    assert r.status_code == 301 and r.headers["location"] == "/agencies#apply"
    # the landing itself carries the full application form
    body = client.get("/agencies").text
    assert 'id="apply"' in body and 'name="agency_name"' in body


# ---- T-P2-02 provision idempotent ----
def test_provision_idempotent_one_org(agency_client, owner_conn):
    client, H = agency_client
    ref = client.post("/api/agencies/intake", data={"agency_name": "Idem", "contact_email": "i@x.com",
                                                    "hq_country": "US"}).json()["ref"]
    r1 = client.post(f"/api/ops/agencies/{ref}/approve", headers=H).json()
    r2 = client.post(f"/api/ops/agencies/{ref}/approve", headers=H).json()
    assert r1["status"] == "live" and r2["status"] == "live"
    cur = owner_conn.cursor()
    # exactly one org, one provisioned-audit for this ref
    assert _count(cur, "SELECT count(*) FROM agencies") == 1
    assert _count(cur, "SELECT count(*) FROM agency_audit WHERE action='agency.provisioned'") == 1


# ---- T-P2-03 fault injection mid-provision -> visible failed step, retry completes ----
def test_fault_injection_leaves_visible_step_and_retry_completes(agency_client, owner_conn):
    client, _ = agency_client
    ref = client.post("/api/agencies/intake", data={"agency_name": "Fault", "contact_email": "f@x.com",
                                                    "hq_country": "IN"}).json()["ref"]
    cur = owner_conn.cursor()
    rid = _count(cur, "SELECT id FROM agency_requests WHERE ref=%s", ref)

    res = prov.provision(owner_conn, rid, fault_step="billing_stub")
    assert res["ok"] is False and res["failed_step"] == "billing_stub" and res["status"] == "provisioning"
    cur.execute("SELECT step,status FROM agency_provision_steps WHERE request_id=%s ORDER BY step", (rid,))
    st = dict(cur.fetchall())
    assert st["create_org"] == "done" and st["plan_params"] == "done" and st["admin_invite"] == "done"
    assert st["billing_stub"] == "failed"                       # visible failed step (no silent partial)
    assert st["ledger_entry"] == "pending" and st["slack_webhook"] == "pending"
    assert _count(cur, "SELECT status FROM agency_requests WHERE id=%s", rid) == "provisioning"  # not live

    res2 = prov.provision(owner_conn, rid)                      # retry
    assert res2["ok"] is True and res2["status"] == "live"
    cur.execute("SELECT count(*) FROM agency_provision_steps WHERE request_id=%s AND status<>'done'", (rid,))
    assert cur.fetchone()[0] == 0


# ---- T-P2-04 invite single-use + expiry ----
def test_agency_invite_single_use_and_expiry(owner_conn):
    cur = owner_conn.cursor()
    cur.execute("INSERT INTO agencies(name,hq_country) VALUES('Inv','US') RETURNING id")
    ag = cur.fetchone()[0]
    token, iid = invites.create_agency_invite(cur, ag, "admin@inv.com")
    owner_conn.commit()
    assert token and invites.preview(cur, token)["email"] == "admin@inv.com"
    assert invites.accept(cur, token) is not None                # first use ok
    owner_conn.commit()
    assert invites.accept(cur, token) is None                    # single-use: second fails
    # expiry
    token2, _ = invites.create_agency_invite(cur, ag, "b@inv.com")
    cur.execute("UPDATE agency_invites SET expires_at=now() - interval '1 day' WHERE token_hash=%s",
                (invites._hash(token2),))
    owner_conn.commit()
    assert invites.preview(cur, token2) is None                  # expired


# ---- T-P2-05 decline mail contains reason + waitlist ----
def test_decline_writes_reasoned_mail(agency_client, owner_conn, monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path))
    dev.clear()
    client, H = agency_client
    ref = client.post("/api/agencies/intake", data={"agency_name": "No", "contact_email": "no@x.com",
                                                    "hq_country": "US"}).json()["ref"]
    r = client.post(f"/api/ops/agencies/{ref}/decline", headers=H, data={"reason": "portfolio too small"})
    assert r.status_code == 200 and r.json()["ok"]
    box = dev.inbox(to="no@x.com")
    # R1: intake now also sends an applicant confirmation email, so filter to the decline note.
    decline = [m for m in box if "waitlist" in m["body"].lower()]
    assert len(decline) == 1
    body = decline[0]["body"].lower()
    assert "portfolio too small" in body and "waitlist" in body
    cur = owner_conn.cursor()
    assert _count(cur, "SELECT status FROM agency_requests WHERE ref=%s", ref) == "declined"


# ---- T-P2-06 status page matches the state machine ----
def test_status_page_reflects_state_machine(agency_client):
    client, H = agency_client
    ref = client.post("/api/agencies/intake", data={"agency_name": "SM", "contact_email": "sm@x.com",
                                                    "hq_country": "US"}).json()["ref"]
    assert "received" in client.get(f"/agencies/status/{ref}").text
    client.get(f"/ops/agencies/{ref}", headers=H)                # reviewer opens -> in_review
    assert "in_review" in client.get(f"/agencies/status/{ref}").text
    client.post(f"/api/ops/agencies/{ref}/approve", headers=H)
    assert "live" in client.get(f"/agencies/status/{ref}").text

    ref2 = client.post("/api/agencies/intake", data={"agency_name": "SM2", "contact_email": "sm2@x.com",
                                                     "hq_country": "US"}).json()["ref"]
    client.post(f"/api/ops/agencies/{ref2}/decline", headers=H, data={"reason": "nope"})
    page = client.get(f"/agencies/status/{ref2}").text
    assert "declined" in page
