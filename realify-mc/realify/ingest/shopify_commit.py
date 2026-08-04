"""Shopify commit — write recognized Shopify reports into the tenant's own-data (spec §5).

Parses products / orders / inventory, resolves the SKU crosswalk (persisting it), and writes seller_skus
+ COGS provenance for Shopify-ONLY SKUs (new rows keyed by the SKU). A SKU that maps to an EXISTING
Amazon SKU is recorded in the crosswalk (the identity link) but does NOT overwrite Amazon-derived
economics — the cross-channel number merge belongs in channel_economics and is a separate step, so this
never corrupts the Amazon rows the dashboard already reads. MCF inventory is not double-counted (the
Amazon-fulfilment pool is Amazon-owned; those SKUs contribute demand, not a Shopify balance)."""
from . import recognizer as rz, extractors_shopify as ex, crosswalk as xw
from .normalize_finance import inventory_allocation
from .. import topology
from ..repositories.seller_repo import SellerRepository
from ..repositories.provenance_repo import ProvenanceRepository
from ..repositories.topology_repo import SkuCrosswalkRepository


def _by_type(tables):
    out = {}
    for _n, df in tables:
        out.setdefault(rz.detect_report_type(df.columns), []).append(df)
    return out


def commit(con, tid, tables, topo=None, parity="MOSTLY", store_id=""):
    """Write the Shopify tables into seller_skus (+ crosswalk + COGS provenance). Caller commits the
    transaction. `topo` (the tenant's persisted topology) sources sku_parity + store_id when given.
    Returns a summary; Shopify-only SKUs become new rows, mapped SKUs stay crosswalk-only."""
    if topo is not None:
        r = topo.resolved.get("sku_parity")
        parity = (r.effective if r else None) or parity
        _sc = [c for c in topo.channels if c.get("platform") == "SHOPIFY"]
        store_id = (_sc[0].get("account_ref") or "") if _sc else store_id
    bt = _by_type(tables)
    products = [r for df in bt.get("SHOP_PRODUCTS", []) for r in ex.products(df)]
    orders = [r for df in bt.get("SHOP_ORDERS", []) for r in ex.orders(df)]
    inv = [r for df in bt.get("SHOP_INVENTORY", []) for r in ex.inventory(df)]
    if not (products or orders or inv):
        return {"shopify_skus": 0, "crosswalk": 0, "unmapped": 0}
    seller = SellerRepository(con)
    amazon_skus = {r["internal_sku"] for r in seller.all(tid) if r.get("internal_sku")}
    entries, summary, arm = xw.auto_map(products, amazon_skus, store_id=store_id, parity=parity)
    cw = SkuCrosswalkRepository(con)
    canon = {}
    for e in entries:
        cw.upsert(tid, "shopify", e["external_sku"], e["canonical_sku_id"], e["status"],
                  store_id=e["store_id"], external_variant_id=e["external_variant_id"])
        if e["canonical_sku_id"]:
            canon[e["external_sku"]] = e["canonical_sku_id"]

    def _canon(sku):
        return canon.get(sku) or (sku or None)

    okeys = topology.by_id("SHOP_ORDERS").natural_keys
    booked = {}
    for o in xw.dedupe_records(orders, okeys):                  # record-level dedup: re-exports don't double-count
        cid = _canon(o.get("sku"))
        if cid:
            booked[cid] = booked.get(cid, 0.0) + float(o.get("qty") or 0)
    prod = {}
    for p in products:
        cid = _canon(p.get("sku"))
        if cid:
            prod[cid] = p
    own = inventory_allocation(inv)["shopify_own"] if inv else {}
    own = {_canon(s): v for s, v in own.items() if _canon(s)}
    prov = ProvenanceRepository(con)
    written = 0
    for cid in set(prod) | set(booked) | set(own):
        if cid in amazon_skus:                                  # mapped to Amazon → link only, don't overwrite
            continue
        row = {"internal_sku": cid, "asin": cid, "channel": "shopify"}
        p = prod.get(cid)
        if p:
            if p.get("cost") is not None:
                row["cogs"] = p["cost"]
            if p.get("price") is not None:
                row["price"] = p["price"]
            if p.get("handle"):
                row["title"] = p["handle"]
        if booked.get(cid):
            row["units_month"] = int(round(booked[cid]))
        if cid in own:
            row["stock_on_hand"] = int(round(own[cid]))
        seller.upsert_full(tid, row)
        if p and p.get("cost") is not None:
            prov.set(tid, cid, "cogs", "seller", "shopify_products", p["cost"])
        written += 1
    return {"shopify_skus": written, "crosswalk": len(entries),
            "unmapped": summary["unmapped_blank"] + summary["parked_bundle"] + summary["unmatched"],
            "reconcile_armed": arm}
