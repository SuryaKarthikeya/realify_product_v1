"""Real per-channel report parsers (roadmap item: 'real CSV report parsers per channel').

The upload grid lists ~7 reports per channel across 5 channels. Rather than 33 bespoke
parsers, we classify each report by the CANONICAL TABLE it feeds, then run one tolerant
parser per kind. Uploading a real report swaps that channel's synthetic values for real
data in the same tables the synthesizer writes — so every downstream detector keeps working
unchanged. Column matching is fuzzy (reuses the upload_parse matcher), so Amazon /
Shopify / Walmart / eBay / TikTok exports with different headers all map.

Kinds and what they update (matched to existing SKUs by ASIN or internal SKU):
  catalog        -> seller_skus.price/title/category, channel_listings.price
  sales_traffic  -> seller_skus.buybox_pct (+ traffic rows: sessions/views/conversion)
  inventory      -> seller_skus.stock_on_hand + recomputed days_of_cover
  returns        -> seller_skus.returns_rate
  settlement     -> settlements rows (gross/fees/payout/reserve)
  orders         -> seller_orders rows
"""
from . import upload_parse as U
from .. import db
from ..repositories.seller_repo import SellerRepository
from ..repositories.order_repo import OrderRepository
from ..repositories.fact_repos import TrafficRepository, SettlementRepository

# ---- classify a report name into a canonical kind (ordered: most specific first) ----
def classify(report):
    r = (report or "").lower()
    def has(*ks): return any(k in r for k in ks)
    if has("return", "refund", "after-sales", "after sales"):     return "returns"
    if has("settlement", "payout", "income", "finances", "transaction"): return "settlement"
    if has("inventory", "on-hand", "on hand", "wfs", "fbt", "storage", "aged"): return "inventory"
    if has("order"):                                              return "orders"
    if has("listing", "products export", "product export", "full-spec", "catalog"): return "catalog"
    if has("sales", "traffic", "session", "conversion", "performance", "buy box", "buybox", "analytics"):
        return "sales_traffic"
    return "sales_traffic"

# ---- per-kind column aliases (canonical field -> header substrings, declared order =
# priority, most specific/correct first — matches classify()'s "ordered: most specific
# first" convention above. 'fnsku' sits last in "sku": it's an Amazon-internal fulfillment
# ID, never the identifier a tenant's known SKUs/ASINs are keyed by, so a file carrying
# both an asin/sku column AND an fnsku column (every real FBA report does) must bind to
# the former, not whichever alias string happens to be longest.) ----
A = {
    "sku":      ["child asin", "asin", "msku", "seller sku", "sku", "item id", "product id", "listing id", "item number", "fnsku"],
    "title":    ["product name", "item name", "title", "name"],
    "price":    ["selling price", "sale price", "item price", "buy box price", "your price", "price"],
    "category": ["product type", "category", "dept"],
    "units":    ["units ordered", "units sold", "quantity sold", "ordered units", "units", "quantity", "qty"],
    "sessions": ["sessions total", "sessions", "visits"],
    "page_views":["page views", "pageviews", "views", "impressions"],
    "conversion":["unit session percentage", "conversion rate", "conversion", "cvr", "unit session"],
    "buybox":   ["featured offer percentage", "buy box percentage", "buy box %", "buybox", "buy box", "featured offer"],
    "stock":    ["afn fulfillable", "fulfillable quantity", "available quantity", "quantity available",
                 "on hand", "on-hand", "sellable", "ending warehouse", "available", "in stock", "stock"],
    "returns":  ["units returned", "returned units", "return quantity", "return qty", "returns", "refunds", "refunded units"],
    "gross":    ["product charges", "principal", "item price", "gross sales", "gross", "sales", "revenue", "total sales"],
    "fees":     ["selling fees", "fba fees", "commission", "total fees", "fees", "fee"],
    "payout":   ["net proceeds", "payout", "net", "total", "deposit"],
    "reserve":  ["reserve", "withheld"],
    "order_id": ["amazon order id", "order id", "order-id", "transaction id", "order number"],
    "date":     ["return date", "settlement date", "purchase date", "order date", "date"],
}

def _matrix_rows(headers, body):
    """Yield dicts keyed by canonical field for each non-empty row."""
    cm = U._build_colmap(headers, A)
    out = []
    for r in body:
        def g(f):
            i = cm.get(f)
            return r[i] if (i is not None and i < len(r)) else None
        sku = (str(g("sku") or "")).strip()
        if not sku or sku.lower() in ("asin", "sku", "nan"):
            continue
        out.append({k: g(k) for k in A}, )
        out[-1]["sku"] = sku
    return out, cm

def _known_skus(con, tid):
    rows = SellerRepository(con).select_columns(tid, ["asin", "internal_sku", "velocity_day", "units_month"])
    by = {}
    for r in rows:
        d = dict(r)
        if d.get("asin"): by[str(d["asin"])] = d
        if d.get("internal_sku"): by[str(d["internal_sku"])] = d
    return by

def ingest_report(con, tenant_id, channel, report, filename, data, log=print):
    kind = classify(report)
    headers, body = U.read_table(filename, data, A)
    if not headers:
        return {"ok": False, "kind": kind, "error": "could not read file"}
    rows, cm = _matrix_rows(headers, body)
    known = _known_skus(con, tenant_id)
    applied = 0; matched = 0; unmatched = 0
    now = db.now_iso()

    def target(sku):
        k = known.get(str(sku))
        return (k["asin"] if k and k.get("asin") else None, k)

    if kind == "catalog":
        for r in rows:
            asin, k = target(r["sku"])
            if not k: unmatched += 1; continue
            price = U._to_float(r.get("price"))
            fields = {}
            if price > 0: fields["price"] = price
            if (r.get("title") or "").strip(): fields["title"] = r["title"].strip()
            if (r.get("category") or "").strip(): fields["category"] = r["category"].strip()
            if fields:
                SellerRepository(con).update_fields_by_sku_or_asin(tenant_id, r["sku"], fields)
                applied += 1
            matched += 1

    elif kind == "sales_traffic":
        TrafficRepository(con).delete_by_channel_date(tenant_id, channel, now[:10])
        for r in rows:
            asin, k = target(r["sku"])
            if not k: unmatched += 1; continue
            matched += 1
            bb = U._to_float(r.get("buybox")); conv = U._to_float(r.get("conversion"))
            sess = int(U._to_float(r.get("sessions"))); pv = int(U._to_float(r.get("page_views")))
            isku = k.get("internal_sku") or r["sku"]
            TrafficRepository(con).insert(tenant_id, channel, isku, now[:10], sess, pv,
                                          round(conv, 2) if conv else None, round(bb, 1) if bb else None)
            if bb > 0:
                SellerRepository(con).update_fields_by_sku_or_asin(tenant_id, r["sku"], {"buybox_pct": round(bb)}); applied += 1

    elif kind == "inventory":
        for r in rows:
            asin, k = target(r["sku"])
            if not k: unmatched += 1; continue
            matched += 1
            stock = U._to_float(r.get("stock"))
            if stock <= 0: continue
            vel = float(k.get("velocity_day") or 0) or 0.0
            doc = round(stock / vel, 1) if vel > 0 else None
            if doc is not None:
                SellerRepository(con).update_fields_by_sku_or_asin(tenant_id, r["sku"], {"stock_on_hand": int(stock), "days_of_cover": doc})
            else:
                SellerRepository(con).update_fields_by_sku_or_asin(tenant_id, r["sku"], {"stock_on_hand": int(stock)})
            applied += 1

    elif kind == "returns":
        # aggregate returned units per sku, then rate = returns / monthly units
        agg = {}
        for r in rows:
            agg[r["sku"]] = agg.get(r["sku"], 0) + U._to_float(r.get("returns") or r.get("units") or 1)
        for sku, ret in agg.items():
            asin, k = target(sku)
            if not k: unmatched += 1; continue
            matched += 1
            um = float(k.get("units_month") or 0)
            rate = round(min(100.0, ret / um * 100), 1) if um > 0 else round(ret, 1)
            SellerRepository(con).update_fields_by_sku_or_asin(tenant_id, sku, {"returns_rate": rate}); applied += 1

    elif kind == "settlement":
        SettlementRepository(con).delete_by_channel(tenant_id, channel)
        for r in rows:
            asin, k = target(r["sku"])
            if k: matched += 1
            else: unmatched += 1
            gross = U._to_float(r.get("gross")); fees = U._to_float(r.get("fees"))
            payout = U._to_float(r.get("payout")) or round(gross - fees, 2)
            SettlementRepository(con).insert(tenant_id, channel, (k.get("internal_sku") if k else None) or r["sku"],
                         (str(r.get("order_id") or "")).strip(), (str(r.get("date") or now[:10])),
                         gross, fees, payout, U._to_float(r.get("reserve")))
            applied += 1

    elif kind == "orders":
        OrderRepository(con).delete_by_channel(tenant_id, channel)
        for r in rows:
            asin, k = target(r["sku"])
            if k: matched += 1
            else: unmatched += 1
            units = int(U._to_float(r.get("units")) or 1); gross = U._to_float(r.get("gross"))
            OrderRepository(con).insert_imported(tenant_id, (str(r.get("order_id") or "")).strip(), asin,
                         (str(r.get("date") or now[:10])), units, gross, channel,
                         (k.get("internal_sku") if k else None) or r["sku"])
            applied += 1

    con.commit()
    log(f"[ingest] {channel}/{report} kind={kind} parsed={len(rows)} matched={matched} applied={applied} unmatched={unmatched}")
    return {"ok": True, "kind": kind, "parsed": len(rows), "matched": matched,
            "applied": applied, "unmatched": unmatched}
