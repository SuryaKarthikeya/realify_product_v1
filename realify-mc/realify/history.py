"""Stage 2 Phase 0 — synthetic history backfill.

A fresh provision has a single snapshot, so trends and forecasts would have nothing
to read. This fabricates ~N days of plausible daily history per SKU per metric that
*lands on the current real value* at day 0 — a gentle drift + small noise, plus weekly
seasonality on the flow metrics (velocity / cover / stock). Deterministic per
(asin, metric) so a demo is reproducible. Real ongoing history accumulates on top via
db.snapshot_metrics() on every pipeline run.
"""
import hashlib, math, datetime as dt
from . import db
from .repositories.seller_repo import SellerRepository
from .repositories.metrics_repo import MetricsRepository

def _rng_seq(asin, metric, n):
    """Deterministic pseudo-random sequence in [-1,1] from a stable seed."""
    seed = hashlib.md5(f"{asin}:{metric}".encode()).hexdigest()
    out = []
    h = int(seed, 16)
    for _ in range(n):
        h = (1103515245 * h + 12345) & 0x7fffffff
        out.append((h / 0x3fffffff) - 1.0)
    return out

def backfill_synthetic(con, tenant_id, days=45):
    """Fabricate `days` of daily history ending at the current value. No-op if any
    history already exists for the tenant (so it never double-seeds)."""
    if MetricsRepository(con).history_exists(tenant_id):
        return 0
    cols = ",".join(db.HISTORY_METRICS)
    rows = SellerRepository(con).select_columns(tenant_id, ["asin"] + db.HISTORY_METRICS)
    now = dt.datetime.now(dt.timezone.utc)
    seasonal = {"velocity_day", "days_of_cover", "stock_on_hand"}
    payload = []
    for r in rows:
        asin = r["asin"]
        for m in db.HISTORY_METRICS:
            cur = r.get(m)
            if cur is None:
                continue
            noise = _rng_seq(asin, m, days + 1)
            drift = 0.18 * noise[0]                       # -18%..+18% net move over the window
            start = cur * (1 - drift) if cur else 0.0
            for i, d in enumerate(range(days, 0, -1)):
                frac = (days - d) / days                  # 0 .. ~1
                base = start + (cur - start) * frac
                seas = (0.10 * math.sin(2 * math.pi * ((days - d) % 7) / 7)) if m in seasonal else 0.0
                val = max(0.0, base * (1 + seas + 0.04 * noise[i + 1]))
                ts = (now - dt.timedelta(days=d)).isoformat()
                payload.append((tenant_id, asin, m, round(val, 3), ts))
            # anchor the most recent historical point to the real current value
            payload.append((tenant_id, asin, m, float(cur), (now - dt.timedelta(hours=2)).isoformat()))
    MetricsRepository(con).insert_history_many(payload)
    con.commit()
    return len(payload)
