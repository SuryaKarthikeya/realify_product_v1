"""Tester ad entity-graph synth (Tier 2). Populates ad_entity_perf / ad_search_term / ad_ingest_summary
so the Fix-Ads surface renders for a tester — writing the SAME table shapes as the customer upload path
(ad_extract.safe_ingest_ad_graph), rows marked source='synthetic'. Deterministic (md5 factor, like
synth_cmaa) and keyed to the existing catalog, so the same tenant/scenario yields the same graph.

Scenarios are rules-as-DATA (AD_SCENARIOS), the seed of the Tier-3 preset system. Each deliberately
produces the Fix-Ads shapes the diagnosis + fallback logic must be tested against:
  * D3 — a shared campaign healthy overall but bleeding on ONE SKU (the case a campaign average hides).
  * D6 — per-SKU campaigns spread ABOVE and BELOW break-even ACoS (both cuts and scale/advisory).
  * D5 — search terms on ~half the campaigns (KEYWORD fidelity for some SKUs, CAMPAIGN_SKU for others).
  * D4 — a minority of unmapped entity rows so coverage lands <100% without zeroing (ads_full).
Idempotent: clears the tenant's three ad tables before regenerating (so resynth can't double/orphan).
"""
import hashlib
from datetime import date

from ..repositories.seller_repo import SellerRepository
from ..repositories.ad_entity_repo import (
    AdEntityPerfRepository, AdSearchTermRepository, AdIngestSummaryRepository)

# named scenario -> generation params (data, not branches). ads_full is the tester default.
AD_SCENARIOS = {
    "ads_full":     {"generate": True,  "mapped": True,  "unmapped_extra": 2},   # RENDERED_OK, coverage <100
    "ads_none":     {"generate": False},                                          # NO_ENTITY_DATA (fallback)
    "ads_unmapped": {"generate": True,  "mapped": False, "unmapped_extra": 0},    # UNMAPPED (alarm, not fallback)
}
DEFAULT_SCENARIO = "ads_full"


def _factor(seed, lo, hi):
    h = int(hashlib.md5(str(seed).encode()).hexdigest(), 16)
    return lo + (h % 1000) / 1000.0 * (hi - lo)


def _even(seed):
    return int(hashlib.md5(str(seed).encode()).hexdigest(), 16) % 2 == 0


def _period():
    y, m = date.today().year, date.today().month
    m -= 1
    if m == 0:
        m, y = 12, y - 1
    return f"{y:04d}-{m:02d}-01"


def _catalog(con, tenant_id):
    """Deterministic catalog slice with a per-SKU break-even ACoS. Skips the null-COGS SKU (QW-2) —
    a cost-unknown SKU can't have a meaningful ad economics shape."""
    out = []
    for r in SellerRepository(con).all(tenant_id):
        sku = r.get("internal_sku") or r.get("asin")
        price, cogs, units = r.get("price"), r.get("cogs"), (r.get("units_month") or 0)
        if not sku or not price or cogs is None or not units:
            continue
        gc = price - cogs - (r.get("referral_fee") or 0) - (r.get("fba_fee") or 0)
        title = (r.get("title") or "").strip() or str(sku)
        out.append({"sku": str(sku), "asin": str(r.get("asin") or sku), "price": float(price),
                    "units": int(units), "be": max(gc / price, 0.01),
                    "title": title, "label": title[:42]})           # label → readable, product-relevant campaigns
    out.sort(key=lambda x: x["sku"])
    return out


def synthesize_ad_graph(con, tenant_id, scenario=DEFAULT_SCENARIO, grain="month"):
    cfg = AD_SCENARIOS.get(scenario) or AD_SCENARIOS[DEFAULT_SCENARIO]
    ep, st, su = (AdEntityPerfRepository(con), AdSearchTermRepository(con), AdIngestSummaryRepository(con))
    ep.clear(tenant_id); st.clear(tenant_id); su.clear(tenant_id)          # idempotent, tester-scoped
    if not cfg.get("generate"):
        return {"scenario": scenario, "entity_rows": 0, "search_terms": 0, "coverage_pct": None}
    catalog = _catalog(con, tenant_id)
    if not catalog:
        return {"scenario": scenario, "entity_rows": 0, "search_terms": 0, "coverage_pct": None}

    per, mapped = _period(), cfg.get("mapped", True)
    rows, terms = [], []

    def add(campaign, ad_group, item, acos, sales, with_terms):
        asin = item["asin"] if mapped else f"UNMAPPED-{item['sku']}"
        isku = item["sku"] if mapped else None
        spend = round(sales * acos, 2)
        clicks = max(int(sales / max(item["price"], 1) * 3), 1)
        orders = max(int(sales / max(item["price"], 1)), 0)
        rows.append({"c": campaign, "g": ad_group, "asin": asin, "adv": (isku or asin), "isku": isku,
                     "spend": spend, "sales": round(sales, 2), "clicks": clicks, "orders": orders})
        if with_terms:
            kw = (item.get("label") or item["sku"]).lower()
            terms.append({"c": campaign, "g": ad_group, "t": f"kw-{item['sku']}", "m": "EXACT",
                          "term": kw, "spend": round(spend * 0.4, 2),
                          "sales": round(sales * 0.8, 2), "clicks": max(clicks // 2, 1), "orders": max(orders, 1)})
            terms.append({"c": campaign, "g": ad_group, "t": "auto", "m": "BROAD",
                          "term": f"cheap {kw}", "spend": round(spend * 0.3, 2),
                          "sales": 0.0, "clicks": max(clicks // 3, 1), "orders": 0})

    # D3 — shared "Brand Core": winner (huge sales / low spend) dominates the blended ACoS below break-even,
    # while the bleeder's own slice sits well above break-even. Search terms present (KEYWORD fidelity).
    core = catalog[:3]
    if len(core) >= 2:
        add("SP Manual · Brand Core", "Brand", core[0], core[0]["be"] * 0.15,
            core[0]["price"] * core[0]["units"] * 0.9, True)                       # winner
        add("SP Manual · Brand Core", "Brand", core[1], core[1]["be"] * 3.0,
            core[1]["price"] * max(core[1]["units"] * 0.05, 1), True)              # bleeder
        if len(core) >= 3:
            add("SP Manual · Brand Core", "Brand", core[2], core[2]["be"] * 0.7,
                core[2]["price"] * core[2]["units"] * 0.4, False)

    # D6 + D5 — one auto campaign per SKU, ACoS spread above/below break-even; terms on ~half (fidelity mix).
    # Campaign named after the PRODUCT (not the raw SKU code) so it reads as a relevant, real campaign.
    for item in catalog:
        acos = item["be"] * _factor(f"{item['sku']}|{scenario}", 0.3, 2.6)
        sales = item["price"] * item["units"] * _factor(f"{item['sku']}s", 0.2, 0.5)
        add(f"SP Auto · {item['label']}", "Auto", item, acos, sales, _even(item["sku"] + "st"))

    # D4 — a minority of unmapped rows (ads_full) so coverage lands ~90%. Sized to ~11% of mapped spend.
    if mapped and cfg.get("unmapped_extra"):
        mapped_spend = sum(r["spend"] for r in rows if r["isku"])
        k = cfg["unmapped_extra"]; each = round(mapped_spend * 0.11 / max(k, 1), 2)
        for j in range(k):
            rows.append({"c": f"SP Auto · Misc {j}", "g": "Auto", "asin": f"NOASIN-{j}", "adv": f"NOSKU-{j}",
                         "isku": None, "spend": each, "sales": round(each * 0.3, 2), "clicks": 15, "orders": 0})

    for r in rows:
        ep.upsert(tenant_id, r["c"], r["g"], r["asin"], r["adv"], r["isku"], per, grain,
                  r["spend"], r["sales"], r["clicks"], r["orders"], source="synthetic")
    for t in terms:
        st.upsert(tenant_id, t["c"], t["g"], t["t"], t["m"], t["term"], per, grain,
                  t["spend"], t["sales"], t["clicks"], t["orders"])

    cov = ep.coverage(tenant_id, grain)
    fidelity = "KEYWORD" if terms else "CAMPAIGN_SKU"
    su.upsert(tenant_id, cov["coverage_pct"], cov["mapped_spend"], cov["unmapped_spend"], fidelity,
              None, has_advertised_product=1, has_search_term=1 if terms else 0, has_campaign_only=0)
    return {"scenario": scenario, "entity_rows": len(rows), "search_terms": len(terms),
            "coverage_pct": cov["coverage_pct"], "fidelity": fidelity}
