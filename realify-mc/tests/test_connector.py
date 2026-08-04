"""Tests for the ChannelConnector seam (#005 1e): typed config, the #004 ads slot, the breaker."""
import os, tempfile, sys

os.environ["REALIFY_DB"] = os.path.join(tempfile.mkdtemp(prefix="realify_conn_"), "t.db")
os.environ.setdefault("MODE", "fixture")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from realify import db, config                                         # noqa: E402
from realify.collectors.base import Collector, ConnectorConfig, AdvertisedProductCollector  # noqa: E402


def test_connector_config_sources_from_config_and_keeps_backcompat_attrs():
    db.init_db()
    c = AdvertisedProductCollector(tenant_id=1)
    assert isinstance(c.cfg, ConnectorConfig)
    assert c.cfg.timeout == config.SOURCE_TIMEOUT
    assert c.cfg.circuit_breaker == config.LIVE_FAIL_CIRCUIT
    assert c.cfg.interval_hours == config.PULL_INTERVAL_HOURS
    # back-compat attributes existing subclasses read directly
    assert c.mode == c.cfg.mode
    assert c.interval_hours == c.cfg.interval_hours


def test_ads_slot_is_noop_until_team7_wires_it():
    db.init_db()
    c = AdvertisedProductCollector(tenant_id=1)
    assert c.source == "ads"
    assert c.fetch_fixture(None, "global", None, None) == []
    assert c.run(force=True) == 0   # nothing persisted; safe to leave registered or not


def test_live_breaker_opens_after_consecutive_failures_without_raising():
    db.init_db()

    class Boom(Collector):
        source = "boomsrc"
        def scopes(self, con):
            return ["a", "b", "c", "d", "e", "f"]
        def fetch_live(self, con, scope, f, t):
            raise RuntimeError("source down")
        def persist(self, con, scope, records):
            return 0

    c = Boom(tenant_id=1, mode="live")
    total = c.run(force=True)        # must not raise, must not hang
    assert total == 0
    # after circuit_breaker consecutive failures, remaining scopes are skipped circuit-open
    con = db.connect()
    rows = con.execute(
        "SELECT status, note FROM pull_log WHERE tenant_id=1 AND source='boomsrc'"
    ).fetchall()
    con.close()
    notes = " ".join((r["note"] or "") for r in rows)
    assert any(r["status"] == "failed" for r in rows)
    assert "circuit-open" in notes


if __name__ == "__main__":
    test_connector_config_sources_from_config_and_keeps_backcompat_attrs()
    test_ads_slot_is_noop_until_team7_wires_it()
    test_live_breaker_opens_after_consecutive_failures_without_raising()
    print("connector OK")
