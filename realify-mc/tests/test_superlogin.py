"""P7 superlogin hardening (default/SQLite suite — superlogin tables are both-engines). T-P7-04 (staff
allowlist, lockout, session TTL, ledgered), T-P7-06 (superlogin signup auto-tags is_internal), grep
test (no /superlogin link in rendered UI)."""
import os
import pathlib
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, superlogin      # noqa: E402
from realify.routers import deps         # noqa: E402
from realify.mail import dev             # noqa: E402

KEY = "superlogin-strong-key-123"


def _setup(monkeypatch, tmp_path):
    monkeypatch.setenv("ADMIN_KEY_HASH", deps.admin_key_hash(KEY))
    monkeypatch.setenv("MAILBOX_DIR", str(tmp_path))
    monkeypatch.setenv("MAIL_DRIVER", "dev")
    dev.clear()


def test_happy_path_creates_ledgered_session(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path)
    con = db.connect()
    code = superlogin.issue_otp(con, "boss@realify.ai")
    res = superlogin.authenticate(con, KEY, "boss@realify.ai", code, "1.2.3.4")
    assert superlogin.verify_session(res["session"]) == "boss@realify.ai"
    n = con.execute("SELECT count(*) FROM superlogin_sessions WHERE email=? AND ip=?",
                    ("boss@realify.ai", "1.2.3.4")).fetchone()[0]
    assert n == 1                                    # session ledgered (who/when/IP)
    con.close()


def test_nonstaff_rejected_and_lockout_after_three(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path)
    con = db.connect()
    for _ in range(3):
        with pytest.raises(superlogin.SuperloginError):
            superlogin.authenticate(con, KEY, "outsider@gmail.com", "000000", "ip")   # non-staff
    assert superlogin.is_locked(con, "outsider@gmail.com") is True
    code = superlogin.issue_otp(con, "outsider@gmail.com")
    with pytest.raises(superlogin.SuperloginError):                                    # locked even if correct
        superlogin.authenticate(con, KEY, "outsider@gmail.com", code, "ip")
    con.close()


def test_session_ttl_enforced(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path)
    con = db.connect()
    code = superlogin.issue_otp(con, "s@realify.ai")
    res = superlogin.authenticate(con, KEY, "s@realify.ai", code, "ip")
    assert superlogin.verify_session(res["session"], max_age=-1) is None              # expired
    con.close()


def test_no_superlogin_link_in_rendered_ui():
    repo = pathlib.Path(__file__).resolve().parent.parent
    # hub.py / backbar.py ARE the staff sandbox surfaces (behind the superlogin gate) — they legitimately
    # reference /superlogin/*; the rule is that CUSTOMER-facing rendered UI must not leak the backdoor.
    _staff = {"hub.py", "backbar.py"}
    files = list(repo.glob("*.html")) + [p for p in (repo / "realify" / "site").rglob("*.py")
                                         if p.name not in _staff]
    offenders = [p.name for p in files if p.exists() and "superlogin" in p.read_text()]
    assert not offenders, offenders


def test_superlogin_hub_lands_personas_and_operator_needs_session(monkeypatch, tmp_path):
    """Post-launch fix 1: after auth, land on the tester hub (four sandbox personas + sandbox control +
    operator actions); the legacy operator function requires the SAME superlogin session."""
    _setup(monkeypatch, tmp_path)
    from run import make_app
    from fastapi.testclient import TestClient
    c = TestClient(make_app())
    # no session -> the hub AND the legacy operator route do not exist (require the same session)
    assert c.get("/superlogin/hub").status_code == 404
    assert c.post("/superlogin/operator/create-tenant",
                  json={"email": "x@realify.ai", "password": "password1", "account": "HQ"}).status_code == 404
    # mint a valid superlogin session (as a successful authenticate would) and attach the cookie
    con = db.connect(); token, _ = superlogin.create_session(con, "op@realify.ai", "1.2.3.4"); con.close()
    c.cookies.set("superlogin_session", token)
    # post-auth landing: the hub renders the four sandbox personas + operator section
    hub = c.get("/superlogin/hub")
    assert hub.status_code == 200
    for persona in ("Realify Admin", "Agency operator", "Managed Brand Owner", "Direct Brand Owner"):
        assert persona in hub.text
    assert "Operator actions" in hub.text and "SANDBOX" in hub.text
    # the legacy operator route now works with the SAME session and keeps the is_internal auto-tag
    r = c.post("/superlogin/operator/create-tenant",
               json={"email": "minted@realify.ai", "password": "password1", "account": "HQ"})
    assert r.status_code == 200 and r.json()["ok"]
    con = db.connect()
    row = con.execute("SELECT is_internal FROM tenants WHERE id=(SELECT tenant_id FROM users WHERE email=?)",
                      ("minted@realify.ai",)).fetchone()
    con.close()
    assert bool(row[0]) is True


def test_superlogin_signup_autotags_internal(monkeypatch, tmp_path):
    _setup(monkeypatch, tmp_path)
    from run import make_app
    from fastapi.testclient import TestClient
    c = TestClient(make_app())
    r = c.post("/api/signup", json={"email": "newstaff@realify.ai", "password": "password1",
                                    "account": "HQ", "admin_key": KEY})
    assert r.status_code == 200 and r.json()["ok"]
    con = db.connect()
    row = con.execute("SELECT is_internal, tenant_kind FROM tenants "
                      "WHERE id=(SELECT tenant_id FROM users WHERE email=?)",
                      ("newstaff@realify.ai",)).fetchone()
    con.close()
    assert bool(row[0]) is True and row[1] == "internal"      # R1: classified tenant_kind='internal'
