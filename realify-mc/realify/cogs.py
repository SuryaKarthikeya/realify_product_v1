"""COGS intake for CUSTOMER accounts — template, validation, and apply.

Customers never have synthesized economics, so COGS must be supplied. We give a
fixed template, validate it on upload, apply the valid rows, and return the rejects
(with reasons) so the caller can log them. Partial application is allowed: valid rows
go in, rejects are reported, the customer can re-upload corrections later.

Template columns:  sku, cogs, currency   (+ optional title)
Validation rejects: blank sku · non-numeric / zero / negative cogs · duplicate sku in
file · sku not present in the uploaded catalog · malformed currency.
"""
from .ingest import upload_parse as U
from . import db
from .repositories.seller_repo import SellerRepository
from .country import profile as _profile

TEMPLATE_HEADERS = ["sku", "cogs", "currency", "title"]
# Declared order = match priority (most specific first) — U._build_colmap tries aliases in
# list order, not by string length, so bare/generic tokens ('cogs', 'cost', 'title', 'name')
# must sit last or they'll shadow a more specific column that's also present in the file.
_ALIASES = {
    "sku":      ["sku", "seller sku", "msku", "asin", "item id", "product id", "internal sku"],
    "cogs":     ["cost of goods", "landed cost", "unit cost", "product cost", "cogs", "cost"],
    "currency": ["currency", "ccy", "curr"],
    "title":    ["product name", "item name", "title", "name"],
}


def template_csv(currency="INR"):
    """Downloadable starter template with two example rows."""
    return ("sku,cogs,currency,title\r\n"
            f"SKU-EXAMPLE-1,123.45,{currency},Example product one\r\n"
            f"SKU-EXAMPLE-2,67.80,{currency},Example product two\r\n")


def parse(filename, data):
    """Tolerant parse -> list of {sku, cogs_raw, currency, title}. Never raises."""
    try:
        headers, body = U.read_table(filename, data, _ALIASES)
    except Exception as e:
        return None, f"Could not read file: {e}"
    cmap = U._build_colmap(headers, _ALIASES)
    if "sku" not in cmap or "cogs" not in cmap:
        return None, "Template needs at least 'sku' and 'cogs' columns."
    rows = []
    for r in body:
        get = lambda k: (r[cmap[k]] if k in cmap and cmap[k] < len(r) else "")
        rows.append({"sku": str(get("sku")).strip(), "cogs_raw": get("cogs"),
                     "currency": str(get("currency")).strip().upper(),
                     "title": str(get("title")).strip()})
    return rows, None


def validate(rows, known_skus, default_currency="INR"):
    """Returns (valid, rejects). valid=[{sku,cogs,currency}], rejects=[{row,sku,reason}].
    known_skus: set of SKUs present in the catalog (asin or internal_sku). If empty, the
    catalog-match check is skipped (caller decides whether that's allowed)."""
    valid, rejects, seen = [], [], set()
    known = set(known_skus or [])
    for i, r in enumerate(rows or []):
        rownum = i + 2  # 1-based + header row
        sku = (r.get("sku") or "").strip()
        if not sku:
            rejects.append({"row": rownum, "sku": "", "reason": "missing SKU"}); continue
        try:
            import re as _re
            cleaned = _re.sub(r"[^0-9.\-]", "", str(r.get("cogs_raw") or "").strip())
            cogs = float(cleaned) if cleaned not in ("", "-", ".") else None
        except Exception:
            cogs = None
        if cogs is None:
            rejects.append({"row": rownum, "sku": sku, "reason": "COGS missing or not a number"}); continue
        if cogs <= 0:
            rejects.append({"row": rownum, "sku": sku, "reason": "COGS must be greater than 0"}); continue
        if sku in seen:
            rejects.append({"row": rownum, "sku": sku, "reason": "duplicate SKU in file"}); continue
        if known and sku not in known:
            rejects.append({"row": rownum, "sku": sku, "reason": "SKU not found in uploaded catalog"}); continue
        cur = r.get("currency") or default_currency
        if len(cur) != 3 or not cur.isalpha():
            rejects.append({"row": rownum, "sku": sku, "reason": f"invalid currency '{cur}'"}); continue
        seen.add(sku)
        valid.append({"sku": sku, "cogs": round(cogs, 2), "currency": cur.upper()})
    return valid, rejects


def known_skus(con, tenant_id):
    rows = SellerRepository(con).select_columns(tenant_id, ["asin", "internal_sku"])
    s = set()
    for r in rows:
        d = dict(r)
        if d.get("asin"): s.add(str(d["asin"]).strip())
        if d.get("internal_sku"): s.add(str(d["internal_sku"]).strip())
    return s


def apply(con, tenant_id, valid, prof=None):
    """Write COGS and recompute the deterministic economics that follow from price + COGS +
    the real referral %. FBA / ad / return costs stay NULL until their reports arrive, so
    margin here is 'before FBA/ads' — honest and improves as more reports are uploaded."""
    prof = prof or _profile("IN")
    rate = prof["referral_pct"]
    sellers = SellerRepository(con)
    applied = 0
    for v in valid:
        row = sellers.price_row_by_sku_or_asin(tenant_id, v["sku"])
        if not row:
            continue
        price = row.get("price")
        cogs = v["cogs"]
        if price:
            referral = round(price * rate, 2)
            net = round(price - cogs - referral, 2)          # before FBA/ads/returns
            margin = round(net / price * 100, 2) if price else None
            floor = round(cogs / (1 - rate), 2)              # covers cogs+referral; rises as fees added
            sellers.update_economics(tenant_id, v["sku"], cogs, referral, net, margin, floor)
        else:
            sellers.update_cogs(tenant_id, v["sku"], cogs)
        applied += 1
    con.commit()
    return applied
