"""Tests for the cutover-hardening build: DATABASE_URL startup guard + admin-key fail-closed."""
import os, sys, tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_hard_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest                                  # noqa: E402
from fastapi import HTTPException              # noqa: E402
from realify import dbengine                   # noqa: E402
from realify.routers import deps               # noqa: E402


# ---- DATABASE_URL startup guard ----
def test_validate_url_rejects_passwordless_postgres():
    with pytest.raises(SystemExit) as ei:
        dbengine.validate_url("postgresql+psycopg://realify_admin:@host:5432/realify")
    assert "no password" in str(ei.value)


def test_validate_url_accepts_good_postgres_and_ignores_sqlite():
    dbengine.validate_url("postgresql+psycopg://realify_admin:s3cret@host:5432/realify")  # no raise
    dbengine.validate_url("sqlite:////tmp/whatever.db")                                    # no raise


def test_validate_url_rejects_garbage():
    with pytest.raises(SystemExit):
        dbengine.validate_url("postgresql://missinghostanddb")


# ---- admin-key fail-closed ----
class _Req:
    def __init__(self, key):
        self.headers = {"x-realify-admin": key}


def test_known_weak_admin_key_is_disabled(monkeypatch):
    monkeypatch.setenv("REALIFY_ADMIN_KEY", "dingbats2027")     # the exposed prototype key
    assert deps.effective_admin_key() == ""
    with pytest.raises(HTTPException):                          # denied even when presenting it
        deps.require_admin(_Req("dingbats2027"))
    assert deps._admin_key_ok("dingbats2027") is False


def test_unset_admin_key_is_disabled(monkeypatch):
    monkeypatch.delenv("REALIFY_ADMIN_KEY", raising=False)
    assert deps.effective_admin_key() == ""
    with pytest.raises(HTTPException):
        deps.require_admin(_Req(""))


def test_strong_admin_key_works(monkeypatch):
    strong = "Zx7Q2m9Kp4Lr8Tn5Wv3Yb6Hc1Df0Gs"
    monkeypatch.setenv("REALIFY_ADMIN_KEY", strong)
    assert deps.effective_admin_key() == strong
    assert deps.require_admin(_Req(strong)) is True
    assert deps._admin_key_ok(strong) is True
    with pytest.raises(HTTPException):                          # wrong key still denied
        deps.require_admin(_Req("nope"))


if __name__ == "__main__":
    import traceback
    for fn in [test_validate_url_rejects_passwordless_postgres,
               test_validate_url_accepts_good_postgres_and_ignores_sqlite,
               test_validate_url_rejects_garbage]:
        fn()
    print("hardening (non-monkeypatch) OK")
