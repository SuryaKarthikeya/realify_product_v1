"""Shopify report extractors (spec §5) — parse a recognized Shopify export DataFrame into the record
shapes the crosswalk (auto_map) and financial normalization (dedupe_records, inventory_allocation,
settle_orders) consume. Headers are normalised (lower/spaced) the same way the recognizer matches them.

Kept separate from report_ingest (which is near the 400-line cap and owns the Amazon extractors); money
parsing reuses report_ingest._num so currency/thousands handling is identical across channels.
"""
import pandas as pd

from .recognizer import _norm
from .report_ingest import _num


def _cols(df):
    return df.rename(columns={c: _norm(c) for c in df.columns})


def _s(v):
    s = "" if v is None else str(v).strip()
    return "" if s.lower() in ("nan", "none") else s


def _get(row, *names):
    for n in names:
        if n in row and pd.notna(row[n]):
            return row[n]
    return None


def _numv(v):
    x = _num(pd.Series([v]))[0]
    return None if pd.isna(x) else round(float(x), 2)


def products(df):
    """SHOP_PRODUCTS → [{variant_id, sku, handle, cost, price}] (cost per item = seller COGS)."""
    df = _cols(df)
    out = []
    for _, r in df.iterrows():
        sku = _s(_get(r, "variant sku", "sku"))
        out.append({"variant_id": _s(_get(r, "variant id")), "sku": sku, "handle": _s(r.get("handle")),
                    "cost": _numv(r.get("cost per item")), "price": _numv(_get(r, "variant price", "price"))})
    return out


def orders(df):
    """SHOP_ORDERS → per line-item [{order_name, lineitem_id, sku, qty, financial_status,
    fulfillment_status}]. lineitem_id is a stable position within the order (Shopify has no line id), so
    a re-export of the same order dedups identically. The order Name is forward-filled across the
    continuation rows Shopify leaves blank."""
    df = _cols(df)
    out, seq, last_name = [], {}, ""
    for _, r in df.iterrows():
        name = _s(r.get("name")) or last_name
        if not name:
            continue
        last_name = name
        i = seq.get(name, 0)
        seq[name] = i + 1
        out.append({"order_name": name, "lineitem_id": "%s#%d" % (name, i),
                    "sku": _s(r.get("lineitem sku")), "qty": _numv(r.get("lineitem quantity")),
                    "financial_status": _s(r.get("financial status")),
                    "fulfillment_status": _s(r.get("fulfillment status"))})
    return out


def payouts(df):
    """SHOP_PAYOUTS → [{transaction_id, type, fee, net, payout_date, order_id}] (settled net-of-fee)."""
    df = _cols(df)
    out = []
    for idx, r in df.iterrows():
        out.append({"transaction_id": _s(_get(r, "transaction id", "id")) or ("txn#%d" % idx),
                    "type": _s(r.get("type")), "fee": _numv(r.get("fee")), "net": _numv(r.get("net")),
                    "payout_date": _s(r.get("payout date")), "order_id": _s(_get(r, "order", "order name"))})
    return out


def inventory(df):
    """SHOP_INVENTORY → [{sku, location, on_hand}] (Available OR On hand)."""
    df = _cols(df)
    out = []
    for _, r in df.iterrows():
        out.append({"sku": _s(r.get("sku")), "location": _s(r.get("location")),
                    "on_hand": _numv(_get(r, "on hand", "available"))})
    return out
