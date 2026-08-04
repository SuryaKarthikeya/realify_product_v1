"""Tests for the TaskRunner seam (#005 1e)."""
import os, tempfile, sys, json, time

os.environ["REALIFY_DB"] = os.path.join(tempfile.mkdtemp(prefix="realify_runner_"), "t.db")
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, runner  # noqa: E402


def test_inline_runner_records_done_with_result():
    db.init_db()
    r = runner.InlineTaskRunner()
    jid = r.submit("test", lambda: {"ok": True, "n": 3}, tenant_id=1)
    job = r.get(jid)
    assert job["state"] == "done"
    assert json.loads(job["result"]) == {"ok": True, "n": 3}
    assert job["tenant_id"] == 1 and job["kind"] == "test"


def test_inline_runner_records_error_without_crashing():
    db.init_db()
    r = runner.InlineTaskRunner()

    def boom():
        raise ValueError("nope")

    jid = r.submit("test", boom, tenant_id=1)   # must NOT raise
    job = r.get(jid)
    assert job["state"] == "error"
    assert "nope" in (job["error"] or "")


def test_thread_runner_completes_async():
    db.init_db()
    r = runner.ThreadTaskRunner()
    jid = r.submit("test", lambda: {"done": 1}, tenant_id=2)
    for _ in range(60):
        if r.get(jid)["state"] in ("done", "error"):
            break
        time.sleep(0.05)
    assert r.get(jid)["state"] == "done"


if __name__ == "__main__":
    test_inline_runner_records_done_with_result()
    test_inline_runner_records_error_without_crashing()
    test_thread_runner_completes_async()
    print("runner OK")
