"""R10.1 — deploy-safety + superlogin hotfix (default/SQLite suite; hermetic).

Covers: (3) fail-closed DB guard — prod/agency mode refuses to start on SQLite / unreachable Postgres,
no silent fallback; (4) superlogin URL-key regression — GET /superlogin renders the key+OTP form with
NO query params, and the admin-key helper never reads the key from the URL; (1) .env is untracked and
gitignored (secrets cannot be clobbered by a `git reset --hard` on the box)."""
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import config, dbengine      # noqa: E402
from realify.routers import deps          # noqa: E402
from realify.routers import pages         # noqa: E402

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------- (3) FAIL-CLOSED DB ----------------

def test_prod_mode_refuses_sqlite(monkeypatch):
    """AGENCY_CONSOLE=on but no Postgres DATABASE_URL ⇒ startup aborts loudly; does NOT serve on SQLite."""
    monkeypatch.setenv("AGENCY_CONSOLE", "on")
    monkeypatch.delenv("REQUIRE_POSTGRES", raising=False)
    monkeypatch.setattr(config, "DATABASE_URL", "", raising=False)     # blank prod URL -> resolves to sqlite
    assert dbengine.dialect() == "sqlite"
    with pytest.raises(SystemExit) as ei:
        dbengine.assert_backend()
    msg = str(ei.value)
    assert "Postgres" in msg and "SQLite" in msg and "Refusing to start" in msg   # clear, loud message


def test_require_postgres_flag_also_forces(monkeypatch):
    monkeypatch.delenv("AGENCY_CONSOLE", raising=False)
    monkeypatch.setenv("REQUIRE_POSTGRES", "1")
    monkeypatch.setattr(config, "DATABASE_URL", "", raising=False)
    with pytest.raises(SystemExit):
        dbengine.assert_backend()


def test_dev_mode_allows_sqlite(monkeypatch):
    """No AGENCY_CONSOLE / REQUIRE_POSTGRES ⇒ SQLite stays the frictionless dev/test default (no abort)."""
    monkeypatch.delenv("AGENCY_CONSOLE", raising=False)
    monkeypatch.delenv("REQUIRE_POSTGRES", raising=False)
    monkeypatch.setattr(config, "DATABASE_URL", "", raising=False)
    dbengine.assert_backend()          # must NOT raise


def test_prod_mode_unreachable_postgres_refuses(monkeypatch):
    """A well-formed but unreachable Postgres URL ⇒ abort (no silent SQLite fallback)."""
    monkeypatch.setenv("REQUIRE_POSTGRES", "1")
    monkeypatch.setattr(config, "DATABASE_URL",
                        "postgresql+psycopg://u:pw@127.0.0.1:6544/nope", raising=False)
    dbengine._engines.clear()          # drop any cached engine for the fake URL
    with pytest.raises(SystemExit) as ei:
        dbengine.assert_backend()
    assert "REACHABLE Postgres" in str(ei.value) or "connection failed" in str(ei.value)
    dbengine._engines.clear()


# ---------------- (4) SUPERLOGIN URL-KEY REGRESSION ----------------

def test_superlogin_get_renders_form_no_query_params(monkeypatch):
    from run import make_app
    from fastapi.testclient import TestClient
    monkeypatch.delenv("AGENCY_CONSOLE", raising=False)
    c = TestClient(make_app())
    r = c.get("/superlogin")                                   # zero query params
    assert r.status_code == 200                                # not 403/404, not a "key required" gate
    body = r.text
    assert 'id=key' in body and 'id=otp' in body and 'id=email' in body   # key + OTP collected in the FORM
    assert "/api/superlogin/authenticate" in body             # posts to the server-side gate


def test_superlogin_key_helper_never_reads_url(monkeypatch):
    """superlogin_key_ok must NOT accept a key from the query string (leaks to logs/history/referer)."""
    class _Req:
        def __init__(self, qs_key):
            self.headers = {}
            self.query_params = {"key": qs_key}
    monkeypatch.setenv("ADMIN_KEY_HASH", deps.admin_key_hash("url-key-secret"))
    # a valid key placed ONLY in the URL must be rejected (helper ignores query_params entirely)
    assert deps.superlogin_key_ok(_Req("url-key-secret")) is False
    # the same key via the body still works
    assert deps.superlogin_key_ok(_Req(""), body_key="url-key-secret") is True


def test_no_query_param_key_read_in_source():
    """Static guard: no handler reads the admin key from the URL query string."""
    # scope to source handlers (this test file legitimately contains the pattern as data)
    hits = subprocess.run(
        ["git", "grep", "-n", "-e", 'query_params.get("key"', "-e", "query_params['key']", "--", "realify/"],
        cwd=_REPO, capture_output=True, text=True).stdout.strip()
    assert hits == "", f"admin key must never be read from the URL, found:\n{hits}"


# ---------------- (1) .env UNTRACKED ----------------

def test_env_is_untracked_and_ignored():
    tracked = subprocess.run(["git", "ls-files", ".env"], cwd=_REPO,
                             capture_output=True, text=True).stdout.strip()
    assert tracked == "", ".env must not be tracked (prod secrets live only on the box)"
    ignored = subprocess.run(["git", "check-ignore", ".env"], cwd=_REPO,
                             capture_output=True, text=True).returncode
    assert ignored == 0, ".env must be gitignored"
    # the placeholder template stays tracked
    assert subprocess.run(["git", "ls-files", ".env.example"], cwd=_REPO,
                          capture_output=True, text=True).stdout.strip() == ".env.example"
