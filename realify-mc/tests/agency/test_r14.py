"""R14 Part C (Postgres/agency): after a world loads, the sandbox synthesizes ALL five lenses — not
just Product Catalog. Profit & Ads / Channels / Intelligence / Category Analyst populate with
world-consistent, locale-correct, deterministic data, and the ACoS decisions reconcile with Profit &
Ads (same wasteful SKUs, recoverable-$ > 0).

NOTE: the lens builders use db.connect() (config.DATABASE_URL). In prod the seller app + agency share
ONE database, so we point config.DATABASE_URL at the agency PG here (what the agency_client fixture and
prod both do) so the builders write to the same DB the sandbox seeded."""
import os

from realify import config
from realify.agency import sandbox, synth, tenancy, lens_synth

_DIRECT = os.environ.get("AGENCY_DATABASE_URL")


def _gcm(row):
    price = row["price"] or 0
    if not price:
        return 0.0
    fees = (row.get("cogs") or 0) + (row.get("referral_fee") or 0) + (row.get("fba_fee") or 0) + (row.get("return_cost_unit") or 0)
    return max((price - fees) / price, 0.01)


def _finalize(monkeypatch, owner_conn, ids):
    monkeypatch.setattr(config, "DATABASE_URL", _DIRECT, raising=False)   # builders' db.connect() → agency PG
    lens_synth.finalize_world(ids)
    owner_conn.rollback()                                                 # fresh read-committed snapshot


def test_all_lenses_populate_and_reconcile(owner_conn, monkeypatch):
    cur = owner_conn.cursor()
    st = sandbox.load_preset(cur, "us_pilot"); owner_conn.commit()
    tid = st["brands"][0]["tenant_id"]
    _finalize(monkeypatch, owner_conn, [tid])
    tenancy.set_brand_scope(cur, [tid])

    # PROFIT & ADS: ad_performance + revenue periods populated
    cur.execute("SELECT count(*) FROM ad_performance WHERE tenant_id=%s", (tid,))
    assert cur.fetchone()[0] > 0, "Profit & Ads (ad_performance) empty"
    cur.execute("SELECT count(*) FROM sku_revenue_period WHERE tenant_id=%s", (tid,))
    assert cur.fetchone()[0] > 0

    # RECONCILIATION: every SKU the ads decision fires on (tacos > 22) is wasteful in Profit & Ads
    # (ACoS > its break-even); recoverable-$ across the portfolio is > 0.
    cur.execute("SELECT internal_sku, price, cogs, referral_fee, fba_fee, return_cost_unit, tacos "
                "FROM seller_skus WHERE tenant_id=%s", (tid,))
    cols = ("internal_sku", "price", "cogs", "referral_fee", "fba_fee", "return_cost_unit", "tacos")
    skus = [dict(zip(cols, r)) for r in cur.fetchall()]
    cur.execute("SELECT internal_sku, SUM(spend), SUM(sales) FROM ad_performance WHERE tenant_id=%s "
                "GROUP BY internal_sku", (tid,))
    adp = {sku: (sp or 0, sa or 0) for sku, sp, sa in cur.fetchall()}
    recoverable = 0.0
    ads_decision_skus, wasteful_skus = set(), set()
    for s in skus:
        sku = s["internal_sku"]; sp, sa = adp.get(sku, (0, 0))
        if (s["tacos"] or 0) > 22:
            ads_decision_skus.add(sku)
        if sa > 0 and (sp / sa) > _gcm(s):
            wasteful_skus.add(sku); recoverable += sp - sa * _gcm(s)
    assert recoverable > 0, "Profit & Ads recoverable-$ is 0"
    assert ads_decision_skus and ads_decision_skus <= wasteful_skus, \
        f"ACoS decisions disagree with Profit & Ads: {ads_decision_skus - wasteful_skus} not wasteful"

    # CHANNELS: cross-channel economics for the US channel set (Amazon/Walmart/Shopify), no India channels
    cur.execute("SELECT DISTINCT channel FROM channel_economics WHERE tenant_id=%s", (tid,))
    chans = {c[0].lower() for c in cur.fetchall()}
    assert chans and any("amazon" in c for c in chans), "Channels (channel_economics) empty"
    assert not any(("flipkart" in c or "shopzee" in c) for c in chans)

    # INTELLIGENCE / CATEGORY ANALYST: the detector pipeline produced cards
    cur.execute("SELECT count(*) FROM cards WHERE tenant_id=%s", (tid,))
    assert cur.fetchone()[0] > 0, "Intelligence/Category feed (cards) empty"
    # CATEGORY ANALYST: the world's categories (US pilot Home/Pet/Outdoor), not a stale "Car cover",
    # and its price bands are locale-correct ($ for a US world, never ₹).
    cur.execute("SELECT DISTINCT category FROM seller_skus WHERE tenant_id=%s", (tid,))
    assert "Car cover" not in {c[0] for c in cur.fetchall()}
    from realify.domain import analyst
    brief = analyst.synthesize_category_analyst(tid)
    bands = brief.scope.price_bands if hasattr(brief, "scope") else brief.price_bands
    assert bands and not any("₹" in b for b in bands) and any("$" in b for b in bands)


def test_channels_and_locale_india(owner_conn, monkeypatch):
    cur = owner_conn.cursor()
    st = sandbox.load_preset(cur, "in_pilot"); owner_conn.commit()
    tid = st["brands"][0]["tenant_id"]
    _finalize(monkeypatch, owner_conn, [tid])
    tenancy.set_brand_scope(cur, [tid])
    cur.execute("SELECT DISTINCT channel FROM channel_economics WHERE tenant_id=%s", (tid,))
    chans = {c[0].lower() for c in cur.fetchall()}
    assert chans and not any("walmart" in c for c in chans)            # India world → no US-only channel
    cur.execute("SELECT count(*) FROM ad_performance WHERE tenant_id=%s", (tid,))
    assert cur.fetchone()[0] > 0                                       # Profit & Ads populated for the ₹ world too


def test_cross_lens_deterministic(owner_conn, monkeypatch):
    cur = owner_conn.cursor()
    p = {"country": "US", "seed": "r14det", "brands_per_agency": 2, "direct_brands": 0,
         "moments": ["acos_over_breakeven", "stockout"]}
    a = synth.generate_world(cur, p); owner_conn.commit()
    tid = a["brands"][0]["tenant_id"]
    _finalize(monkeypatch, owner_conn, [tid])
    cur.execute("SELECT internal_sku, period_start, spend, sales FROM ad_performance WHERE tenant_id=%s "
                "ORDER BY internal_sku, period_start", (tid,))
    snap1 = cur.fetchall()
    b = synth.generate_world(cur, p); owner_conn.commit()              # same seed+params → identical
    tid2 = b["brands"][0]["tenant_id"]
    _finalize(monkeypatch, owner_conn, [tid2])
    cur.execute("SELECT internal_sku, period_start, spend, sales FROM ad_performance WHERE tenant_id=%s "
                "ORDER BY internal_sku, period_start", (tid2,))
    assert snap1 and snap1 == cur.fetchall()                          # byte-identical ad synthesis across runs
