"""Collector / ChannelConnector framework (#005 1e seam) — tenant-scoped.

A connector pulls from one external channel. The contract:
  - `source`: stable id; `scopes(con)`: what to pull; `window(con, scope)`: the incremental window
    from the pull_log watermark; `fetch_live` / `fetch_fixture`: get records (live API vs seeded
    offline data); `persist(con, scope, records)`: write through the data layer.
  - Every run is bounded by a typed `ConnectorConfig` (mode, per-call timeout, consecutive-failure
    circuit breaker, interval). Live failures degrade gracefully: the breaker opens after N
    consecutive empties/errors and the run is skipped — never hung. Fixture mode always succeeds,
    which is also the offline path hermetic tests use.

This is the seam the Competitive-data team subclasses (guide §3C); where the period-aware
Advertising connector (#004) and future per-tenant OAuth marketplace connectors plug in.
"""
import datetime as dt
from dataclasses import dataclass
from .. import db, config


@dataclass(frozen=True)
class ConnectorConfig:
    """Typed, immutable bounds for one connector run."""
    mode: str = "fixture"          # "live" | "fixture"
    timeout: float = 8.0           # per-call socket timeout (live mode)
    circuit_breaker: int = 3       # stop after N consecutive live failures/empties
    interval_hours: float = 4.0    # minimum spacing between pulls per scope

    @classmethod
    def for_source(cls, source, mode=None, interval_hours=None):
        return cls(
            mode=mode or config.MODE.get(source, "fixture"),
            timeout=config.SOURCE_TIMEOUT,
            circuit_breaker=config.LIVE_FAIL_CIRCUIT,
            interval_hours=interval_hours if interval_hours is not None else config.PULL_INTERVAL_HOURS,
        )


class Collector:
    source = "base"

    def __init__(self, tenant_id, mode=None, interval_hours=None):
        self.tenant_id = tenant_id
        if mode is None:
            # Tester accounts always synthesize market data (fixture), regardless of the global
            # prod MODE: a tester's synthetic catalog has no presence on live Keepa, so a live pull
            # returns nothing and the tester would see no market signals. Customers use the
            # configured mode (live on prod). An explicit `mode=` argument still wins.
            try:
                con = db.connect()
                if db.get_account_type(con, tenant_id) == "tester":
                    mode = "fixture"
                con.close()
            except Exception:
                pass
        self.cfg = ConnectorConfig.for_source(self.source, mode, interval_hours)
        # Back-compat attributes (existing subclasses read these directly).
        self.mode = self.cfg.mode
        self.interval_hours = self.cfg.interval_hours

    def scopes(self, con):
        return ["global"]

    def window(self, con, scope):
        wm = db.last_watermark(con, self.tenant_id, self.source, scope)
        to = db.now_iso()
        if wm:
            frm = wm
        else:
            frm = (dt.datetime.now(dt.timezone.utc)
                   - dt.timedelta(days=config.FIRST_PULL_BACKFILL_DAYS)).replace(microsecond=0).isoformat()
        return frm, to

    def fetch_live(self, con, scope, window_from, window_to):
        raise NotImplementedError
    def fetch_fixture(self, con, scope, window_from, window_to):
        raise NotImplementedError
    def persist(self, con, scope, records):
        raise NotImplementedError

    def run(self, force=False):
        import socket
        con = db.connect()
        total = 0
        consec_fail = 0          # live circuit breaker: stop after N consecutive failures/empties
        old_timeout = socket.getdefaulttimeout()
        if self.cfg.mode == "live":
            socket.setdefaulttimeout(self.cfg.timeout)
        try:
            for scope in self.scopes(con):
                started = db.now_iso()
                if not force and not db.due_for_pull(con, self.tenant_id, self.source, scope, self.cfg.interval_hours):
                    db.record_pull(con, self.tenant_id, self.source, scope, started, "skipped", 0, None, None,
                                   note=f"within {self.cfg.interval_hours}h interval")
                    continue
                if self.cfg.mode == "live" and consec_fail >= self.cfg.circuit_breaker:
                    db.record_pull(con, self.tenant_id, self.source, scope, started, "skipped", 0, None, None,
                                   note="circuit-open (live source failing/empty)")
                    continue
                frm, to = self.window(con, scope)
                try:
                    records = self.fetch_live(con, scope, frm, to) if self.cfg.mode == "live" \
                              else self.fetch_fixture(con, scope, frm, to)
                    n = self.persist(con, scope, records)
                    db.record_pull(con, self.tenant_id, self.source, scope, started, "ok", n, frm, to,
                                   note=f"mode={self.cfg.mode}")
                    total += n
                    consec_fail = 0 if (n > 0 or self.cfg.mode != "live") else consec_fail + 1
                except Exception as e:
                    db.record_pull(con, self.tenant_id, self.source, scope, started, "failed", 0, frm, to, note=str(e)[:200])
                    consec_fail += 1
        finally:
            socket.setdefaulttimeout(old_timeout)
        con.close()
        return total


class AdvertisedProductCollector(Collector):
    """Reserved slot for the #004 ad spec (CMAA). Advertising metrics (spend, sales, ACoS, TACoS)
    per ASIN per PERIOD — period-aware ingestion, with the certain-vs-estimated dollar separation
    preserved at persistence so detectors can distinguish reported spend from modelled attribution.

    Source: a seller ad-report upload first, then the Amazon Advertising API (official only — never
    scraped). NOT registered in scheduler.collectors() yet — Team 7 implements fetch + persist and
    registers it. Fixture is a no-op, so wiring this in early changes no behaviour.
    """
    source = "ads"

    def scopes(self, con):
        return ["global"]

    def fetch_fixture(self, con, scope, window_from, window_to):
        return []

    def persist(self, con, scope, records):
        return 0
