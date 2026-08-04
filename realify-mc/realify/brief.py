"""Workspace Brief — the top-of-page summary (Opportunity $ / # SKUs / At Risk $ tiles) plus a
two-sentence narrative. Every number here is a plain aggregate over real rows: revenue/margin for
this window vs. the immediately-prior window of equal length (straight from seller_orders dates
— the same components api.kpis() sums), real Sum(exposure_inr) over open cards (excluding
api.FABRICATED_EXPOSURE card types — never sum a hard-coded constant as if it were computed), and
the real finding text of the single highest-exposure at-risk card. The narrative sentences are a
fixed template filled with those numbers — there is no LLM step here, unlike realify/headline.py's
optional Claude-phrasing path.

Money in this narrative is always $ with K/M/B scale, independent of the tenant's own country
profile (realify/country.py) — a Brief-specific display choice; currency localization everywhere
else in the app (cards, KPI substats) is untouched.

Lives in its own module, not api.py (already over the 400-line file cap enforced by
tests/test_file_length.py) — same reasoning as realify/actions.py.
"""
import datetime as dt
import re

from . import api, db
from .actions import _plain
from .repositories.card_repo import CardRepository
from .repositories.order_repo import OrderRepository
from .repositories.seller_repo import SellerRepository

_AT_RISK_SEV = ("crit", "act")
_EMDASH_RE = re.compile(r"\s*—\s*")
# Some card templates append a fixed "about <money>/mo at stake" clause
# (realify/pipeline/generate.py's `expph`), rendered in the tenant's own locale (e.g. ₹20K,
# $69.0K). Swapped here for the real exposure_inr figure formatted $K/M/B, so the Brief's own
# money mentions stay consistent even when the borrowed card text is locale-flavored. Cards
# without this exact clause are left untouched rather than guessing at a different template.
_STAKE_RE = re.compile(r"[₹$][\d,.]+\s*(?:cr|L|K|M|B)?/mo at stake", re.IGNORECASE)


def _fmt_usd(x):
    """$ + K/M/B, independent of tenant locale (see module docstring)."""
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "$0"
    sign = "-" if x < 0 else ""
    x = abs(x)
    if x >= 1e9:
        return f"{sign}${x / 1e9:.2f}B"
    if x >= 1e6:
        return f"{sign}${x / 1e6:.2f}M"
    if x >= 1e3:
        return f"{sign}${x / 1e3:.1f}K"
    return f"{sign}${x:,.0f}"


def _no_emdash(text):
    """Card finding/why text is authored with em dashes as a clause separator
    (realify/pipeline/generate.py); normalize to a comma so none leak into this plain-text
    narrative."""
    return _EMDASH_RE.sub(", ", text).rstrip(", ")


def _economics(rows, cogs_by_asin):
    """Sum(revenue, margin, units) over already-fetched order rows. margin here = gross -
    referral_fee - fba_fee - cogs — intentionally NOT the full CM1/CM2/CM3 (no ad spend, storage
    fees, payment-proc proxy): attributable ad spend isn't reliably date-sliceable into an
    arbitrary prior window for every tenant, and this only needs a directional, apples-to-apples
    MoM signal, not another margin variant to reconcile against the KPI cards."""
    rev = referral = fba = cogs_tot = units = 0.0
    for o in rows:
        u = o["units"] or 0
        rev += o["gross"] or 0; units += u
        referral += o["referral_fee"] or 0; fba += o["fba_fee"] or 0
        cogs_tot += cogs_by_asin.get(o["asin"], 0) * u
    margin = rev - referral - fba - cogs_tot
    margin_pct = (margin / rev * 100) if rev else None
    return dict(revenue=rev, margin=margin, margin_pct=margin_pct, units=units)


def _category_driver(rows_cur, rows_prior, cat_by_asin):
    """The one category responsible for most of the revenue delta between the two periods, or
    None if no category clearly stands out — never name a driver from a split, ambiguous delta."""
    def _by_cat(rows):
        out = {}
        for o in rows:
            c = cat_by_asin.get(o["asin"]) or "Uncategorized"
            out[c] = out.get(c, 0.0) + (o["gross"] or 0)
        return out
    cur, prior = _by_cat(rows_cur), _by_cat(rows_prior)
    if not cur and not prior:
        return None
    deltas = {c: cur.get(c, 0.0) - prior.get(c, 0.0) for c in set(cur) | set(prior)}
    total_delta = sum(deltas.values())
    top_cat, top_delta = max(deltas.items(), key=lambda kv: abs(kv[1]))
    if total_delta == 0 or abs(top_delta) < abs(total_delta) * 0.5:
        return None
    return top_cat


def _headline(revenue, mom_pct, margin_pts, driver, window):
    rev_s = _fmt_usd(revenue)
    if mom_pct is None:
        s = (f"Revenue is {rev_s} over the last {window} days; not enough order history yet "
             f"for a month-over-month comparison.")
    else:
        direction = "up" if mom_pct >= 0 else "down"
        s = f"Revenue is {rev_s} over the last {window} days, {direction} {abs(mom_pct)}% vs. the prior period"
        if margin_pts is not None:
            m_dir = "up" if margin_pts >= 0 else "down"
            s += f", with margin {m_dir} {abs(margin_pts)} points"
        s += f", driven mainly by {driver}." if driver else "."
    return _no_emdash(s)


def _detail(at_risk_cards):
    n = len(at_risk_cards)
    if n == 0:
        return "No SKUs are currently flagged at risk."
    plural = "s" if n != 1 else ""
    verb = "are" if n != 1 else "is"
    lead = f"{n} SKU{plural} {verb} currently flagged at risk"
    top = at_risk_cards[0]
    finding = _plain(top.get("finding"))
    exposure = top.get("exposure_inr")
    if exposure and finding:
        finding = _STAKE_RE.sub(f"{_fmt_usd(exposure)}/mo at stake", finding)
    if not finding:
        s = lead + "."
    else:
        asin = top.get("asin")
        who = f", the most exposed being {asin}" if asin else ""
        s = f"{lead}{who}: {finding}"
        if not s.endswith("."):
            s += "."
    return _no_emdash(s)


def compute_brief(tenant_id, window=30):
    con = db.connect()
    try:
        today = dt.date.today()
        since = (today - dt.timedelta(days=window)).isoformat()
        prior_since = (today - dt.timedelta(days=2 * window)).isoformat()

        cogs_by_asin = {r["asin"]: (r["cogs"] or 0) for r in
                        SellerRepository(con).select_columns(tenant_id, ["asin", "cogs"])}
        cat_by_asin = {r["asin"]: r["category"] for r in
                       SellerRepository(con).select_columns(tenant_id, ["asin", "category"])}

        orders = OrderRepository(con)
        rows_cur = orders.range_rows(tenant_id, since)
        rows_prior = orders.range_rows(tenant_id, prior_since, since)
        current = _economics(rows_cur, cogs_by_asin)
        prior = _economics(rows_prior, cogs_by_asin)

        revenue_mom_pct = margin_pts_mom = None
        if prior["revenue"] > 0:
            revenue_mom_pct = round((current["revenue"] - prior["revenue"]) / prior["revenue"] * 100, 1)
            if current["margin_pct"] is not None and prior["margin_pct"] is not None:
                margin_pts_mom = round(current["margin_pct"] - prior["margin_pct"], 1)
        driver = _category_driver(rows_cur, rows_prior, cat_by_asin)

        cards = CardRepository(con)
        opportunity = cards.sum_exposure_inr(tenant_id, ("opp",), api.FABRICATED_EXPOSURE)
        at_risk = cards.sum_exposure_inr(tenant_id, _AT_RISK_SEV, api.FABRICATED_EXPOSURE)
        sku_count = cards.count_distinct_skus(tenant_id)

        at_risk_cards = [c for c in cards.feed(tenant_id)
                          if c["severity"] in _AT_RISK_SEV and c["status"] != "done"
                          and c["card_type"] not in api.FABRICATED_EXPOSURE]
        at_risk_cards.sort(key=lambda c: -(c.get("exposure_inr") or 0))

        return {
            "opportunity": round(opportunity),
            "sku_count": sku_count,
            "at_risk": round(at_risk),
            "headline": _headline(current["revenue"], revenue_mom_pct, margin_pts_mom, driver, window),
            "detail": _detail(at_risk_cards),
        }
    finally:
        con.close()
