"""Synthesize the period-level ad + revenue data that Profit & Ads reads, from the seller_skus rows
the synthesizer already produced. TESTER-ONLY: gives a demo/tester account a fully working
Profit & Ads (ACoS, TACoS-over-time, quadrants, wasted spend) with a realistic spread across the
four quadrants — the same tables (`ad_performance`, `sku_revenue_period`) a real Sponsored Products
report + settlement upload would fill. Deterministic per SKU so the demo is stable across runs.
"""
import hashlib
from datetime import date

from ..repositories.seller_repo import SellerRepository
from ..repositories.ad_performance_repo import AdPerformanceRepository
from ..repositories.revenue_period_repo import RevenuePeriodRepository
from ..repositories.provenance_repo import ProvenanceRepository


def _recent_months(n=3):
    y, m, out = date.today().year, date.today().month, []
    for _ in range(n):
        m -= 1
        if m == 0:
            m, y = 12, y - 1
        out.append(f"{y:04d}-{m:02d}-01")
    return list(reversed(out))   # oldest -> newest


def _factor(seed, lo, hi):
    """Deterministic value in [lo, hi] from a string seed."""
    h = int(hashlib.md5(str(seed).encode()).hexdigest(), 16)
    return lo + (h % 1000) / 1000.0 * (hi - lo)


def synthesize_cmaa(con, tenant_id, months=3):
    """Write `ad_performance` + `sku_revenue_period` rows derived from each SKU's own economics.
    ACoS is spread around each SKU's break-even so the portfolio lands across all four quadrants.
    Idempotent: clears this tenant's prior synthetic ad/revenue/provenance first, so a resynthesize
    (which re-provisions in place rather than wiping) can't leave stale periods or dropped SKUs."""
    con.execute("DELETE FROM ad_performance WHERE tenant_id=?", (tenant_id,))
    con.execute("DELETE FROM sku_revenue_period WHERE tenant_id=?", (tenant_id,))
    con.execute("DELETE FROM sku_field_provenance WHERE tenant_id=? AND source=?", (tenant_id, "synthetic"))
    rows = SellerRepository(con).all(tenant_id)
    adp, rev = AdPerformanceRepository(con), RevenuePeriodRepository(con)
    provr = ProvenanceRepository(con)
    periods = _recent_months(months)
    written = 0
    for r in rows:
        sku = r.get("internal_sku") or r.get("asin")   # canonical key (load_seller_data stamps 'SKU-'+asin)
        price, cogs, units_m = r.get("price"), r.get("cogs"), (r.get("units_month") or 0)
        if not sku or not price or not units_m:
            continue
        if cogs is None:
            continue    # QW-2: cost-unknown SKU -> no fabricated ad/revenue; Profit & Ads shows "Needs COGS"
        # mark the demo economics as seller-known so certainty computes ('certain') like real data
        for f in ("price", "cogs", "referral_fee", "fba_fee"):
            if r.get(f) is not None:
                provr.set(tenant_id, sku, f, "seller", source="synthetic", value=r.get(f))
        gc = price - (cogs or 0) - (r.get("referral_fee") or 0) - (r.get("fba_fee") or 0) - (r.get("return_cost_unit") or 0)
        gcm = max(gc / price, 0.01)                      # break-even ACoS = gross contribution margin
        acos = gcm * _factor(sku, 0.45, 1.7)             # deterministic spread: some healthy (<be), some wasteful (>be)
        # R14: a SKU the "Cut ACoS" decision fires on (tacos > the 22% break-even) is FORCED above its
        # break-even here, so Profit & Ads always agrees with that decision (decisions ⊆ lens). SKUs the
        # decision doesn't flag keep their natural spread.
        tac = r.get("tacos")
        if tac and float(tac) > 22:
            acos = max(acos, gcm * 1.15)
        for per in periods:
            units = max(int(units_m * _factor(f"{sku}{per}", 0.8, 1.2)), 1)
            revenue = units * price
            ad_sales = revenue * _factor(f"{sku}s", 0.25, 0.6)   # ad-attributed share of sales
            spend = ad_sales * acos
            adp.upsert(tenant_id, sku, per, "month", round(spend, 2), round(ad_sales, 2), source="synthetic")
            rev.upsert(tenant_id, sku, per, "month", round(revenue, 2), units)
            written += 2
    return written
