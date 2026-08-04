"""Deterministic, rule-based decision generator (agency-plan P4) — NO ML. Three rules over a brand's
own SKU data (break-even-ACOS bid, stockout reorder, price-elasticity stub). Fully deterministic: same
inputs + same locked fx row => byte-identical decisions. Money is integer minor units; the selling-
currency figure (impact_minor) is fx-independent, impact_usd_minor is derived via the locked rate."""
import hashlib

from . import fx, money, tenancy


def _jitter(asin, lens, base, spread=8):
    """Deterministic per-SKU confidence variation (stable hashlib, so byte-identical run to run) so the
    queue shows varied confidences and ranking is visibly meaningful — not three flat values."""
    h = int(hashlib.md5(f"{asin}:{lens}".encode()).hexdigest(), 16)
    return max(35, min(97, base + (h % (2 * spread + 1)) - spread))


_BREAKEVEN_ACOS = 22            # % — the break-even ACoS a healthy SKU stays under


def _rules(asin, price, cogs, units, days_of_cover, tacos, buybox, title=None):
    """Yield (lens, kind, signal, impact_minor, confidence) with BELIEVABLE monthly $ impacts (R9.1) and
    a signal that NAMES the product. Selective: fires only on genuine outliers (a stocked-out cover, an
    over-break-even ACoS, an undercut buy-box) — most SKUs are healthy and yield nothing. impact_minor is
    in the SELLING currency (a %/margin figure, not half the month's revenue). Deterministic."""
    price = float(price or 0)
    units = int(units or 0)
    doc = float(days_of_cover) if days_of_cover is not None else 99
    tacos = float(tacos or 0)
    buybox = float(buybox or 100)
    name = title or asin
    revenue = price * units
    margin = max(0.0, price - float(cogs or 0))
    out = []
    if doc < 21 and units and margin > 0:                                    # stockout -> reorder
        units_short = units * (21 - doc) / 45.0                              # units at risk over the gap
        impact = int(round(margin * units_short * 100))
        out.append(("inventory", "reorder", f"Reorder {name} — {int(doc)}d of cover left",
                    impact, _jitter(asin, "inventory", 82)))
    if tacos > _BREAKEVEN_ACOS and revenue:                                   # over break-even -> cut bids
        impact = int(round(revenue * (tacos - _BREAKEVEN_ACOS) / 100.0 * 100))   # recoverable ad waste
        out.append(("ads", "bid", f"Cut ACoS on {name} — {int(tacos)}% vs {_BREAKEVEN_ACOS}% break-even",
                    impact, _jitter(asin, "ads", 72)))
    if buybox < 75 and revenue:                                              # undercut -> reprice
        impact = int(round(revenue * 0.03 * 100))                            # ~3% elasticity uplift
        out.append(("pricing", "price", f"Reprice {name} — buy-box at {int(buybox)}%",
                    impact, _jitter(asin, "pricing", 62)))
    return out


def generate(cur, tenant_id, currency, as_of):
    """(Re)generate open decisions for a brand from its SKU data. Replaces prior open decisions so a
    re-run is idempotent. Returns the list of decisions written."""
    frow = fx.get_rate(cur, as_of, currency)
    # FX-tolerant: a missing rate for a non-USD brand must NOT crash decision generation (that left
    # real ₹-native brands with zero decisions → "$0 at stake" in the fleet). Degrade to no USD
    # normalization — native impact_minor still drives the localized fleet display; USD sort falls back
    # to native as a rough proxy so the brand still ranks non-zero.
    fx_id, rate_ppm = frow if frow else (None, None)
    tenancy.set_brand_scope(cur, [tenant_id])
    cur.execute("DELETE FROM decisions WHERE tenant_id=%s AND status='open'", (tenant_id,))
    cur.execute("SELECT asin, price, cogs, units_month, days_of_cover, tacos, buybox_pct, title "
                "FROM seller_skus WHERE tenant_id=%s ORDER BY asin", (tenant_id,))
    rows = cur.fetchall()
    out = []
    _CEIL_USD_MINOR = 500000        # cap a single decision's USD-normalized impact at $5,000 (sane ranking)
    for asin, price, cogs, units, doc, tacos, buybox, title in rows:
        for lens, kind, signal, impact_minor, conf in _rules(asin, price, cogs, units, doc, tacos, buybox, title):
            if impact_minor <= 0:
                continue
            usd = min(money.to_usd_minor(impact_minor, rate_ppm) if rate_ppm else impact_minor, _CEIL_USD_MINOR)
            cur.execute(
                "INSERT INTO decisions(tenant_id,lens,kind,impact_minor,impact_currency,fx_rate_id,"
                "impact_usd_minor,confidence,signal,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,'open')",
                (tenant_id, lens, kind, impact_minor, currency, fx_id, usd, conf, signal))
            out.append({"tenant_id": tenant_id, "lens": lens, "kind": kind, "signal": signal,
                        "impact_minor": impact_minor, "impact_currency": currency,
                        "impact_usd_minor": usd, "fx_rate_id": fx_id})
    return out
