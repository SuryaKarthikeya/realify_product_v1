"""R0 fix 2: on provision the admin invite is emailed (existing token row) and the acceptance route
sets a password, starts a session, and lands in the agency workspace. The "invite emailed" label is
rendered only when the ledgered send exists."""
import re

from realify.agency import funnel, provision as prov
from realify.mail import dev


def _mkreq(cur, name, email):
    return funnel.create_request(cur, {"agency_name": name, "contact_name": None, "contact_email": email,
                                       "hq_country": "US", "am_headcount": 2, "reporting_hours": None})


def _rid(cur, ref):
    cur.execute("SELECT id FROM agency_requests WHERE ref=%s", (ref,))
    return cur.fetchone()[0]


def test_provision_emails_invite_then_accept_lands_in_workspace(agency_client, owner_conn,
                                                                monkeypatch, tmp_path):
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path))
    monkeypatch.setenv("MAIL_DRIVER", "dev")
    dev.clear()
    client, H = agency_client
    cur = owner_conn.cursor()
    ref = _mkreq(cur, "InvCo", "admin@invco.com")
    owner_conn.commit()
    res = prov.provision(owner_conn, _rid(cur, ref))
    assert res["ok"] and res["status"] == "live"

    box = dev.inbox(to="admin@invco.com")
    assert box, "invite email was not sent"
    token = re.search(r"/agency/invite/([A-Za-z0-9_-]+)", box[-1]["body"]).group(1)

    assert client.get(f"/agency/invite/{token}").status_code == 200          # accept page renders
    r = client.post(f"/api/agency/invite/{token}/accept", data={"password": "password1"})
    assert r.status_code == 200 and r.json()["redirect"] == "/agency/console"
    assert client.get("/agency/console").status_code == 200                  # workspace reachable in-session
    # single-use: the link is now spent
    assert client.post(f"/api/agency/invite/{token}/accept",
                       data={"password": "password1"}).status_code == 409
    # detail label asserts the ledgered send
    owner_conn.rollback()
    assert "Invite emailed to" in client.get(f"/ops/agencies/{ref}", headers=H).text


def test_invite_label_absent_when_send_fails(agency_client, owner_conn, monkeypatch):
    client, H = agency_client
    cur = owner_conn.cursor()
    ref = _mkreq(cur, "FailCo", "a@failco.com")
    owner_conn.commit()
    import realify.mail as mailmod

    def _boom(*a, **k):
        raise RuntimeError("smtp down")
    monkeypatch.setattr(mailmod, "send", _boom)
    res = prov.provision(owner_conn, _rid(cur, ref))
    assert res["ok"] is False and res["failed_step"] == "admin_invite"        # visible failed step
    page = client.get(f"/ops/agencies/{ref}", headers=H).text
    assert "Invite emailed to" not in page and "Invite not emailed" in page   # label absent w/o ledgered send
