"""R19 — agency team management: the founding OWNER (agencies.owner_user_id, set on first accept) invites
teammates by email; accepting makes them agency_admin members who see the whole fleet; only the owner may
invite/remove; removing a teammate HARD-DELETES their account (via the lifecycle, ledger-footprint safe).
Runs on the harness PG (agency_client points db.connect() at it)."""
import re

from realify import auth, db
from realify.mail import dev


def _owner_session(client, H, email, pw="ownerpw1"):
    """Provision an agency + accept its invite so `client` is authed as the founding OWNER. Returns aid."""
    ref = client.post("/api/agencies/intake", data={"agency_name": "TeamCo", "contact_name": "Own",
                      "contact_email": email, "hq_country": "US", "am_headcount": "2",
                      "reporting_hours": "4"}).json()["ref"]
    assert client.post(f"/api/ops/agencies/{ref}/approve", headers=H).json()["ok"]
    body = "\n".join(m["body"] for m in dev.inbox(to=email))
    tok = re.search(r"/agency/invite/([A-Za-z0-9_-]+)", body).group(1)
    assert client.post(f"/api/agency/invite/{tok}/accept", json={"password": pw}).json()["ok"]
    with db.connect() as con:
        return con.execute("SELECT agency_id FROM agency_requests WHERE ref=?", (ref,)).fetchone()["agency_id"]


def test_owner_invite_membership_owner_gate_and_hard_delete(agency_client, owner_conn):
    client, H = agency_client
    dev.clear()
    aid = _owner_session(client, H, "owner@tc.co")                    # client session = founding owner
    cur = owner_conn.cursor()
    cur.execute("SELECT owner_user_id FROM agencies WHERE id=%s", (str(aid),))
    owner_uid = cur.fetchone()[0]
    assert owner_uid is not None                                     # owner set on first accept

    # owner invites a teammate (default role agency_admin)
    r = client.post("/api/agency/team/invite", json={"email": "mate@tc.co"})
    assert r.status_code == 200 and r.json()["role"] == "agency_admin", r.text
    tok = re.search(r"/agency/invite/([A-Za-z0-9_-]+)",
                    "\n".join(m["body"] for m in dev.inbox(to="mate@tc.co"))).group(1)
    # teammate accepts → becomes a member (session now switches to the teammate)
    assert client.post(f"/api/agency/invite/{tok}/accept", json={"password": "matepw1"}).json()["ok"]
    owner_conn.rollback()
    cur.execute("SELECT user_id, role FROM agency_members WHERE agency_id=%s ORDER BY created_at", (str(aid),))
    mem = cur.fetchall()
    assert len(mem) == 2 and mem[1][1] == "agency_admin"             # owner + teammate, all-brands role
    mate_uid = mem[1][0]

    # the teammate (non-owner) CANNOT invite or remove — owner-only
    assert client.post("/api/agency/team/invite", json={"email": "x@tc.co"}).status_code == 403
    assert client.post("/api/agency/team/remove", json={"uid": owner_uid}).status_code == 403

    # owner signs back in, removes the teammate → membership gone AND the user account hard-deleted
    assert client.post("/api/login", json={"email": "owner@tc.co", "password": "ownerpw1"}).status_code == 200
    assert client.post("/api/agency/team/remove", json={"uid": owner_uid}).status_code == 400   # can't remove self
    rr = client.post("/api/agency/team/remove", json={"uid": mate_uid})
    assert rr.status_code == 200 and rr.json()["ok"], rr.text
    owner_conn.rollback()
    cur.execute("SELECT count(*) FROM agency_members WHERE agency_id=%s AND user_id=%s", (str(aid), mate_uid))
    assert cur.fetchone()[0] == 0                                    # membership removed
    cur.execute("SELECT count(*) FROM users WHERE id=%s", (mate_uid,))
    assert cur.fetchone()[0] == 0                                    # user account hard-deleted (R19 decision)


def test_invite_existing_user_adds_membership_without_error(agency_client, owner_conn):
    client, H = agency_client
    dev.clear()
    aid = _owner_session(client, H, "owner2@tc.co")
    auth.signup("existing@x.co", "existingpw1", "Existing Org")       # pre-existing Realify account
    r = client.post("/api/agency/team/invite", json={"email": "existing@x.co"})
    assert r.status_code == 200, r.text
    tok = re.search(r"/agency/invite/([A-Za-z0-9_-]+)",
                    "\n".join(m["body"] for m in dev.inbox(to="existing@x.co"))).group(1)
    acc = client.post(f"/api/agency/invite/{tok}/accept", json={"password": "irrelevant"})
    # existing account: no error, no password reset/auto-login — added to the team, sign in as themselves
    assert acc.json()["ok"] and acc.json().get("existing") is True and acc.json()["redirect"] == "/signin", acc.text
    owner_conn.rollback()
    cur = owner_conn.cursor()
    cur.execute("SELECT id FROM users WHERE email=%s", ("existing@x.co",))
    euid = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM agency_members WHERE agency_id=%s AND user_id=%s", (str(aid), euid))
    assert cur.fetchone()[0] == 1                                    # membership added → sees the full hub
