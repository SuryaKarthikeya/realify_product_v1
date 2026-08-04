"""Fix C: tester accounts pull collectors in fixture mode regardless of global MODE; customers
use the configured mode. An explicit mode= argument always wins. (config.MODE is a frozen
import-time snapshot, so the tests patch it directly rather than via the environment.)"""
import os, sys, tempfile

os.environ.setdefault("REALIFY_DB", os.path.join(tempfile.mkdtemp(prefix="realify_cm_"), "t.db"))
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, config                          # noqa: E402
from realify.repositories.tenant_repo import TenantRepository  # noqa: E402
from realify.collectors.keepa_collector import KeepaCollector  # noqa: E402

_LIVE = {"keepa": "live", "recalls": "live", "news": "live", "trends": "live"}


def _mk(account_type):
    con = db.connect()
    tid = TenantRepository(con).create("t")
    con.commit()
    if account_type:
        db.set_account_type(con, tid, account_type)
        con.commit()
    con.close()
    return tid


def test_tester_forces_fixture_even_when_global_live(monkeypatch):
    monkeypatch.setattr(config, "MODE", _LIVE)
    assert KeepaCollector(_mk("tester")).mode == "fixture"


def test_customer_uses_global_mode(monkeypatch):
    monkeypatch.setattr(config, "MODE", _LIVE)
    assert KeepaCollector(_mk("customer")).mode == "live"


def test_explicit_mode_overrides_tester_default(monkeypatch):
    monkeypatch.setattr(config, "MODE", _LIVE)
    assert KeepaCollector(_mk("tester"), mode="live").mode == "live"
