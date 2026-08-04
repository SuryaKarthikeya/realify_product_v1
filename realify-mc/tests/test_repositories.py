"""Tests for the repository layer + auth (workstream 1b of #005).

Runnable two ways:
  * standalone:  python3 tests/test_repositories.py   (no pytest needed)
  * pytest:      pytest tests/                          (discovered as test_* functions)

Each run uses a throwaway SQLite DB (REALIFY_DB set before importing realify), so it never
touches dev/prod data. These are also the seed of the CI suite (workstream 1f).
"""
import os, tempfile, importlib, sys

# Isolate the DB BEFORE importing anything that reads config.DB_PATH.
_TMP = tempfile.mkdtemp(prefix="realify_test_")
os.environ["REALIFY_DB"] = os.path.join(_TMP, "test.db")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, auth                                  # noqa: E402
from realify.repositories import (                            # noqa: E402
    UnitOfWork, TenantRepository, UserRepository, InviteRepository,
)


def _fresh_db():
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(os.environ["REALIFY_DB"] + suffix)
        except OSError:
            pass
    db.init_db()


# ---------------- TenantRepository ----------------
def test_tenant_create_get_and_account_type_lock():
    _fresh_db()
    with UnitOfWork() as uow:
        tid = uow.tenants.create("Acme")
        assert isinstance(tid, int) and tid > 0
        t = uow.tenants.get(tid)
        assert t["name"] == "Acme" and not t["provisioned"]
        # account type is free to change until provisioned
        assert uow.tenants.set_account_type(tid, "tester") is True
        assert uow.tenants.set_account_type(tid, "customer") is True
        assert uow.tenants.get_account_type(tid) == "customer"
        assert uow.tenants.set_account_type(tid, "bogus") is False   # invalid
        # provision -> type locks
        uow.tenants.set_provisioned(tid, "uploaded")
        assert uow.tenants.set_account_type(tid, "tester") is False  # locked, differs
        assert uow.tenants.set_account_type(tid, "customer") is True # same -> ok
        assert uow.tenants.get(tid)["provisioned"] == 1


def test_tenant_delete_frees_email():
    _fresh_db()
    uid, tid = auth.signup("solo@x.com", "secret123")
    with UnitOfWork() as uow:
        assert uow.users.get_by_email("solo@x.com") is not None
        uow.tenants.delete(tid)
        assert uow.users.get_by_email("solo@x.com") is None   # email released
    # re-signup with same email now works
    uid2, tid2 = auth.signup("solo@x.com", "secret123")
    assert uid2 and tid2 != tid


# ---------------- UserRepository ----------------
def test_user_crud_and_members():
    _fresh_db()
    with UnitOfWork() as uow:
        tid = uow.tenants.create("Org")
        u1 = uow.users.create("a@x.com", "h", "s", tid)
        u2 = uow.users.create("b@x.com", "h", "s", tid)
        assert uow.users.count_members(tid) == 2
        assert {m["email"] for m in uow.users.list_members(tid)} == {"a@x.com", "b@x.com"}
        uow.users.set_role(u2, "member")
        assert uow.users.get_by_id(u2)["role"] == "member"
        uow.users.delete(u2)
        assert uow.users.count_members(tid) == 1
        assert uow.users.get_by_email("A@X.com") is not None  # case-insensitive lookup (u1 survives)


# ---------------- InviteRepository ----------------
def test_invite_lifecycle():
    _fresh_db()
    with UnitOfWork() as uow:
        tid = uow.tenants.create("Org")
        owner = uow.users.create("owner@x.com", "h", "s", tid)
        iid = uow.invites.create(tid, "invitee@x.com", "member", "hash123", "2099-01-01T00:00:00", owner)
        assert uow.invites.get_by_token_hash("hash123")["status"] == "pending"
        assert len(uow.invites.list(tid)) == 1
        assert uow.invites.revoke(tid, iid) is True
        assert uow.invites.revoke(tid, iid) is False   # already revoked -> no-op
        assert uow.invites.get_by_token_hash("hash123")["status"] == "revoked"


# ---------------- UnitOfWork semantics ----------------
def test_uow_closes_and_propagates_on_exception():
    _fresh_db()
    closed = {}
    try:
        with UnitOfWork() as uow:
            uow.tenants.create("Org")
            closed["con"] = uow.con
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    else:
        raise AssertionError("exception should propagate, not be suppressed")
    # connection closed after the block
    import sqlite3
    try:
        closed["con"].execute("SELECT 1")
        raise AssertionError("connection should be closed")
    except sqlite3.ProgrammingError:
        pass


# ---------------- auth (uses repositories under the hood) ----------------
def test_auth_signup_login_and_duplicate():
    _fresh_db()
    uid, tid = auth.signup("user@x.com", "password1")
    assert uid and tid
    assert auth.login("user@x.com", "password1") == (uid, tid)
    assert auth.login("user@x.com", "wrong") is None
    assert auth.login("nobody@x.com", "password1") is None
    try:
        auth.signup("user@x.com", "password1")
        raise AssertionError("duplicate email should raise")
    except ValueError as e:
        assert "already exists" in str(e)


def test_auth_accept_invite_single_use():
    _fresh_db()
    owner_id, tid = auth.signup("owner@x.com", "password1")
    raw = "rawtoken-xyz"
    with UnitOfWork() as uow:
        uow.invites.create(tid, "join@x.com", "member", auth.hash_token(raw),
                           "2099-01-01T00:00:00", owner_id)
    prev = auth.invite_preview(raw)
    assert prev["email"] == "join@x.com" and prev["org"] == "owner"
    new_uid, new_tid = auth.accept_invite("password1", raw)
    assert new_tid == tid and new_uid != owner_id
    # single-use: second accept fails, preview now None
    assert auth.invite_preview(raw) is None
    try:
        auth.accept_invite("password1", raw)
        raise AssertionError("invite should be single-use")
    except ValueError:
        pass


# ---------------- SettingsRepository ----------------
def test_settings_repo():
    _fresh_db()
    with UnitOfWork() as uow:
        tid = uow.tenants.create("Org")
        assert uow.settings.get(tid, "country", "IN") == "IN"   # default when unset
        uow.settings.set(tid, "country", "US")
        assert uow.settings.get(tid, "country") == "US"
        uow.settings.set(tid, "country", "GB")                  # upsert
        assert uow.settings.get(tid, "country") == "GB"


# ---------------- PullLogRepository ----------------
def test_pull_repo():
    _fresh_db()
    with UnitOfWork() as uow:
        tid = uow.tenants.create("Org")
        assert uow.pulls.due(tid, "keepa", "all", 4) is True            # never pulled
        uow.pulls.record(tid, "keepa", "all", "2026-01-01T00:00:00", "ok", 5, "2026-01-01", "2026-01-02")
        assert uow.pulls.last_watermark(tid, "keepa", "all") == "2026-01-02"
        assert uow.pulls.last_successful_pull_time(tid, "keepa", "all") is not None
        assert uow.pulls.due(tid, "keepa", "all", 100000) is False      # just pulled, huge interval


# ---------------- MetricsRepository ----------------
def test_metrics_repo():
    _fresh_db()
    with UnitOfWork() as uow:
        tid = uow.tenants.create("Org")
        assert uow.metrics.snapshot(tid) == 0   # no seller_skus rows yet
        uow.con.execute("INSERT INTO metric_history(tenant_id,asin,metric,value,captured_at) VALUES(?,?,?,?,?)",
                        (tid, "A1", "net_margin_pct", 10.0, "2026-01-01T00:00:00"))
        uow.con.execute("INSERT INTO metric_history(tenant_id,asin,metric,value,captured_at) VALUES(?,?,?,?,?)",
                        (tid, "A1", "net_margin_pct", 12.0, "2026-01-02T00:00:00"))
        uow.con.commit()
        series = uow.metrics.series(tid, "A1", "net_margin_pct")
        assert [v for _, v in series] == [10.0, 12.0]   # ascending by captured_at


# ---------------- delegation parity: db.* == repository result ----------------
def test_db_delegators_match_repositories():
    _fresh_db()
    con = db.connect()
    tid = db.create_tenant(con, "Org")              # delegator
    assert TenantRepository(con).get(tid) == db.get_tenant(con, tid)
    db.create_user(con, "p@x.com", "h", "s", tid)
    assert db.get_user_by_email(con, "p@x.com") == UserRepository(con).get_by_email("p@x.com")
    assert db.count_members(con, tid) == 1
    con.close()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {fn.__name__}: {type(e).__name__}: {e}")
            raise
    print(f"\n{passed}/{len(fns)} tests passed")
