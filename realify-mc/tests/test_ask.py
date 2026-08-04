"""Acceptance tests for the Ask surface scaffolding (agent skeleton + stub narrator).

Covers: the new tables + repository round-trip, the model registry + usage view + monthly cap shaping,
the tool router (data-grounded / honest-empty + freeform category routing), the service turn
(persists user+assistant, bumps usage), and the HTTP surface end to end — categories, models, the SSE
`POST /api/ask` frame sequence, conversation history, feedback, and follow-ups. Model is a stub; the
narrator seam is the single swap point for the future self-hosted model.
"""
import json
import os
import sys
import tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_ask_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402

from realify import db  # noqa: E402
from realify.repositories.ask_repo import AskRepository  # noqa: E402
from realify.ask import models as ask_models, tools as ask_tools, service  # noqa: E402


@pytest.fixture
def client():
    import run
    return TestClient(run.make_app())


def _customer(client, email):
    from realify import auth as _auth
    _auth.signup(email, "secret123", "AskCo")
    assert client.post("/api/login", json={"email": email, "password": "secret123"}).status_code == 200
    with db.connect() as con:
        tid = con.execute("SELECT tenant_id FROM users WHERE email=?", (email,)).fetchone()["tenant_id"]
        db.set_account_type(con, tid, "customer")
        con.commit()
    return tid


def _frames(resp):
    out = []
    for block in resp.text.split("\n\n"):
        block = block.strip()
        if block.startswith("data:"):
            out.append(json.loads(block[len("data:"):].strip()))
    return out


# ---- repository ----
def test_repo_roundtrip():
    with db.connect() as con:
        r = AskRepository(con)
        cid = r.create_conversation(1, 7, "realify-pro", title="hi")
        r.add_message(1, cid, "user", "why is margin down?")
        mid = r.add_message(1, cid, "assistant", "because X", parts=[{"type": "text", "text": "because X"}])
        con.commit()
        assert r.conversation(1, cid)["id"] == cid
        msgs = r.messages(1, cid)
        assert [m["role"] for m in msgs] == ["user", "assistant"]
        assert msgs[1]["parts"][0]["type"] == "text"          # parts round-trip as JSON

        r.set_feedback(1, mid, "good"); con.commit()
        assert r.feedback(1, mid) == "good"
        r.set_feedback(1, mid, "bad"); con.commit()
        assert r.feedback(1, mid) == "bad"                    # upsert overwrites, no dup

        fid = r.add_followup(1, 7, cid, mid, "because X"); con.commit()
        assert any(f["id"] == fid for f in r.followups(1))

        r.bump_usage(1, "realify-pro"); r.bump_usage(1, "realify-pro")
        r.bump_usage(1, "realify-fast"); con.commit()
        u = r.usage(1)
        assert u["total"] == 3 and u["by_model"]["realify-pro"] == 2

        # tenant isolation: tenant 2 sees none of tenant 1's rows
        assert r.conversations(2, 7) == [] and r.usage(2)["total"] == 0


# ---- model registry + usage shaping ----
def test_models_and_usage_view():
    assert ask_models.default_model_id() == "realify-pro"
    assert ask_models.get_model("nope")["id"] == "realify-pro"        # unknown → default, never fails
    v = ask_models.usage_view({"period": "2026-07", "total": 25, "by_model": {"realify-pro": 25}})
    assert v["cap"] == 100 and v["used"] == 25 and v["pct"] == 25 and v["remaining"] == 75
    assert any(m["id"] == "realify-fast" for m in v["by_model"])       # every model appears in the breakdown


# ---- tool router ----
def test_tools_route_and_empty():
    assert ask_tools.route_category("why is my ACoS so high?") == "ads"
    assert ask_tools.route_category("who is undercutting me") == "competition"
    assert ask_tools.route_category("hello there") is None
    facts = ask_tools.gather(999, category="ads", question="where am I wasting spend?")   # no data
    assert facts["count"] == 0 and facts["category"] == "ads" and facts["items"] == []
    assert set(ask_tools.CATEGORY_QUESTIONS) == {"performance", "cash", "ads", "forecasts", "competition"}
    assert all(len(qs) == 5 for qs in ask_tools.CATEGORY_QUESTIONS.values())


# ---- service turn ----
def test_service_run_persists_and_bumps(client):
    tid = _customer(client, "ask-svc@x.com")
    res = service.run(tid, None, None, "why is margin down?", model_id="realify-pro", category="performance")
    assert res["conversation_id"] and res["assistant_message_id"]
    assert res["content"] and isinstance(res["parts"], list)
    assert res["usage"]["used"] == 1
    with db.connect() as con:
        msgs = AskRepository(con).messages(tid, res["conversation_id"])
    assert [m["role"] for m in msgs] == ["user", "assistant"]


# ---- HTTP surface ----
def test_categories_endpoint(client):
    _customer(client, "ask-cats@x.com")
    d = client.get("/api/ask/categories").json()
    assert d["ok"] and [c["id"] for c in d["categories"]] == \
        ["performance", "cash", "ads", "forecasts", "competition"]
    assert all(len(c["questions"]) == 5 for c in d["categories"])


def test_models_endpoint(client):
    _customer(client, "ask-models@x.com")
    d = client.get("/api/ask/models").json()
    assert d["ok"] and d["default"] == "realify-pro" and len(d["models"]) == 2
    assert d["usage"]["cap"] == 100 and d["usage"]["used"] == 0


def test_ask_stream_and_history(client):
    _customer(client, "ask-stream@x.com")
    resp = client.post("/api/ask", json={"message": "why is margin down?", "category": "performance"})
    assert resp.status_code == 200
    frames = _frames(resp)
    types = [f["type"] for f in frames]
    assert types[0] == "meta" and "delta" in types and "usage" in types and types[-1] == "done"
    meta = frames[0]
    assert meta["conversation_id"]
    text = "".join(f["text"] for f in frames if f["type"] == "delta")
    assert text.strip()                                              # streamed prose is non-empty
    assert frames[[f["type"] for f in frames].index("usage")]["usage"]["used"] == 1

    # history now lists the conversation, with the user + assistant turns
    convs = client.get("/api/ask/conversations").json()["conversations"]
    assert len(convs) == 1 and convs[0]["id"] == meta["conversation_id"]
    full = client.get(f"/api/ask/conversations/{meta['conversation_id']}").json()
    assert [m["role"] for m in full["messages"]] == ["user", "assistant"]

    # usage bumped
    assert client.get("/api/ask/usage").json()["usage"]["used"] == 1


def test_feedback_and_followup(client):
    _customer(client, "ask-fb@x.com")
    frames = _frames(client.post("/api/ask", json={"message": "which SKUs are losing money?",
                                                   "category": "performance"}))
    mid = frames[0]["message_id"]
    assert client.post("/api/ask/feedback", json={"message_id": mid, "rating": "good"}).json()["ok"]
    assert client.post("/api/ask/feedback", json={"message_id": mid, "rating": "nope"}).status_code == 400
    assert client.post("/api/ask/followup",
                       json={"message_id": mid, "snippet": "revisit this"}).json()["ok"]
    fu = client.get("/api/ask/followups").json()["followups"]
    assert len(fu) == 1 and fu[0]["message_id"] == mid


def test_ask_requires_auth(client):
    assert client.post("/api/ask", json={"message": "hi"}).status_code == 401
    assert client.get("/api/ask/models").status_code == 401


if __name__ == "__main__":
    for _n, _f in sorted(globals().items()):
        if _n.startswith("test_"):
            print("SKIP standalone (needs pytest fixtures)" if _f.__code__.co_argcount else _f())
