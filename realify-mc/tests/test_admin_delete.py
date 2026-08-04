"""Admin full-account delete + audit: a deleted account's data is wiped and its email freed for a clean
re-signup, one audit row survives the wipe, and the action is guarded (admin key + typed-name confirm)."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_adm_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest                                          # noqa: E402
from realify import db, auth                           # noqa: E402
from run import make_app                               # noqa: E402
from fastapi.testclient import TestClient              # noqa: E402

ADMIN = "strong-admin-key-xyz-9271"                    # non-weak (deps._WEAK_ADMIN_KEYS)
KEY = {"x-realify-admin": ADMIN}


@pytest.fixture(autouse=True)
def _admin_key(monkeypatch, _isolated_db):
    monkeypatch.setenv("REALIFY_ADMIN_KEY", ADMIN)     # scoped to this module; require_admin reads it live


def _client():
    return TestClient(make_app())


def test_audit_table_is_persistent_not_tenant_scoped():
    # must survive the wipe: no literal tenant_id column, and absent from the teardown list
    with db.connect() as con:
        cols = [r[1] for r in con.execute("PRAGMA table_info(deleted_account_audit)")]
    assert "deleted_tenant_id" in cols and "tenant_id" not in cols
    assert "deleted_account_audit" not in db.TENANT_DATA_TABLES


def test_full_delete_frees_email_and_writes_audit():
    c = _client()
    uid, tid = auth.signup("del@x.com", "hunter2pw", "DeleteCo")
    with db.connect() as con:
        assert db.get_tenant(con, tid) and db.get_user_by_email(con, "del@x.com")

    r = c.post(f"/api/admin/tenants/{tid}/delete", headers=KEY, json={"confirm": "DeleteCo", "by": "shiva"})
    assert r.status_code == 200 and r.json()["ok"]
    assert r.json()["deleted"]["emails"] == ["del@x.com"]

    # fully gone + email freed
    with db.connect() as con:
        assert db.get_tenant(con, tid) is None
        assert db.get_user_by_email(con, "del@x.com") is None
    uid2, tid2 = auth.signup("del@x.com", "hunter2pw", "Fresh")   # regular flow reclaims the email
    assert tid2 != tid

    # audit survived with the right record
    dl = c.get("/api/admin/deletions", headers=KEY).json()
    row = next((x for x in dl["deletions"] if x["deleted_tenant_id"] == tid), None)
    assert row and row["tenant_name"] == "DeleteCo" and "del@x.com" in (row["emails"] or "")
    assert row["deleted_by"] == "shiva" and row["member_count"] == 1


def test_delete_is_guarded():
    c = _client()
    uid, tid = auth.signup("guard@x.com", "hunter2pw", "GuardCo")
    # no admin key -> 403 (and the account must NOT be deleted)
    assert c.post(f"/api/admin/tenants/{tid}/delete", json={"confirm": "GuardCo"}).status_code == 403
    # wrong confirmation text -> 400
    assert c.post(f"/api/admin/tenants/{tid}/delete", headers=KEY, json={"confirm": "nope"}).status_code == 400
    # unknown tenant -> 404
    assert c.post("/api/admin/tenants/999999/delete", headers=KEY, json={"confirm": "x"}).status_code == 404
    # survived the blocked attempts
    with db.connect() as con:
        assert db.get_tenant(con, tid) is not None
    # deletions endpoint also requires the key
    assert c.get("/api/admin/deletions").status_code == 403


if __name__ == "__main__":
    print("run under pytest (needs conftest fixtures)")
