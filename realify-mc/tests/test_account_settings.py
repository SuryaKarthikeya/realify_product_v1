"""Settings scaffolds: authed change-password + avatar (migration 0040). Backward-compatible additions."""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_acct_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402
from realify import db, auth  # noqa: E402


@pytest.fixture
def client():
    import run
    return TestClient(run.make_app())


def _login(client, email):
    auth.signup(email, "secret123", "AcctCo")
    assert client.post("/api/login", json={"email": email, "password": "secret123"}).status_code == 200


def test_change_password_flow(client):
    _login(client, "pw@x.com")
    # wrong current -> 400, unchanged
    r = client.post("/api/account/password", json={"current": "nope", "new": "newpass123"})
    assert r.status_code == 400 and not r.json()["ok"]
    # too short -> 400
    assert client.post("/api/account/password", json={"current": "secret123", "new": "x"}).status_code == 400
    # correct -> 200, and the new password logs in
    assert client.post("/api/account/password", json={"current": "secret123", "new": "newpass123"}).json()["ok"]
    client.post("/api/logout")
    assert client.post("/api/login", json={"email": "pw@x.com", "password": "newpass123"}).status_code == 200
    assert client.post("/api/login", json={"email": "pw@x.com", "password": "secret123"}).status_code != 200


def test_avatar_set_and_exposed_in_me(client):
    _login(client, "av@x.com")
    tiny = "data:image/png;base64," + ("A" * 40)
    assert client.post("/api/account/avatar", json={"avatar": tiny}).json()["ok"]
    assert client.get("/api/me").json()["avatar"] == tiny
    # oversized rejected
    assert client.post("/api/account/avatar", json={"avatar": "data:image/png;base64," + "A" * 500000}).status_code == 400
    # non-image rejected
    assert client.post("/api/account/avatar", json={"avatar": "javascript:evil"}).status_code == 400


def test_password_requires_auth(client):
    assert client.post("/api/account/password", json={"current": "a", "new": "abcdef"}).status_code == 401
    assert client.post("/api/account/avatar", json={"avatar": ""}).status_code == 401


if __name__ == "__main__":
    print("run via pytest")
