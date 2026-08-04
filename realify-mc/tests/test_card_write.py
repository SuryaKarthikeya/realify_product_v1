"""Card WRITE / materialization path tests (workstream 1b).

Covers the riskiest card operations now behind CardRepository: materialize upsert + dedup +
is_new, the stale-prune that must PRESERVE dismissed/done cards, status writes (dismiss/done),
and research save/clear. Runnable standalone or via pytest.
"""
import os, tempfile, sys, time

_TMP = tempfile.mkdtemp(prefix="realify_cardwrite_test_")
os.environ["REALIFY_DB"] = os.path.join(_TMP, "test.db")
# Hermetic + deterministic: force fixture mode BEFORE importing config, so provisioning uses
# synthetic data, makes no live external calls (no Keepa/News token burn), and a re-run is
# reproducible. Without this, a local MODE=live env makes the dedup re-run non-deterministic.
for _k in ("MODE", "MODE_KEEPA", "MODE_NEWS", "MODE_RECALLS", "MODE_TRENDS"):
    os.environ[_k] = "fixture"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, api, tasks                          # noqa: E402
from realify.pipeline.materialize import run_pipeline       # noqa: E402
from realify.repositories import UnitOfWork                 # noqa: E402
from run import make_app                                    # noqa: E402
from fastapi.testclient import TestClient                   # noqa: E402


def _provision():
    for suffix in ("", "-wal", "-shm"):
        try: os.remove(os.environ["REALIFY_DB"] + suffix)
        except OSError: pass
    db.init_db()
    c = TestClient(make_app())
    from realify import auth as _auth
    _auth.signup("cw@x.com", "password1")               # /api/signup back door gated (P0.9)
    c.post("/api/login", json={"email": "cw@x.com", "password": "password1"})
    c.post("/api/account/type", json={"account_type": "tester"})
    c.post("/api/onboard", json={"mode": "synthetic", "source": "sample", "country": "IN"})
    for _ in range(40):
        if c.get("/api/onboard/status").json().get("pct", 0) >= 100:
            break
        time.sleep(0.5)
    con = db.connect()
    tid = con.execute("SELECT tenant_id FROM users WHERE email='cw@x.com'").fetchone()["tenant_id"]
    con.close()
    return c, tid


def test_materialize_dedup_prune_and_status_writes():
    c, tid = _provision()
    feed = api.get_feed(tid)
    assert len(feed) > 0
    first = feed[0]

    # --- status write: dismiss removes from feed ---
    n_before = len(feed)
    res = tasks.dismiss(tid, first["id"], done=False)
    assert res.get("ok") is not False
    feed_after = api.get_feed(tid)
    assert all(card["id"] != first["id"] for card in feed_after), "dismissed card still in feed"
    assert len(feed_after) == n_before - 1

    # --- re-run pipeline: dedup (no duplicate cards) + dismissed card preserved (not resurrected) ---
    with UnitOfWork() as uow:
        n_open_before = uow.cards.count_open(tid)
        dks_before = uow.cards.existing_dedup_keys(tid)
    out = run_pipeline(tid)
    assert out["status"] if "status" in out else True
    with UnitOfWork() as uow:
        dks_after = uow.cards.existing_dedup_keys(tid)
        # second run of identical data => everything is an update, nothing brand-new
        assert out["new"] == 0, f"re-run should produce 0 new, got {out['new']}"
        # dedup keys stable (no duplication)
        assert dks_after == dks_before, "dedup keys changed across identical re-run"
        # invariant (holds regardless of data): no duplicate (tenant_id, dedup_key) rows
        dupes = uow.con.execute(
            "SELECT dedup_key, COUNT(*) c FROM cards WHERE tenant_id=? GROUP BY dedup_key HAVING COUNT(*)>1",
            (tid,)).fetchall()
        assert not dupes, f"duplicate cards for dedup_keys: {[d['dedup_key'] for d in dupes]}"
        # the dismissed card survived the prune (status preserved)
        dismissed = uow.con.execute(
            "SELECT status FROM cards WHERE id=? AND tenant_id=?", (first["id"], tid)
        ).fetchone()
        assert dismissed is not None and dismissed["status"] == "dismissed"

    # --- mark done also writes status ---
    feed_now = api.get_feed(tid)
    target = feed_now[0]
    tasks.dismiss(tid, target["id"], done=True)
    with UnitOfWork() as uow:
        row = uow.con.execute("SELECT status FROM cards WHERE id=? AND tenant_id=?",
                              (target["id"], tid)).fetchone()
        assert row["status"] == "done"


def test_research_save_and_clear():
    c, tid = _provision()
    feed = api.get_feed(tid)
    dk = feed[0]["dedup_key"]
    with UnitOfWork() as uow:
        assert uow.cards.research_payload(tid, dk) is None
        uow.cards.save_research(tid, dk, '{"l2": {"l2_invoked": false}}')
        uow.commit()
        assert uow.cards.research_payload(tid, dk) is not None
        uow.cards.clear_research(tid)
        uow.commit()
        assert uow.cards.research_payload(tid, dk) is None


if __name__ == "__main__":
    for fn in (test_materialize_dedup_prune_and_status_writes, test_research_save_and_clear):
        fn(); print(f"  PASS  {fn.__name__}")
    print("\n2/2 tests passed")
