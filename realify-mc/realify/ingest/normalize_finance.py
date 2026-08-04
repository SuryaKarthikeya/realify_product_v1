"""Financial normalization for cross-channel onboarding (spec §5).

The MCF shared-inventory rule: Multi-Channel Fulfilment means Amazon and Shopify draw from ONE physical
FBA pool, so we must NOT sum Amazon FBA on-hand + the Shopify "Amazon Fulfillment" location (that
double-counts). Shopify contributes DEMAND for MCF SKUs, not a separate inventory balance; the MCF
fulfilment fee lives on the Amazon side (AMZ_MCF_FEES) — absent from every Shopify file — so Shopify
margin for an MCF SKU stays PARTIAL until that fee arrives.

Booked vs settled: SHOP_ORDERS is booked (reported), SHOP_PAYOUTS is settled net-of-fee (actual). They
COEXIST and join on order id; an order with no payout yet is NOT-YET-PAID-OUT (a state, not an error —
mirrors Amazon settled/unsettled). Actual wins where present (the existing _BASIS_RANK precedence).
"""
AMAZON_FULFILLMENT_LOCATION = "amazon fulfillment"          # normalized form of the Shopify location name
SETTLED, NOT_YET_PAID_OUT = "SETTLED", "NOT_YET_PAID_OUT"


def _norm(s):
    return " ".join(str(s or "").strip().lower().split())


def inventory_allocation(shopify_inv, amazon_location=AMAZON_FULFILLMENT_LOCATION):
    """Split Shopify inventory rows [{sku, location, on_hand|available}] into own-pool on-hand vs the
    shared Amazon (MCF) pool. Units at the Amazon-fulfilment location are Amazon-owned — excluded from
    Shopify's own on-hand; their SKUs are flagged MCF (they draw from the shared FBA pool)."""
    own, mcf_skus = {}, set()
    for r in shopify_inv:
        sku = str(r.get("sku") or "").strip()
        if not sku:
            continue
        on_hand = float(r.get("on_hand") if r.get("on_hand") is not None else (r.get("available") or 0))
        if _norm(r.get("location")) == _norm(amazon_location):
            mcf_skus.add(sku)                                # shared FBA pool — NOT Shopify's own balance
        else:
            own[sku] = own.get(sku, 0.0) + on_hand
    return {"shopify_own": own, "mcf_skus": mcf_skus, "mcf_detected": bool(mcf_skus)}


def combined_on_hand(sku, amazon_fba_on_hand, shopify_own_on_hand, mcf_skus):
    """Physical on-hand for a SKU across channels. For an MCF SKU it's the single Amazon pool (never
    summed with the Shopify 'Amazon Fulfillment' line). For a self/3PL SKU the pools are genuinely
    separate, so they add."""
    if sku in mcf_skus:
        return float(amazon_fba_on_hand or 0)                # one pool — do NOT add Shopify units
    return float(amazon_fba_on_hand or 0) + float(shopify_own_on_hand or 0)


def mcf_margin_status(sku, mcf_skus, has_mcf_fee):
    """Shopify margin for an MCF SKU is PARTIAL until AMZ_MCF_FEES lands (the fulfilment cost is on the
    Amazon side, absent from every Shopify file)."""
    if sku in mcf_skus and not has_mcf_fee:
        return "partial"
    return "complete"


def settle_orders(booked, payouts, on="order_id"):
    """Join booked orders (SHOP_ORDERS) to settled payouts (SHOP_PAYOUTS) on order id. Matched → settled
    net (actual). Unmatched → NOT_YET_PAID_OUT (a state, not an error). Booked (reported) and settled
    (actual) coexist; the caller writes both bases and actual wins where present."""
    net_by_order = {}
    for p in payouts:
        oid = str(p.get(on) or "").strip()
        if oid:
            net_by_order[oid] = net_by_order.get(oid, 0.0) + float(p.get("net") or 0)
    out = []
    for b in booked:
        oid = str(b.get(on) or "").strip()
        settled = net_by_order.get(oid)
        out.append({**b, "settled_net": settled,
                    "state": SETTLED if settled is not None else NOT_YET_PAID_OUT})
    return out
