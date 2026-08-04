"""Regression test: /api/me must not 500 when the session points to a tenant that no
longer exists (deleted account or reset DB). It should treat the session as logged out.

Reproduces the 2026-06-29 production 500 (TypeError: 'NoneType' object is not subscriptable
at run.py me: t["name"]). Runnable standalone or via pytest.
"""
import os, tempfile, sys

_TMP = tempfile.mkdtemp(prefix="realify_me_test_")
os.environ["REALIFY_DB"] = os.path.join(_TMP, "test.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db                                   # noqa: E402
from run import make_app                                 # noqa: E402
from fastapi.testclient import TestClient                # noqa: E402


def test_me_with_stale_session_returns_logged_out_not_500():
    for suffix in ("", "-wal", "-shm"):
        try: os.remove(os.environ["REALIFY_DB"] + suffix)
        except OSError: pass
    db.init_db()
    c = TestClient(make_app())
    from realify import auth as _auth
    _auth.signup("stale@x.com", "password1")            # /api/signup back door gated (P0.9)
    r = c.post("/api/login", json={"email": "stale@x.com", "password": "password1"})
    assert r.status_code == 200
    me = c.get("/api/me")
    assert me.status_code == 200 and me.json()["authed"] is True
    tid = me.json().get("tenant")  # name; resolve real id via db
    # delete the tenant out-of-band (simulates account deletion / DB reset under a live cookie)
    con = db.connect()
    row = con.execute("SELECT tenant_id FROM users WHERE email=?", ("stale@x.com",)).fetchone()
    db.delete_tenant(con, row["tenant_id"]); con.close()
    # same client (same session cookie) -> tenant gone
    me2 = c.get("/api/me")
    assert me2.status_code == 200, f"expected 200, got {me2.status_code}"
    assert me2.json()["authed"] is False, "stale session should report logged out"


if __name__ == "__main__":
    test_me_with_stale_session_returns_logged_out_not_500()
    print("  PASS  test_me_with_stale_session_returns_logged_out_not_500")
    print("\n1/1 tests passed")
