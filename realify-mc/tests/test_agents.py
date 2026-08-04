"""Agents subsystem scaffolding: migration 0041 tables, the repo + hash-chained Autonomy Ledger, the
service (roster/hire/tester-seed), and the /api/agents surface. Behavior gating lives in flags; here we
verify the framework structure, honesty (Observe default), the tamper-evident ledger, and the tester seed.
"""
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_agents_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402
from realify import db, auth  # noqa: E402
from realify.repositories.agent_repo import AgentRepository  # noqa: E402
from realify.agents import catalog, service  # noqa: E402


@pytest.fixture
def client():
    import run
    return TestClient(run.make_app())


def _login(client, email, account_type="customer"):
    auth.signup(email, "secret123", "AgentCo")
    assert client.post("/api/login", json={"email": email, "password": "secret123"}).status_code == 200
    with db.connect() as con:
        tid = con.execute("SELECT tenant_id FROM users WHERE email=?", (email,)).fetchone()["tenant_id"]
        db.set_account_type(con, tid, account_type)
        con.commit()
    return tid


def test_catalog_framework():
    assert [a["id"] for a in catalog.AUTONOMY] == ["observe", "suggest", "assist", "act"]
    assert catalog.specialist("pricing")["flagship"] is True
    assert len(catalog.SPECIALISTS) == 5
    assert any(g["kind"] == "contribution_floor" for g in catalog.GUARDRAILS)


def test_repo_and_hash_chained_ledger():
    with db.connect() as con:
        r = AgentRepository(con)
        aid = r.create(1, "pricing", "Pricing", autonomy="observe", guardrails=catalog.default_guardrails())
        r.add_task(1, aid, "Reprice", cadence="daily", autonomy="suggest")
        r.log_decision(1, aid, None, "S1", "Margin", "SKU-1", "Held price", {}, "+$312/mo", 0.89, "applied")
        r.log_decision(1, aid, None, "S2", "Ads", "SKU-2", "Cut spend", {}, "+$180/mo", 0.78, "applied")
        con.commit()
        assert len(r.tasks(1, aid)) == 1
        led = r.ledger(1)
        assert len(led) == 2 and led[0]["seq"] == 2                     # newest-first, seq increments
        assert r.ledger_intact(1) is True                              # chain verifies
        # tamper a row -> chain breaks
        con.execute("UPDATE agent_decision SET action='HACKED' WHERE seq=1 AND tenant_id=1"); con.commit()
        assert r.ledger_intact(1) is False
        # tenant isolation
        assert r.list(2) == [] and r.ledger(2) == []


def test_customer_starts_empty_no_seed(client):
    _login(client, "ag-cust@x.com", "customer")
    d = client.get("/api/agents").json()
    assert d["ok"] and d["agents"] == []                               # real customer: honest-empty
    assert d["feature_on"] is False                                    # behavior off by default
    assert len(d["specialists"]) == 5


def test_tester_gets_seeded_workforce(client):
    _login(client, "ag-test@x.com", "tester")
    d = client.get("/api/agents").json()
    assert len(d["agents"]) == 1 and d["agents"][0]["specialist"] == "pricing"   # seeded Pricing specialist
    led = client.get("/api/agents/ledger").json()
    assert led["intact"] is True and len(led["decisions"]) >= 5        # seeded sample decisions
    assert any("Dutch Oven" in x["target_sku"] for x in led["decisions"])


def test_hire_starts_in_observe(client):
    _login(client, "ag-hire@x.com", "customer")
    r = client.post("/api/agents", json={"specialist": "discovery"}).json()
    assert r["ok"]
    d = client.get("/api/agents/" + r["agent_id"]).json()
    assert d["ok"] and d["agent"]["autonomy"] == "observe"             # never starts acting
    assert client.post("/api/agents", json={"specialist": "bogus"}).status_code == 400


def test_pause_resume(client):
    _login(client, "ag-pause@x.com", "tester")
    aid = client.get("/api/agents").json()["agents"][0]["id"]
    assert client.post("/api/agents/" + aid + "/pause", json={"pause": True}).json()["ok"]
    assert client.get("/api/agents/" + aid).json()["agent"]["status"] == "paused"


def test_requires_auth(client):
    assert client.get("/api/agents").status_code == 401


if __name__ == "__main__":
    print("run via pytest")
