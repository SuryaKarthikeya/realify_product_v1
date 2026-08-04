"""Live reconcile — bake real Amazon PDP (product info) + Keepa (competitor info) into a
tenant's served data, then re-baseline `seller_skus` to the live truth.

Per tenant:
  1. Keepa live pull  -> keepa_snapshots (price/BSR/rating/reviews/buybox) + competitor_offers
                         (needs KEEPA_BULK_OFFERS>0 for offers; KEEPA_KEY + MODE_KEEPA=live).
  2. Amazon PDP pull  -> keepa_snapshots, source="amazon_pdp" (authoritative CURRENT price/
                         rating/reviews/title/image/availability; newest -> wins).
  3. re-baseline seller_skus from the newest LIVE (non-fixture) snapshot per ASIN:
       price, rating, review_count, title  <- live-observable ground truth
     + recompute the price-derived economics holding the referral RATE (%-of-price) fixed:
         rate            = referral_fee / price          (from the pre-update row)
         referral_fee'   = rate * price'
         net_profit_unit'= price' - cogs - referral_fee' - fba_fee - ad_cost_unit - return_cost_unit
         net_margin_pct' = 100 * net_profit_unit' / price'
         breakeven_floor'= (cogs + fba_fee + ad_cost_unit + return_cost_unit) / (1 - rate)
     Per-unit absolute fees (cogs/fba/ad/return) are price-independent and kept as-is. Any
     field the live pull couldn't observe is left untouched (never overwritten with 0/NULL).

Idempotent and reversible-by-re-pull. Honest: a blocked/failed ASIN keeps its prior value
(logged), never a fabricated one.
"""
import json
from .. import db
from ..collectors.keepa_collector import KeepaCollector
from ..collectors.amazon_pdp_collector import AmazonPdpCollector
from ..repositories.seller_repo import SellerRepository


def pull_live(tenant_id, log=print):
    """Force a live pull for both market sources. Returns {source: records}."""
    out = {}
    for col in (KeepaCollector(tenant_id, mode="live"), AmazonPdpCollector(tenant_id, mode="live")):
        try:
            n = col.run(force=True)
        except Exception as e:
            n = 0
            log(f"[reconcile][t{tenant_id}] {col.source} pull error: {str(e)[:140]}")
        out[col.source] = n
        log(f"[reconcile][t{tenant_id}] {col.source:11s} live records={n}")
    return out


def _latest_live_snapshot(con, tenant_id, asin):
    """Newest non-fixture snapshot for an ASIN, preferring the Amazon PDP row."""
    rows = con.execute(
        "SELECT price, rating, review_count, bsr, buybox_seller, captured_at, raw "
        "FROM keepa_snapshots WHERE tenant_id=? AND asin=? "
        "AND (raw IS NULL OR raw NOT LIKE '%fixture%') "
        "ORDER BY CASE WHEN raw LIKE '%amazon_pdp%' THEN 0 ELSE 1 END, captured_at DESC",
        (tenant_id, asin)).fetchall()
    return dict(rows[0]) if rows else None


def rebaseline_seller_skus(con, tenant_id, log=print):
    """Overwrite live-observable fields + recompute price-derived economics. Returns a
    per-ASIN diff list [{asin, before:{...}, after:{...}}] for the ones that changed."""
    repo = SellerRepository(con)
    asins = repo.asins(tenant_id)
    changed = []
    for asin in asins:
        snap = _latest_live_snapshot(con, tenant_id, asin)
        if not snap:
            continue
        raw = {}
        try:
            raw = json.loads(snap.get("raw") or "{}")
        except (ValueError, TypeError):
            raw = {}

        live_price = snap["price"] if snap["price"] and snap["price"] > 0 else None
        live_rating = snap["rating"] if snap["rating"] and snap["rating"] > 0 else None
        live_reviews = snap["review_count"] if snap["review_count"] is not None else None
        live_title = raw.get("title")
        if live_price is None and live_rating is None and live_reviews is None and not live_title:
            continue

        cur = repo.by_asin(tenant_id, asin) or {}
        sets, params, after = [], [], {}

        def put(col, val):
            sets.append(f"{col}=?"); params.append(val); after[col] = val

        if live_title:
            put("title", live_title[:200])
        if live_rating is not None:
            put("rating", round(live_rating, 2))
        if live_reviews is not None:
            put("review_count", int(live_reviews))

        if live_price is not None:
            put("price", round(live_price, 2))
            old_price = cur.get("price")
            ref = cur.get("referral_fee")
            rate = (ref / old_price) if (ref is not None and old_price) else None
            # per-unit absolutes stay fixed with price
            cogs = cur.get("cogs"); fba = cur.get("fba_fee")
            ad = cur.get("ad_cost_unit"); ret = cur.get("return_cost_unit")
            if rate is not None:
                new_ref = round(rate * live_price, 2)
                put("referral_fee", new_ref)
                if None not in (cogs, fba, ad, ret):
                    fixed = cogs + fba + ad + ret
                    net = live_price - cogs - new_ref - fba - ad - ret
                    put("net_profit_unit", round(net, 2))
                    put("net_margin_pct", round(100.0 * net / live_price, 2))
                    if rate < 1:
                        put("breakeven_floor", round(fixed / (1 - rate), 2))

        if not sets:
            continue
        con.execute(f"UPDATE seller_skus SET {', '.join(sets)} WHERE tenant_id=? AND asin=?",
                    (*params, tenant_id, asin))
        before = {k: cur.get(k) for k in after}
        changed.append({"asin": asin, "before": before, "after": after})
    con.commit()
    log(f"[reconcile][t{tenant_id}] re-baselined {len(changed)}/{len(asins)} SKUs from live snapshots")
    return changed


def _own_store(con, tenant_id):
    """The seller's own Amazon storefront = the modal Buy Box owner across their PDP snapshots
    (a private-label seller holds the Buy Box on its own listings). Used to tell the seller's
    own offers apart from genuine third-party rivals."""
    rows = con.execute(
        "SELECT buybox_seller FROM keepa_snapshots WHERE tenant_id=? AND raw LIKE '%amazon_pdp%' "
        "AND buybox_seller IS NOT NULL AND buybox_seller<>'?'", (tenant_id,)).fetchall()
    if not rows:
        return None
    counts = {}
    for r in rows:
        s = r["buybox_seller"]
        counts[s] = counts.get(s, 0) + 1
    return max(counts, key=counts.get)


def drop_own_offers(con, tenant_id, log=print):
    """A seller's OWN storefront offer is not a competitor — remove it from competitor_offers so
    the 'N undercutting you' count reflects genuine third-party rivals only."""
    own = _own_store(con, tenant_id)
    if not own:
        return None
    con.execute("DELETE FROM competitor_offers WHERE tenant_id=? AND seller=?", (tenant_id, own))
    con.commit()
    log(f"[reconcile][t{tenant_id}] dropped own-store offers (seller={own!r}) — competitors only")
    return own


def reconcile_tenant(tenant_id, log=print):
    """Full path: pull live (Keepa + PDP), re-baseline seller_skus, drop own-store offers."""
    pulls = pull_live(tenant_id, log)
    con = db.connect()
    try:
        changed = rebaseline_seller_skus(con, tenant_id, log)
        own = drop_own_offers(con, tenant_id, log)
    finally:
        con.close()
    return {"pulls": pulls, "rebaselined": len(changed), "own_store_excluded": own, "changes": changed}
